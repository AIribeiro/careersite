"""Focused, deep-linkable sections for verified Executive Advisory members.

Only the selected workspace is rendered. Existing Supabase authorization, request
ownership, scorecard revisions, and rollout entitlements remain in their own
service modules; this file never grants access or bypasses an approval.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from page_advisory_client_journey import (
    CLOSED, STATUS, _client_requests, _display_conversation, _request_form,
)
from site_assets import ADVISORY_EMAIL

VIEWS = (
    "overview", "requests", "messages", "scorecard", "rollout", "account",
)
VIEW_LABELS = {
    "overview": "Overview",
    "requests": "Requests",
    "messages": "Conversations",
    "scorecard": "AI Scorecard",
    "rollout": "Rollout Advisor",
    "account": "Account",
}
MEMBER_CSS = """
<style>
.st-key-native_advisory_content {max-width:1140px!important}
.advisory-member-lead{margin:15px 0 26px}
.advisory-member-lead .kicker{font:800 11px/1.5 Arial,sans-serif;
 color:#986040;letter-spacing:.14em;text-transform:uppercase}
.advisory-member-lead h2{font:500 clamp(29px,3.5vw,43px)/1.18 Georgia,serif;
 color:#172c42;margin:9px 0 10px}
.advisory-member-lead p{font-size:15px;line-height:1.75;color:#536479;
 max-width:790px;margin:0}
.advisory-member-status{padding:17px 20px;border:1px solid #ddd7ce;
 background:#fffdfa;color:#263e52;font-size:14px;line-height:1.6;margin:8px 0 22px}
.advisory-member-status strong{color:#173047}
.st-key-native_advisory_content [data-testid="stPills"]{
 background:#fffdfa;border:1px solid #ded6ca;padding:10px 12px;
 border-radius:9px;margin-bottom:16px
}
.st-key-native_advisory_content [data-testid="stPills"] button{
 min-height:42px!important;font-weight:700!important
}
.st-key-native_advisory_content [data-testid="stVerticalBlockBorderWrapper"]{
 border-color:#ded8cf!important;
}
.st-key-native_advisory_content [data-testid="stMetric"]{
 border:0!important;
}
@media(max-width:700px), (max-device-width:700px){
 .advisory-member-lead{margin:8px 0 16px}
 .advisory-member-lead p{font-size:14px}
 .advisory-member-status{padding:14px 15px}
 .st-key-native_advisory_content [data-testid="stPills"]{padding:7px}
}
</style>
"""


def navigate(view: str, request_id: str = "") -> None:
    """Navigate without a full browser reload, preserving the Auth session."""
    if view not in VIEWS:
        return
    st.query_params["view"] = view
    if view == "messages" and request_id:
        st.query_params["request"] = request_id
    else:
        st.query_params.pop("request", None)
    st.rerun()


def _nav_changed() -> None:
    view = st.session_state.get("advisory_member_navigation")
    if view in VIEWS:
        st.query_params["view"] = view
        st.query_params.pop("request", None)


def member_navigation() -> str:
    """A single-row, touch-scrollable menu; URL preserves the active section."""
    requested = str(st.query_params.get("view") or "overview").lower()
    if requested not in VIEWS:
        requested = "overview"
    # Browser back/forward and links from public service pages win over old UI state.
    if st.session_state.get("advisory_member_navigation") != requested:
        st.session_state["advisory_member_navigation"] = requested
    st.pills(
        "Advisory sections", VIEWS,
        format_func=lambda v: VIEW_LABELS[v],
        selection_mode="single", key="advisory_member_navigation",
        on_change=_nav_changed, label_visibility="collapsed", wrap=False,
        width="stretch",
    )
    return requested


def section_heading(kicker: str, title: str, description: str = "") -> None:
    st.html(
        '<div class="advisory-member-lead">'
        '<span class="kicker">' + escape(kicker) + '</span>'
        '<h2>' + escape(title) + '</h2>'
        + ('<p>' + escape(description) + '</p>' if description else "")
        + '</div>'
    )


def _load_requests(token: str, uid: str) -> list[dict] | None:
    try:
        return _client_requests(token, uid)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("Advisory requests are temporarily unavailable. Try again.")
        return None


def _status(request: dict) -> tuple[str, str]:
    return STATUS.get(str(request.get("status") or "submitted"), STATUS["submitted"])


def _request_summary(request: dict, *, show_details: bool = True) -> None:
    title, explanation = _status(request)
    st.markdown("**" + str(request.get("title") or "Advisory request") + "**")
    st.caption("Submitted " + str(request.get("created_at") or "")[:10] +
               " · " + str(request.get("decision_timing") or "Timeframe not set"))
    st.markdown("**" + title + "** — " + explanation)
    if request.get("next_step"):
        st.info("Next step: " + str(request["next_step"]))
    if show_details:
        with st.expander("Decision and context"):
            st.write(str(request.get("desired_outcome") or ""))
            if request.get("business_context"):
                st.caption("Business context")
                st.write(str(request["business_context"]))


def render_overview(session: dict, user: dict, profile: dict) -> None:
    token = str(session["access_token"])
    uid = str(user["id"])
    first = str(profile.get("first_name") or "").strip()
    section_heading(
        "PRIVATE CLIENT DASHBOARD",
        "Welcome" + (", " + first if first else "") + ".",
        "Your decisions, approved services and advisory correspondence—"
        "each in its own private workspace.",
    )
    requests = _load_requests(token, uid)
    current = next(
        (r for r in requests if str(r.get("status")) not in CLOSED), None
    ) if requests is not None else None
    if current is not None:
        status, explanation = _status(current)
        st.html(
            '<div class="advisory-member-status"><strong>'
            + escape(status) + "</strong> · "
            + escape(str(current.get("title") or "Your advisory request"))
            + "<div>" + escape(explanation) + "</div></div>"
        )
        if str(current.get("status")) == "awaiting_client":
            if st.button("Respond to the advisory request", type="primary",
                         key="dashboard_respond"):
                navigate("messages", str(current["id"]))
    else:
        st.html(
            '<div class="advisory-member-status">'
            '<strong>Advisory account active.</strong> '
            'Choose a service below or submit a specific executive decision '
            'for individual review.</div>'
        )

    a, b, c = st.columns(3, gap="medium")
    with a:
        with st.container(border=True):
            st.caption("01 · PERSONAL ADVISORY")
            st.markdown("#### Executive discussion")
            st.write("Submit a decision, track its review and agree any next step.")
            st.caption(
                "Open request: " + ("Yes" if current else "No")
                if requests is not None else "Request status temporarily unavailable"
            )
            if st.button("Manage requests", key="overview_requests",
                         use_container_width=True):
                navigate("requests")
            if st.button("Open conversations", key="overview_messages",
                         use_container_width=True):
                navigate("messages")
    with b:
        with st.container(border=True):
            st.caption("02 · AI INVESTMENT DECISIONS")
            st.markdown("#### Portfolio Scorecard")
            st.write("Compare competing initiatives and record investment decisions.")
            st.caption("Individually approved private workspace")
            if st.button("Open AI Scorecard", key="overview_scorecard",
                         use_container_width=True):
                navigate("scorecard")
    with c:
        with st.container(border=True):
            st.caption("03 · AI ADOPTION & SCALE")
            st.markdown("#### Rollout Readiness Advisor")
            st.write("Assess rollout conditions and receive an executive decision brief.")
            st.caption("Single-session service · Individual approval")
            if st.button("Open Rollout Advisor", key="overview_rollout",
                         use_container_width=True):
                navigate("rollout")

    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### Included with your advisory account")
        st.write("Full Premium Reader Library access is included. Your editorial "
                 "library and your advisory workspaces remain separate.")
    with right:
        if st.button("Open Premium Reader Library", key="overview_library",
                     use_container_width=True):
            st.query_params.clear()
            st.query_params["page"] = "readers"
            st.rerun()


def render_requests(session: dict, user: dict, profile: dict) -> None:
    section_heading(
        "YOUR ADVISORY REQUESTS", "Decisions and requests",
        "Review your requests and their current status. Discussions "
        "and replies have a separate conversation workspace.",
    )
    token = str(session["access_token"])
    uid = str(user["id"])
    requests = _load_requests(token, uid)
    if requests is None:
        return
    current = next(
        (r for r in requests if str(r.get("status")) not in CLOSED), None
    )
    if current:
        with st.container(border=True):
            st.caption("CURRENT REQUEST")
            _request_summary(current)
            if st.button("View conversation and reply", type="primary",
                         key="requests_open_current"):
                navigate("messages", str(current["id"]))
        st.info("You have an open request. New service access requests can "
                "be added to that engagement from the relevant service page.")
    else:
        # Existing form retains its single-open-request server-side checks.
        _request_form(token, uid, profile)
    past = [r for r in requests if current is None or r["id"] != current["id"]]
    if past:
        st.markdown("### Request history")
        for idx, request in enumerate(past):
            with st.expander(str(request.get("title") or "Request") +
                             " · " + _status(request)[0]):
                _request_summary(request, show_details=False)
                st.write(str(request.get("desired_outcome") or ""))
                if request.get("business_context"):
                    st.caption("Business context")
                    st.write(str(request["business_context"]))
                if st.button("Open this conversation", key="requests_old_" + str(idx)):
                    navigate("messages", str(request["id"]))


def render_messages(session: dict, user: dict) -> None:
    section_heading(
        "PRIVATE CORRESPONDENCE", "Your conversations",
        "Messages, proposals and responses for your submitted advisory requests. "
        "This is not a public chat.",
    )
    token = str(session["access_token"])
    uid = str(user["id"])
    requests = _load_requests(token, uid)
    if requests is None:
        return
    if not requests:
        st.info("No conversations yet. Submit an advisory request to begin.")
        if st.button("Submit an advisory request", key="messages_new"):
            navigate("requests")
        return
    ids = [str(r["id"]) for r in requests]
    request_id = str(st.query_params.get("request") or "")
    selected_index = ids.index(request_id) if request_id in ids else 0
    selected = st.selectbox(
        "Conversation", ids,
        index=selected_index,
        format_func=lambda rid: next(
            (str(r.get("title") or "Advisory request") + " · " + _status(r)[0]
             for r in requests if str(r["id"]) == rid), "Advisory request"
        ),
        key="advisory_member_conversation",
    )
    target = next((r for r in requests if str(r["id"]) == selected), None)
    if target:
        _display_conversation(token, uid, target)
    st.caption("For account support: " + ADVISORY_EMAIL)
