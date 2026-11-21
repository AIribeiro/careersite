"""Editorial demand and tagged acquisition, from aggregate server-side page opens.

A page open is not a reader, unique visitor or completed read. No individual
events, cookies or browser storage are collected by this reporting layer.
"""
from __future__ import annotations

from html import escape
import json
from urllib import error, request

import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers

_CHANNEL_LABELS = {
    "untagged": "Untagged / unknown",
    "linkedin": "LinkedIn", "email": "Email", "cv": "CV links",
    "outreach": "Outreach", "application": "Applications",
    "chatgpt": "ChatGPT", "search": "Search",
    "social": "Other social", "other_tagged": "Other tagged",
}
_WINDOWS = {"last_hour", "today", "yesterday", "this_week",
            "last_week", "this_month", "last_month", "this_year", "all"}


@st.cache_data(ttl=75, max_entries=16, show_spinner=False)
def content_load_report(window: str) -> dict:
    if window not in _WINDOWS:
        raise ValueError("Unsupported aggregate period")
    body = json.dumps({"p_window": window}).encode("utf-8")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_content_load_report_v1",
        data=body, headers=public_analytics_rpc_headers(), method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            data = json.load(response)
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Content demand aggregate unavailable") from exc
    if not isinstance(data, dict) or data.get("available") is not True:
        raise RuntimeError("Unexpected content aggregate response")
    return data


def _number(row: dict, key: str) -> int:
    return max(0, int(row.get(key) or 0))


def render_content_demand(window: str) -> None:
    """Two understated, actionable lists; never misleading zero-engagement cards."""
    try:
        report = content_load_report(window)
        count = _number(report, "portfolio_loads")
        if count == 0:
            st.caption(
                "Publication-level and tagged-source counts will appear when the "
                "new content counter receives its first portfolio or article opens. Older page-only "
                "counts cannot be reconstructed at article level."
            )
            return
        publications = [
            row for row in report.get("top_content", [])
            if isinstance(row, dict) and row.get("slug") and _number(row, "loads")
        ][:6]
        all_channels = [
            row for row in report.get("channels", [])
            if isinstance(row, dict) and _number(row, "loads")
        ][:8]
        channels = [row for row in all_channels
                    if str(row.get("channel")) != "untagged"][:6]
        broad_pages = [
            row for row in report.get("top_pages", [])
            if isinstance(row, dict) and row.get("page") and _number(row, "loads")
        ][:7]
        # Older page-only loads and newer untagged loads both have
        # unknown acquisition channels. Never relabel them "direct".
        unknown_loads = _number(report, "unattributed_portfolio_loads") + sum(
            _number(row, "loads") for row in all_channels
            if str(row.get("channel")) == "untagged"
        )
        channel_coverage = sum(_number(row, "loads") for row in channels)
    except (RuntimeError, ValueError, TypeError, OverflowError):
        st.caption("Content and source breakdown is temporarily unavailable.")
        return

    top_article = max((_number(item, "loads") for item in publications or broad_pages), default=1)
    top_channel = max(unknown_loads, *(_number(item, "loads") for item in channels), 1)
    publication_title = "Most-opened publications" if publications else "Most-visited portfolio pages"
    publication_items = []
    for row in publications:
        slug = str(row.get("slug") or "").strip()
        if not slug:
            continue
        from urllib.parse import quote
        page = "briefing" if row.get("page") == "briefing" else "thinking"
        url = "https://jairribeiro.com/?page=" + page + "&article=" + quote(slug, safe="-")
        title = escape(slug.replace("-", " ").title())
        views = _number(row, "loads")
        width = max(3, round(views / max(1, top_article) * 100))
        publication_items.append(
            f'<a class="pd-item" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'<span class="pd-line"><span class="pd-label">{title}</span>'
            f'<strong>{views:,}</strong></span><span class="pd-rail"><span style="width:{width}%"></span></span></a>'
        )
    if not publication_items:
        page_names = {
            "home": "Home", "about": "About", "impact": "Leadership Impact",
            "briefing": "Executive Briefing", "briefings": "Briefings Library",
            "thinking": "Thinking & Articles", "advisory": "Advisory",
            "advisory-market-signals": "AI & Data Market Signals",
            "ai-data-governance": "AI & Data Governance",
            "contact": "Contact", "presence": "Speaking & Publications",
        }
        for row in broad_pages:
            page = str(row.get("page") or "")
            views = _number(row, "loads")
            width = max(3, round(views / max(1, top_article) * 100))
            label = escape(page_names.get(page, page.replace("-", " ").title()))
            publication_items.append(
                '<div class="pd-item"><span class="pd-line">'
                f'<span class="pd-label">{label}</span><strong>{views:,}</strong></span>'
                f'<span class="pd-rail"><span style="width:{width}%"></span></span></div>'
            )
        if not publication_items:
            publication_items = ['<p class="pd-empty">No portfolio opens recorded for this period.</p>']

    channel_items = []
    for row in channels:
        channel = str(row.get("channel") or "untagged")
        label = escape(_CHANNEL_LABELS.get(channel, "Other tagged"))
        views = _number(row, "loads")
        width = max(3, round(views / max(1, top_channel) * 100))
        channel_items.append(
            '<div class="pd-item"><span class="pd-line">'
            f'<span class="pd-label">{label}</span><strong>{views:,}</strong></span>'
            f'<span class="pd-rail"><span style="width:{width}%"></span></span></div>'
        )

    if unknown_loads:
        width = max(3, round(unknown_loads / max(1, top_channel) * 100))
        channel_items.append(
            '<div class="pd-item"><span class="pd-line">'
            '<span class="pd-label">Source not classified</span>'
            f'<strong>{unknown_loads:,}</strong></span>'
            f'<span class="pd-rail"><span style="width:{width}%"></span></span></div>'
        )
    if not channel_items:
        channel_items.append('<p class="pd-empty">No known tagged sources in this period.</p>')

    recorded = f"{count:,}"
    editorial = f"{_number(report, 'editorial_page_loads'):,}"
    known = f"{channel_coverage:,}"
    st.html(f"""
<style>
.pd-wrap {{ margin:0 0 13px; font-family:Inter,Arial,sans-serif; color:#1e3143; }}
.pd-header {{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:5px;
  padding:9px 2px 12px; }}
.pd-header strong {{ font-size:14px; }}
.pd-header small {{ font-size:11px; color:#647388; }}
.pd-cols {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
.pd-panel {{ border:1px solid #dce2e7; background:#fff; border-radius:10px; padding:14px 15px 12px; }}
.pd-panel h3 {{ font-size:12px; margin:0 0 11px; font-weight:750; }}
.pd-item {{ display:block; padding:5px 0 8px; color:inherit; text-decoration:none; }}
.pd-line {{ display:flex; justify-content:space-between; gap:10px; font-size:11px; }}
.pd-label {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:86%; }}
.pd-line strong {{ font-variant-numeric:tabular-nums; font-weight:750; }}
.pd-rail {{ display:block; margin-top:5px; height:4px; background:#f0f1f1; border-radius:10px; overflow:hidden; }}
.pd-rail span {{ display:block; height:100%; background:#a37b64; border-radius:10px; }}
.pd-empty {{ color:#697789; font-size:11px; }}
.pd-note {{ font-size:10px; color:#697789; line-height:1.55; margin:10px 2px 0; }}
@media(max-width:650px){{.pd-cols{{grid-template-columns:1fr}} .pd-panel{{padding:12px}}}}
</style>
<section class="pd-wrap" aria-label="Content demand and acquisition channels">
 <div class="pd-header"><strong>Which content is being opened, and where requests come from</strong>
 <small>{recorded} portfolio opens · {editorial} editorial-route opens</small></div>
 <div class="pd-cols">
  <div class="pd-panel"><h3>{publication_title}</h3>{''.join(publication_items)}</div>
  <div class="pd-panel"><h3>Acquisition sources · {known} tagged opens</h3>{''.join(channel_items)}</div>
 </div>
 <p class="pd-note">Page totals begin 20 November 2026; detailed per-publication
 and tagged-source breakdowns began 21 November. Earlier source information is
 explicitly unclassified, not assumed direct. Use tagged LinkedIn and email
 links for improved source measurement. A load is not a unique person or
 reading completion; repeated and automated requests can still be counted.</p>
</section>
""")
