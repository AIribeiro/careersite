"""Send owner-approved Advisory service access emails via existing Supabase Auth.

Both Library and Advisory registration already use /auth/v1/otp. We use this
same channel for an existing, verified account after the owner approves a
service. Supabase Auth emails are magic links / OTPs, not customizable
per-event transactional emails; the member portal shows exact service access.
"""
from __future__ import annotations

from urllib.parse import urlencode

from page_reader_native import _callback_origin
from reader_membership import EMAIL
from site_cms import ANALYTICS_URL, _request_json, _rest_url

SERVICE_NAMES = {
    "scorecard": "AI Portfolio Prioritization Scorecard",
    "rollout": "Enterprise AI Rollout Readiness Advisor",
}


def _send_using_supabase_auth(recipient: str, service: str) -> str:
    """Use existing Auth mailer; never create accounts or fake login emails."""
    email = str(recipient or "").strip().lower()
    if service not in SERVICE_NAMES or not EMAIL.fullmatch(email):
        raise ValueError("Invalid Advisory service or recipient")
    callback = _callback_origin("advisory-access") + "/?page=advisory-access"
    url = ANALYTICS_URL.rstrip("/") + "/auth/v1/otp?" + urlencode({
        "redirect_to": callback,
    })
    _request_json(
        "POST", url,
        payload={"email": email, "create_user": False},
        timeout=15,
    )
    # Means HTTP acceptance, not inbox delivery.
    return "supabase-auth-accepted"


def deliver_approval_notice(token: str, notification_id: str) -> dict:
    """Claim an approved event and send one Supabase Auth account-access email."""
    if not notification_id:
        raise ValueError("Notification ID required")
    claimed = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_email_claim_v1"),
        token=token, payload={"p_id": notification_id}, timeout=12,
    )
    if not isinstance(claimed, dict) or str(claimed.get("id")) != notification_id:
        raise RuntimeError("Notification claim could not be confirmed")
    if not claimed.get("claimed"):
        return {"state": str(claimed.get("state") or "pending"),
                "id": notification_id}
    sent = False
    provider_id = ""
    category = ""
    try:
        provider_id = _send_using_supabase_auth(
            str(claimed["to"]), str(claimed["service_key"])
        )
        sent = True
    except RuntimeError as exc:
        err = str(exc).lower()
        category = "supabase_auth_rate_limited" if (
            "rate limit" in err or "429" in err
        ) else "supabase_auth_rejected"
    except (TimeoutError, ConnectionError, OSError):
        category = "supabase_auth_transport_error"
    except (ValueError, KeyError):
        category = "invalid_notification"
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_email_finish_v1"),
        token=token,
        payload={
            "p_id": notification_id, "p_sent": sent,
            "p_provider_message_id": provider_id,
            "p_error_category": category,
        }, timeout=12,
    )
    if not isinstance(result, dict) or str(result.get("id")) != notification_id:
        raise RuntimeError("Notification outcome could not be confirmed")
    return {"state": result.get("state"), "id": notification_id,
            "error_category": category, "provider_message_id": provider_id}


def approval_notice_message(result: dict) -> str:
    status = str(result.get("state") or "")
    if status == "sent":
        return (
            "Access approved. Supabase Auth accepted the existing account-access "
            "email request. It uses the current login email template."
        )
    if status == "sending":
        return "The Supabase Auth access email is still being processed."
    if result.get("error_category") == "supabase_auth_rate_limited":
        return (
            "Access approved, but Supabase Auth rate-limited the access email. "
            "Retry later; the grant is unchanged."
        )
    return (
        "Access approved, but Supabase Auth did not accept the access email. "
        "Retry below; the service grant is unchanged."
    )
