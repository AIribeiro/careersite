"""Owner-only, ISO-week-aware WEEKLY AI content report.

This is a classification of existing session-scoped events, not a second tracker.
Never add its subset metrics to whole-portfolio totals. Older periods remain
unmeasured when the weekly section was not instrumented.
"""
from __future__ import annotations

from urllib.parse import urlencode

import altair as alt
import streamlit as st

from page_content_intelligence import fetch_intelligence
from site_cms import fetch_published_articles
from thinking_weekly_brief import edition_week, is_weekly_brief, sorted_editions

BASE_URL = "https://jairribeiro-ai.streamlit.app"


def _n(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "—"


def weekly_ai_report(data: dict, editions: list[object]) -> dict:
    """Deterministic aggregate-only metrics from the established owner RPC.

    A section reached by a session and an edition opened by that session are
    separate stages. Neither is added to website visitors or article totals.
    """
    ordered = sorted_editions(editions)
    performance = {
        str(row.get("content") or ""): row
        for row in data.get("performance", [])
        if row.get("kind") == "article"
    }
    sections = {
        (str(row.get("page") or ""), str(row.get("section_key") or "")): row
        for row in data.get("section_reach", [])
    }
    cards = data.get("article_cards", []) or []
    ctas = data.get("cta_placements", []) or []
    feature = sections.get(("thinking", "weekly-ai-feature"), {})
    archive = sections.get(("thinking", "weekly-ai-archive"), {})
    source_links = [
        row for row in ctas
        if str(row.get("element_key") or "").startswith("weekly-ai-source:")
        and str(row.get("placement") or "").endswith(":weekly-ai-reader")
    ]
    archive_buttons = [
        row for row in ctas
        if str(row.get("element_key") or "") == "weekly_ai_archive_open"
        and str(row.get("placement") or "").endswith(":weekly-ai-feature")
    ]
    weekly_cards = [
        row for row in cards
        if str(row.get("element_key") or "").startswith("weekly-ai-")
        and (
            str(row.get("placement") or "").endswith(":weekly-ai-feature")
            or str(row.get("placement") or "").endswith(":weekly-ai-archive")
        )
    ]

    rows = []
    for article in ordered:
        year, week, start, end = edition_week(article)
        row = performance.get(article.slug, {})
        sessions = _n(row.get("sessions"))
        rows.append({
            "Week": f"Vecka {week} · {year}",
            "Week start": start.isoformat(),
            "Coverage": f"{start.strftime('%d %b')}–{end.strftime('%d %b %Y')}",
            "Headline": article.title,
            "Slug": article.slug,
            "Views": _n(row.get("views")),
            "Edition sessions": sessions,
            "Engaged ≥10s": _n(row.get("engaged_sessions")),
            "Engaged rate": _pct(_n(row.get("engaged_sessions")), sessions),
            "Confirmed read time (s)": row.get("avg_active_seconds"),
            "Share sessions": _n(row.get("sharing_sessions")),
            "Reached 75%": _pct(_n(row.get("three_quarter_sessions")), _n(row.get("depth_measured_sessions"))),
            "Later CV sessions": _n(row.get("later_cv_sessions")),
            "Later contact sessions": _n(row.get("later_contact_sessions")),
            "URL": f"{BASE_URL}/thinking/{article.slug}",
        })

    return {
        "rows": rows,
        "issue_count": len(rows),
        "feature_sessions": _n(feature.get("reached_sessions")),
        "feature_page_sessions": _n(feature.get("page_sessions")),
        "archive_sessions": _n(archive.get("reached_sessions")),
        "archive_page_sessions": _n(archive.get("page_sessions")),
        "reader_sessions": sum(row["Edition sessions"] for row in rows),
        "reader_views": sum(row["Views"] for row in rows),
        "engaged_sessions": sum(row["Engaged ≥10s"] for row in rows),
        "share_sessions": sum(row["Share sessions"] for row in rows),
        "source_click_sessions": sum(_n(row.get("click_sessions")) for row in source_links),
        "source_click_exposures": sum(_n(row.get("exposed_sessions")) for row in source_links),
        "source_rows": [{
            "Publisher": str(row.get("element_key") or "").split(":", 1)[-1],
            "Exposed sessions": _n(row.get("exposed_sessions")),
            "Click sessions": _n(row.get("click_sessions")),
        } for row in source_links],
        "issue_ctrs": [{
            "Week / issue": str(row.get("element_key") or ""),
            "Placement": str(row.get("placement") or ""),
            "Exposed sessions": _n(row.get("exposed_sessions")),
            "Click sessions": _n(row.get("click_sessions")),
        } for row in weekly_cards],
        "archive_link_exposures": sum(_n(row.get("exposed_sessions")) for row in archive_buttons),
        "archive_link_clicks": sum(_n(row.get("click_sessions")) for row in archive_buttons),
    }


def render_weekly_ai_analytics(window: str) -> None:
    st.subheader("WEEKLY AI · Content performance")
    st.caption(
        "Source: the existing first-party analytics events and published CMS editions. "
        "All counts are anonymous browser sessions, not identified readers or recruiters. "
        "This view is a subset of Thinking / article activity, never an additional site total."
    )
    try:
        data = fetch_intelligence(window)
    except RuntimeError as exc:
        st.warning(str(exc))
        return
    try:
        editions = list(fetch_published_articles())
    except RuntimeError:
        st.warning("The Weekly AI edition catalogue is unavailable; counts are not shown without verified issue metadata.")
        return

    report = weekly_ai_report(data, editions)
    if not report["issue_count"]:
        st.info("There are no published Weekly AI editions yet.")
        return

    feature_exposures = report["feature_sessions"]
    page_sessions = report["feature_page_sessions"]
    reader_sessions = report["reader_sessions"]
    engagement = report["engaged_sessions"]

    st.markdown("#### From visibility to reading")
    a, b, c, d = st.columns(4)
    a.metric("Feature reached", feature_exposures, help="Distinct page sessions with ≥15% of the Weekly AI feature visible.")
    b.metric("Feature reach", _pct(feature_exposures, page_sessions),
             help="Feature reached / Thinking landing-page sessions. Not all Thinking visits use the landing page.")
    c.metric("Weekly edition reads", reader_sessions,
             help="Sum of distinct edition-session reads. Reading two editions in one session counts twice.")
    d.metric("Engaged edition reads", _pct(engagement, reader_sessions),
             help="Edition sessions with ≥10 seconds measured active reading time; not a completion rate.")

    st.caption(
        "This is a staged view, not a conversion funnel: opening an edition directly can bypass the Thinking feature. "
        "Historical periods before the new feature tracking started cannot be reconstructed as section impressions."
    )
    a, b, c, d = st.columns(4)
    a.metric("Weekly article views", report["reader_views"])
    b.metric("Archive reached", report["archive_sessions"],
             help="Distinct sessions that visibly reached the archive section, not all archive-route loads.")
    c.metric("Archive-link clicks", report["archive_link_clicks"],
             help="Only clicks from browser sessions with an observed archive-link exposure.")
    d.metric("Publisher link clicks", report["source_click_sessions"],
             help="Sum of publisher-level click sessions after exposure; one session may open multiple publishers.")

    if report["archive_link_exposures"]:
        st.caption(
            f"Archive-link click-through after visible exposure: "
            f"{_pct(report['archive_link_clicks'], report['archive_link_exposures'])} "
            f"({report['archive_link_clicks']} of {report['archive_link_exposures']} exposed sessions)."
        )

    st.markdown("#### Weekly edition history")
    weekly_rows = report["rows"]
    if len(weekly_rows) > 1:
        graph_rows = list(reversed([{
            "Week": r["Week"], "Reads": r["Edition sessions"],
            "Engaged": r["Engaged ≥10s"], "Shares": r["Share sessions"],
        } for r in weekly_rows]))
        st.altair_chart(
            alt.Chart(alt.Data(values=graph_rows)).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("Week:N", title="Swedish ISO week", sort=None),
                y=alt.Y("Reads:Q", title="Edition-session reads", axis=alt.Axis(tickMinStep=1)),
                tooltip=["Week:N", alt.Tooltip("Reads:Q"), alt.Tooltip("Engaged:Q"), alt.Tooltip("Shares:Q")],
            ).properties(height=260),
            use_container_width=True,
        )
    st.dataframe([{
        "Week": r["Week"],
        "News period": r["Coverage"],
        "Edition": r["Headline"],
        "Views": r["Views"],
        "Reader sessions": r["Edition sessions"],
        "Engaged ≥10s": r["Engaged ≥10s"],
        "Engaged rate": r["Engaged rate"],
        "Avg confirmed seconds": r["Confirmed read time (s)"] if r["Confirmed read time (s)"] is not None else "—",
        "Shares": r["Share sessions"],
        "Reached 75%": r["Reached 75%"],
        "Later CV": r["Later CV sessions"],
        "Later contact": r["Later contact sessions"],
        "Link": r["URL"],
    } for r in weekly_rows], hide_index=True, use_container_width=True, column_config={
        "Link": st.column_config.LinkColumn("Read edition")
    })
    st.caption(
        "Read rates are edition-session rates; scroll rates use only depth-measured sessions. "
        "Later CV/contact actions mean subsequent events in the same browser tab, not proven causal outcomes."
    )

    if report["issue_ctrs"]:
        with st.expander("Feature & archive open performance", expanded=False):
            st.dataframe([{
                "Edition": r["Week / issue"],
                "Placement": r["Placement"],
                "Card seen": r["Exposed sessions"],
                "Opened after exposure": r["Click sessions"],
                "CTR": _pct(r["Click sessions"], r["Exposed sessions"]),
            } for r in report["issue_ctrs"]], hide_index=True, use_container_width=True)
    if report["source_rows"]:
        with st.expander("Original publisher link interactions", expanded=False):
            st.dataframe([{
                "Publisher": r["Publisher"],
                "Link exposed": r["Exposed sessions"],
                "Clicks after exposure": r["Click sessions"],
                "CTR": _pct(r["Click sessions"], r["Exposed sessions"]),
            } for r in report["source_rows"]], hide_index=True, use_container_width=True)
    st.caption(
        f"Time window: {data.get('period_label', window)}. All metrics reuse the existing owner-only "
        "analytics reporting window and content-quality controls. No new visitor identifiers, cookies or raw URLs are stored."
    )
