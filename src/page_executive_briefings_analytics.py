"""Executive Briefings analytics from existing first-party content observations.

These are partitions of portfolio page/article analytics, not new visitor
counters. Only published CMS items classified as Executive Briefing qualify.
"""
from __future__ import annotations

from urllib.parse import urljoin

import altair as alt
import streamlit as st

from page_content_intelligence import fetch_intelligence
from site_cms import article_relative_url, fetch_published_articles

_BASE = "https://jairribeiro-ai.streamlit.app/"


def _number(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (ValueError, TypeError):
        return 0


def _percentage(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.1%}" if denominator else "—"


def published_briefings(catalogue: list[object]) -> list[object]:
    """Never infer a briefing from a title, URL or draft."""
    return sorted(
        (article for article in catalogue
         if getattr(article, "status", "") == "published"
         and str(getattr(article, "kind", "")).strip().casefold() == "executive briefing"),
        key=lambda item: (str(getattr(item, "published_at", "")), str(item.slug)),
        reverse=True,
    )


def briefing_analytics_report(data: dict, catalogue: list[object]) -> dict:
    """Aggregate only the already deduplicated per-content RPC records.

    Different briefings viewed by one browser session produce two item-session
    reads, never two distinct people. The library is a portfolio PAGE and its
    page views must never be added to article readership totals.
    """
    briefings = published_briefings(catalogue)
    by_content = {
        (str(row.get("kind") or ""), str(row.get("content") or "")): row
        for row in data.get("performance", [])
        if isinstance(row, dict)
    }
    library = by_content.get(("page", "briefings"), {})
    sections = {
        (str(row.get("page") or ""), str(row.get("section_key") or "")): row
        for row in data.get("section_reach", [])
        if isinstance(row, dict)
    }
    library_reach = sections.get(("briefings", "briefings-library"), {})
    home_reach = sections.get(("home", "home-executive-briefings"), {})
    card_rows = [
        row for row in data.get("article_cards", [])
        if isinstance(row, dict)
        and str(row.get("element_key") or "") in {item.slug for item in briefings}
        and str(row.get("placement") or "").endswith(":briefings-library")
    ]
    cards_by_slug: dict[str, list[dict]] = {}
    for card in card_rows:
        cards_by_slug.setdefault(str(card.get("element_key")), []).append(card)

    rows = []
    for article in briefings:
        perf = by_content.get(("article", article.slug), {})
        exposures = sum(_number(card.get("exposed_sessions"))
                        for card in cards_by_slug.get(article.slug, []))
        clicks = sum(_number(card.get("click_sessions"))
                     for card in cards_by_slug.get(article.slug, []))
        sessions = _number(perf.get("sessions"))
        depth_sessions = _number(perf.get("depth_measured_sessions"))
        engaged = _number(perf.get("engaged_sessions"))
        seconds = perf.get("avg_active_seconds")
        try:
            seconds = round(float(seconds), 1) if seconds is not None else None
        except (ValueError, TypeError):
            seconds = None
        rows.append({
            "Title": article.title,
            "Slug": article.slug,
            "URL": urljoin(_BASE, article_relative_url(article)),
            "Published": getattr(article, "published_iso", ""),
            "Views": _number(perf.get("views")),
            "Read sessions": sessions,
            "Engaged reads": engaged,
            "Engagement": _percentage(engaged, sessions),
            "Avg confirmed seconds": seconds,
            "Depth measured": depth_sessions,
            "Reached 75%": _number(perf.get("three_quarter_sessions")),
            "Depth rate": _percentage(_number(perf.get("three_quarter_sessions")), depth_sessions),
            "Share sessions": _number(perf.get("sharing_sessions")),
            "Later CV": _number(perf.get("later_cv_sessions")),
            "Later contact": _number(perf.get("later_contact_sessions")),
            "Card exposures": exposures,
            "Card clicks": clicks,
            "Card CTR": _percentage(clicks, exposures),
        })

    return {
        "rows": rows,
        "published_count": len(briefings),
        "read_count": sum(row["Read sessions"] for row in rows),
        "view_count": sum(row["Views"] for row in rows),
        "engaged_count": sum(row["Engaged reads"] for row in rows),
        "share_count": sum(row["Share sessions"] for row in rows),
        "later_cv_count": sum(row["Later CV"] for row in rows),
        "later_contact_count": sum(row["Later contact"] for row in rows),
        "library_views": _number(library.get("views")),
        "library_sessions": _number(library.get("sessions")),
        "library_reached": _number(library_reach.get("reached_sessions")),
        "home_reached": _number(home_reach.get("reached_sessions")),
        "card_exposures": sum(row["Card exposures"] for row in rows),
        "card_clicks": sum(row["Card clicks"] for row in rows),
    }


def render_executive_briefings_analytics(window: str) -> None:
    """Read-only, public-safe reporting used by owner and public content views."""
    from page_analytics import REPORTING_WINDOW_LABELS

    st.subheader("Executive Briefings · Content performance")
    st.caption(
        f"Reporting period: {REPORTING_WINDOW_LABELS.get(window, window)}. "
        "Published briefings are measured with the same first-party events as "
        "Articles and Weekly AI. The figures below are a subset of portfolio "
        "activity, not extra traffic or identified people."
    )
    try:
        catalogue = list(fetch_published_articles())
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.warning(
            "The published briefing catalogue is unavailable. "
            "Readership cannot be reliably classified until the catalogue loads."
        )
        return

    try:
        data = fetch_intelligence(window)
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.warning("Executive Briefings reporting is temporarily unavailable.")
        return

    report = briefing_analytics_report(data, catalogue)
    if not report["published_count"]:
        st.info("No Executive Briefings are published yet.")
        return

    st.markdown("#### From discovery to readership")
    a, b, c, d = st.columns(4, gap="small")
    a.metric("Library visits", f"{report['library_views']:,}",
             help="Recorded views of the Executive Briefings library page. Also included in Portfolio visits.")
    b.metric("Briefing reads", f"{report['read_count']:,}",
             help="Distinct sessions per published briefing. One session reading two briefings counts as two item reads.")
    c.metric("Engaged reads", _percentage(report["engaged_count"], report["read_count"]),
             help="Briefing-item sessions with at least ten seconds of measured activity.")
    d.metric("Later contact", f"{report['later_contact_count']:,}",
             help="Summed briefing-item sessions with a subsequent contact event. This is not a distinct-visitor or conversion count.")

    st.caption(
        f"{report['published_count']} published briefings · "
        f"{report['view_count']:,} recorded briefing article views · "
        f"{report['share_count']:,} briefing-item sharing sessions. "
        "An article opened directly can bypass the library; these are not sequential funnel stages."
    )

    st.markdown("#### Library discovery and opens")
    a, b, c, d = st.columns(4, gap="small")
    a.metric("Library reached", f"{report['library_reached']:,}",
             help="Distinct library-page sessions that visibly reached the briefing cards.")
    b.metric("Card exposures", f"{report['card_exposures']:,}",
             help="Summed published-briefing card exposure sessions, not unique people.")
    c.metric("Card opens", f"{report['card_clicks']:,}",
             help="Summed observed card-click sessions after exposure; direct opens excluded.")
    d.metric("Card click-through", _percentage(report["card_clicks"], report["card_exposures"]),
             help="Exposed-card to clicked-card sessions. A session viewing several cards appears several times.")

    st.caption(
        "Library card exposures begin only after instrumentation was added. "
        "Direct article links, search and social referrals can produce reads without library clicks; "
        "historical impressions cannot be reconstructed."
    )

    rows = report["rows"]
    ranked = sorted(rows, key=lambda row: (-row["Read sessions"], row["Title"]))
    st.markdown("#### Which briefings earn attention?")
    graph_rows = [
        {"Briefing": row["Title"], "Reads": row["Read sessions"],
         "Engaged": row["Engaged reads"], "Later contact": row["Later contact"],
         "Views": row["Views"]}
        for row in ranked
    ]
    if any(row["Reads"] for row in graph_rows):
        chart = (
            alt.Chart(alt.Data(values=graph_rows))
            .mark_bar(cornerRadiusEnd=5, size=22)
            .encode(
                x=alt.X("Reads:Q", title="Briefing-item sessions", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Briefing:N", title=None,
                        sort=[row["Briefing"] for row in graph_rows],
                        axis=alt.Axis(labelLimit=300)),
                tooltip=["Briefing:N", alt.Tooltip("Reads:Q", format=","),
                         alt.Tooltip("Views:Q", format=","),
                         alt.Tooltip("Engaged:Q", format=","),
                         alt.Tooltip("Later contact:Q", format=",")],
            ).properties(height=max(190, 50 * len(graph_rows)))
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No recorded briefing reads in the selected reporting period.")

    st.markdown("#### Individual briefing performance")
    st.dataframe(
        [{
            "Briefing": row["Title"],
            "Read briefing": row["URL"],
            "Views": row["Views"],
            "Reader sessions": row["Read sessions"],
            "Engaged ≥10s": row["Engaged reads"],
            "Engaged rate": row["Engagement"],
            "Avg confirmed seconds": row["Avg confirmed seconds"] if row["Avg confirmed seconds"] is not None else "—",
            "Reached 75%": row["Depth rate"],
            "Shares": row["Share sessions"],
            "Later CV": row["Later CV"],
            "Later contact": row["Later contact"],
        } for row in ranked],
        hide_index=True, use_container_width=True,
        column_config={"Read briefing": st.column_config.LinkColumn("Read briefing")},
    )
    st.caption(
        "Read sessions and shares are per briefing; the same session may contribute "
        "to several rows. The ≥75% rate uses only depth-measured reading sessions. "
        "Average time is shown only for sessions with sufficient measured activity. "
        "Later contact and CV actions are ordered within the tracked session, not "
        "evidence that a briefing caused them."
    )

    with st.expander("Library-card detail and measurement definitions", expanded=False):
        st.dataframe(
            [{
                "Briefing": row["Title"],
                "Card seen": row["Card exposures"],
                "Opened after exposure": row["Card clicks"],
                "Observed CTR": row["Card CTR"],
            } for row in ranked], hide_index=True, use_container_width=True,
        )
        st.caption(
            f"Library-page sessions: {report['library_sessions']:,}; "
            f"home-page briefing-strip reach: {report['home_reached']:,}. "
            "These are separate content events, not a deduplicated visitor journey."
        )
        st.caption(
            "Reporting follows the existing source and test-traffic exclusions. "
            "No new visitor identifiers, database tables or tracking cookies are introduced."
        )
