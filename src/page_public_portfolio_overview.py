"""Public portfolio-only analytics landing; no recruiting/market/forecast reads."""
from __future__ import annotations

import altair as alt
import streamlit as st

from analytics_reporting_period import initialize_reporting_period, remember_reporting_period
from page_analytics import (
    REPORTING_WINDOWS, REPORTING_WINDOW_LABELS, _fetch_dashboard,
)
from page_article_analytics import _article_title
from page_content_intelligence import content_label, fetch_intelligence
from portfolio_insight_engine import derive_portfolio_insights


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
    articles = portfolio_visit_rows(report, "article")
    quality = report.get("quality") or {}
    page_views = max(0, int(quality.get("page_views") or 0))
    article_views = max(0, int(quality.get("article_views") or 0))
    page_sessions = max(0, int(quality.get("page_sessions") or 0))
    article_sessions = max(0, int(quality.get("article_sessions") or 0))

    top_insights, deeper_insights = derive_portfolio_insights(report, pages, articles)
    st.subheader("What stands out")
    st.caption(
        "Current-period observations interpreted from recorded portfolio "
        "activity. Interpretations change with the reporting window."
    )
    summaries = st.columns(2, gap="large")
    for column, insight in zip(summaries, top_insights):
        with column:
            st.markdown(f"**{insight.heading}**")
            st.write(insight.interpretation)
            st.caption(insight.basis)

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
    st.subheader("Portfolio intelligence")
    st.caption(
        "A closer interpretation of exploration, reading depth, continued "
        "navigation and changes over time. Each finding includes its evidence "
        "and limits rather than assuming what a visitor intended."
    )
    details = st.columns(2, gap="large")
    for index, insight in enumerate(deeper_insights):
        with details[index % 2]:
            st.markdown(f"**{insight.heading}**")
            st.write(insight.interpretation)
            st.caption(insight.basis)

    st.caption(
        "Page and article sessions are measured independently and must not be "
        "summed as unique visitors. These are content observations, not evidence "
        "that any particular employer or recruiter visited."
    )
    st.caption(
        "For reading depth, distribution sources, WEEKLY AI performance and "
        "measurement diagnostics, open Explore content."
    )
