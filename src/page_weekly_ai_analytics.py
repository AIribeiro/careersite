"""Owner-only, ISO-week-aware WEEKLY AI content report.

This is a classification of existing session-scoped events, not a second tracker.
Never add its subset metrics to whole-portfolio totals. Older periods remain
unmeasured when the weekly section was not instrumented.
"""
from __future__ import annotations

from urllib.parse import urlencode

import altair as alt
import streamlit as st

from page_analytics import _dashboard_payload
from page_content_intelligence import _fetch_rpc, fetch_intelligence
from site_cms import fetch_published_articles
from thinking_weekly_brief import edition_week, is_weekly_brief, sorted_editions

BASE_URL = "https://jairribeiro-ai.streamlit.app"


def render_weekly_campaigns(audio: dict | None, editions: list[object]) -> None:
    st.markdown("#### Where Weekly AI readers come from")
    if audio is None or "campaigns" not in audio:
        st.info("Campaign breakdown is temporarily unavailable.")
        return
    catalogue = {a.slug: a.title for a in sorted_editions(editions)}
    rows = [r for r in audio["campaigns"] if r.get("article_slug") in catalogue]
    if not rows:
        st.info("No Weekly AI reading visits in this reporting window.")
        return
    selected = st.selectbox("Weekly edition", [""] + list(catalogue),
                           format_func=lambda s: catalogue.get(s, "All editions"), key="weekly_campaign_edition")
    rows = [r for r in rows if not selected or r["article_slug"] == selected]
    campaign = st.selectbox("Campaign", [""] + sorted({r["campaign"] for r in rows}),
                            format_func=lambda c: c or "All campaigns", key="weekly_campaign_filter")
    rows = [r for r in rows if not campaign or r["campaign"] == campaign]
    chart = [{"Source": "X" if r["channel"] == "x" else r["channel"],
              "Campaign": r["campaign"], "Content tag": r["content"],
              "Role": "Weekly AI" if r["role"] == "weeklyai" else r["role"],
              "Edition": catalogue[r["article_slug"]], "Reads": r["reads"],
              "Engaged reads": r["engaged_reads"], "Audio starts": r["audio_starts"],
              "Share sessions": r["share_sessions"]} for r in rows]
    a, b, c = st.columns(3)
    a.metric("Campaign reading visits", sum(r["Reads"] for r in chart))
    b.metric("Engaged reading visits", sum(r["Engaged reads"] for r in chart))
    c.metric("Reading visits with audio", sum(r["Audio starts"] for r in chart))
    st.altair_chart(alt.Chart(alt.Data(values=chart)).mark_bar(cornerRadiusEnd=5).encode(
        y=alt.Y("Source:N", sort="-x", title=None),
        x=alt.X("sum(Reads):Q", title="Edition-session reads", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("Content tag:N"),
        tooltip=["Source:N", "Content tag:N", alt.Tooltip("sum(Reads):Q", title="Reads")],
    ).properties(height=240), use_container_width=True)
    with st.expander("Campaign and content details"):
        st.dataframe(chart, hide_index=True, use_container_width=True)
    st.caption("Each edition/session belongs to its first recorded article-view attribution in this window. "
               "Repeat views, heartbeats and audio events do not create extra reading visits. "
               "These are a subset of edition reads, not additional visitors. 'work' is a content tag, not a reader identity.")
    st.caption("Content tags are measured from this update onward. Earlier visits without utm_content remain unrecorded; "
               "direct or untagged traffic stays visible.")


def _n(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "—"


def weekly_ai_report(data: dict, editions: list[object], audio: dict | None = None) -> dict:
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
    audio_by_slug = {
        str(item.get("slug") or ""): item
        for item in (audio or {}).get("editions", [])
    }
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
        audio_row = audio_by_slug.get(article.slug, {})
        audio_starts = _n(audio_row.get("starts"))
        audio_completions = _n(audio_row.get("completions"))
        sessions = _n(row.get("sessions"))
        rows.append({
            "Week": f"Week {week} · {year}",
            "Week start": start.isoformat(),
            "Coverage": f"{start.strftime('%d %b')}–{end.strftime('%d %b %Y')}",
            "Headline": article.title,
            "Slug": article.slug,
            "Views": _n(row.get("views")),
            "Audio starts": audio_starts,
            "Audio reached 25%": _n(audio_row.get("progress_25")),
            "Audio reached 50%": _n(audio_row.get("progress_50")),
            "Audio reached 75%": _n(audio_row.get("progress_75")),
            "Audio completions": audio_completions,
            "Audio completion rate": _pct(audio_completions, audio_starts),
            "Estimated listening (min)": round(float(audio_row.get("estimated_listened_seconds") or 0) / 60, 1),
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
        "audio_available": audio is not None,
        "audio_listening_sessions": _n((audio or {}).get("started_sessions")),
        "audio_completed_sessions": _n((audio or {}).get("completed_sessions")),
        "audio_edition_starts": _n((audio or {}).get("edition_starts")),
        "audio_edition_completions": _n((audio or {}).get("edition_completions")),
        "audio_estimated_minutes": round(float((audio or {}).get("estimated_listened_seconds") or 0) / 60, 1),
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
    period = {
        "last_hour": "Last hour", "today": "Today",
        "7d": "Last 7 days", "14d": "Last 14 days", "30d": "Last 30 days",
        "60d": "Last 60 days", "90d": "Last 90 days",
    }.get(window, window)
    st.caption(
        f"Reporting window: **{period}**. Source: first-party analytics and published CMS editions. "
        "Counts are anonymous browser sessions, not identified people. "
        "WEEKLY AI is a subset of Thinking, never an additional site total."
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

    audio_data = None
    audio_error = None
    try:
        audio_data = _fetch_rpc("careersite_weekly_audio_analytics_v1", _dashboard_payload(window))
    except RuntimeError as exc:
        audio_error = str(exc)

    report = weekly_ai_report(data, editions, audio_data)
    if not report["issue_count"]:
        st.info("There are no published Weekly AI editions yet.")
        return

    render_weekly_campaigns(audio_data, editions)

    feature_exposures = report["feature_sessions"]
    page_sessions = report["feature_page_sessions"]
    reader_sessions = report["reader_sessions"]
    engagement = report["engaged_sessions"]

    st.markdown("#### From visibility to reading")
    a, b, c, d = st.columns(4)
    a.metric("Feature reached", feature_exposures, help="Distinct page sessions with ≥15% of the Weekly AI feature visible.")
    b.metric("Feature reach", _pct(feature_exposures, page_sessions),
             help="Feature reached / Thinking landing-page sessions. Not all Thinking visits use the landing page.")
    c.metric("Edition reads", reader_sessions,
             help="Sum of distinct edition-session reads. Reading two editions in one session counts twice.")
    d.metric("Engaged reads", _pct(engagement, reader_sessions),
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

    if report["archive_sessions"] > 0 and not report["feature_sessions"]:
        st.caption(
            "The archive was reached without recorded impressions of the Thinking feature. "
            "Direct links to the archive can produce this pattern; the two metrics are not a sequential funnel."
        )

    st.markdown("#### Audio listening")
    if not report["audio_available"]:
        st.warning(
            "Audio listening metrics are temporarily unavailable; written-reading metrics remain valid. "
            + (audio_error or "")
        )
    else:
        p, q, r, t = st.columns(4)
        p.metric("Audio starts", report["audio_listening_sessions"],
                 help="Distinct anonymous sessions with an observed MP3 playback start, across all weeks.")
        q.metric("Audio completed", report["audio_completed_sessions"],
                 help="Sessions with an observed natural playback end after at least 85% cumulative playback.")
        r.metric("Completion rate", _pct(report["audio_edition_completions"], report["audio_edition_starts"]),
                 help="Completed edition-sessions / started edition-sessions; distinct by session and week.")
        t.metric("Audio minutes", report["audio_estimated_minutes"],
                 help="Sum of estimated actual played seconds, capped at each edition duration per session; not server MP3 requests.")
        if not report["audio_edition_starts"]:
            st.caption(
                "No instrumented embedded-audio playback starts were recorded in this window. "
                "This does not establish that nobody listened: direct MP3 links, external players "
                "and activity before tracking began are not measurable here."
            )
        st.caption(
            "Embedded playback starts and 25/50/75% milestones count once per browser session and edition. "
            "Seeking to the end is not a completion. Listening counts are not additional article views "
            "or unique people; multiple weeks may be listened to in the same session."
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
                x=alt.X("Week:N", title="ISO week", sort=None),
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
        "Audio starts": r["Audio starts"] if report["audio_available"] else "—",
        "Heard ≥50%": r["Audio reached 50%"] if report["audio_available"] else "—",
        "Audio completed": r["Audio completions"] if report["audio_available"] else "—",
        "Audio completion rate": r["Audio completion rate"] if report["audio_available"] else "—",
        "Audio minutes": r["Estimated listening (min)"] if report["audio_available"] else "—",
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
