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


OVERVIEW_CSS = """
<style>
/* Advisory Overview follows the Rollout Readiness Advisor design vocabulary.
   Service-specific approvals and data are still owned by their source modules. */
.advisory-overview .summarybar{margin-bottom:7px}
.advisory-overview .status-panel{background:#fffdfa;border:1px solid #d9d5cd;
 border-left:5px solid #b07751;padding:clamp(19px,3vw,28px);margin:8px 0 12px}
.advisory-overview .status-panel h3{font:500 clamp(22px,2.7vw,30px)/1.2 Georgia,serif;
 color:#19314a;margin:7px 0 9px;overflow-wrap:anywhere}
.advisory-overview .status-panel p{font:14px/1.7 Arial,sans-serif;
 color:#43576a;margin:0 0 10px;overflow-wrap:anywhere}
.advisory-overview .status-panel p:last-child{margin-bottom:0}
.advisory-overview .status-panel .next-action{padding-top:11px;margin-top:11px;
 border-top:1px solid #e4ded5}
.advisory-overview .eyebrow{display:block}
.advisory-overview .membership-note{background:#f1f4f4;border-left:3px solid #8ca1a4;
 padding:18px 21px;font:13px/1.7 Arial,sans-serif;color:#3c5465;margin:12px 0 18px}
.advisory-overview .membership-note strong{display:block;color:#203c52;margin-bottom:5px}
.advisory-overview .membership-note p{margin:0}
.advisory-service-intro{padding:4px 2px 0;min-height:202px;color:#193047}
.advisory-service-intro .eyebrow{display:block;font:800 10px/1.5 Arial,sans-serif;
 text-transform:uppercase;letter-spacing:.15em;color:#a36c46}
.advisory-service-intro h3{font:500 clamp(21px,2.25vw,26px)/1.23 Georgia,serif;
 margin:10px 0;color:#193047;overflow-wrap:anywhere}
.advisory-service-intro p{font:13px/1.65 Arial,sans-serif;color:#546879;
 margin:0 0 12px;overflow-wrap:anywhere}
.advisory-service-intro .outcome{font-size:12px;color:#253e52;margin:0 0 11px}
.advisory-service-intro .outcome strong{color:#203b52}
.advisory-service-intro .access{font:700 11px/1.55 Arial,sans-serif;
 color:#855a41;padding-top:9px;border-top:1px solid #e6dfd5;margin:0}
.st-key-overview_card_discussion [data-testid="stVerticalBlockBorderWrapper"],
.st-key-overview_card_scorecard [data-testid="stVerticalBlockBorderWrapper"],
.st-key-overview_card_rollout [data-testid="stVerticalBlockBorderWrapper"],
.st-key-overview_card_investment [data-testid="stVerticalBlockBorderWrapper"]{
 background:#fffdfa!important;border-color:#ddd7cc!important;
 border-radius:0!important;padding:19px 21px!important;
 box-shadow:0 3px 14px rgba(14,33,54,.025)}
@media(max-width:760px),(max-device-width:760px){
 .advisory-service-intro{min-height:0;padding:0}
 .advisory-overview .status-panel{padding:18px}
 .st-key-overview_card_discussion [data-testid="stVerticalBlockBorderWrapper"],
 .st-key-overview_card_scorecard [data-testid="stVerticalBlockBorderWrapper"],
 .st-key-overview_card_rollout [data-testid="stVerticalBlockBorderWrapper"],
 .st-key-overview_card_investment [data-testid="stVerticalBlockBorderWrapper"]{
  padding:16px!important}
}
</style>
"""


OVERVIEW_SECTIONS = ("workspaces", "process", "membership")
OVERVIEW_LABELS = {
    "workspaces": "My workspaces",
    "process": "How Advisory works",
    "membership": "Membership & access",
}


def _overview_nav_changed() -> None:
    selected = st.session_state.get("advisory_overview_section")
    if selected in OVERVIEW_SECTIONS:
        st.query_params["overview_section"] = selected


def _overview_navigation() -> str:
    requested = str(st.query_params.get("overview_section") or "workspaces")
    if requested not in OVERVIEW_SECTIONS:
        requested = "workspaces"
    if st.session_state.get("advisory_overview_section") != requested:
        st.session_state["advisory_overview_section"] = requested
    st.pills(
        "Advisory overview sections", OVERVIEW_SECTIONS,
        format_func=lambda value: OVERVIEW_LABELS[value],
        selection_mode="single", required=True,
        key="advisory_overview_section",
        on_change=_overview_nav_changed,
        label_visibility="collapsed", wrap=False, width="stretch",
    )
    return requested


def _overview_service_copy(number: str, category: str, title: str,
                           description: str, outcome: str, access: str) -> None:
    """Keep all service summaries consistent with the Rollout's executive cards."""
    st.html(
        '<section class="advisory-service-intro">'
        '<span class="eyebrow">' + escape(number + " · " + category) + '</span>'
        '<h3>' + escape(title) + '</h3>'
        '<p>' + escape(description) + '</p>'
        '<p class="outcome"><strong>You receive · </strong>' + escape(outcome) + '</p>'
        '<p class="access">ACCESS · ' + escape(access) + '</p>'
        '</section>'
    )


def render_overview(session: dict, user: dict, profile: dict) -> None:
    """Executive dashboard: one current decision, four distinct service routes."""
    from page_rollout_workspace_ui import WORKSPACE_CSS

    token = str(session["access_token"])
    uid = str(user["id"])
    requests = _load_requests(token, uid)
    open_requests = (
        [r for r in requests if str(r.get("status") or "submitted") not in CLOSED]
        if requests is not None else []
    )
    current = open_requests[0] if open_requests else None

    # Read actual entitlements: an active account does not mean these services
    # have been individually approved.
    try:
        from page_advisory_scorecard_workspace import _read_workspaces
        scorecard_status = ("Approved workspace" if _read_workspaces(token, uid)
                            else "Individual approval required")
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        scorecard_status = "Access status unavailable"
    try:
        from page_advisory_rollout import _entitlements
        rollout_status = ("Access approved" if _entitlements(token, uid)
                          else "Individual approval required")
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        rollout_status = "Access status unavailable"

    if requests is None:
        request_indicator = "Temporarily unavailable"
    elif current is not None:
        request_indicator = "Needs your input" if str(current.get("status")) == "awaiting_client" else "In progress"
    else:
        request_indicator = "None open"

    st.html(
        WORKSPACE_CSS + OVERVIEW_CSS +
        '<div class="rl-workspace advisory-overview">'
        '<section class="hero">'
        '<span class="eyebrow">Private executive decision advisory</span>'
        '<h2>A clear view of your next AI decision.</h2>'
        '<p>Follow your advisory discussions, access your approved services '
        'and choose the right assessment for the decision in front of you. '
        'Each service has its own private workspace.</p>'
        '</section><div class="summarybar">'
        '<span>ACCOUNT · Verified Advisory member</span>'
        '<span>SERVICES · Four distinct options</span>'
        '<span>CURRENT REQUEST · ' + escape(request_indicator) + '</span>'
        '</div></div>'
    )

    section = _overview_navigation()
    if section == "process":
        st.html(
            '<div class="rl-workspace advisory-overview">'
            '<div class="section-head"><span class="eyebrow">How it works</span>'
            '<h3>From your decision to a useful next step.</h3>'
            '<p>Use the self-service advisors for structured recommendations; '
            'use personal advisory for decisions that call for a discussion.</p></div>'
            '<div class="steps">'
            '<div><b>01</b><strong>Choose the decision</strong>'
            '<span>Open a service to see its scope, expected output and access requirements.</span></div>'
            '<div><b>02</b><strong>Provide focused context</strong>'
            '<span>Complete the relevant assessment, or submit a private request for review.</span></div>'
            '<div><b>03</b><strong>Review the outcome</strong>'
            '<span>Read your assessment or correspondence and act on its stated next steps.</span></div>'
            '</div><div class="callout">'
            '<strong>Different services, different decisions</strong>'
            'Automated assessments are structured decision aids, not regulatory '
            'approvals. Personal advisory requests are considered individually; '
            'submitting a request does not guarantee an engagement.</div></div>'
        )
        if st.button("Explore advisory services", type="primary",
                     key="overview_process_services"):
            st.query_params["overview_section"] = "workspaces"
            st.rerun()
        return

    if section == "membership":
        st.html(
            '<div class="rl-workspace advisory-overview">'
            '<div class="section-head"><span class="eyebrow">Your membership</span>'
            '<h3>Private advice, with clear access rules.</h3>'
            '<p>Your verified account gives you access to personal advisory requests '
            'and the Investment Decision Advisor. Portfolio Scorecard and '
            'Rollout Readiness are individually approved services.</p></div>'
            '<div class="three-col">'
            '<article><span class="eyebrow">01 · Private access</span>'
            '<strong>Your own records</strong>'
            '<p>Requests, messages and saved decisions remain tied to your verified account.</p></article>'
            '<article><span class="eyebrow">02 · Service approval</span>'
            '<strong>Access by service</strong>'
            '<p>Check each service for its current entitlement and request access where needed.</p></article>'
            '<article><span class="eyebrow">03 · Reader membership</span>'
            '<strong>Full library access</strong>'
            '<p>Your Advisory membership includes the Premium Reader Library.</p></article>'
            '</div><div class="callout"><strong>Account and library</strong>'
            'Your editorial library and private Advisory decisions remain separate '
            'workspaces. Use your Account tab to manage your Advisory profile.</div></div>'
        )
        if st.button("Open Premium Reader Library", type="primary",
                     key="overview_library", use_container_width=False):
            st.query_params.clear()
            st.query_params["page"] = "readers"
            st.rerun()
        return

    st.html(
        '<div class="rl-workspace advisory-overview">'
        '<div class="section-head"><span class="eyebrow">Your current position</span>'
        '<h3>What needs attention now.</h3>'
        '<p>Your most recent open request, based on its recorded status. '
        'Service assessments are managed in their own workspaces.</p></div></div>'
    )
    if current is not None:
        status, explanation = _status(current)
        next_step = str(current.get("next_step") or "").strip()
        outcome = str(current.get("desired_outcome") or "").strip()
        st.html(
            '<div class="rl-workspace advisory-overview"><div class="status-panel">'
            '<span class="eyebrow">Advisory request · ' + escape(status) + '</span>'
            '<h3>' + escape(str(current.get("title") or "Your advisory request")[:180]) + '</h3>'
            '<p>' + escape(explanation) + '</p>'
            + ('<p><strong>Decision sought · </strong>' + escape(outcome[:400]) + '</p>'
               if outcome else '')
            + ('<p class="next-action"><strong>Recorded next step · </strong>' +
               escape(next_step[:850]) + '</p>' if next_step else '')
            + '</div></div>'
        )
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button(
                "Read and respond" if str(current.get("status")) == "awaiting_client"
                else "Open current conversation",
                type="primary", key="overview_current_conversation",
                use_container_width=True,
            ):
                navigate("messages", str(current["id"]))
        with c2:
            if st.button("View request details", key="overview_current_request",
                         use_container_width=True):
                navigate("requests")
    elif requests is None:
        st.html(
            '<div class="rl-workspace advisory-overview"><div class="status-panel">'
            '<span class="eyebrow">Request status unavailable</span>'
            '<h3>Your service workspaces remain accessible.</h3>'
            '<p>Request history could not be retrieved. Open Requests to retry '
            'or continue in an approved service.</p></div></div>'
        )
        if st.button("Review requests", key="overview_requests_retry"):
            navigate("requests")
    else:
        st.html(
            '<div class="rl-workspace advisory-overview"><div class="status-panel">'
            '<span class="eyebrow">No open personal advisory requests</span>'
            '<h3>Start with the decision you need to make.</h3>'
            '<p>Explore a decision advisor below, or submit a specific question '
            'for individual advisory review.</p></div></div>'
        )
        if st.button("Submit an advisory request", type="primary",
                     key="overview_new_request"):
            navigate("requests")

    st.html(
        '<div class="rl-workspace advisory-overview">'
        '<div class="section-head"><span class="eyebrow">Your advisory services</span>'
        '<h3>Four services. Four distinct decision needs.</h3>'
        '<p>See what each service delivers, check your access and open '
        'the relevant workspace. No need to navigate a single long assessment page.</p>'
        '</div></div>'
    )
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(border=True, key="overview_card_discussion"):
            _overview_service_copy(
                "01", "Personal advisory", "Executive discussion",
                "Bring a business decision for private review, questions and "
                "an individually agreed next step.",
                "Private correspondence and recorded next actions",
                "Request-based advisory" +
                (" · Open request" if current is not None else ""),
            )
            if st.button("Manage requests", key="overview_requests",
                         use_container_width=True):
                navigate("requests")
            if st.button("Open conversations", key="overview_messages",
                         use_container_width=True):
                navigate("messages")
    with right:
        with st.container(border=True, key="overview_card_scorecard"):
            _overview_service_copy(
                "02", "Portfolio investment", "AI Portfolio Scorecard",
                "Assess competing AI initiatives on common criteria to "
                "support investment and prioritization choices.",
                "Portfolio comparison and executive decision record",
                scorecard_status,
            )
            if st.button("Open Scorecard workspace", key="overview_scorecard",
                         use_container_width=True):
                navigate("scorecard")

    left2, right2 = st.columns(2, gap="medium")
    with left2:
        with st.container(border=True, key="overview_card_rollout"):
            _overview_service_copy(
                "03", "Adoption and scale", "Enterprise AI Rollout Readiness Advisor",
                "Test whether a pilot is ready to scale, needs more "
                "evidence or should pause.",
                "Readiness verdict, executive actions and private decision brief",
                rollout_status,
            )
            if st.button("Open Rollout Advisor", key="overview_rollout",
                         use_container_width=True):
                navigate("rollout")
    with right2:
        with st.container(border=True, key="overview_card_investment"):
            _overview_service_copy(
                "04", "Single opportunity", "AI Investment Decision Advisor",
                "Evaluate one proposed AI opportunity and decide whether "
                "to invest, experiment, hold or stop.",
                "Focused recommendation and executive decision brief",
                "Included with verified Advisory membership",
            )
            if st.button("Open Investment Decision Advisor", key="overview_investment",
                         use_container_width=True):
                navigate("decision")

    st.html(
        '<div class="rl-workspace advisory-overview"><div class="membership-note">'
        '<strong>Included with your Advisory account</strong>'
        '<p>Full Premium Reader Library access is included. Your editorial '
        'library and private advisory records remain separate.</p>'
        '</div></div>'
    )
    if st.button("Open Premium Reader Library", key="overview_library",
                 use_container_width=False):
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
