from __future__ import annotations

import streamlit as st

from site_owner_persistence import (persistent_owner_session, show_owner_login_or_refresh,
                                    browser_owner_signout)
from page_analytics import (
    render_analytics_dashboard as render_site_analytics_dashboard,
    _noindex, _dashboard_css, REPORTING_WINDOWS, REPORTING_WINDOW_LABELS,
)
from page_article_analytics import render_article_analytics, render_reader_sources
from page_content_intelligence import render_content_intelligence
from page_job_search_analytics import render_job_search_analytics
from page_job_market_insights import render_swedish_job_market
from page_analytics_overview import render_analytics_overview


_VIEWS = {
    "overview": "Overview",
    "portfolio": "Portfolio",
    "jobs": "Job search",
    "market": "Swedish market",
}
_VIEW_STATE_KEY = "careersite_analytics_view"


def _owner_session() -> dict | None:
    """Share a verified, persistently restorable owner session with the CMS."""
    return persistent_owner_session()


def _owner_login() -> None:
    st.title("Portfolio Analytics")
    st.caption("Private evidence for your portfolio, recruitment progress and the Swedish market. One sign-in covers all sections.")
    show_owner_login_or_refresh("analytics")


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
    """Owner-only, bookmarkable analytics views with one shared session."""
    _noindex()
    _dashboard_css()

    session = _owner_session()
    if session is None:
        _owner_login()
        return

    # Native Streamlit navigation preserves st.session_state. HTML links with
    # target="_self" created new sessions and repeatedly triggered login.
    if _VIEW_STATE_KEY not in st.session_state:
        st.session_state[_VIEW_STATE_KEY] = _url_view()

    nav, portfolio, account = st.columns([7, 1.5, 1.2], vertical_alignment="center")
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
            # Stay on the same Streamlit connection so the owner session survives.
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.rerun()
    with account:
        if st.button("Sign out", key="analytics_owner_signout"):
            browser_owner_signout()
            return
    st.caption("Overview → direction and actions  ·  Portfolio → reach and behavior  ·  Job search → conversion and pipeline  ·  Market → external context")
    st.divider()

    if section == "overview":
        render_analytics_overview(session)
        return
    if section == "jobs":
        render_job_search_analytics(session)
        return
    if section == "market":
        render_swedish_job_market(session)
        return

    st.title("Portfolio performance")
    st.caption("Understand which content earns qualified attention and what visitors do next. "
               "A recorded visit is not a person or a recruiter identification.")
    kind = st.segmented_control(
        "Portfolio focus", options=["page","article"],
        default="page",
        format_func=lambda value: "Pages & profile" if value == "page" else "Articles & thinking",
        key="analytics_portfolio_kind", width="stretch",
    ) or "page"
    window_options = [key for key, _ in REPORTING_WINDOWS]
    window = st.selectbox(
        "Reporting period",
        window_options,
        index=window_options.index("last_hour"),
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
        help="Choose a complete enough window for interpretation. Hourly and daily views are primarily operational checks.",
    )
    if str(window) in ("last_hour","today"):
        st.caption("Short windows are useful for monitoring, not for judging hiring or content outcomes.")
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
