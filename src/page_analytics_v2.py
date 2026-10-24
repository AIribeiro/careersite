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
from page_public_portfolio_overview import render_public_portfolio_overview


_VIEWS = {
    "overview": "Visits & reads",
    "portfolio": "Explore content",
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


def _render_public_analytics() -> None:
    """Public content reporting only; no hiring, labour market or forecast."""
    legacy = str(st.query_params.get("view", "")).lower().strip()
    if legacy in ("pages", "articles"):
        # Force legacy reader bookmarks onto the detailed content view even
        # when the current browser had a different Analytics tab selected.
        st.session_state["analytics_portfolio_kind"] = (
            "article" if legacy == "articles" else "page"
        )
        st.session_state[_VIEW_STATE_KEY] = "portfolio"
    elif _VIEW_STATE_KEY not in st.session_state:
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
    st.caption("Public portfolio engagement: visits, article reads, content reach and reader journeys.")
    st.divider()

    if section == "overview":
        render_public_portfolio_overview()
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
        help="Starts with the first period with recorded sessions: Last hour → Today → 7 → 30 → 90 → 365 days. If all are empty, shows 365 days. Your manual selection is kept while you use Analytics.",
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

# One Analytics URL with content-only public reporting and authenticated
# hiring intelligence / CMS. The full legacy job dashboards are kept private.
_WORKSPACE_STATE_KEY = "careersite_analytics_workspace"
_WORKSPACE_LABELS = {
    "public": "Public analytics",
    "private": "Private analytics",
    "cms": "CMS",
}


def _resolve_workspace(requested: object, authenticated: bool) -> str:
    """Never route an anonymous browser to a private analytics/CMS renderer."""
    value = str(requested or "public").lower().strip()
    return value if authenticated and value in ("private", "cms") else "public"


def _workspace_from_url(authenticated: bool) -> str:
    explicit = st.query_params.get("workspace", None)
    # Pre-migration bookmarks to job reports are private even when the old
    # link does not carry an explicit workspace parameter.
    requested = str(st.query_params.get("view", "")).lower().strip()
    if explicit is None and requested in ("jobs", "market", "predictions", "hiring", "deep", "attribution", "meetings", "followups"):
        explicit = "private"
    return _resolve_workspace(explicit, authenticated)


def _update_workspace_url() -> None:
    workspace = st.session_state.get(_WORKSPACE_STATE_KEY, "public")
    if workspace in ("private", "cms"):
        st.query_params["workspace"] = workspace
    else:
        st.query_params.pop("workspace", None)
        # A private deep-link marker must not immediately bounce the owner
        # back into the private workspace after selecting Public analytics.
        if str(st.query_params.get("view", "")).lower() in (
            "jobs", "market", "predictions", "hiring", "deep", "attribution", "meetings",
        ):
            st.query_params["view"] = "overview"


def render_analytics_dashboard() -> None:
    """Public analytics by default; verified owners also see private reports and CMS."""
    _noindex()
    _dashboard_css()

    # Reuse the existing Supabase owner identity check, refresh and device
    # restoration. A failed authentication service must never block public
    # analytics or grant access to a private renderer.
    from page_admin import _session as owner_session, _dashboard as owner_dashboard
    from page_admin import _css as owner_css
    from site_owner_persistence import show_owner_login_or_refresh

    try:
        owner = owner_session()
    except (RuntimeError, TimeoutError, ValueError):
        owner = None

    workspace = _workspace_from_url(authenticated=owner is not None)
    st.session_state[_WORKSPACE_STATE_KEY] = workspace
    # An anonymous browser cannot follow an old job/forecast deep link.
    # Its public navigation and reporting always fall back to content only.
    if owner is None and st.session_state.get(_VIEW_STATE_KEY) not in _VIEWS:
        st.session_state[_VIEW_STATE_KEY] = "overview"

    if owner is None:
        # Do not even create a password widget until sign-in is selected:
        # the anonymous public dashboard must remain entirely read-only.
        _, login_column = st.columns([7, 1.5], vertical_alignment="center")
        with login_column:
            if st.button("Owner sign in", key="analytics_owner_login_toggle"):
                st.session_state["analytics_owner_login_open"] = not bool(
                    st.session_state.get("analytics_owner_login_open")
                )
        if st.session_state.get("analytics_owner_login_open"):
            with st.expander("Owner sign in", expanded=True):
                # Reuse the proven native form, including Cloud-safe fallback.
                show_owner_login_or_refresh("analytics")
        _render_public_analytics()
        return

    navigation, portfolio = st.columns([7, 1.5], vertical_alignment="center")
    with navigation:
        # Streamlit removes hidden widget state on reruns. Keep CMS navigation
        # locked during editing so unsaved drafts cannot be lost by switching
        # to another workspace before using the editor's own back/save controls.
        editing = bool(st.session_state.get("cms_edit_id")) and workspace == "cms"
        workspace = st.segmented_control(
            "Analytics workspace",
            options=list(_WORKSPACE_LABELS),
            format_func=lambda value: _WORKSPACE_LABELS[value],
            key=_WORKSPACE_STATE_KEY,
            on_change=_update_workspace_url,
            disabled=editing,
            label_visibility="collapsed",
            width="stretch",
        ) or "public"
    with portfolio:
        if workspace == "public":
            if st.button("Sign out", key="analytics_owner_signout"):
                from site_owner_persistence import browser_owner_signout as owner_signout
                owner_signout()
                return
        elif st.button(
            "Portfolio", key="owner_workspace_back_to_portfolio",
            disabled=editing,
        ):
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.rerun()

    if editing:
        st.caption("Finish article editing or return to the article list to change workspaces.")

    if workspace == "public":
        _render_public_analytics()
        return

    st.divider()
    owner_css()
    owner_dashboard(owner, workspace_mode="private" if workspace == "private" else "CMS")
