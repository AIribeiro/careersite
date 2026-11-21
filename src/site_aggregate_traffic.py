"""Consent-independent server-side page-load counts with coarse content reach.

Counts route opens in daily aggregate buckets by page, public article slug and
broad campaign channel. Does not transmit IP addresses, cookies, user agents,
referrers, full URLs, account data or visitor/session identifiers. One count is
a page load, never a verified visitor. Detailed behavior remains opt-in.
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


_CHANNELS = frozenset({
    "linkedin", "email", "cv", "outreach", "application",
    "chatgpt", "search", "social", "other_tagged", "untagged",
})


def _channel(source: str = "", utm_source: str = "", referrer: str = "") -> str:
    """Classify source strings without storing free-text tags or full referrers."""
    from urllib.parse import urlsplit
    tag = (utm_source or source or "").strip().lower()[:100]
    if tag:
        if tag in {"li", "linkedin", "linkedin.com", "www.linkedin.com"} or "linkedin" in tag:
            return "linkedin"
        if tag in {"chatgpt", "chatgpt.com", "openai", "openai.com"}:
            return "chatgpt"
        if tag in {"google", "bing", "search", "duckduckgo"}:
            return "search"
        if tag in {"email", "newsletter", "mail"}:
            return "email"
        if tag in {"cv", "outreach", "application", "social"}:
            return tag
        return "other_tagged"
    try:
        host = (urlsplit(referrer).hostname or "").lower()
    except ValueError:
        host = ""
    if host.endswith("linkedin.com"):
        return "linkedin"
    if host in {"chatgpt.com", "chat.openai.com"}:
        return "chatgpt"
    if host.endswith(("google.com", "bing.com", "duckduckgo.com")):
        return "search"
    # Untagged means unknown, NOT a proven direct visit.
    return "untagged"


def _submit_load(page: str, content_slug: str, channel: str) -> None:
    """Atomic Supabase RPC increments the total and its content breakdown."""
    payload = json.dumps({
        "p_page": page, "p_content": content_slug, "p_channel": channel,
    }).encode("utf-8")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_content_load_record_v1",
        data=payload, headers=public_analytics_rpc_headers(), method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            if response.status not in (200, 204):
                logging.warning("Aggregate content count returned HTTP %s", response.status)
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        logging.warning("Aggregate content count delivery failed: %s", type(exc).__name__)


def record_page_load(
    page: str, article_slug: str = "", *, source: str = "",
    utm_source: str = "", referrer: str = "",
) -> None:
    """Count a route open once per Streamlit server session, not each widget rerun.

    A fresh Streamlit session or repeated external navigation can produce more
    than one load for the same person; this is not unique-person measurement.
    """
    if page not in PUBLIC_PAGES:
        return
    import re
    content_slug = (
        str(article_slug).strip().lower()[:150]
        if page in {"thinking", "briefing"} else ""
    )
    if content_slug and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", content_slug):
        content_slug = ""
    route = (page, content_slug)
    state_key = "_aggregate_last_route_v1"
    if st.session_state.get(state_key) == route:
        return
    st.session_state[state_key] = route
    channel = _channel(source, utm_source, referrer)
    try:
        _POOL.submit(_submit_load, page, content_slug, channel)
    except RuntimeError:
        st.session_state.pop(state_key, None)
        logging.warning("Aggregate content count executor unavailable")

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
        reader_workspace = max(0, int(data.get("reader_page_loads", 0)))
        portfolio_content = max(0, int(data.get(
            "portfolio_page_loads",
            all_count - privacy - reader_workspace
            - max(0, int(data.get("advisory_access_loads", 0))),
        )))
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
 <h3>Page activity · separate content from account traffic</h3>
 <p>Daily counts without visitor identifiers, since 20 November.
 Reader Library workspace loads are separated from portfolio and publication opens.
 These are page requests, not unique visitors; repeat and automated requests can count.</p></div>
 <div class="pa-basic-stats">
  <div><strong class="pa-basic-value">{portfolio_content:,}</strong><span class="pa-basic-label">Portfolio &amp; content</span></div>
  <div><strong class="pa-basic-value">{reader_workspace:,}</strong><span class="pa-basic-label">Reader workspace</span></div>
  <div><strong class="pa-basic-value">{all_count:,}</strong><span class="pa-basic-label">All public loads</span></div>
 </div>
</section>
""")
    if privacy:
        st.caption(f"{privacy:,} Privacy-page loads are excluded from the portfolio-content figure.")

    trend = data.get("daily_trend", [])
    if isinstance(trend, list) and len(trend) > 1:
        daily = []
        for row in trend:
            if not isinstance(row, dict):
                continue
            label = str(row.get("visit_day") or "")[:10]
            try:
                loads = max(0, int(row.get("portfolio") or 0))
            except (TypeError, ValueError, OverflowError):
                continue
            if len(label) == 10:
                daily.append({"Day": label, "Portfolio opens": loads})
        if len(daily) > 1:
            import altair as alt
            chart = (
                alt.Chart(alt.Data(values=daily)).mark_bar(cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("Day:O", title=None),
                    y=alt.Y("Portfolio opens:Q", title="Portfolio loads"),
                    tooltip=["Day:O", "Portfolio opens:Q"],
                ).properties(height=115)
            )
            st.altair_chart(chart, use_container_width=True)
            st.caption("Daily portfolio loads · excludes Reader Library, privacy and Advisory login.")

    if window == "last_hour":
        st.caption("This counter resolves by day, so the selected Last hour displays Today.")


@st.cache_data(ttl=300, max_entries=2, show_spinner=False)
def monthly_content_rollup() -> tuple[list[dict], list[dict]]:
    """Read retained MONTHLY totals and public-content ranks, never raw sessions."""
    base = ANALYTICS_URL.rstrip("/") + "/rest/v1/"
    sources = (
        "careersite_analytics_monthly_public_v1?select=month,page_views,article_views,"
        "article_interactions,cta_clicks,cv_downloads,audio_starts,audio_completions"
        "&order=month.asc",
        "careersite_analytics_lifetime_content_public_v1?select=content_kind,content,views"
        "&order=views.desc&limit=1000",
    )
    output = []
    for source in sources:
        req = request.Request(base + source, headers=public_analytics_rpc_headers(), method="GET")
        try:
            with request.urlopen(req, timeout=6) as response:
                rows = json.load(response)
        except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("Monthly aggregate trend is temporarily unavailable") from exc
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise RuntimeError("Monthly aggregate reporting returned an unexpected format")
        output.append(rows)
    return output[0], output[1]


def render_monthly_optin_trend() -> None:
    """Optional compact visual, with retained counts rather than a raw data table."""
    with st.expander("Long-term readership · monthly history", expanded=False):
        st.caption(
            "Monthly retained view counts, not unique people. Before 20 Nov 2026 the "
            "tracking rules were broader; after that date detailed statistics require opt-in. "
            "The series is therefore not directly comparable across the change."
        )
        try:
            months, articles = monthly_content_rollup()
            data = []
            for row in months:
                month = str(row.get("month") or "")[:7]
                if len(month) != 7:
                    continue
                data.extend([
                    {"Month": month, "Type": "Portfolio pages",
                     "Views": max(0, int(row.get("page_views") or 0))},
                    {"Month": month, "Type": "Articles & briefings",
                     "Views": max(0, int(row.get("article_views") or 0))},
                ])
            if not data:
                st.caption("No monthly summary is available yet.")
                return
            import altair as alt
            chart = (
                alt.Chart(alt.Data(values=data))
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("Month:O", title=None, sort=sorted({x["Month"] for x in data})),
                    y=alt.Y("Views:Q", title="Recorded views", stack="zero"),
                    color=alt.Color("Type:N", title=None),
                    tooltip=["Month:N", "Type:N", "Views:Q"],
                )
                .properties(height=200)
            )
            st.altair_chart(chart, use_container_width=True)
            if articles:
                labels = []
                for article in [item for item in articles if item.get("content_kind") == "article"][:3]:
                    slug = str(article.get("content") or "").strip()
                    views = max(0, int(article.get("views") or 0))
                    if slug and views:
                        labels.append(f"{slug.replace('-', ' ').title()} ({views:,})")
                if labels:
                    st.caption("Historically most opened publications: " + " · ".join(labels))
            st.caption("Monthly totals are retained after 90-day raw-event deletion.")
        except (RuntimeError, TypeError, ValueError, OverflowError):
            st.caption("Retained monthly trends are temporarily unavailable.")
