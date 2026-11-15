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

MEMBER_EXPERIENCE_VERSION = "premium_conversations_20261115"

VIEWS = (
    "overview", "requests", "messages", "scorecard", "rollout", "decision", "account",
)
VIEW_LABELS = {
    "overview": "Overview",
    "requests": "Requests",
    "messages": "Conversations",
    "scorecard": "AI Scorecard",
    "rollout": "Rollout Advisor",
    "decision": "Investment Advisor",
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
        selection_mode="single", required=True, key="advisory_member_navigation",
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


OVERVIEW_CSS = """
<style>
/* Advisory Overview uses the Rollout Advisor's editorial hierarchy and palette. */
.ao-home .hero{margin-top:4px}
.ao-home .summarybar{gap:9px 22px}
.ao-home .section-head{margin:28px 0 14px}
.ao-focus{background:#fffdfa;border:1px solid #ded7cc;
 border-left:5px solid #b07751;padding:clamp(18px,2.7vw,27px);margin:12px 0 17px}
.ao-focus .eyebrow,.ao-service-content .eyebrow,.ao-library .eyebrow{
 font:800 10px/1.45 Arial,sans-serif;text-transform:uppercase;
 letter-spacing:.17em;color:#a36c46}
.ao-focus h3{font:500 clamp(23px,2.7vw,30px)/1.2 Georgia,serif;
 margin:8px 0;color:#193047;overflow-wrap:anywhere}
.ao-focus p{font:14px/1.67 Arial,sans-serif;color:#40576a;
 max-width:850px;margin:7px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}
.ao-focus .ao-status{display:inline-block;margin:9px 0 3px;
 font:700 11px/1.5 Arial,sans-serif;color:#87573e;
 background:#f6eee6;padding:5px 10px}
.ao-focus--quiet{border-left-color:#93a4ab;background:#f7f8f7}
.ao-service-content{min-height:180px}
.ao-service-content .eyebrow{display:block;margin-bottom:13px}
.ao-service-content h3{font:500 clamp(21px,2.3vw,28px)/1.2 Georgia,serif;
 margin:0 0 11px;color:#193047;overflow-wrap:anywhere}
.ao-service-content p{font:14px/1.62 Arial,sans-serif;
 color:#4c6275;margin:0 0 12px}
.ao-service-content .ao-output{font:700 12px/1.55 Arial,sans-serif;
 color:#29445b;margin:0 0 13px}
.ao-service-access{border-top:1px solid #e9e2d8;padding:10px 0 2px;
 font:700 11px/1.6 Arial,sans-serif;color:#586d7b}
.ao-service-access--approved{color:#37645b}
.ao-service-access--pending{color:#925f45}
.ao-service-access--unknown{color:#6e727b}
.ao-library{background:#f8f5ef;border:1px solid #e0d9ce;
 padding:20px 23px;margin:16px 0}
.ao-library strong{display:block;font:500 22px/1.25 Georgia,serif;
 color:#1e364b;margin:8px 0}
.ao-library p{font:13px/1.65 Arial,sans-serif;color:#526777;margin:0}
.st-key-overview_card_advisory,.st-key-overview_card_scorecard,
.st-key-overview_card_rollout,.st-key-overview_card_investment{
 background:#fffdfa!important;border-color:#ded7cc!important;
 border-radius:0!important
}
.st-key-overview_card_advisory button,.st-key-overview_card_scorecard button,
.st-key-overview_card_rollout button,.st-key-overview_card_investment button{
 min-height:43px!important;font-weight:700!important
}
@media(max-width:760px),(max-device-width:760px){
 .ao-home .summarybar{gap:7px 14px}
 .ao-service-content{min-height:0}
 .ao-focus{padding:18px}
 .ao-library{padding:17px}
}
</style>
"""


def _overview_service_content(
    number: str, category: str, title: str, description: str,
    output: str, access: str, access_kind: str = "",
) -> None:
    """Render a service's promise and actual access state, never a fake control."""
    kind = (" ao-service-access--" + access_kind
            if access_kind in {"approved", "pending", "unknown"} else "")
    st.html(
        '<div class="ao-service-content">'
        '<span class="eyebrow">' + escape(number + " · " + category) + '</span>'
        '<h3>' + escape(title) + '</h3>'
        '<p>' + escape(description) + '</p>'
        '<div class="ao-output">You receive · ' + escape(output) + '</div>'
        '<div class="ao-service-access' + kind + '">'
        + escape(access) + '</div></div>'
    )


def render_overview(session: dict, user: dict, profile: dict) -> None:
    """A decision-oriented home, not a second page listing every service's tools."""
    from page_rollout_workspace_ui import WORKSPACE_CSS

    token = str(session["access_token"])
    uid = str(user["id"])
    first = str(profile.get("first_name") or "").strip()
    requests = _load_requests(token, uid)

    # Show only verified entitlements. Account membership does not grant service access.
    try:
        from page_advisory_scorecard_workspace import _read_workspaces
        scorecard_approved = bool(_read_workspaces(token, uid))
        scorecard_status = ("Workspace approved" if scorecard_approved
                            else "Individual approval required")
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        scorecard_approved = None
        scorecard_status = "Access status temporarily unavailable"

    try:
        from page_advisory_rollout import _entitlements
        rollout_approved = bool(_entitlements(token, uid))
        rollout_status = ("Access approved" if rollout_approved
                          else "Individual approval required")
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        rollout_approved = None
        rollout_status = "Access status temporarily unavailable"

    open_requests = ([r for r in requests
                      if str(r.get("status") or "submitted") not in CLOSED]
                     if requests is not None else [])
    current = open_requests[0] if open_requests else None
    request_summary = (str(len(open_requests)) + " open advisory request" +
                       ("" if len(open_requests) == 1 else "s")
                       if requests is not None else "Status unavailable")
    known = [flag for flag in (scorecard_approved, rollout_approved)
             if flag is not None]
    access_summary = (str(sum(known)) + " of 2 approved services"
                      if len(known) == 2 else "Some access statuses unavailable")

    st.html(
        WORKSPACE_CSS + OVERVIEW_CSS +
        '<div class="rl-workspace ao-home">'
        '<section class="hero"><span class="eyebrow">Private executive advisory</span>'
        '<h2>Your AI decisions. One private starting point.</h2>'
        '<p>See what needs your attention, choose the right decision service, '
        'and return to your existing work without losing its context.</p></section>'
        '<div class="summarybar">'
        '<span>ACCOUNT · Verified advisory member</span>'
        '<span>REQUESTS · ' + escape(request_summary) + '</span>'
        '<span>APPROVAL-BASED ACCESS · ' + escape(access_summary) + '</span>'
        '</div>'
        '<div class="section-head"><span class="eyebrow">Your current position</span>'
        '<h3>' + ("Continue your advisory discussion." if current else
                  "Your next decision starts here.") + '</h3>'
        '<p>One clear next step, with your requests and decision records '
        'kept in their respective workspaces.</p></div></div>'
    )
    if current:
        status, explanation = _status(current)
        next_step = str(current.get("next_step") or "").strip()
        st.html(
            '<div class="rl-workspace ao-home"><section class="ao-focus">'
            '<span class="eyebrow">Open executive advisory request</span>'
            '<h3>' + escape(str(current.get("title") or "Your advisory request"))
            + '</h3><span class="ao-status">' + escape(status) + '</span>'
            '<p>' + escape(next_step if next_step else explanation)
            + '</p></section></div>'
        )
        left, right = st.columns(2, gap="small")
        with left:
            label = ("Read and respond" if str(current.get("status")) == "awaiting_client"
                     else "Open this conversation")
            if st.button(label, type="primary", key="dashboard_open_conversation",
                         use_container_width=True):
                navigate("messages", str(current["id"]))
        with right:
            if st.button("Review all requests", key="dashboard_all_requests",
                         use_container_width=True):
                navigate("requests")
    elif requests is None:
        st.html(
            '<div class="rl-workspace ao-home"><div class="ao-focus ao-focus--quiet">'
            '<span class="eyebrow">Request status unavailable</span>'
            '<h3>Your request history could not be loaded.</h3>'
            '<p>Other services remain available according to their own '
            'permissions. You can retry from the Requests tab.</p></div></div>'
        )
    else:
        st.html(
            '<div class="rl-workspace ao-home"><div class="ao-focus ao-focus--quiet">'
            '<span class="eyebrow">No open personal advisory request</span>'
            '<h3>Have a decision you want to discuss?</h3>'
            '<p>Submit a focused business decision for individual review, '
            'or open one of the self-service advisors below.</p></div></div>'
        )
        if st.button("Start an executive advisory request", type="primary",
                     key="dashboard_new_request", use_container_width=True):
            navigate("requests")

    st.html(
        '<div class="rl-workspace ao-home"><div class="section-head">'
        '<span class="eyebrow">Your decision services</span>'
        '<h3>Four pathways. A distinct outcome for each.</h3>'
        '<p>Open the service that matches your decision. Existing assessments, '
        'conversations and their records remain in separate private workspaces.</p>'
        '</div></div>'
    )

    first_row = st.columns(2, gap="medium")
    with first_row[0]:
        with st.container(border=True, key="overview_card_advisory"):
            _overview_service_content(
                "01", "PERSONAL ADVISORY", "Executive discussion",
                "Submit a leadership decision for individual review and continue "
                "the conversation as its scope develops.",
                "Private discussion and agreed next steps",
                (str(len(open_requests)) + " open request" +
                 ("" if len(open_requests) == 1 else "s"))
                if requests is not None else "Request status unavailable",
                "approved" if current else "unknown",
            )
            if st.button("Manage advisory requests", key="overview_requests",
                         use_container_width=True):
                navigate("requests")
    with first_row[1]:
        with st.container(border=True, key="overview_card_scorecard"):
            _overview_service_content(
                "02", "PORTFOLIO INVESTMENT", "AI Portfolio Scorecard",
                "Compare competing AI initiatives, determine investment priorities, "
                "and document the rationale behind your portfolio decisions.",
                "Prioritized initiatives and decision record",
                scorecard_status,
                "approved" if scorecard_approved else
                "pending" if scorecard_approved is False else "unknown",
            )
            if st.button("Open Scorecard", key="overview_scorecard",
                         use_container_width=True):
                navigate("scorecard")

    second_row = st.columns(2, gap="medium")
    with second_row[0]:
        with st.container(border=True, key="overview_card_rollout"):
            _overview_service_content(
                "03", "ADOPTION AND SCALE", "AI Rollout Readiness Advisor",
                "Assess whether a pilot is ready to scale, identify critical "
                "release conditions, and determine the responsible next step.",
                "Readiness verdict, executive actions and PDF brief",
                rollout_status,
                "approved" if rollout_approved else
                "pending" if rollout_approved is False else "unknown",
            )
            if st.button("Open Rollout Advisor", key="overview_rollout",
                         use_container_width=True):
                navigate("rollout")
    with second_row[1]:
        with st.container(border=True, key="overview_card_investment"):
            _overview_service_content(
                "04", "SINGLE AI OPPORTUNITY", "AI Investment Decision Advisor",
                "Assess one business opportunity and decide whether to invest, "
                "run a focused experiment, hold, or stop.",
                "Investment recommendation and executive decision brief",
                "Included · No separate approval",
                "approved",
            )
            if st.button("Open Investment Advisor", key="overview_investment",
                         use_container_width=True):
                navigate("decision")

    st.html(
        '<div class="rl-workspace ao-home"><div class="section-head">'
        '<span class="eyebrow">Included with your account</span>'
        '<h3>Your executive reading library.</h3></div></div>'
    )
    a, b = st.columns([3, 1], gap="medium", vertical_alignment="center")
    with a:
        st.html(
            '<div class="ao-library"><span class="eyebrow">Premium Reader Library</span>'
            '<strong>Research and briefings, alongside your decisions.</strong>'
            '<p>Full reader access is included with your Advisory account. '
            'Reading and decision workspaces remain separate.</p></div>'
        )
    with b:
        if st.button("Open Reader Library", key="overview_library",
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


def _conversation_changed() -> None:
    selected = st.session_state.get("advisory_member_conversation")
    if selected:
        st.query_params["request"] = str(selected)



def render_messages(session: dict, user: dict) -> None:
    """Focused conversation workspace using the Rollout Advisor design language."""
    from page_advisory_conversation_workspace import render_conversation_workspace
    render_conversation_workspace(session, user)
