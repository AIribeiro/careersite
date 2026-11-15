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
}
PAGE_SERVICES = {
    "advisory-decision": "decision",
    "advisory-rollout": "rollout",
    "advisory-scorecard": "scorecard",
    "advisory-leadership": "workshop",
}


@st.cache_data(ttl=20, show_spinner=False)
def service_visibility() -> dict[str, bool]:
    """Fetch availability for all five services in one request, fail closed."""
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


def service_enabled(service_key: str) -> bool:
    """Do not advertise a new service start when availability cannot be verified."""
    if service_key not in SERVICE_LABELS:
        return False
    try:
        return service_visibility()[service_key]
    except (RuntimeError, ValueError, TimeoutError, KeyError, OSError):
        return False


def public_service_cta(service_key: str, url: str, label: str, event: str) -> str:
    """Render an active service link or a non-clickable, accessible pause state."""
    if service_enabled(service_key):
        return (
            '<a class="advisory-ready-link" href="' + url +
            '" target="_self" data-hq-event="' + event + '">' + label +
            ' <span aria-hidden="true">→</span></a>'
        )
    return (
        '<span class="advisory-ready-link advisory-ready-link--unavailable" '
        'role="status" aria-disabled="true">Temporarily unavailable</span>'
    )


def suppress_paused_detail_ctas(document: str, page: str) -> str:
    """Keep public methodology visible, but prevent links starting paused services."""
    service_key = PAGE_SERVICES.get(page)
    if not service_key or service_enabled(service_key):
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
