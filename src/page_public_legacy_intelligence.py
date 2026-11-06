"""Additional read-only panels for the public Advanced Insights tabs.

Only anonymous aggregate RPC outputs are requested. All channel names are
coarsened in the model, while the publisher's existing content/CTA wording
comes from publicly observed page instrumentation.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import json
from urllib import error, request

import streamlit as st

from page_analytics import (
    ACCENT, BLUE, GREEN, _bar_chart, _dashboard_payload, _seconds,
)
from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers
from portfolio_legacy_signal_model import (
    channel_rollup, device_comparison, n, percentage, seven_day_comparison,
    traffic_findings,
)


@st.cache_data(ttl=300, max_entries=12, show_spinner=False)
def fetch_public_content_aggregate(window: str) -> dict:
    """Public content/attention report without CMS metadata or owner behavior RPC."""
    payload = _dashboard_payload(window)
    payload["p_article_metadata"] = []
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_content_intelligence_v2",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=public_analytics_rpc_headers(),
    )
    try:
        with request.urlopen(req, timeout=18) as response:
            data = json.load(response)
    except (error.HTTPError, error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("Public content observations are temporarily unavailable.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected public content response.")
    return data


def _content_name(value: object) -> str:
    slug = str(value or "").strip().lower()
    if slug.startswith("article:"):
        slug = slug[8:]
    if not slug or len(slug) > 150 or "?" in slug or "/" in slug:
        return "Other content"
    return slug.replace("-", " ").replace("_", " ").strip().title()[:100]


def _cta_name(value: object) -> str:
    """Never reflect URLs, identifiers or Markdown injection into the public UI."""
    text = str(value or "").strip()
    lowered = text.lower()
    if not text or len(text) > 100 or any(token in lowered for token in (
        "http", "utm_", "role=", "source=", "mailto:", "@", "token", "secret",
    )):
        return "Unlabeled action"
    return "".join(
        char for char in text
        if char.isalnum() or char in " -_.,:()!?&·→↓↗+/’'"
    ).strip()[:90] or "Unlabeled action"


def _chart(rows: list[dict], name: str, value: str, limit: int = 12) -> None:
    if not rows:
        st.caption("No qualifying observations in the selected period.")
        return
    _bar_chart(rows, name, value=value, limit=limit, color=BLUE, height=310)


def _metric_rate(label: str, top: object, bottom: object,
                 *, number: bool = True) -> None:
    rate = percentage(top, bottom)
    st.metric(label, f"{rate:.1f}%" if rate is not None else "—",
              f"{n(top):,} of {n(bottom):,} observations" if number else None)


def _insights(data: dict, window: str) -> None:
    today = datetime.now(ZoneInfo("Europe/Stockholm")).date()
    findings = traffic_findings(data, today=today, window=window)
    st.markdown("#### What the traffic evidence shows")
    st.caption(
        "Ranked signals from recorded aggregates. Each finding separates the evidence, "
        "its interpretation and the next thing worth checking."
    )
    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**{finding['title']}**")
            st.caption(finding["evidence"])
            st.write(finding["meaning"])
            st.markdown(f"*Next check:* {finding['next_check']}")

    comparison = seven_day_comparison(
        data.get("daily", []), today=today, window=window,
        period_since=data.get("period_since"),
    )
    if comparison:
        st.markdown("#### Completed-week momentum")
        cols = st.columns(3)
        cols[0].metric("Last 7 complete days", f"{comparison['recent']:,} sessions")
        cols[1].metric("Previous 7 complete days", f"{comparison['previous']:,} sessions")
        change = comparison["change_pct"]
        cols[2].metric("Change", f"{change:+.1f}%" if change is not None else "—")
        st.caption(
            f"Compared {comparison['recent_start']:%d %b}–{comparison['recent_end']:%d %b} "
            f"with {comparison['previous_start']:%d %b}–{comparison['previous_end']:%d %b}. "
            "Today is excluded. Rates require at least 20 sessions in the previous period."
        )
    else:
        st.caption("Two comparable completed weeks are not available inside this selected window. Choose All for a broader baseline.")

    st.caption(
        "For content paths, placement-level CTA observations and web performance, "
        "choose the corresponding deeper analysis view. Those reports load only when selected."
    )


def _channels(data: dict) -> None:
    totals = data.get("totals") or {}
    all_sessions = n(totals.get("sessions"))
    grouped = channel_rollup(data.get("attribution", []))
    st.markdown("#### Acquisition channel outcomes")
    st.caption(
        "First-touch source/role cohorts are consolidated into broad channels. "
        "Exact source tags, employer names, campaigns and contact data are not published. "
        "Engagement and article-reach counts can overlap within a channel."
    )
    rows = []
    for item in grouped:
        rows.append({
            "Channel": item["Channel"],
            "Sessions": item["sessions"],
            "Share of sessions": f"{percentage(item['sessions'],all_sessions):.1f}%"
                if percentage(item["sessions"],all_sessions) is not None else "—",
            "Engaged sessions": item["engaged_sessions"],
            "Engagement rate": (
                f"{item['Engagement rate']:.1f}%" if item["Engagement rate"] is not None else "—"),
            "Recorded article-reach sessions": item["article_sessions"],
            "CV-opening sessions": item["cv_sessions"],
        })
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)
        _chart([{"Channel": r["Channel"], "Sessions": r["Sessions"]} for r in rows],
               "Channel", "Sessions")
        rate_rows = [
            {"Channel": r["Channel"], "Engagement %": r0["Engagement rate"]}
            for r, r0 in zip(rows, grouped)
            if r["Sessions"] >= 20 and r0["Engagement rate"] is not None
        ]
        if rate_rows:
            st.markdown("**Recorded engagement by channel (20+ sessions)**")
            _chart(rate_rows, "Channel", "Engagement %")
    else:
        st.caption("No channel counts are available.")
    st.caption(
        "These are observed attribution tags. Direct/unattributed traffic is not proven "
        "direct navigation. Recorded article-reach sessions use this traffic collector's "
        "definitions and are not directly comparable to content-reader sessions in the "
        "newer publication collector."
    )


def _article_rows(report: dict) -> list[dict]:
    rows = []
    for item in report.get("performance", []):
        if not isinstance(item, dict) or item.get("kind") != "article":
            continue
        sessions = n(item.get("sessions"))
        if sessions == 0:
            continue
        coverage = n(item.get("depth_measured_sessions"))
        read_depth = percentage(item.get("three_quarter_sessions"), coverage)
        rows.append({
            "Article": _content_name(item.get("content")),
            "Views": n(item.get("views")),
            "Reader sessions": sessions,
            "Engaged sessions": n(item.get("engaged_sessions")),
            "Depth measured": coverage,
            "75% depth reached": f"{read_depth:.1f}%"
                if coverage >= 20 and read_depth is not None else "—",
            "Later portfolio sessions": n(item.get("later_portfolio_sessions")),
        })
    return sorted(rows, key=lambda row: (-row["Reader sessions"], row["Article"]))


def _journey_rows(report: dict) -> list[dict]:
    rows = []
    for item in report.get("journeys", []):
        if not isinstance(item, dict) or n(item.get("sessions")) < 2:
            continue
        rows.append({
            "From": _content_name(item.get("from_content")),
            "To": _content_name(item.get("to_content")),
            "Sessions": n(item.get("sessions")),
            "Recorded transitions": n(item.get("transitions")),
        })
    return sorted(rows, key=lambda row: (-row["Sessions"], row["From"], row["To"]))


def _content(report: dict) -> None:
    st.markdown("#### Content attention and onward journeys")
    quality = report.get("quality") or {}
    multi = report.get("multi_article") or {}
    ordered = report.get("ordered_funnel") or {}
    cols = st.columns(3)
    with cols[0]:
        _metric_rate("Multi-article readers", multi.get("multi_article_sessions"),
                     multi.get("reader_sessions"))
    with cols[1]:
        _metric_rate("Article share of content sessions",
                     quality.get("article_sessions"), quality.get("content_sessions"))
    with cols[2]:
        _metric_rate("Article → Experience", ordered.get("article_to_impact_sessions"),
                     ordered.get("article_sessions"))
    st.caption(
        "Multi-article sessions count browser-tab sessions with multiple distinct articles. "
        "Article → Experience requires an observed ordered path, not simply both pages having views. "
        "The middle metric is article session share of content sessions, not telemetry coverage."
    )

    rows = _article_rows(report)
    st.markdown("**Article attention and follow-on activity**")
    if rows:
        st.dataframe(rows[:20], hide_index=True, use_container_width=True)
        _chart([{"Article": row["Article"][:55], "Reader sessions": row["Reader sessions"]}
                for row in rows[:10]], "Article", "Reader sessions", limit=10)
    else:
        st.caption("No recorded article sessions in this period.")

    st.markdown("**Most common observed content-to-content paths**")
    journeys = _journey_rows(report)
    if journeys:
        st.dataframe(journeys[:18], hide_index=True, use_container_width=True)
    else:
        st.caption("No consecutive content transitions recorded.")
    st.caption(
        "Path counts represent consecutive recorded content views within one browser session. "
        "They do not show all navigation clicks or prove why a visitor continued. "
        "This newer content collector uses a different session eligibility rule "
        "from the historical traffic report; their totals must not be reconciled."
    )

    section_rows = []
    for item in report.get("section_reach", []):
        if not isinstance(item, dict):
            continue
        base = n(item.get("page_sessions"))
        seen = n(item.get("reached_sessions"))
        rate = percentage(seen, base)
        if base < 20 or rate is None:
            continue
        section_rows.append({
            "Page": _content_name(item.get("page")),
            "Section": str(item.get("section_label") or "Unnamed section")[:90],
            "Sessions reaching section": seen,
            "Page sessions": base,
            "Reach": f"{rate:.1f}%",
        })
    st.markdown("**Section visibility on recorded pages**")
    if section_rows:
        pages = sorted({row["Page"] for row in section_rows})
        preferred = pages.index("Home") if "Home" in pages else 0
        chosen = st.selectbox("Page for section visibility",
                              pages, index=preferred, key="portfolio_legacy_section_page")
        matching = sorted((row for row in section_rows if row["Page"] == chosen),
                          key=lambda r: -r["Sessions reaching section"])
        st.dataframe(matching[:22], hide_index=True, use_container_width=True)
        st.caption(
            "Section-reach percentage divides measured reach by page-session observations. "
            "It may be lower when historical section instrumentation was incomplete."
        )
    else:
        st.caption("Not enough section-level observations.")


def _ctas(report: dict) -> None:
    st.markdown("#### CTA exposure and recorded activation")
    st.caption(
        "A CTA can be seen without being clicked. Showing both exposure and activation "
        "helps prioritize tests, but zero recorded clicks is not evidence that the design failed."
    )
    rows = []
    for item in report.get("cta_placements", []):
        if not isinstance(item, dict):
            continue
        exposed = n(item.get("exposed_sessions"))
        clicked = n(item.get("click_sessions"))
        if exposed < 10:
            continue
        rate = percentage(clicked, exposed)
        rows.append({
            "CTA": _cta_name(item.get("label")),
            "Exposed sessions": exposed,
            "Click sessions": clicked,
            "Recorded click/exposure": f"{rate:.1f}%" if rate is not None else "—",
            "_rate": rate,
        })
    rows.sort(key=lambda row: (-row["Exposed sessions"], row["CTA"]))
    if not rows:
        st.caption("CTA exposure has not been recorded in sufficient volume.")
        return
    st.dataframe([{key: value for key, value in row.items() if not key.startswith("_")}
                  for row in rows[:25]], hide_index=True, use_container_width=True)
    st.markdown("**Most exposed calls to action**")
    _chart([{"CTA": row["CTA"][:65], "Exposed": row["Exposed sessions"]}
            for row in rows[:12]], "CTA", "Exposed")
    st.markdown("**Candidates to investigate**")
    zeros = [row for row in rows if row["Exposed sessions"] >= 30 and row["Click sessions"] == 0]
    if zeros:
        for row in zeros[:6]:
            st.markdown(
                f"- **{row['CTA']}**: {row['Exposed sessions']:,} exposed sessions; "
                "no recorded click sessions. Check the element's tracking and placement."
            )
    else:
        st.caption("No zero-click CTA has at least 30 recorded exposed sessions.")
    st.caption(
        "Exposure and click-session instrumentation may have changed over time; "
        "cross-section rates should not be treated as conversion experiments."
    )


def _experience(report: dict) -> None:
    st.markdown("#### Browser loading and visual stability")
    st.caption(
        "Historical device-level browser telemetry, including p75 values (75th percentile). "
        "These are observations, not a fresh site audit or a Google CrUX field report."
    )
    rows = []
    for row in report.get("experience", []):
        if not isinstance(row, dict):
            continue
        measured = n(row.get("measured_sessions"))
        if measured < 10:
            continue
        lcp = row.get("p75_lcp_ms")
        ttfb = row.get("p75_ttfb_ms")
        cls = row.get("p75_cls")
        slow = percentage(row.get("slow_lcp_sessions"), measured)
        unstable = percentage(row.get("unstable_cls_sessions"), measured)
        rows.append({
            "Device": str(row.get("device_type") or "Unknown").title(),
            "Measured sessions": measured,
            "p75 LCP": f"{float(lcp)/1000:.2f}s" if lcp is not None else "—",
            "p75 TTFB": f"{float(ttfb)/1000:.2f}s" if ttfb is not None else "—",
            "p75 CLS": f"{float(cls):.3f}" if cls is not None else "—",
            "LCP > 2.5s": f"{slow:.1f}%" if slow is not None else "—",
            "CLS > 0.1": f"{unstable:.1f}%" if unstable is not None else "—",
            "_lcp": float(lcp) if lcp is not None else None,
        })
    if not rows:
        st.caption("Insufficient browser timing observations for this reporting window.")
        return
    st.dataframe([{k: v for k, v in row.items() if not k.startswith("_")}
                  for row in rows], hide_index=True, use_container_width=True)
    chart_rows = [
        {"Device": row["Device"], "p75 load time (s)": round(row["_lcp"]/1000, 2)}
        for row in rows if row["_lcp"] is not None
    ]
    if chart_rows:
        _chart(chart_rows, "Device", "p75 load time (s)")
    priority = [row for row in rows if row["Measured sessions"] >= 30
                and row["_lcp"] is not None and row["_lcp"] > 2500]
    if priority:
        st.markdown("**Areas to investigate first**")
        for row in sorted(priority, key=lambda r: -r["_lcp"]):
            st.write(
                f"{row['Device']}: p75 LCP {row['p75 LCP']} across "
                f"{row['Measured sessions']:,} measured sessions. "
                "Recheck current navigation, hero images, fonts and page hydration."
            )
    unstable = [row for row in rows if row["Measured sessions"] >= 30
                and row["p75 CLS"] != "—" and float(row["p75 CLS"]) > 0.1]
    if unstable:
        for row in unstable:
            st.write(
                f"{row['Device']}: p75 layout-shift score {row['p75 CLS']}. "
                "Check late-loading images, dynamic sections and font swaps."
            )
    st.caption(
        "LCP reflects loading of the largest rendered element; CLS reflects unexpected "
        "layout movement. Historical browser/support coverage may differ by device. "
        "Do not infer that performance caused a change in engagement from this chart alone."
    )


def _coverage(traffic: dict, report: dict) -> None:
    st.markdown("#### Data completeness and interpretation")
    quality = report.get("quality") or {}
    totals = traffic.get("totals") or {}
    browser_sessions = n(totals.get("sessions"))
    content_sessions = n(quality.get("content_sessions"))
    st.caption(
        "Browser-session traffic and content-session reporting use different observation "
        "rules and may not reconcile. Never sum them as unique people."
    )
    left, middle, right = st.columns(3)
    with left:
        _metric_rate("Confirmed active duration",
                     totals.get("confirmed_duration_sessions"), browser_sessions)
    with middle:
        _metric_rate("Newer content measurements",
                     quality.get("measured_content_sessions"), content_sessions)
    with right:
        _metric_rate("Attention measurements",
                     quality.get("attention_measured_content_sessions"), content_sessions)
    st.caption(
        f"Newer content instrumentation began: "
        f"{str(quality.get('new_measurement_since') or 'unknown')[:10]}; "
        f"attention instrumentation began: "
        f"{str(quality.get('attention_measurement_since') or 'unknown')[:10]}. "
        "Earlier readings cannot be retroactively measured."
    )
    st.markdown("**Reporting limitations**")
    st.markdown(
        "- Repeat visits can produce more than one view; visitors are not identified across sessions.\n"
        "- Recorded clicks, exposure, scroll depth and active time have different coverage.\n"
        "- A missing engagement heartbeat is unconfirmed time, not a zero-second visit.\n"
        "- Broad source cohorts do not identify recruiters, companies or individuals.\n"
        "- Site navigation changed on 23 October 2026; historical route comparisons mix structures.\n"
        "- Device differences and traffic changes are associations, not causal evidence.\n"
        "- Hiring outcomes, private campaigns and raw telemetry remain outside this public dashboard."
    )


@st.cache_data(ttl=300, max_entries=12, show_spinner=False)
def fetch_public_behavior_aggregate(window: str) -> dict:
    """Separate on-demand UX report with no raw event or visitor access."""
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_behavior_intelligence",
        data=json.dumps(_dashboard_payload(window)).encode("utf-8"),
        method="POST",
        headers=public_analytics_rpc_headers(),
    )
    try:
        with request.urlopen(req, timeout=18) as response:
            data = json.load(response)
    except (error.HTTPError, error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("Browser-behavior reporting is temporarily unavailable.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected browser-behavior response.")
    return data


def _behavior(report: dict) -> None:
    st.markdown("#### Attention, browser errors and interaction friction")
    quality = report.get("quality") or {}
    sessions = n(quality.get("behavior_sessions"))
    st.caption(
        f"{sessions:,} browser sessions with behavior instrumentation in this reporting window. "
        "These diagnostics began on "
        f"{str(quality.get('behavior_first_seen') or 'an unknown date')[:10]}. "
        "Errors are diagnostic signals, not confirmed failed page visits."
    )
    st.markdown("**Browser resource and script error signals**")
    errors = []
    for row in report.get("ux_signals", []):
        if not isinstance(row, dict):
            continue
        count = n(row.get("sessions"))
        if not count:
            continue
        raw = str(row.get("error_type") or "").lower()
        if "resource" in raw:
            error_kind = "Resource load"
        elif "type" in raw:
            error_kind = "Type error"
        elif "string" in raw:
            error_kind = "Script error"
        else:
            error_kind = "Other reported error"
        errors.append({
            "Page": _content_name(row.get("page")),
            "Error category": error_kind,
            "Sessions with signal": count,
            "Recorded events": n(row.get("events")),
        })
    errors.sort(key=lambda row: (-row["Sessions with signal"], row["Page"]))
    if errors:
        st.dataframe(errors[:18], hide_index=True, use_container_width=True)
        st.caption(
            "Error categories on the same page can overlap in one browser session. "
            "Inspect runtime logs and failed assets to identify causes."
        )
    else:
        st.caption("No recorded error signals for this period.")

    st.markdown("**Section-level attention where measured**")
    attention = []
    for row in report.get("section_attention", []):
        if not isinstance(row, dict):
            continue
        observed = n(row.get("measured_attention_sessions"))
        if observed < 20:
            continue
        median = row.get("median_attention_seconds")
        if median is None:
            continue
        try:
            med = max(0.0, float(median))
        except (TypeError, ValueError):
            continue
        attention.append({
            "Page": _content_name(row.get("page")),
            "Section": _cta_name(row.get("section_label")),
            "Measured sessions": observed,
            "Median visible attention": f"{med:.1f}s",
            "_median": med,
        })
    attention.sort(key=lambda row: (-row["Measured sessions"], row["Page"]))
    if attention:
        st.dataframe([{k: v for k, v in row.items() if k != "_median"}
                      for row in attention[:20]], hide_index=True,
                     use_container_width=True)
    else:
        st.caption("Not enough measured section-attention sessions.")
    st.caption(
        "Visible attention is not proof of reading or comprehension. "
        "Historical sections may have different measurement coverage."
    )

    st.markdown("**CTA hover/attention versus clicks**")
    elements = []
    for row in report.get("element_attention", []):
        if not isinstance(row, dict):
            continue
        exposed = n(row.get("exposed_sessions"))
        if exposed < 30 or str(row.get("element_kind") or "").lower() not in (
            "cta", "link", "button",
        ):
            continue
        elements.append({
            "Element": _cta_name(row.get("element_label")),
            "Exposed": exposed,
            "Hovered": n(row.get("hover_sessions")),
            "Attentive (2s+)": n(row.get("attentive_2s_sessions")),
            "Clicked": n(row.get("click_sessions")),
        })
    elements.sort(key=lambda row: (-row["Exposed"], row["Element"]))
    if elements:
        st.dataframe(elements[:18], hide_index=True, use_container_width=True)
    else:
        st.caption("No qualifying CTA hover observations. Browser/input support varies.")
    st.caption(
        "Hover and attention are not available on all devices. "
        "Do not compare hover rate on touchscreens with desktop mouse use."
    )

    st.markdown("**Browser attention interruptions by device**")
    devices = []
    for row in report.get("behavior_summary", []):
        if not isinstance(row, dict):
            continue
        counted = n(row.get("sessions"))
        if counted < 20:
            continue
        try:
            losses = float(row.get("avg_focus_losses") or 0)
        except (TypeError, ValueError):
            losses = 0.0
        devices.append({
            "Device": str(row.get("device_type") or "Unknown").title(),
            "Measured sessions": counted,
            "Avg focus losses": round(max(0.0, losses), 1),
            "Data-saver share": (
                f"{percentage(row.get('save_data_sessions'), counted):.1f}%"
                if percentage(row.get("save_data_sessions"), counted) is not None else "—"),
        })
    if devices:
        st.dataframe(devices, hide_index=True, use_container_width=True)
    else:
        st.caption("Not enough browser-context observations.")
    st.caption(
        "A focus loss can reflect ordinary multitasking rather than a problem with "
        "the page. Device and browser reporting capabilities vary."
    )


def render_public_deep_insights(section: str, window: str, traffic: dict) -> None:
    """On-demand advanced reports. One additional public content RPC at most."""
    if section == "signals":
        _insights(traffic, window)
        return
    if section == "channels":
        _channels(traffic)
        return
    if section == "behavior":
        try:
            behavior = fetch_public_behavior_aggregate(window)
        except RuntimeError as exc:
            st.warning(str(exc))
            return
        _behavior(behavior)
        return
    try:
        content = fetch_public_content_aggregate(window)
    except RuntimeError as exc:
        st.warning(str(exc))
        st.caption("Traffic reports remain available; no missing values are represented as zero.")
        return
    if section == "content":
        _content(content)
    elif section == "ctas":
        _ctas(content)
    elif section == "experience":
        _experience(content)
    elif section == "coverage":
        _coverage(traffic, content)
