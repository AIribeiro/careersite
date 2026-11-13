"""Keep authenticated reader navigation on one Streamlit WebSocket.

HTML anchors normally reload Streamlit and discard st.session_state, forcing
another email OTP. A v2 component captures same-origin portfolio navigation
and passes the destination through Streamlit's widget channel instead.
Never put access or refresh tokens in the URL, JS, or browser storage.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs

import streamlit as st


_ALLOWED_PAGES = frozenset({
    "home", "impact", "thinking", "briefings", "briefing", "about",
    "contact", "ai-data-governance", "readers", "advisory", "advisory-access",
    "privacy", "analytics",
})
_ALLOWED_QUERY = frozenset({
    "page", "article", "briefings_page", "weekly_ai", "access", "pdf",
    "signin", "download", "utm_source", "utm_medium", "utm_campaign",
    "utm_content", "source", "role", "go",
})

_JS = r"""
export default function(component) {
  const { setTriggerValue } = component;
  const onPortfolioClick = (event) => {
    if (event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const anchor = event.target.closest?.('a[href]');
    if (!anchor || anchor.hasAttribute('download') ||
        anchor.target === '_blank' || anchor.closest('[contenteditable="true"]')) return;
    let url;
    try { url = new URL(anchor.href, window.location.href); } catch (_) { return; }
    if (url.origin !== window.location.origin || url.pathname !== window.location.pathname)
      return;
    const page = url.searchParams.get('page');
    if (!['home','impact','thinking','briefings','briefing','about',
           'contact','ai-data-governance','readers','advisory',
           'advisory-access','privacy','analytics'].includes(page)) return;
    // Let ordinary within-page hash links continue to behave normally.
    if (url.search === window.location.search && url.hash) return;
    if (url.search.length > 1900) return;
    event.preventDefault();
    setTriggerValue('route', url.search);
  };
  document.addEventListener('click', onPortfolioClick, true);
  return () => document.removeEventListener('click', onPortfolioClick, true);
}
"""


def _parse_portfolio_route(query: object) -> dict[str, str] | None:
    """Allow only first-party public destinations; never accept auth secrets."""
    if not isinstance(query, str) or not query.startswith("?") or len(query) > 1900:
        return None
    try:
        raw = parse_qs(query[1:], keep_blank_values=False, strict_parsing=False,
                       max_num_fields=25)
    except ValueError:
        return None
    if set(raw) - _ALLOWED_QUERY or any(len(v) != 1 for v in raw.values()):
        return None
    params = {key: values[0] for key, values in raw.items()}
    if params.get("page") not in _ALLOWED_PAGES:
        return None
    if any(len(value) > 400 for value in params.values()):
        return None
    if ("article" in params and not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", params["article"]
    )):
        return None
    return params


def mount_reader_navigation() -> None:
    """Mount once per authenticated rerun, ahead of the site's HTML document."""
    component = st.components.v2.component(
        "reader_portfolio_same_session_links", js=_JS,
    )
    result = component(key="reader_portfolio_route", on_route_change=lambda: None)
    route = _parse_portfolio_route(getattr(result, "route", None))
    if route is None:
        return
    if dict(st.query_params) == route:
        return
    st.query_params.from_dict(route)
    st.rerun()
