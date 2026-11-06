"""Advanced visitor insights for the anonymous Portfolio Analytics overview.

This is deliberately NOT the owner-only detailed renderer: it consumes only the
existing aggregate public dashboard RPC and never calls hiring intelligence,
source/campaign audits, private job data, or authenticated reporting endpoints.
The tabs are visible by default; only the active tab renders its report.
"""
from __future__ import annotations

import streamlit as st

from analytics_event_labels import event_label
from page_analytics import (
    ACCENT, BLUE, GREEN, REPORTING_WINDOW_LABELS,
    _bar_chart, _count, _daily_chart, _donut_chart, _duration_chart,
    _fetch_dashboard, _funnel, _hour_chart, _page_rows, _pct, _section,
    _seconds,
)


_SECTIONS = {
    "signals": "Executive findings",
    "overview": "Traffic overview",
    "audience": "Audience",
    "discovery": "Discovery paths",
    "engagement": "Engagement",
    "actions": "Actions & conversions",
    "channels": "Channel outcomes",
    "content": "Content & journeys",
    "ctas": "CTA opportunities",
    "experience": "Site performance",
    "behavior": "Attention & friction",
    "coverage": "Data quality",
}


@st.cache_data(ttl=300, max_entries=12, show_spinner=False)
def _cached_public_traffic(window: str) -> dict:
    """Reuse the same approved anonymous aggregate for each drill-down rerun."""
    return _fetch_dashboard(window)


def _source_channel(label: object) -> str:
    """Map historical source tags to broad channels, never reveal raw tags."""
    raw = str(label or "").strip().lower().split("?", 1)[0].split("&", 1)[0]
    if any(value in raw for value in ("linkedin", "lnkd.in")):
        return "LinkedIn"
    if raw in ("cv", "resume", "résumé", "curriculum-vitae") or raw.startswith("cv-"):
        return "CV distribution"
    if any(value in raw for value in ("google", "bing", "search", "duckduckgo")):
        return "Search"
    if any(value in raw for value in ("newsletter", "email", "outlook", "gmail")):
        return "Email / newsletter"
    if raw in ("x", "wa", "fb") or any(value in raw for value in (
        "facebook", "instagram", "threads", "twitter", "x.com",
        "whatsapp", "reddit", "bluesky",
    )):
        return "Other social"
    if raw in ("", "direct", "direct/unknown", "unattributed", "unknown", "none", "(direct)"):
        return "Direct / unattributed"
    return "Other sources"


def _channel_rows(rows: object) -> list[dict]:
    """Aggregate mutually exclusive first-touch source cohorts into broad groups."""
    if not isinstance(rows, list):
        return []
    grouped: dict[str, int] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        channel = _source_channel(item.get("attribution_source"))
        grouped[channel] = grouped.get(channel, 0) + _count(item.get("sessions"))
    return [
        {"channel": channel, "sessions": count}
        for channel, count in sorted(grouped.items(), key=lambda entry: (-entry[1], entry[0]))
        if count > 0
    ]


def _event_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    return [
        {"activity": event_label(row.get("event_name")), "sessions": _count(row.get("sessions"))}
        for row in rows if isinstance(row, dict)
    ]


def render_public_legacy_insights(window: str) -> None:
    """Render historical visitor insights with no sign-in or owner data access."""
    st.subheader("Advanced Insights")
    st.caption(
        "Explore audience, acquisition, content journeys and engagement using recorded portfolio data. "
        "These are recorded browser sessions, not unique visitors or identified employers. "
        "Automation and unconfirmed sessions may be included."
    )
    try:
        data = _cached_public_traffic(window)
    except (ValueError, RuntimeError, TimeoutError):
        st.warning("Advanced Insights are temporarily unavailable.")
        return

    totals = data.get("totals") if isinstance(data.get("totals"), dict) else {}
    sessions = _count(totals.get("sessions"))
    engaged = _count(totals.get("engaged_sessions"))
    cv_sessions = _count(totals.get("cv_sessions"))
    contact_sessions = _count(totals.get("contact_channel_sessions"))
    cv_downloads = next(
        (_count(row.get("events")) for row in data.get("events", [])
         if isinstance(row, dict) and row.get("event_name") == "cv_download"),
        0,
    )
    period = str(data.get("period_label") or REPORTING_WINDOW_LABELS.get(window, window))
    st.caption(f"Reporting period: {period} · first-party aggregate analytics")
    # Native stateful tabs keep navigation directly visible. Only the active
    # panel renders: Streamlit otherwise eagerly computes all tab bodies,
    # triggering every analytics RPC and chart on every interaction.
    tab_keys = list(_SECTIONS)
    tabs = st.tabs(
        [_SECTIONS[name] for name in tab_keys],
        key="portfolio_advanced_insights_tabs",
        on_change="rerun",
        width="stretch",
    )
    opened = next(
        ((name, tab) for name, tab in zip(tab_keys, tabs) if tab.open),
        None,
    )
    if opened is None:
        return  # No active tab during a transient widget-state update.
    section, active_tab = opened
    if st.button("Refresh advanced insights", key="portfolio_advanced_refresh"):
        _cached_public_traffic.clear()
        from page_public_legacy_intelligence import (
            fetch_public_content_aggregate, fetch_public_behavior_aggregate,
        )
        fetch_public_content_aggregate.clear()
        fetch_public_behavior_aggregate.clear()
        st.rerun()

    with active_tab:
        if section == "overview":
            metrics = st.columns(4)
            metrics[0].metric("Measured sessions", sessions)
            metrics[1].metric("Engaged sessions", engaged, _pct(engaged, sessions))
            metrics[2].metric("Pages per session",
                              f"{float(totals.get('avg_pages_per_session') or 0):.2f}")
            metrics[3].metric("Average active time", _seconds(totals.get("avg_active_seconds")))
            left, right = st.columns([1.6, 1], gap="large")
            with left:
                _section("Traffic", "Sessions over time")
                _daily_chart(data.get("daily", []))
            with right:
                _section("Exploration", "Depth of portfolio journey")
                _funnel(sessions, _count(totals.get("impact_sessions")),
                        _count(totals.get("lens_sessions")), cv_sessions)
            left, right = st.columns(2, gap="large")
            with left:
                _section("Portfolio", "Pages explored by sessions")
                _bar_chart(_page_rows(data.get("pages", [])), "page_label",
                           value="sessions", limit=12, color=BLUE)
            with right:
                _section("Leadership lenses", "Most explored role lenses")
                _bar_chart(data.get("lenses", []), "lens", limit=8)

        elif section == "audience":
            from page_public_legacy_intelligence import _kpi_strip
            devices = sorted(
                (row for row in data.get("devices", []) if isinstance(row, dict)),
                key=lambda row: -_count(row.get("sessions")),
            )
            countries = [row for row in data.get("countries", [])
                         if isinstance(row, dict) and _count(row.get("sessions"))]
            top = devices[0] if devices else {}
            _kpi_strip([
                ("Tracked devices", str(len([d for d in devices if _count(d.get("sessions"))])),
                 "Recorded device categories"),
                ("Largest device cohort",
                 str(top.get("device_type") or "—").title(),
                 f"{_count(top.get('sessions')):,} browser sessions"),
                ("Country coverage", str(len(countries)),
                 "Coarse country codes, not verified identities"),
            ])
            left, right = st.columns(2, gap="large")
            with left:
                _section("Audience", "Device mix · measured sessions")
                _bar_chart(devices, "device_type", value="sessions",
                           limit=6, height=280)
                _section("Technology", "Browsers")
                _bar_chart(data.get("browsers", []), "browser_family", color=BLUE)
                _section("Locale", "Browser languages")
                _bar_chart(data.get("languages", []), "language")
            with right:
                _section("Geography", "Countries")
                _bar_chart(data.get("countries", []), "country_code", color=GREEN)
                _section("Technology", "Operating systems")
                _bar_chart(data.get("operating_systems", []), "os_family", color=BLUE)
                _section("Locale", "Time zones")
                _bar_chart(data.get("timezones", []), "timezone")
            st.caption("Geography is coarse country-level reporting; no IP addresses or individual identities are shown.")

        elif section == "discovery":
            from page_public_legacy_intelligence import _kpi_strip
            broad = _channel_rows(data.get("attribution", []))
            directly = sum(_count(row.get("sessions")) for row in broad
                           if row.get("channel") == "Direct / unattributed")
            landings = [row for row in data.get("landing_pages", [])
                        if isinstance(row, dict) and _count(row.get("sessions"))]
            _kpi_strip([
                ("Broad acquisition channels", str(len(broad)),
                 "Groups of observed first-touch attribution"),
                ("Unattributed traffic", f"{_pct(directly,sessions)}",
                 f"{directly:,} of {sessions:,} browser sessions"),
                ("Recorded entry destinations", str(len(landings)),
                 "Distinct landing destinations with observations"),
            ])
            left, right = st.columns(2, gap="large")
            with left:
                _section("Acquisition", "Broad first-touch channels",
                         "Historical source tags are grouped; individual campaigns and role tags are not public.")
                _bar_chart(_channel_rows(data.get("attribution", [])), "channel",
                           limit=8, color=ACCENT)
                _section("Navigation", "Landing pages")
                _bar_chart(data.get("landing_pages", []), "landing_page",
                           limit=10, color=GREEN)
            with right:
                _section("Navigation", "Exit pages")
                _bar_chart(data.get("exit_pages", []), "exit_page", limit=10, color=BLUE)
                _section("Reach", "Portfolio destinations")
                _bar_chart(_page_rows(data.get("pages", [])), "page_label",
                           value="sessions", limit=12)
            st.caption("First-touch channel groups describe recorded source tags, not confirmed reader origins.")

        elif section == "engagement":
            from page_public_legacy_intelligence import _kpi_strip
            confirmed = _count(totals.get("confirmed_duration_sessions"))
            _kpi_strip([
                ("Recorded engagement", _pct(engaged, sessions),
                 f"{engaged:,} of {sessions:,} browser sessions"),
                ("Median active time", _seconds(totals.get("median_active_seconds")),
                 "Observed visible activity; not inferred reading time"),
                ("Confirmed duration", _pct(confirmed, sessions),
                 f"{confirmed:,} of {sessions:,} sessions"),
            ])
            left, right = st.columns(2, gap="large")
            with left:
                _section("Engagement", "Active time distribution")
                _duration_chart(data.get("duration_buckets", []))
                _section("Timing", "Sessions by weekday · Stockholm")
                _bar_chart(data.get("weekdays", []), "weekday", horizontal=False,
                           limit=7, color=GREEN,
                           sort=["Monday", "Tuesday", "Wednesday", "Thursday",
                                 "Friday", "Saturday", "Sunday"])
            with right:
                _section("Timing", "Sessions by hour · Stockholm")
                _hour_chart(data.get("hours", []))
                _section("Engagement", "Engaged sessions by device")
                _bar_chart(data.get("devices", []), "device_type",
                           value="engaged_sessions", color=BLUE)
            st.caption("Active time counts visible engagement. Sessions without confirmation remain unconfirmed, not zero seconds.")

        elif section == "actions":
            metrics = st.columns(4)
            metrics[0].metric("CV downloads", cv_downloads)
            metrics[1].metric("CV-opening sessions", cv_sessions)
            metrics[2].metric("Contact-channel sessions", contact_sessions)
            metrics[3].metric("Single-page sessions", _count(totals.get("single_page_sessions")))
            left, right = st.columns(2, gap="large")
            with left:
                _section("Interactions", "Observed activity by session",
                         "A session may contribute to several activity types.")
                _bar_chart(_event_rows(data.get("events", [])),
                           "activity", limit=12, color=GREEN)
            with right:
                _section("Journey", "Recorded reach into portfolio sections")
                _funnel(sessions, _count(totals.get("impact_sessions")),
                        _count(totals.get("lens_sessions")), cv_sessions)
            st.caption("CV and contact events indicate actions, not verified recruiter intent or a hiring outcome.")

        elif section in ("signals", "channels", "content", "ctas", "experience", "behavior", "coverage"):
            from page_public_legacy_intelligence import render_public_deep_insights
            render_public_deep_insights(section, window, data)

        st.caption(
            "Owner-only hiring intelligence, individual campaign/source audits and raw telemetry "
            "remain in the authenticated workspace. Recorded-session totals are not equivalent "
            "to quality-filtered portfolio readership."
        )
