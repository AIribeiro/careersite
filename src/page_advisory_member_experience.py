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
from page_rollout_workspace_ui import WORKSPACE_CSS

MEMBER_EXPERIENCE_VERSION = "rollout_consistent_overview_20261115"

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


REQUEST_SECTIONS = ("overview", "current", "history", "new")
REQUEST_LABELS = {
    "overview": "About requests",
    "current": "Current request",
    "history": "My history",
    "new": "New request",
}
REQUEST_CSS = """
<style>
.rq-workspace .case{background:#fffdfa;border:1px solid #d9d5cd;
 border-left:5px solid #b07751;padding:clamp(20px,3vw,30px);margin:13px 0}
.rq-workspace .case h3{font:500 clamp(23px,3vw,33px)/1.2 Georgia,serif;
 color:#19314a;margin:8px 0 11px;overflow-wrap:anywhere}
.rq-workspace .case p{font-size:14px;line-height:1.72;color:#3b5367;
 margin:0 0 9px;white-space:pre-wrap;overflow-wrap:anywhere}
.rq-workspace .case .status{font-size:16px;font-weight:700;color:#1c3a51}
.rq-workspace .detail{background:#fffdfa;border:1px solid #ddd7cc;
 padding:20px 23px;margin:12px 0}
.rq-workspace .detail strong{display:block;font-size:11px;letter-spacing:.11em;
 text-transform:uppercase;color:#a36c46;margin-bottom:9px}
.rq-workspace .detail p{font-size:14px;line-height:1.75;color:#344d62;
 white-space:pre-wrap;overflow-wrap:anywhere;margin:0}
.rq-workspace .note{padding:17px 20px;background:#f8f4ec;border:1px solid #e0d7ca;
 color:#3a5267;font-size:13px;line-height:1.7;margin:15px 0}
.rq-workspace .note strong{display:block;color:#213d53;margin-bottom:5px}
.rq-workspace .three-col article p,.rq-workspace .steps span{overflow-wrap:anywhere}
.st-key-native_advisory_content [data-testid="stPills"] button{white-space:nowrap}
@media(max-width:760px),(max-device-width:760px){
 .rq-workspace .case,.rq-workspace .detail{padding:18px}
 .rq-workspace .note{padding:15px}
 .rq-workspace .summarybar{gap:7px 15px}
}
</style>
"""


def _request_safe(value: object, limit: int = 2000) -> str:
    return escape(str(value if value is not None else "")[:limit], quote=True)


def _request_nav_changed() -> None:
    selected = st.session_state.get("advisory_request_navigation")
    if selected in REQUEST_SECTIONS:
        st.query_params["requests_section"] = selected


def _go_request_section(section: str) -> None:
    if section in REQUEST_SECTIONS:
        st.query_params["requests_section"] = section
        st.rerun()


def _request_navigation() -> str:
    requested = str(st.query_params.get("requests_section") or "overview").lower()
    if requested not in REQUEST_SECTIONS:
        requested = "overview"
    if st.session_state.get("advisory_request_navigation") != requested:
        st.session_state["advisory_request_navigation"] = requested
    st.pills(
        "Request sections", REQUEST_SECTIONS,
        format_func=lambda v: REQUEST_LABELS[v],
        selection_mode="single", required=True,
        key="advisory_request_navigation", on_change=_request_nav_changed,
        label_visibility="collapsed", wrap=False, width="stretch",
    )
    return requested


def _request_guidance(request: dict) -> str:
    # One shared source for client next-action language in Requests and Conversations.
    from page_advisory_conversation_workspace import STATE_GUIDANCE
    state = str(request.get("status") or "submitted")
    return STATE_GUIDANCE.get(state, STATE_GUIDANCE["submitted"])


def _request_case(request: dict, *, title: str = "Selected request") -> None:
    status, description = _status(request)
    st.html(
        '<div class="rl-workspace rq-workspace"><div class="case">'
        '<span class="eyebrow">' + _request_safe(title, 90) + ' · ' +
        _request_safe(str(request.get("created_at") or "")[:10]) + '</span>'
        '<h3>' + _request_safe(request.get("title") or "Executive advisory request", 160) + '</h3>'
        '<p class="status">' + _request_safe(status) + '</p>'
        '<p>' + _request_safe(description) + '</p>'
        '</div></div>'
    )


def _request_next_step(request: dict) -> None:
    st.html(
        '<div class="rl-workspace rq-workspace"><div class="section-head">'
        '<span class="eyebrow">Your current position</span>'
        '<h3>What happens next</h3>'
        '<p>Guidance based on the recorded request status, not a promised date or approval.</p>'
        '</div><div class="note"><strong>What you should do now</strong>' +
        _request_safe(_request_guidance(request)) + '</div></div>'
    )
    next_step = str(request.get("next_step") or "").strip()
    if next_step:
        st.html(
            '<div class="rl-workspace rq-workspace"><div class="detail">'
            '<strong>Next step recorded in your advisory request</strong>'
            '<p>' + _request_safe(next_step, 1800) + '</p>'
            '</div></div>'
        )


def _request_context(request: dict) -> None:
    st.html(
        '<div class="rl-workspace rq-workspace"><div class="section-head">'
        '<span class="eyebrow">Decision and context</span>'
        '<h3>What this request contains</h3>'
        '<p>Review the question, outcome and timing as originally submitted.</p>'
        '</div><div class="detail"><strong>Decision or outcome sought</strong><p>' +
        _request_safe(request.get("desired_outcome") or "Not provided", 3000) +
        '</p></div>'
        + (
            '<div class="detail"><strong>Business context</strong><p>' +
            _request_safe(request.get("business_context"), 3000) + '</p></div>'
            if request.get("business_context") else ""
        ) +
        '<div class="three-col">'
        '<article><span class="eyebrow">01 · Submitted</span><strong>' +
        _request_safe(str(request.get("created_at") or "")[:10] or "Not available") +
        '</strong><p>When this request was recorded.</p></article>'
        '<article><span class="eyebrow">02 · Decision horizon</span><strong>' +
        _request_safe(request.get("decision_timing") or "Not specified", 80) +
        '</strong><p>Your stated business timing, not a response commitment.</p></article>'
        '<article><span class="eyebrow">03 · Contact preference</span><strong>' +
        _request_safe(request.get("contact_preference") or "Not specified", 80) +
        '</strong><p>A preference, not a confirmed appointment.</p></article>'
        '</div></div>'
    )


def _request_overview(requests: list[dict], current: dict | None) -> None:
    status = _status(current)[0] if current else "No open request"
    count = len(requests)
    st.html(
        WORKSPACE_CSS + REQUEST_CSS +
        '<div class="rl-workspace rq-workspace"><section class="hero">'
        '<span class="eyebrow">Private executive advisory</span>'
        '<h2>One business question. A clear path to the next decision.</h2>'
        '<p>Submit a defined leadership challenge, follow its individual review '
        'and keep your decision context and correspondence in one private record.</p>'
        '</section><div class="summarybar">'
        '<span>ACCESS · Verified Advisory account</span>'
        '<span>FORMAT · Individual request and conversation</span>'
        '<span>RECORDS · ' + str(count) + ' request' + ("" if count == 1 else "s") +
        '</span></div>'
        '<div class="section-head"><span class="eyebrow">What you receive</span>'
        '<h3>One request. Three clear stages.</h3>'
        '<p>An individual advisory review, not an automatic consulting engagement '
        'or a substitute for the self-service decision advisors.</p></div>'
        '<div class="three-col">'
        '<article><span class="eyebrow">01 · Your question</span>'
        '<strong>A defined decision</strong><p>The challenge, desired outcome '
        'and relevant business context are saved together.</p></article>'
        '<article><span class="eyebrow">02 · The review</span>'
        '<strong>A visible status</strong><p>See whether your request is being '
        'reviewed, needs your input or has moved into a discussion.</p></article>'
        '<article><span class="eyebrow">03 · The next step</span>'
        '<strong>A private response</strong><p>Use Conversations for questions, '
        'scope discussions and any agreed next actions.</p></article>'
        '</div>'
        '<div class="section-head"><span class="eyebrow">How it works</span>'
        '<h3>Focused request. Considered response.</h3></div>'
        '<div class="steps">'
        '<div><b>01</b><strong>Describe the decision</strong>'
        '<span>Explain the outcome you need, your context and timing.</span></div>'
        '<div><b>02</b><strong>Individual review</strong>'
        '<span>Your request is assessed for relevance, scope and availability.</span></div>'
        '<div><b>03</b><strong>Discuss what comes next</strong>'
        '<span>If selected, clarify scope and next steps in Conversations.</span></div>'
        '</div><div class="callout">'
        '<strong>What this request does not approve</strong>'
        'Submitting a request does not grant access to the AI Scorecard or Rollout Advisor, '
        'confirm a meeting or guarantee a pro-bono engagement. Service access is '
        'reviewed separately from the relevant advisor page.</div>'
        '<div class="section-head"><span class="eyebrow">Your advisory record</span>'
        '<h3>' + _request_safe(status) + '</h3>'
        '<p>' + (
            'Open your current request to see what it covers and what happens next.'
            if current else
            'No active request is awaiting a decision or response. You can begin a new one.'
        ) + '</p></div></div>'
    )
    if current:
        _request_case(current, title="Current request")
        a, b = st.columns(2, gap="medium")
        with a:
            if st.button("Review current request", type="primary",
                         key="rq_overview_current", use_container_width=True):
                _go_request_section("current")
        with b:
            if st.button("Open conversation and reply", key="rq_overview_conversation",
                         use_container_width=True):
                navigate("messages", str(current["id"]))
    else:
        if st.button("Start a new advisory request", type="primary",
                     key="rq_overview_new"):
            _go_request_section("new")
    if requests:
        if st.button("Browse request history", key="rq_overview_history"):
            _go_request_section("history")


def render_requests(session: dict, user: dict, profile: dict) -> None:
    """Private request workspace following the Rollout Advisor's visual hierarchy."""
    st.markdown("### Executive Advisory Requests")
    st.caption("A focused request, individual review and a recorded next step.")
    section = _request_navigation()
    token = str(session["access_token"])
    uid = str(user["id"])
    requests = _load_requests(token, uid)
    if requests is None:
        return
    current = next(
        (r for r in requests if str(r.get("status")) not in CLOSED), None
    )
    previous = [r for r in requests if current is None or r["id"] != current["id"]]
    if section == "overview":
        _request_overview(requests, current)
        return
    if section == "current":
        if current is None:
            st.html(
                WORKSPACE_CSS + REQUEST_CSS +
                '<div class="rl-workspace rq-workspace"><div class="section-head">'
                '<span class="eyebrow">Current advisory request</span>'
                '<h3>No open request</h3>'
                '<p>Completed and declined requests remain available in My history.</p>'
                '</div></div>'
            )
            if st.button("Create a new request", type="primary", key="rq_current_new"):
                _go_request_section("new")
            return
        st.html(WORKSPACE_CSS + REQUEST_CSS)
        _request_case(current, title="Current advisory request")
        _request_next_step(current)
        _request_context(current)
        a, b = st.columns(2, gap="medium")
        with a:
            label = ("Read and respond" if str(current.get("status")) == "awaiting_client"
                     else "Open conversation")
            if st.button(label, type="primary", key="rq_current_conversation",
                         use_container_width=True):
                navigate("messages", str(current["id"]))
        with b:
            if st.button("Back to requests overview", key="rq_current_overview",
                         use_container_width=True):
                _go_request_section("overview")
        st.caption("Conversations contain the actual messages. This page records "
                   "the request and its status; it does not grant service access.")
        return
    if section == "history":
        st.html(
            WORKSPACE_CSS + REQUEST_CSS +
            '<div class="rl-workspace rq-workspace"><div class="section-head">'
            '<span class="eyebrow">Saved advisory record</span>'
            '<h3>Your previous requests</h3>'
            '<p>Select a request to see its original decision context, status '
            'and correspondence. Nothing is lost when a discussion is closed.</p>'
            '</div></div>'
        )
        if not previous:
            st.info("There are no previous requests yet. Your current request has its own tab.")
            if current and st.button("Open current request", key="rq_history_current"):
                _go_request_section("current")
            return
        by_id = {str(r["id"]): r for r in previous}
        chosen = st.selectbox(
            "Select a previous request", list(by_id),
            format_func=lambda rid: (
                str(by_id[rid].get("title") or "Advisory request") + " · " +
                _status(by_id[rid])[0] + " · " +
                str(by_id[rid].get("created_at") or "")[:10]
            ),
            key="advisory_request_history_selected",
        )
        selected = by_id[chosen]
        _request_case(selected, title="Selected previous request")
        _request_context(selected)
        if st.button("Open this conversation", type="primary", key="rq_history_conversation"):
            navigate("messages", str(selected["id"]))
        return
    # New requests retain the existing RLS-protected, single-active-request form.
    st.html(
        WORKSPACE_CSS + REQUEST_CSS +
        '<div class="rl-workspace rq-workspace"><div class="section-head">'
        '<span class="eyebrow">New executive request</span>'
        '<h3>Define the decision you want to make.</h3>'
        '<p>Start with one specific business challenge. You will see its '
        'progress and correspondence in your private Advisory account.</p>'
        '</div></div>'
    )
    if current:
        st.html(
            '<div class="rl-workspace rq-workspace"><div class="note">'
            '<strong>One open advisory request at a time</strong>'
            'Your existing request remains active. Continue the discussion there. '
            'Requests for access to individual self-service advisors can be '
            'submitted on their own service pages.</div></div>'
        )
        _request_case(current, title="Existing open request")
        a, b = st.columns(2, gap="medium")
        with a:
            if st.button("Review my open request", type="primary",
                         key="rq_new_current", use_container_width=True):
                _go_request_section("current")
        with b:
            if st.button("Continue the conversation", key="rq_new_messages",
                         use_container_width=True):
                navigate("messages", str(current["id"]))
    else:
        _request_form(token, uid, profile)


def _conversation_changed() -> None:
    selected = st.session_state.get("advisory_member_conversation")
    if selected:
        st.query_params["request"] = str(selected)



def render_messages(session: dict, user: dict) -> None:
    """Focused conversation workspace using the Rollout Advisor design language."""
    from page_advisory_conversation_workspace import render_conversation_workspace
    render_conversation_workspace(session, user)
