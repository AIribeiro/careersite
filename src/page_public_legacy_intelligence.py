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


def _dashboard_header(title: str, evidence: str) -> None:
    st.markdown(f"#### {title}")
    st.caption(evidence)


def _kpi_strip(items: list[tuple[str, str, str]]) -> None:
    """Headline + denominator/context, without exposing underlying records."""
    if not items:
        return
    cols = st.columns(len(items), gap="medium")
    for col, (label, value, context) in zip(cols, items):
        with col:
            with st.container(border=True):
                st.metric(label, value)
                st.caption(context)


def _ranked_chart(
    rows: list[dict], label: str, measure: str, *,
    title: str, note: str = "", color: str = BLUE,
    limit: int = 9, percentage_axis: bool = False,
) -> None:
    """Compact aggregate bar chart, with precise counts in hover tooltips.

    Charts rank measured cohorts, not individual sessions. No raw tables,
    unbounded category lists, or private source labels are rendered.
    """
    st.markdown(f"**{title}**")
    if note:
        st.caption(note)
    clean = []
    for row in rows:
        if not isinstance(row, dict) or not str(row.get(label) or "").strip():
            continue
        try:
            value = float(row.get(measure))
        except (TypeError, ValueError):
            continue
        if not (0 <= value < float("inf")):
            continue
        clean.append({
            **row,
            label: str(row[label])[:85],
            measure: value,
        })
    clean.sort(key=lambda item: (-item[measure], item[label]))
    clean = clean[:limit]
    if not clean:
        st.caption("Not enough recorded observations for this comparison.")
        return
    ordered = [row[label] for row in clean]
    max_value = max(row[measure] for row in clean)
    height = max(180, min(420, len(clean) * 37))
    tooltip = [
        {"field": label, "type": "nominal", "title": label},
        {"field": measure, "type": "quantitative",
         "title": measure, "format": ".1f" if percentage_axis else ",.0f"},
    ]
    for dimension in ("Sessions", "Exposed", "Clicked", "Measured sessions", "Page sessions", "Recorded transitions"):
        if dimension in clean[0] and dimension != measure:
            tooltip.append({"field": dimension, "type": "quantitative",
                            "title": dimension, "format": ",.0f"})
    st.vega_lite_chart(
        data=clean,
        spec={
            "height": height,
            "mark": {"type": "bar", "cornerRadiusEnd": 5, "color": color},
            "encoding": {
                "y": {"field": label, "type": "nominal", "sort": ordered,
                      "axis": {"title": None, "labelLimit": 230, "labelColor": "#625e59"}},
                "x": {"field": measure, "type": "quantitative",
                      "scale": {"domain": [0, max(1.0, max_value * 1.12)]},
                      "axis": {"title": "%" if percentage_axis else None,
                               "gridColor": "#eee9e3",
                               "format": ".1f" if percentage_axis else ",.0f"}},
                "tooltip": tooltip,
            },
            "config": {"view": {"stroke": None},
                       "axis": {"ticks": False, "domain": False, "labelFontSize": 12}},
        },
        use_container_width=True,
        theme=None,
    )


def _decision_note(observation: str, next_check: str) -> None:
    with st.container(border=True):
        st.markdown(f"**What the evidence suggests:** {observation}")
        st.caption(f"Next to examine: {next_check}")


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
    sessions = n(totals.get("sessions"))
    grouped = channel_rollup(data.get("attribution", []))
    _dashboard_header(
        "Acquisition and attention by channel",
        "A channel is the first observed traffic source, grouped to protect "
        "campaign and relationship details. Outcomes are browser-session signals.",
    )
    if not grouped:
        st.info("No comparable channel observations in this period.")
        return
    direct = next((r["sessions"] for r in grouped
                   if r["Channel"] == "Direct / unattributed"), 0)
    measured = sum(row["sessions"] for row in grouped)
    credited = max(0, sessions - direct) if measured == sessions else max(0, measured - direct)
    leader = max((r for r in grouped if r["Channel"] != "Direct / unattributed"),
                 key=lambda r: r["sessions"], default=None)
    _kpi_strip([
        ("Recorded sessions", f"{sessions:,}", "Traffic collector; not unique people"),
        ("Source-tagged sessions", f"{credited:,}",
         "First-touch attribution outside direct / unattributed"),
        ("Largest tagged channel", leader["Channel"] if leader else "—",
         f"{leader['sessions']:,} sessions" if leader else "No named channel observed"),
    ])
    if measured != sessions:
        st.caption("Grouped channels do not reconcile to the traffic total in this window. "
                   "Shares use the grouped source cohort only.")

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        _ranked_chart(
            [{"Channel": r["Channel"], "Sessions": r["sessions"],
              "Measured sessions": r["sessions"]} for r in grouped],
            "Channel", "Sessions", title="Reach by broad channel", color=ACCENT,
            note="Mutually exclusive first-touch cohorts; exact counts on hover.",
        )
    with right:
        eligible = [
            {"Channel": r["Channel"],
             "Engagement rate (%)": r["Engagement rate"],
             "Sessions": r["sessions"],
             "Engaged sessions": r["engaged_sessions"]}
            for r in grouped if r["sessions"] >= 20
            and r["Engagement rate"] is not None
        ]
        _ranked_chart(
            eligible, "Channel", "Engagement rate (%)",
            title="Recorded engagement by channel", percentage_axis=True,
            note="Only channels with 20+ recorded sessions; not a measure of visitor identity.",
            color=GREEN,
        )

    st.markdown("**What happens after acquisition?**")
    cohorts = [
        {"Channel": r["Channel"],
         "Article reach (%)": percentage(r["article_sessions"], r["sessions"]),
         "CV-opening sessions": r["cv_sessions"],
         "Sessions": r["sessions"]}
        for r in grouped if r["sessions"] >= 20
        and percentage(r["article_sessions"], r["sessions"]) is not None
    ]
    _ranked_chart(cohorts, "Channel", "Article reach (%)",
                  title="Recorded article reach among source cohorts",
                  note="Uses the traffic collector's article definition, not the publication reader total.",
                  percentage_axis=True, limit=7, color=BLUE)
    if direct and sessions >= 50 and direct / sessions >= .35:
        _decision_note(
            f"{direct:,} of {sessions:,} sessions are direct / unattributed. "
            "This is an acquisition measurement gap, not proof of direct navigation.",
            "Check tagging consistency across shared portfolio links before comparing channels.",
        )
    elif leader and leader["sessions"] >= 20:
        _decision_note(
            f"{leader['Channel']} has the largest recorded source-tagged cohort "
            f"({leader['sessions']:,} sessions). Reach alone does not measure qualified attention.",
            "Compare engagement and subsequent article reach before increasing distribution.",
        )
    st.caption("Channel groups are aggregated, not individual campaigns. Channel-specific "
               "engagement and article sessions can overlap. Do not combine these counts "
               "or equate them with identified visitors, employers or hiring intent.")


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
    _dashboard_header(
        "Reading depth and audience journeys",
        "Which content earns attention, where readers move next, and how far "
        "visitors reach through individual pages. Only measured sessions count.",
    )
    quality = report.get("quality") or {}
    multi = report.get("multi_article") or {}
    ordered = report.get("ordered_funnel") or {}
    reader_sessions = n(multi.get("reader_sessions"))
    multi_sessions = n(multi.get("multi_article_sessions"))
    ordered_sessions = n(ordered.get("article_to_impact_sessions"))
    article_sessions = n(ordered.get("article_sessions"))
    _kpi_strip([
        ("Article-reading sessions", f"{reader_sessions:,}",
         "Content reader cohort; not unique people"),
        ("Multi-article share",
         f"{percentage(multi_sessions, reader_sessions):.1f}%"
         if percentage(multi_sessions, reader_sessions) is not None else "—",
         f"{multi_sessions:,} of {reader_sessions:,} reader sessions"),
        ("Article → Experience",
         f"{percentage(ordered_sessions, article_sessions):.1f}%"
         if percentage(ordered_sessions, article_sessions) is not None else "—",
         f"{ordered_sessions:,} of {article_sessions:,} ordered sessions"),
    ])
    rows = _article_rows(report)
    journeys = _journey_rows(report)
    left, right = st.columns(2, gap="large")
    with left:
        _ranked_chart(
            [{"Article": row["Article"][:60], "Reader sessions": row["Reader sessions"],
              "Measured sessions": row["Depth measured"]} for row in rows[:12]],
            "Article", "Reader sessions", title="Publications earning reader sessions",
            note="Ranked by measured browser sessions, not all-time popularity.",
            color=ACCENT,
        )
    with right:
        depth = []
        for row in rows:
            measured = row["Depth measured"]
            source = next((item for item in report.get("performance", [])
                           if isinstance(item, dict) and item.get("kind") == "article"
                           and _content_name(item.get("content")) == row["Article"]), None)
            if not source or measured < 20:
                continue
            rate = percentage(source.get("three_quarter_sessions"), measured)
            if rate is None:
                continue
            depth.append({"Article": row["Article"][:60], "Reached 75% (%)": rate,
                          "Measured sessions": measured})
        _ranked_chart(
            depth, "Article", "Reached 75% (%)",
            title="Deep-reading evidence", percentage_axis=True, color=GREEN,
            note="75% article-depth reach among 20+ depth-measured sessions. "
                 "Unavailable is not interpreted as zero.",
        )

    st.markdown("#### Confirmed paths between portfolio content")
    if journeys:
        path_rows = [
            {"Journey": f"{row['From'][:32]} → {row['To'][:32]}",
             "Sessions": row["Sessions"],
             "Recorded transitions": row["Recorded transitions"]}
            for row in journeys[:12]
        ]
        _ranked_chart(path_rows, "Journey", "Sessions",
                      title="Most frequent consecutive destinations",
                      note="A transition requires two recorded content views in one tab. "
                           "Counts overlap across different paths.", limit=10, color=BLUE)
        top = journeys[0]
        _decision_note(
            f"The most frequently observed continuation is "
            f"{top['From']} → {top['To']} ({top['Sessions']:,} sessions). "
            "This describes navigation, not the visitor's motivation.",
            "Review whether contextual links make the next relevant page easier to find.",
        )
    else:
        st.info("No consecutive content-view transitions were recorded in this period.")

    section_rows = []
    for item in report.get("section_reach", []):
        if not isinstance(item, dict):
            continue
        base = n(item.get("page_sessions"))
        reached = n(item.get("reached_sessions"))
        rate = percentage(reached, base)
        if base < 20 or rate is None:
            continue
        section_rows.append({
            "Page": _content_name(item.get("page")),
            "Section": _cta_name(item.get("section_label")),
            "Section reach (%)": rate,
            "Sessions": reached,
            "Page sessions": base,
        })
    st.markdown("#### Section reach within a page")
    if section_rows:
        pages = sorted({row["Page"] for row in section_rows})
        preferred = pages.index("Home") if "Home" in pages else 0
        selected = st.selectbox("Page to compare", pages, index=preferred,
                                key="portfolio_advanced_section_page")
        matching = [row for row in section_rows if row["Page"] == selected]
        _ranked_chart(matching, "Section", "Section reach (%)",
                      title=f"Recorded visibility · {selected}",
                      note="Page-session denominator displayed on hover. "
                           "Historical sections may have incomplete instrumentation.",
                      percentage_axis=True, color=GREEN, limit=12)
    else:
        st.caption("Not enough section-reach observations to compare this period.")
    st.caption(
        "Article reading, navigation transitions and section reach come from the "
        "content collector. Do not reconcile these sessions to the historical "
        "traffic collector or infer individual reader identity."
    )


def _ctas(report: dict) -> None:
    _dashboard_header(
        "Calls to action: visibility and response",
        "CTA exposures and clicks are recorded independently. This is a "
        "diagnostic for placement and measurement, not an A/B test.",
    )
    rows = []
    for item in report.get("cta_placements", []):
        if not isinstance(item, dict):
            continue
        exposed, clicked = n(item.get("exposed_sessions")), n(item.get("click_sessions"))
        if exposed < 10:
            continue
        placement = str(item.get("placement") or "").split(":", 1)[0].lower()
        page = placement if placement in (
            "home", "about", "impact", "thinking", "briefings",
            "briefing", "contact", "ai-data-governance",
        ) else "portfolio"
        name = _cta_name(item.get("label"))
        rate = percentage(clicked, exposed)
        rows.append({
            "Action": f"{name[:53]} · {page.title()}",
            "Exposed": exposed, "Clicked": clicked,
            "Recorded response (%)": rate,
        })
    rows.sort(key=lambda row: (-row["Exposed"], row["Action"]))
    if not rows:
        st.info("There is not enough instrumented CTA exposure in this period.")
        return
    audit = [row for row in rows if row["Exposed"] >= 30 and row["Clicked"] == 0]
    activated = sum(1 for row in rows if row["Clicked"] >= 1)
    most = rows[0]
    _kpi_strip([
        ("Measured placements", f"{len(rows):,}", "10+ exposed sessions per placement"),
        ("With recorded clicks", f"{activated:,}", "Placement observations; not unique visitors"),
        ("Check tracking or placement", f"{len(audit):,}",
         "30+ exposed sessions with no recorded clicks"),
    ])
    left, right = st.columns(2, gap="large")
    with left:
        _ranked_chart(rows, "Action", "Exposed",
                      title="Most visible calls to action",
                      note="Exposure means a CTA was observed, not that it was read.",
                      color=ACCENT, limit=10)
    with right:
        eligible = [row for row in rows
                    if row["Exposed"] >= 30 and row["Recorded response (%)"] is not None]
        _ranked_chart(eligible, "Action", "Recorded response (%)",
                      title="Recorded response where measurable",
                      note="Click-session / exposure-session ratio for 30+ exposed sessions. "
                           "Counts and denominator on hover.",
                      color=GREEN, percentage_axis=True, limit=10)
    st.markdown("#### Which action merits investigation?")
    if audit:
        ranked = sorted(audit, key=lambda row: -row["Exposed"])
        for row in ranked[:3]:
            _decision_note(
                f"{row['Action']} was observed in {row['Exposed']:,} exposure sessions "
                "without a recorded click session. This is not proof the CTA failed.",
                "Confirm the click event fires and the placement is visible before changing the copy.",
            )
    elif most["Exposed"] >= 30:
        _decision_note(
            f"{most['Action']} has the widest recorded exposure "
            f"({most['Exposed']:,} placement sessions).",
            "Compare observed responses against comparable placements, then examine destination confirmation.",
        )
    st.caption(
        "Exposure and click collection changed across some site releases. "
        "Placements can be seen by the same browser session; counts cannot be "
        "summed as independent people or used as experimental conversion estimates."
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
