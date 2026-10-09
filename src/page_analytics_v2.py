from __future__ import annotations

import streamlit as st

from site_cms import ensure_owner_session, owner_signin
from page_analytics import (
    render_analytics_dashboard as render_site_analytics_dashboard,
    _noindex, _dashboard_css, REPORTING_WINDOWS, REPORTING_WINDOW_LABELS,
)
from page_article_analytics import render_article_analytics, render_reader_sources
from page_content_intelligence import render_content_intelligence
from page_job_search_analytics import render_job_search_analytics


_VIEWS = {
    "pages": "Page Views",
    "articles": "Article Views",
    "jobs": "Job Search Analytics",
}
_VIEW_STATE_KEY = "careersite_analytics_view"


def _owner_session() -> dict | None:
    """Share the CMS owner session across the three analytics views."""
    session = ensure_owner_session(st.session_state.get("cms_auth"))
    if session:
        st.session_state["cms_auth"] = session
    else:
        st.session_state.pop("cms_auth", None)
    return session


def _owner_login() -> None:
    st.title("Portfolio Analytics")
    st.caption("Private owner reporting. One sign-in covers Page Views, Article Views and Job Search Analytics.")
    with st.form("analytics_owner_signin", clear_on_submit=True):
        password = st.text_input("Owner password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        try:
            st.session_state["cms_auth"] = owner_signin(password)
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError):
            st.error("Sign-in failed. Check your owner password and try again.")


def _url_view() -> str:
    view = str(st.query_params.get("view", "pages"))
    return view if view in _VIEWS else "pages"


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

    nav, portfolio, account = st.columns([6, 1.6, 1], vertical_alignment="center")
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
            st.session_state.pop("cms_auth", None)
            st.rerun()
    st.divider()

    if section == "jobs":
        render_job_search_analytics(session)
        return

    st.title(_VIEWS[section])
    window = st.selectbox(
        "Reporting window",
        [key for key, _ in REPORTING_WINDOWS],
        index=0,
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
    )
    render_reader_sources(str(window), "page" if section == "pages" else "article")
    render_content_intelligence("page" if section == "pages" else "article", str(window))
    st.divider()
    if section == "pages":
        render_site_analytics_dashboard()
    else:
        render_article_analytics()
