"""Server-side, consent-independent page-load totals.

Records only the date and an allowlisted page label in a daily aggregate.
No browser-supplied identifiers, IPs, user agents, article slugs, query strings,
referrers or behavioural paths are transmitted to the counter. This is not
unique-visitor measurement. Detailed client analytics remains consent-gated.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from html import escape
import json
import logging
from urllib import error, request

import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers

PUBLIC_PAGES = frozenset({
    "home", "impact", "thinking", "briefings", "briefing", "about",
    "certifications", "presence", "contact", "advisory", "advisory-scorecard",
    "advisory-rollout", "advisory-decision", "advisory-leadership",
    "advisory-renewal", "advisory-market-signals", "advisory-market-demo",
    "advisory-access", "privacy", "ai-data-governance", "readers",
})
_WINDOW_LABELS = {
    "last_hour": "Today (daily resolution)",
    "today": "Today",
    "yesterday": "Yesterday",
    "this_week": "This week",
    "last_week": "Last week",
    "this_month": "This month",
    "last_month": "Last month",
    "this_year": "This year",
    "all": "Since 20 Nov 2026",
}
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="aggregate-page-load")


def _submit_load(page: str) -> None:
    """Post only an allowlisted page; never send request or browser metadata."""
    payload = json.dumps({"p_page": page}).encode("utf-8")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_aggregate_page_load_v1",
        data=payload, headers=public_analytics_rpc_headers(), method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            if response.status not in (200, 204):
                logging.warning("Aggregate page count returned HTTP %s", response.status)
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        # Only the class name: do not log a request URL, browser metadata or any token.
        logging.warning("Aggregate page count could not be delivered: %s", type(exc).__name__)


def record_page_load(page: str, article_slug: str = "") -> None:
    """Count a navigation once per Streamlit session, not on each widget rerun.

    Article slugs help distinguish navigations but are stored ONLY in ephemeral
    Streamlit server session state. Only the page label reaches Supabase.
    """
    if page not in PUBLIC_PAGES:
        return
    route = (page, str(article_slug)[:160] if page in {"thinking", "briefing"} else "")
    state_key = "_aggregate_last_route_v1"
    if st.session_state.get(state_key) == route:
        return
    st.session_state[state_key] = route
    try:
        _POOL.submit(_submit_load, page)
    except RuntimeError:
        # Let a future rerun retry if the executor has shut down.
        st.session_state.pop(state_key, None)
        logging.warning("Aggregate page count executor unavailable")


@st.cache_data(ttl=90, max_entries=16, show_spinner=False)
def basic_page_load_report(window: str) -> dict:
    selected = "today" if window == "last_hour" else window
    if selected not in _WINDOW_LABELS:
        raise ValueError("Unsupported aggregate reporting period")
    payload = json.dumps({"p_window": selected}).encode("utf-8")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_aggregate_page_load_report_v1",
        data=payload, headers=public_analytics_rpc_headers(), method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            result = json.load(response)
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Anonymous page-load totals are temporarily unavailable") from exc
    if not isinstance(result, dict) or type(result.get("available")) is not bool:
        raise RuntimeError("Anonymous page-load totals returned an invalid response")
    return result


def render_basic_page_loads(window: str) -> None:
    """Compact premium-style public metric, distinct from consented views."""
    try:
        data = basic_page_load_report(window)
        if data.get("available") is False:
            st.caption("Server-side page-load measurement began on 20 November 2026; the selected period predates its start.")
            return
        all_count = max(0, int(data.get("all_page_loads", 0)))
        privacy = max(0, int(data.get("privacy_page_loads", 0)))
        other = max(0, int(data.get("non_privacy_page_loads", 0)))
        if all_count != privacy + other:
            raise ValueError("Aggregate counts did not reconcile")
    except (RuntimeError, ValueError, TypeError, OverflowError):
        st.caption("Basic server-side page-load counts are temporarily unavailable.")
        return
    period = escape(_WINDOW_LABELS.get(window, "Selected period"))
    st.html(f"""
<style>
.pa-basic-traffic {{
 display:flex;align-items:center;justify-content:space-between;gap:20px;
 flex-wrap:wrap;padding:17px 22px;margin:14px 0;border:1px solid #d9dfe5;
 border-radius:12px;background:#fbfaf7;color:#182d46;font-family:Inter,Arial,sans-serif;
}}
.pa-basic-traffic .pa-basic-eyebrow {{
 font-size:10px;text-transform:uppercase;letter-spacing:.11em;font-weight:800;
 color:#b36843;margin:0 0 6px;
}}
.pa-basic-traffic h3 {{font-size:16px;font-weight:750;margin:0 0 5px}}
.pa-basic-traffic p {{font-size:12px;color:#526478;line-height:1.5;margin:0;max-width:620px}}
.pa-basic-traffic .pa-basic-stats {{display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}}
.pa-basic-traffic .pa-basic-value {{display:block;font-size:30px;font-weight:800;line-height:1.1;color:#182d46}}
.pa-basic-traffic .pa-basic-label {{display:block;font-size:11px;color:#536479;padding-top:6px}}
@media(max-width:650px) {{
 .pa-basic-traffic {{padding:16px;align-items:flex-start}}
 .pa-basic-traffic .pa-basic-stats {{gap:18px}}
 .pa-basic-traffic .pa-basic-value {{font-size:25px}}
}}
</style>
<section class="pa-basic-traffic" aria-label="Anonymous daily page-load totals">
 <div><p class="pa-basic-eyebrow">Server-side measurement · {period}</p>
 <h3>Page loads, without optional statistics</h3>
 <p>Daily aggregate counts, starting 20 November 2026. No visitor IDs or browsing histories in this counter.
 Repeated loads count; these are not unique visitors.</p></div>
 <div class="pa-basic-stats">
  <div><strong class="pa-basic-value">{other:,}</strong><span class="pa-basic-label">Excluding Privacy</span></div>
  <div><strong class="pa-basic-value">{privacy:,}</strong><span class="pa-basic-label">Privacy</span></div>
  <div><strong class="pa-basic-value">{all_count:,}</strong><span class="pa-basic-label">All page loads</span></div>
 </div>
</section>
""")
    if window == "last_hour":
        st.caption("This basic counter has daily resolution, so Today is shown instead of Last hour.")
