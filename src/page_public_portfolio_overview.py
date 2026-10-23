"""Public portfolio-only analytics landing; no recruiting/market/forecast reads."""
from __future__ import annotations

import altair as alt
import streamlit as st

from analytics_reporting_period import initialize_reporting_period, remember_reporting_period
from page_analytics import (
    REPORTING_WINDOWS, REPORTING_WINDOW_LABELS, _fetch_dashboard,
    _dashboard_payload,
)
from page_article_analytics import _article_title
from page_content_intelligence import (
    _article_metadata, _fetch_rpc, content_label, fetch_intelligence,
)
from portfolio_signal_brief import ranked_portfolio_signals
from page_home_journey import render_home_journey

# Routes retired in the October 2026 six-page navigation redesign.
RETIRED_ROUTES = {"presence", "certifications", "enterprise", "transformation", "governance", "consulting"}
from site_cms import fetch_published_articles
from thinking_weekly_brief import edition_label, is_weekly_brief


def portfolio_visit_rows(report: dict, kind: str) -> list[dict]:
    """Classified page/article views; repeat views are not unique visitors."""
    if kind not in ("page", "article"):
        raise ValueError("Unsupported portfolio content kind")
    values = []
    for row in report.get("performance", []):
        if not isinstance(row, dict) or row.get("kind") != kind:
            continue
        views = max(0, int(row.get("views") or 0))
        if views < 1:
            continue
        content = str(row.get("content") or "")
        label = _article_title(content) if kind == "article" else content_label(content)
        if kind == "page" and content in RETIRED_ROUTES:
            label += " · retired route"
        values.append({
            "Content": label,
            "Slug": content,
            "Views": views,
            "Sessions": max(0, int(row.get("sessions") or 0)),
        })
    return sorted(values, key=lambda row: (-row["Views"], row["Content"]))


def split_reader_rows(
    articles: list[dict], published_editions: list[object],
) -> tuple[list[dict], list[dict]]:
    """Separate regular essays from verified WEEKLY AI editions.

    Both groups retain the existing first-party article-view grain, not a
    second WEEKLY AI tracker. Only published CMS records with the exact
    Weekly AI + Weekly Brief classification qualify. Edition-specific
    reading sessions may overlap between editions and other essays.
    """
    weekly = {
        edition.slug: edition
        for edition in published_editions
        if getattr(edition, "status", "") == "published"
        and is_weekly_brief(edition)
    }
    essays: list[dict] = []
    editions: list[dict] = []
    for row in articles:
        slug = str(row.get("Slug") or "")
        if slug in weekly:
            item = dict(row)
            item["Title"] = item["Content"]
            item["Content"] = edition_label(weekly[slug])
            editions.append(item)
        else:
            essays.append(row)
    return essays, sorted(editions, key=lambda r: (-r["Views"], r["Content"]))


def _ranking_chart(rows: list[dict], *, compact: bool = False) -> None:
    """Equal chart heights keep all three content cards aligned on desktop."""
    if not rows:
        st.caption("No recorded views for this content in the selected period.")
        return
    top = rows[:5] if compact else rows[:7]
    tooltips = ["Content:N", alt.Tooltip("Views:Q", format=","),
                alt.Tooltip("Sessions:Q", format=",")]
    if any(r.get("Title") for r in top):
        tooltips.insert(1, "Title:N")
    chart = (
        alt.Chart(alt.Data(values=top))
        .mark_bar(cornerRadiusEnd=5, size=20 if compact else 22)
        .encode(
            x=alt.X("Views:Q", title="Recorded views",
                    axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Content:N", sort=[r["Content"] for r in top],
                    title=None, axis=alt.Axis(labelLimit=145 if compact else 250)),
            tooltip=tooltips,
        ).properties(height=220 if compact else max(180, 38 * len(top)))
    )
    st.altair_chart(chart, width="stretch")


@st.cache_data(ttl=300, show_spinner=False)
def _recent_content_report() -> dict:
    """Lightweight recent comparison, rechecked within five minutes.

    Only existing anonymous content aggregates are read. Hiring data is never
    queried in the public page. Behaviour RPC isn't needed for the brief.
    """
    payload = _dashboard_payload("7d")
    payload["p_article_metadata"] = _article_metadata()
    return _fetch_rpc("careersite_content_intelligence_v2", payload)


def render_public_portfolio_overview() -> None:
    """Visits and article reading are the first public evidence, never hiring."""
    st.title("Portfolio visits & reads")
    st.caption(
        "What visitors explore across the portfolio and which articles receive "
        "attention. Browser sessions are not identified people; repeat views count."
    )
    initialize_reporting_period(st.session_state, _fetch_dashboard)
    window = st.selectbox(
        "Reporting period",
        [name for name, _ in REPORTING_WINDOWS],
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
        on_change=remember_reporting_period,
        args=(st.session_state,),
        help="Starts with the most recent window containing recorded sessions; "
             "a manual selection is retained.",
    )
    try:
        report = fetch_intelligence(str(window))
    except (RuntimeError, ValueError, TimeoutError) as exc:
        st.warning("Portfolio reporting is temporarily unavailable.")
        st.caption(str(exc))
        return

    pages = portfolio_visit_rows(report, "page")
    historical_routes = [row for row in pages if row["Slug"] in RETIRED_ROUTES]
    current_routes = [row for row in pages if row["Slug"] not in RETIRED_ROUTES]
    articles = portfolio_visit_rows(report, "article")
    quality = report.get("quality") or {}
    page_views = max(0, int(quality.get("page_views") or 0))
    article_views = max(0, int(quality.get("article_views") or 0))
    page_sessions = max(0, int(quality.get("page_sessions") or 0))
    # The content RPC reports WEEKLY AI as ordinary article-view rows.
    # Use published format metadata to make mutually exclusive visual groups.
    catalogue_available = True
    try:
        published_editions = list(fetch_published_articles())
    except RuntimeError:
        published_editions = []
        catalogue_available = False
    regular_articles, weekly_editions = split_reader_rows(articles, published_editions)
    regular_views = sum(row["Views"] for row in regular_articles)
    regular_item_sessions = sum(row["Sessions"] for row in regular_articles)
    weekly_views = sum(row["Views"] for row in weekly_editions)
    weekly_item_sessions = sum(row["Sessions"] for row in weekly_editions)
    rows_reconcile = regular_views + weekly_views == article_views

    st.caption("Portfolio structure changed on 23 October 2026: six public destinations now replace the former nested navigation. Selected windows spanning that date mix two different navigation designs; compare journeys on complete days within each design, not raw historical page rankings.")
    if historical_routes:
        with st.expander("Historical routes in this reporting window", expanded=False):
            st.caption("These retired routes are preserved as historical observations. Their older views are not silently reassigned to About or Experience; new visits through legacy links are attributed to the destination actually rendered.")
            st.dataframe([{"Former destination": row["Content"], "Recorded views": row["Views"], "Page sessions": row["Sessions"]} for row in historical_routes], hide_index=True, use_container_width=True)
    # Identical card heights and chart heights; 3 columns on desktop,
    # Streamlit naturally stacks them for narrow/mobile viewports.
    pages_col, articles_col, weekly_col = st.columns(3, gap="medium")
    with pages_col:
        with st.container(border=True, height=510):
            st.markdown("#### Portfolio visits")
            st.metric("Page views", f"{page_views:,}")
            st.caption(f"{page_sessions:,} page-view sessions · {len(current_routes)} active destinations with recorded views")
            st.markdown("**Pages receiving attention**")
            _ranking_chart(current_routes, compact=True)
    with articles_col:
        with st.container(border=True, height=510):
            st.markdown("#### Article readership")
            st.metric("Article views", f"{regular_views:,}" if catalogue_available else "—")
            if catalogue_available:
                st.caption(
                    f"{regular_item_sessions:,} article-item sessions · "
                    f"{len(regular_articles)} read articles"
                )
                st.markdown("**Most-read articles**")
                _ranking_chart(regular_articles, compact=True)
            else:
                st.caption("Article/edition breakdown temporarily unavailable.")
    with weekly_col:
        with st.container(border=True, height=510):
            st.markdown("#### WEEKLY AI")
            st.metric("Edition views", f"{weekly_views:,}" if catalogue_available else "—")
            if catalogue_available:
                st.caption(
                    f"{weekly_item_sessions:,} edition-item sessions · "
                    f"{len(weekly_editions)} read editions"
                )
                st.markdown("**Most-read WEEKLY AI editions**")
                _ranking_chart(weekly_editions, compact=True)
            else:
                st.caption("Published edition metadata is temporarily unavailable.")

    if catalogue_available and not rows_reconcile:
        st.caption(
            "The per-content view breakdown does not reconcile with the overall "
            "article-view total for this window; investigate reporting coverage "
            "before comparing the two reading categories."
        )
    st.caption(
        "Article readership excludes WEEKLY AI editions. Both are partitions of "
        "existing article views, not additional website traffic. Item-session "
        "observations can overlap across content and are not unique readers."
    )

    if st.button("Refresh insights", key="portfolio_refresh_insights"):
        _recent_content_report.clear()
        st.rerun()

    recent_report = None
    if str(window) in ("14d", "30d", "60d", "90d", "365d"):
        try:
            recent_report = _recent_content_report()
        except (RuntimeError, ValueError, TimeoutError, PermissionError):
            # A failed background comparator does not make the selected-period
            # visits/read charts unavailable, nor imply missing activity.
            recent_report = None

    latest_articles = (portfolio_visit_rows(recent_report, "article")
                       if recent_report else None)
    latest_pages = (portfolio_visit_rows(recent_report, "page")
                    if recent_report else None)
    top_insights, deeper_insights, limitations = ranked_portfolio_signals(
        report, pages, articles, window=str(window),
        recent_report=recent_report, recent_articles=latest_articles,
        recent_pages=latest_pages,
    )
    st.subheader("What changed and why it matters")
    st.caption(
        "Highest-signal evidence first. Recent seven-day movements inform the "
        "interpretation of broad historical reporting windows."
        if recent_report else
        "Selected-period findings, ranked by evidence and relevance."
    )
    summaries = st.columns(len(top_insights), gap="large")
    for column, insight in zip(summaries, top_insights):
        with column:
            st.markdown(f"**{insight.title}**")
            st.write(insight.message)
            st.markdown(f"*Next to examine:* {insight.next_check}")
            st.caption(insight.evidence)

    st.divider()
    render_home_journey(str(window))

    st.divider()
    st.subheader("Other relevant portfolio signals")
    st.caption(
        "Further evidence appears only when its sample and relevance justify "
        "a finding. Lower-confidence notes are kept in the evidence drilldown."
    )
    if deeper_insights:
        details = st.columns(min(2, len(deeper_insights)), gap="large")
        for index, insight in enumerate(deeper_insights):
            with details[index % len(details)]:
                st.markdown(f"**{insight.title}**")
                st.write(insight.message)
                st.markdown(f"*Next to examine:* {insight.next_check}")
                st.caption(insight.evidence)
    else:
        st.caption("No further high-confidence changes in this period.")

    with st.expander("Evidence, measurement limits and comparison rules", expanded=False):
        st.caption(
            "Signals use classified views, article-session observations and "
            "source/campaign cohorts. These are not unique people or evidence "
            "of particular readers' intentions."
        )
        for limitation in limitations:
            st.write(limitation)
        if not limitations:
            st.write("No additional evidence limitations were flagged for these signals.")
        if recent_report:
            st.caption(
                "Recent comparison refreshes within five minutes. Use Refresh insights "
                "to request a fresh report."
            )

    st.caption(
        "Page and article sessions are measured independently and must not be "
        "summed as unique visitors. These are content observations, not evidence "
        "that any particular employer or recruiter visited."
    )
    st.caption(
        "For reading depth, distribution sources, WEEKLY AI audio performance "
        "and measurement diagnostics, open Explore content."
    )
