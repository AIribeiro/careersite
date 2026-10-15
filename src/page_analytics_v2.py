from __future__ import annotations

import streamlit as st

from page_analytics import (
    render_analytics_dashboard as render_site_analytics_dashboard,
    _noindex, _dashboard_css, REPORTING_WINDOWS, REPORTING_WINDOW_LABELS, _fetch_dashboard,
)
from analytics_reporting_period import initialize_reporting_period, remember_reporting_period
from page_article_analytics import render_article_analytics, render_reader_sources
from page_content_intelligence import render_content_intelligence
from page_weekly_ai_analytics import render_weekly_ai_analytics
from page_public_predictions import render_public_hiring_predictions
from page_public_analytics import (
    render_public_analytics_overview, render_public_job_search,
    render_public_swedish_market,
)


_VIEWS = {
    "overview": "Overview",
    "portfolio": "Portfolio",
    "jobs": "Job search",
    "predictions": "Job predictions",
    "market": "Swedish market",
}
_VIEW_STATE_KEY = "careersite_analytics_view"


def _url_view() -> str:
    raw = str(st.query_params.get("view", "overview"))
    # Older bookmarks remain valid after unifying Page and Article views.
    if raw in ("pages", "articles"):
        st.session_state["analytics_portfolio_kind"] = "article" if raw == "articles" else "page"
        return "portfolio"
    return raw if raw in _VIEWS else "overview"


def _update_view_url() -> None:
    """Change report views without reloading the Streamlit session."""
    view = st.session_state.get(_VIEW_STATE_KEY)
    if view in _VIEWS:
        st.query_params["view"] = view
    else:
        st.session_state[_VIEW_STATE_KEY] = _url_view()


def render_analytics_dashboard() -> None:
    """Public, read-only analytics. The CMS remains separately authenticated."""
    _noindex()
    _dashboard_css()

    if _VIEW_STATE_KEY not in st.session_state:
        st.session_state[_VIEW_STATE_KEY] = _url_view()

    nav, portfolio = st.columns([7, 1.5], vertical_alignment="center")
    with nav:
        section = st.segmented_control(
            "Analytics view",
            options=list(_VIEWS),
            format_func=lambda view: _VIEWS[view],
            key=_VIEW_STATE_KEY,
            on_change=_update_view_url,
            label_visibility="collapsed",
            width="stretch",
        ) or _url_view()
    with portfolio:
        if st.button("Portfolio", key="analytics_back_to_portfolio"):
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.rerun()
    st.caption("Start with interpreted findings and visual comparisons. Exact counts and reconciliation checks remain available as drill-downs.")
    st.divider()

    if section == "overview":
        render_public_analytics_overview()
        return
    if section == "jobs":
        render_public_job_search()
        return
    if section == "market":
        render_public_swedish_market()
        return
    if section == "predictions":
        render_public_hiring_predictions()
        return

    st.title("Portfolio performance")
    st.caption("Understand which content earns qualified attention and what visitors do next. "
               "A recorded visit is not a person or a recruiter identification.")
    kind = st.segmented_control(
        "Portfolio focus", options=["page","article","weekly_ai"],
        default="page",
        format_func=lambda value: {"page": "Pages & profile", "article": "Articles & thinking", "weekly_ai": "WEEKLY AI"}[value],
        key="analytics_portfolio_kind", width="stretch",
    ) or "page"
    window_options = [key for key, _ in REPORTING_WINDOWS]
    initialize_reporting_period(st.session_state, _fetch_dashboard)
    window = st.selectbox(
        "Reporting period",
        window_options,
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
        on_change=remember_reporting_period,
        args=(st.session_state,),
        help="Starts with Last hour, or Today when the last hour has zero recorded sessions. Your selection is kept while you use Analytics.",
    )
    if str(window) in ("last_hour","today"):
        st.caption("Short windows are useful for monitoring, not for judging hiring or content outcomes.")
    if kind == "weekly_ai":
        render_weekly_ai_analytics(str(window))
        return
    render_content_intelligence(str(kind), str(window))
    if st.toggle("Inspect legacy traffic reports and detailed source tables",
                 value=False,key="analytics_show_historical"):
        st.caption("Legacy reporting includes unfiltered traffic for continuity. "
                   "It should not replace the qualified-session and behavior measures above.")
        render_reader_sources(str(window), str(kind))
        if kind == "page":
            render_site_analytics_dashboard()
        else:
            render_article_analytics()
