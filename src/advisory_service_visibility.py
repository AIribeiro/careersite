"""Single source of truth for Advisory service availability.

This catalogue is public-read-only; toggles require the verified owner's RPC.
Service availability never alters existing assessment history or approvals.
"""
from __future__ import annotations

import re

import streamlit as st

from site_cms import _request_json, _rest_url

SERVICE_LABELS = {
    "requests": "Personal executive advisory",
    "decision": "AI Investment Decision Advisor",
    "rollout": "Enterprise AI Rollout Readiness Advisor",
    "scorecard": "AI Portfolio Prioritization Scorecard",
    "workshop": "Executive AI Leadership Workshop",
    "renewal": "AI Portfolio Renewal Advisor",
    "market-signals": "AI & Data Market Signals",
}
PAGE_SERVICES = {
    "advisory-decision": "decision",
    "advisory-rollout": "rollout",
    "advisory-scorecard": "scorecard",
    "advisory-leadership": "workshop",
    "advisory-renewal": "renewal",
    "advisory-market-signals": "market-signals",
    "advisory-market-demo": "market-signals",
}


@st.cache_data(ttl=20, show_spinner=False)
def service_visibility() -> dict[str, bool]:
    """Fetch availability for all registered services in one request, fail closed."""
    rows = _request_json(
        "GET",
        _rest_url(
            "portfolio_advisory_service_visibility?"
            "select=service_key,is_enabled&order=service_key.asc"
        ),
        timeout=10,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Service availability could not be read.")
    status = {}
    for row in rows:
        key = str(row.get("service_key") or "")
        if key in SERVICE_LABELS and type(row.get("is_enabled")) is bool:
            status[key] = row["is_enabled"]
    if set(status) != set(SERVICE_LABELS):
        raise RuntimeError("Advisory service catalogue is incomplete.")
    return status


def service_enabled(service_key: str, *, admin: bool = False) -> bool:
    """Disabled means hidden for regular users; admins retain normal access."""
    if service_key not in SERVICE_LABELS:
        return False
    if admin:
        return True
    try:
        return service_visibility()[service_key]
    except (RuntimeError, ValueError, TimeoutError, KeyError, OSError):
        return False


def public_service_cta(service_key: str, url: str, label: str, event: str, *, admin: bool = False) -> str:
    """Render an active service link or a non-clickable, accessible pause state."""
    if service_enabled(service_key, admin=admin):
        return (
            '<a class="advisory-ready-link" href="' + url +
            '" target="_self" data-hq-event="' + event + '">' + label +
            ' <span aria-hidden="true">→</span></a>'
        )
    return (
        '<span class="advisory-ready-link advisory-ready-link--unavailable" '
        'role="status" aria-disabled="true">Temporarily unavailable</span>'
    )


def suppress_paused_detail_ctas(document: str, page: str, *, admin: bool = False) -> str:
    """Keep public methodology visible, but prevent links starting paused services."""
    service_key = PAGE_SERVICES.get(page)
    if not service_key or service_enabled(service_key, admin=admin):
        return document
    # All entry CTAs from these pages point to Advisory Access with a service view.
    # Do not touch methodology, footer, privacy, or generic Advisory account links.
    expression = (
        r'<a\b(?=[^>]*\bhref="\?page=advisory-access(?:&amp;|&)view='
        + re.escape(service_key) +
        r'(?:&amp;[^"]*|&[^"]*)?")[^>]*>.*?</a>'
    )
    replacement = (
        '<span class="sc-btn" aria-disabled="true" role="status" '
        'style="opacity:.55;cursor:not-allowed;background:#697787;'
        'border-color:#697787;color:#fff">Temporarily unavailable</span>'
    )
    return re.sub(expression, replacement, document, flags=re.IGNORECASE | re.DOTALL)


def advisory_role(token: str) -> str:
    """Read the caller's role from Supabase, never from user-editable metadata."""
    if not token:
        return "regular"
    role = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_my_role_v1"),
        token=token, payload={}, timeout=10,
    )
    if role not in ("admin", "regular"):
        raise RuntimeError("Unable to verify Advisory role.")
    return role


def viewer_is_admin() -> bool:
    """Trust only verified password sessions; never a claimed email or URL state."""
    if isinstance(st.session_state.get("reader_native_session"), dict):
        try:
            from page_reader_native import _session
            from page_advisory_portal import _password_authenticated
            session, user = _session()
            if (session and user and user.get("email_confirmed_at")
                    and _password_authenticated(session)
                    and advisory_role(str(session["access_token"])) == "admin"):
                return True
        except (RuntimeError, ValueError, TimeoutError, KeyError, OSError):
            pass
    # The portfolio owner's CMS session is separate from Reader/Advisory.
    # Recheck it against Supabase; a stale Streamlit flag is never enough.
    if isinstance(st.session_state.get("cms_auth"), dict):
        try:
            from page_owner_reader_management import _verify_owner
            token = _verify_owner(st.session_state["cms_auth"])
            return advisory_role(token) == "admin"
        except (PermissionError, RuntimeError, ValueError, TimeoutError, KeyError, OSError):
            pass
    return False
