"""Legacy visitor diagnostics for the anonymous Portfolio Analytics overview.

This is deliberately NOT the owner-only legacy renderer: it consumes only the
existing aggregate public dashboard RPC and never calls hiring intelligence,
source/campaign audits, private job data, or authenticated reporting endpoints.
The section is loaded only after the visitor enables the legacy-insights toggle.
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
    st.subheader("Legacy visitor analytics")
    st.caption(
        "The original traffic, audience and exploration reports, retained for historical comparison. "
        "These are recorded browser sessions, not unique visitors or identified employers. "
        "Automation and unconfirmed sessions may be included."
    )
    try:
        data = _cached_public_traffic(window)
    except (ValueError, RuntimeError, TimeoutError):
        st.warning("Legacy visitor reporting is temporarily unavailable.")
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
    st.caption(f"Reporting period: {period} · first-party historical aggregates")
    # One native select control avoids a horizontal bar of eleven tiny tabs
    # on mobile. Each report is rendered only when selected.
    section = st.selectbox(
        "Explore historical analytics",
        options=list(_SECTIONS),
        format_func=lambda name: _SECTIONS[name],
        index=0,
        key="portfolio_legacy_insights_section_v2",
    ) or "signals"
    if st.button("Refresh legacy reports", key="portfolio_legacy_refresh"):
        _cached_public_traffic.clear()
        from page_public_legacy_intelligence import (
            fetch_public_content_aggregate, fetch_public_behavior_aggregate,
        )
        fetch_public_content_aggregate.clear()
        fetch_public_behavior_aggregate.clear()
        st.rerun()

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
        left, right = st.columns(2, gap="large")
        with left:
            _section("Audience", "Device mix")
            _donut_chart(data.get("devices", []), "device_type")
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
        "remain in the authenticated workspace. Legacy totals are not equivalent "
        "to quality-filtered portfolio readership."
    )
