"""Private owner-triggered transactional emails for Advisory service approvals.

A database-approved grant creates one durable notification event. Sending uses
Resend's idempotency key (or the configured Resend SMTP credentials). These
messages are service-access confirmations, never editorial subscriptions.
No secret, credential, or arbitrary recipient comes from a browser control.
"""
from __future__ import annotations

from email.message import EmailMessage
from html import escape
import json
import os
import smtplib
import ssl
from urllib import error, request

import streamlit as st

from site_cms import _request_json, _rest_url

FROM_ADDRESS = "advisory@jairribeiro.com"
PORTAL_URL = "https://jairribeiro.com/?page=advisory-access"
SERVICE_NAMES = {
    "scorecard": "AI Portfolio Prioritization Scorecard",
    "rollout": "Enterprise AI Rollout Readiness Advisor",
}


def _secret(key: str) -> str:
    """Read server-only environment / Streamlit secrets, never return to clients."""
    value = str(os.environ.get(key) or "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(key) or "").strip()
    except (KeyError, AttributeError, OSError, FileNotFoundError):
        return ""


def mail_transport_ready() -> bool:
    """Check whether a server-side transactional sender is configured."""
    return bool(_secret("RESEND_API_KEY") or _secret("RESEND_SMTP_PASSWORD")
                or _secret("SMTP_PASSWORD"))


def _message(service: str) -> tuple[str, str, str]:
    if service not in SERVICE_NAMES:
        raise ValueError("Unsupported Advisory email service")
    name = SERVICE_NAMES[service]
    subject = f"Your {name} access is approved | Jair Ribeiro Advisory"
    plain = (
        f"Your individual access to {name} is now approved.\n\n"
        "You can sign in to your Advisory account using your existing email "
        "and password to open the service:\n"
        f"{PORTAL_URL}\n\n"
        "The service is available on a complimentary, individually approved basis. "
        "This access notice does not create a paid engagement or subscribe you "
        "to marketing emails.\n\n"
        "For help, reply to advisory@jairribeiro.com.\n\n"
        "Jair Ribeiro\nExecutive AI & Data Advisory"
    )
    html = (
        '<div style="max-width:620px;margin:auto;color:#15263d;'
        'font-family:Arial,sans-serif;line-height:1.65">'
        '<p style="font-size:13px;color:#637083;font-weight:bold">JAIR RIBEIRO · ADVISORY</p>'
        "<h2>Your service access is approved.</h2>"
        f"<p>You now have individual access to <strong>{escape(name)}</strong>.</p>"
        "<p>Sign in with your existing Advisory account to open the service.</p>"
        f'<p><a href="{PORTAL_URL}" style="display:inline-block;background:#173b64;'
        'color:white;padding:12px 20px;border-radius:6px;text-decoration:none">'
        "Open your Advisory account</a></p>"
        "<p>This is a complimentary access confirmation, not a marketing subscription "
        "or a paid engagement.</p>"
        f'<p style="font-size:13px">Questions? <a href="mailto:{FROM_ADDRESS}">'
        f"{FROM_ADDRESS}</a></p>"
        "<p>Jair Ribeiro<br>Executive AI &amp; Data Advisory</p></div>"
    )
    return subject, plain, html


def _send_using_resend(notification_id: str, recipient: str, service: str,
                       api_key: str) -> str:
    subject, plain, html = _message(service)
    payload = {
        "from": f"Jair Ribeiro Advisory <{FROM_ADDRESS}>",
        "to": [recipient],
        "reply_to": FROM_ADDRESS,
        "subject": subject,
        "text": plain,
        "html": html,
    }
    req = request.Request(
        "https://api.resend.com/emails", method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Idempotency-Key": "advisory-approval/" + notification_id,
        },
    )
    with request.urlopen(req, timeout=18) as response:
        body = json.loads(response.read(10000).decode("utf-8"))
    if not isinstance(body, dict) or not body.get("id"):
        raise RuntimeError("Provider did not confirm the message")
    return str(body["id"])[:180]


def _send_using_smtp(recipient: str, service: str, password: str) -> str:
    subject, plain, html = _message(service)
    username = _secret("RESEND_SMTP_USERNAME") or _secret("SMTP_USERNAME") or "resend"
    host = _secret("RESEND_SMTP_HOST") or _secret("SMTP_HOST") or "smtp.resend.com"
    port = int(_secret("RESEND_SMTP_PORT") or _secret("SMTP_PORT") or "465")
    msg = EmailMessage()
    msg["From"] = f"Jair Ribeiro Advisory <{FROM_ADDRESS}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Reply-To"] = FROM_ADDRESS
    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=18,
                              context=ssl.create_default_context()) as connection:
            connection.login(username, password)
            connection.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=18) as connection:
            connection.starttls(context=ssl.create_default_context())
            connection.login(username, password)
            connection.send_message(msg)
    # SMTP acceptance does not prove inbox delivery.
    return "smtp-accepted"


def _send_provider(notification_id: str, recipient: str, service: str) -> str:
    if service not in SERVICE_NAMES or "@" not in recipient:
        raise ValueError("Invalid service notification record")
    api_key = _secret("RESEND_API_KEY")
    if api_key:
        return _send_using_resend(notification_id, recipient, service, api_key)
    smtp_pass = _secret("RESEND_SMTP_PASSWORD") or _secret("SMTP_PASSWORD")
    if smtp_pass:
        return _send_using_smtp(recipient, service, smtp_pass)
    raise RuntimeError("mail_configuration_missing")


def deliver_approval_notice(token: str, notification_id: str) -> dict:
    """Claim and dispatch one pending event; report delivery honestly."""
    if not notification_id:
        raise ValueError("Notification ID required")
    claimed = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_email_claim_v1"),
        token=token, payload={"p_id": notification_id}, timeout=12,
    )
    if not isinstance(claimed, dict) or str(claimed.get("id")) != notification_id:
        raise RuntimeError("Mail claim could not be confirmed")
    if not claimed.get("claimed"):
        return {"state": str(claimed.get("state") or "pending"), "id": notification_id}
    sent = False
    provider_id = ""
    category = ""
    try:
        provider_id = _send_provider(
            notification_id, str(claimed["to"]), str(claimed["service_key"])
        )
        sent = True
    except error.HTTPError as exc:
        category = "provider_http_" + str(exc.code)
    except (TimeoutError, ConnectionError, OSError, smtplib.SMTPException):
        category = "provider_transport_error"
    except RuntimeError as exc:
        category = (
            "configuration_missing" if str(exc) == "mail_configuration_missing"
            else "provider_unconfirmed"
        )
    except (ValueError, KeyError):
        category = "invalid_notification"
    completed = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_email_finish_v1"),
        token=token,
        payload={
            "p_id": notification_id,
            "p_sent": sent,
            "p_provider_message_id": provider_id,
            "p_error_category": category,
        },
        timeout=12,
    )
    if not isinstance(completed, dict) or str(completed.get("id")) != notification_id:
        raise RuntimeError("Mail result was not recorded")
    return {"state": completed.get("state"), "id": notification_id,
            "error_category": category, "provider_message_id": provider_id}


def approval_notice_message(result: dict) -> str:
    status = str(result.get("state") or "")
    if status == "sent":
        return "Access approved. Transactional email accepted by the mail provider."
    if status == "sending":
        return "The notification is being processed; it will not be sent again during this attempt."
    if result.get("error_category") == "configuration_missing":
        return ("Access approved, but email has NOT been sent: set RESEND_API_KEY "
                "or RESEND_SMTP_PASSWORD in the private Streamlit app secrets. "
                "The notification is retained for retry.")
    return "Access approved, but the email was NOT sent. Use Retry notification below."
