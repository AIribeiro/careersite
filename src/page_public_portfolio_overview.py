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
        values.append({
            "Content": label,
            "Slug": content,
            "Views": views,
            "Sessions": max(0, int(row.get("sessions") or 0)),
        })
    return sorted(values, key=lambda row: (-row["Views"], row["Content"]))


def _ranking_chart(rows: list[dict]) -> None:
    if not rows:
        st.info("No classified views recorded in this period.")
        return
    top = rows[:7]
    chart = (
        alt.Chart(alt.Data(values=top))
        .mark_bar(cornerRadiusEnd=5, size=22)
        .encode(
            x=alt.X("Views:Q", title="Recorded views",
                    axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Content:N", sort=[r["Content"] for r in top],
                    title=None, axis=alt.Axis(labelLimit=250)),
            tooltip=["Content:N", alt.Tooltip("Views:Q", format=","),
                     alt.Tooltip("Sessions:Q", format=",")],
        ).properties(height=max(180, 38 * len(top)))
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
    if st.button("Refresh insights", key="portfolio_refresh_insights"):
        _recent_content_report.clear()
        st.rerun()
    try:
        report = fetch_intelligence(str(window))
    except (RuntimeError, ValueError, TimeoutError) as exc:
        st.warning("Portfolio reporting is temporarily unavailable.")
        st.caption(str(exc))
        return

    pages = portfolio_visit_rows(report, "page")
    articles = portfolio_visit_rows(report, "article")
    quality = report.get("quality") or {}
    page_views = max(0, int(quality.get("page_views") or 0))
    article_views = max(0, int(quality.get("article_views") or 0))
    page_sessions = max(0, int(quality.get("page_sessions") or 0))
    article_sessions = max(0, int(quality.get("article_sessions") or 0))

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
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(border=True):
            st.markdown("#### Portfolio visits")
            st.metric("Page views", f"{page_views:,}")
            st.caption(f"{page_sessions:,} page-view sessions · {len(pages)} visited pages")
            st.markdown("**Pages receiving attention**")
            _ranking_chart(pages)
    with right:
        with st.container(border=True):
            st.markdown("#### Article readership")
            st.metric("Article views", f"{article_views:,}")
            st.caption(f"{article_sessions:,} reading sessions · {len(articles)} read articles")
            st.markdown("**Most-read articles**")
            _ranking_chart(articles)

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
        "For reading depth, distribution sources, WEEKLY AI performance and "
        "measurement diagnostics, open Explore content."
    )
