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
    "overview": "Overview & trends",
    "audience": "Audience & origins",
    "attribution": "Attribution & campaigns",
    "content": "Content & actions",
    "experience": "Engagement & UX",
    "quality": "Data quality",
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


def _overview_dashboard(data: dict, window: str) -> None:
    """Outcome-led traffic trends, destinations and measured exploration."""
    from page_public_legacy_intelligence import _insights, _kpi_strip
    totals = data.get("totals") or {}
    sessions = _count(totals.get("sessions"))
    engaged = _count(totals.get("engaged_sessions"))
    cv_sessions = _count(totals.get("cv_sessions"))
    _insights(data, window)
    st.markdown("#### Traffic and exploration")
    _kpi_strip([
        ("Recorded sessions", f"{sessions:,}", "Browser sessions, not unique people"),
        ("Engaged sessions", _pct(engaged, sessions),
         f"{engaged:,} of {sessions:,} recorded sessions"),
        ("Median active time", _seconds(totals.get("median_active_seconds")),
         "Measured visible engagement only"),
    ])
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        _section("Traffic", "Recorded sessions over time")
        _daily_chart(data.get("daily", []))
    with right:
        _section("Reach", "Portfolio section observations")
        _funnel(sessions, _count(totals.get("impact_sessions")),
                _count(totals.get("lens_sessions")), cv_sessions)
        st.caption("Each stage is a separate observed cohort, not a sequential conversion funnel.")
    left, right = st.columns(2, gap="large")
    with left:
        _section("Destinations", "Most visited portfolio pages")
        _bar_chart(_page_rows(data.get("pages", [])), "page_label",
                   value="sessions", limit=10, color=BLUE)
    with right:
        _section("Leadership", "Role-lens exploration")
        _bar_chart(data.get("lenses", []), "lens", limit=8, color=GREEN)


def _audience_origin_dashboard(data: dict) -> None:
    """Visitor origin is an observed browser and referral context, not identity."""
    from page_public_legacy_intelligence import _kpi_strip, _ranked_chart
    from portfolio_public_attribution import referrer_cohorts
    totals = data.get("totals") or {}
    sessions = _count(totals.get("sessions"))
    countries = sorted(
        (row for row in data.get("countries", [])
         if isinstance(row, dict) and _count(row.get("sessions"))),
        key=lambda row: -_count(row.get("sessions")),
    )
    devices = sorted(
        (row for row in data.get("devices", [])
         if isinstance(row, dict) and _count(row.get("sessions"))),
        key=lambda row: -_count(row.get("sessions")),
    )
    referrers = referrer_cohorts(data.get("referrers", []))
    referrer_total = sum(row["sessions"] for row in referrers)
    no_referrer = sum(row["sessions"] for row in referrers
                      if row["Label"] == "No referrer recorded")
    known_referrers = max(0, referrer_total - no_referrer)
    leading_country = countries[0] if countries else {}
    leading_device = devices[0] if devices else {}
    st.markdown("#### Where recorded sessions appear to originate")
    st.caption(
        "Country is coarse network geography. Referrer is a browser-provided origin "
        "host; it often goes missing when links open in apps or privacy controls "
        "strip it. A country or referrer cannot identify a person, employer "
        "or confirm that a session was human."
    )
    _kpi_strip([
        ("Top country",
         str(leading_country.get("country_code") or "—").upper(),
         f"{_count(leading_country.get('sessions')):,} sessions; network-level estimate"),
        ("Known referrer hosts",
         f"{known_referrers:,}",
         f"{no_referrer:,} of {referrer_total:,} referrer-cohort sessions have no recorded host"),
        ("Main device", str(leading_device.get("device_type") or "—").title(),
         f"{_count(leading_device.get('sessions')):,} recorded sessions"),
    ])
    left, right = st.columns(2, gap="large")
    with left:
        _ranked_chart(
            [{"Country": str(row.get("country_code") or "Unknown").upper(),
              "Sessions": _count(row.get("sessions"))} for row in countries],
            "Country", "Sessions", title="Sessions by observed country",
            note="Network location, not nationality or verified human audience.",
            color=GREEN, limit=12,
        )
    with right:
        tagged_referrers = [
            {"Referrer": row["Label"], "Sessions": row["sessions"]}
            for row in referrers if row["Label"] != "No referrer recorded"
        ]
        _ranked_chart(
            tagged_referrers, "Referrer", "Sessions",
            title="Recognized referring websites",
            note="Known referrer hosts only. Untagged/direct sessions are "
                 "shown in the KPI above rather than hidden from measurement.",
            color=BLUE, limit=10,
        )

    st.markdown("#### Entry and exit patterns")
    left, right = st.columns(2, gap="large")
    with left:
        _section("Navigation", "Where sessions begin")
        _bar_chart(data.get("landing_pages", []), "landing_page",
                   limit=10, color=ACCENT)
    with right:
        _section("Navigation", "Where sessions last appear")
        _bar_chart(data.get("exit_pages", []), "exit_page",
                   limit=10, color=BLUE)
    st.caption("An observed exit is not proof that the visitor abandoned the site; "
               "browser-tab and tracking rules affect these counts.")

    st.markdown("#### Browser and device context")
    left, right = st.columns(2, gap="large")
    with left:
        _section("Device", "Measured device mix")
        _donut_chart(devices, "device_type")
        _section("Locale", "Browser languages")
        _bar_chart(data.get("languages", []), "language", limit=8)
    with right:
        _section("Technology", "Browser families")
        _bar_chart(data.get("browsers", []), "browser_family", color=BLUE)
        _section("Platform", "Operating systems")
        _bar_chart(data.get("operating_systems", []), "os_family", color=GREEN)
    with st.expander("Additional regional context", expanded=False):
        _section("Locale", "Browser time zones")
        _bar_chart(data.get("timezones", []), "timezone", limit=12)
    st.caption("Browser language and time zone are software settings, not "
               "verified residences. Automated sessions may be present.")


def _engagement_traffic_dashboard(data: dict) -> None:
    from page_public_legacy_intelligence import _kpi_strip
    totals = data.get("totals") or {}
    sessions = _count(totals.get("sessions"))
    engaged = _count(totals.get("engaged_sessions"))
    confirmed = _count(totals.get("confirmed_duration_sessions"))
    st.markdown("#### Interaction depth and timing")
    _kpi_strip([
        ("Recorded engagement", _pct(engaged, sessions),
         f"{engaged:,} of {sessions:,} browser sessions"),
        ("Median active time", _seconds(totals.get("median_active_seconds")),
         "Confirmed visible activity; not verified reading"),
        ("Duration measured", _pct(confirmed, sessions),
         f"{confirmed:,} of {sessions:,} sessions"),
    ])
    left, right = st.columns(2, gap="large")
    with left:
        _section("Engagement", "Observed active-time distribution")
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
    st.caption("Unconfirmed active time is not a zero-second visit. Timing and "
               "device comparisons describe recorded sessions only.")


def _traffic_actions(data: dict) -> None:
    from page_public_legacy_intelligence import _kpi_strip
    totals = data.get("totals") or {}
    cv_downloads = next((
        _count(row.get("events")) for row in data.get("events", [])
        if isinstance(row, dict) and row.get("event_name") == "cv_download"
    ), 0)
    _kpi_strip([
        ("CV downloads", f"{cv_downloads:,}", "Recorded download events"),
        ("CV-opening sessions", f"{_count(totals.get('cv_sessions')):,}",
         "Sessions reaching the CV"),
        ("Contact-channel sessions",
         f"{_count(totals.get('contact_channel_sessions')):,}",
         "Observed contact interaction, not confirmed recruitment"),
    ])
    _section("Actions", "Recorded interaction cohorts",
             "A browser session may register multiple event types.")
    _bar_chart(_event_rows(data.get("events", [])),
               "activity", limit=12, color=GREEN, height=300)


def render_public_legacy_insights(window: str) -> None:
    """Advanced Insights, public and visible by default, grouped into six tabs."""
    st.subheader("Advanced Insights")
    st.caption(
        "Portfolio reach, audience origin, tagged campaigns, content outcomes "
        "and browser experience. Counts are first-party aggregates, not "
        "unique visitors, occupations or identified organizations."
    )
    try:
        data = _cached_public_traffic(window)
    except (ValueError, RuntimeError, TimeoutError):
        st.warning("Advanced Insights are temporarily unavailable.")
        return
    period = str(data.get("period_label") or REPORTING_WINDOW_LABELS.get(window, window))
    st.caption(f"Reporting period: {period} · measured browser and content cohorts")
    tab_keys = list(_SECTIONS)
    tabs = st.tabs(
        [_SECTIONS[name] for name in tab_keys],
        key="portfolio_advanced_insights_tabs_v2",
        on_change="rerun",
        width="stretch",
    )
    opened = next(
        ((name, tab) for name, tab in zip(tab_keys, tabs) if tab.open),
        None,
    )
    if opened is None:
        return
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
            _overview_dashboard(data, window)
        elif section == "audience":
            _audience_origin_dashboard(data)
        elif section == "attribution":
            from page_public_legacy_intelligence import (
                _channels, _attribution_families, fetch_public_content_aggregate,
            )
            _channels(data)
            try:
                content = fetch_public_content_aggregate(window)
            except RuntimeError:
                st.warning("Campaign details are temporarily unavailable; "
                           "source-channel aggregates remain current.")
            else:
                _attribution_families(data, content)
        elif section == "content":
            from page_public_legacy_intelligence import (
                _content, _ctas, fetch_public_content_aggregate,
            )
            try:
                content = fetch_public_content_aggregate(window)
            except RuntimeError:
                st.warning("Content and CTA reporting is temporarily unavailable.")
            else:
                _content(content)
                st.divider()
                _ctas(content)
            st.divider()
            st.markdown("#### Portfolio actions")
            _traffic_actions(data)
        elif section == "experience":
            from page_public_legacy_intelligence import render_public_deep_insights
            _engagement_traffic_dashboard(data)
            st.divider()
            render_public_deep_insights("experience", window, data)
            st.divider()
            render_public_deep_insights("behavior", window, data)
        elif section == "quality":
            from page_public_legacy_intelligence import render_public_deep_insights
            render_public_deep_insights("coverage", window, data)
        st.caption(
            "Anonymous aggregates only. Private recruiting records, individual "
            "campaign audit trails and raw telemetry stay in the authenticated workspace. "
            "Traffic, content and browser observations use distinct definitions."
        )
