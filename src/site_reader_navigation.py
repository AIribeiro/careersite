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
    "home",
    "impact",
    "thinking",
    "briefings",
    "briefing",
    "about",
    "certifications",
    "contact",
    "advisory",
    "advisory-scorecard",
    "advisory-rollout",
    "advisory-access",
    "privacy",
    "enterprise",
    "transformation",
    "governance",
    "consulting",
    "ai-data-governance",
    "readers",
    "analytics",
})
_ALLOWED_QUERY = frozenset({
    "page",
    "article",
    "briefings_page",
    "weekly_ai",
    "access",
    "pdf",
    "signin",
    "download",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "source",
    "role",
    "go",
    "view",
    "request",
    "workspace",
})

_JS = r"""
export default function(component) {
  const { setTriggerValue } = component;
  const allowedPages = new Set(["home","impact","thinking","briefings","briefing","about","certifications","contact","advisory","advisory-scorecard","advisory-rollout","advisory-access","privacy","enterprise","transformation","governance","consulting","ai-data-governance","readers","analytics"]);
  const allowedParams = new Set(["page","article","briefings_page","weekly_ai","access","pdf","signin","download","utm_source","utm_medium","utm_campaign","utm_content","utm_term","source","role","go","view","request","workspace"]);
  const advisoryViews = new Set(["overview","requests","messages","scorecard","rollout","account"]);
  const brandedHosts = new Set(['jairribeiro.com', 'advisory.jairribeiro.com']);
  const onPortfolioClick = (event) => {
    if (event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const anchor = event.target.closest?.('a[href]');
    if (!anchor || anchor.hasAttribute('download') ||
        (anchor.target && anchor.target !== '_self') ||
        anchor.closest('[contenteditable="true"]')) return;
    let url;
    try { url = new URL(anchor.href, window.location.href); } catch (_) { return; }
    const current = new URL(window.location.href);
    const sameAppPath = url.origin === current.origin &&
                        url.pathname === current.pathname;
    const firstPartyRoute = url.protocol === 'https:' &&
                            brandedHosts.has(url.hostname) && url.pathname === '/';
    if (!sameAppPath && !firstPartyRoute) return;
    if (url.search.length > 1900) return;
    const route = new URLSearchParams(url.search);
    for (const key of route.keys()) {
      if (!allowedParams.has(key) || route.getAll(key).length !== 1) return;
    }
    // Branded home links without a query should stay in the existing WebSocket.
    const page = route.get('page') || (firstPartyRoute && !url.search ? 'home' : null);
    if (!allowedPages.has(page)) return;
    const article = route.get('article');
    if (article && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(article)) return;
    const view = route.get('view');
    if (view && (page !== 'advisory-access' || !advisoryViews.has(view))) return;
    const request = route.get('request');
    if (request && (page !== 'advisory-access' || view !== 'messages' ||
        !/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(request))) return;
    if (route.has('workspace') && page !== 'analytics') return;
    // Do not interfere with section anchors on the current page.
    if (sameAppPath && url.search === current.search && url.hash) return;
    if (!route.has('page')) route.set('page', page);
    event.preventDefault();
    setTriggerValue('route', '?' + route.toString());
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
    if "view" in params and (
        params["page"] != "advisory-access" or
        params["view"] not in {"overview", "requests", "messages", "scorecard", "rollout", "account"}
    ):
        return None
    if "request" in params and (
        params["page"] != "advisory-access" or params.get("view") != "messages" or
        not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", params["request"])
    ):
        return None
    if "workspace" in params and params["page"] != "analytics":
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
