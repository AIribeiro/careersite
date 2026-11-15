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
    # Retrieve actual entitlements, not inferred approvals from account status.
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
            st.caption(scorecard_status)
            if st.button("Open Scorecard workspace", key="overview_scorecard",
                         use_container_width=True):
                navigate("scorecard")
    with c:
        with st.container(border=True):
            st.caption("03 · AI ADOPTION & SCALE")
            st.markdown("#### Rollout Readiness Advisor")
            st.write("Assess rollout conditions and receive an executive decision brief.")
            st.caption(rollout_status + " · Single-session service")
            if st.button("Open Rollout Advisor", key="overview_rollout",
                         use_container_width=True):
                navigate("rollout")

    st.divider()
    with st.container(border=True):
        st.caption("04 · SINGLE AI OPPORTUNITY")
        st.markdown("#### AI Investment Decision Advisor")
        st.write("Should you invest, experiment, hold or stop? Assess one opportunity and receive a concise executive decision brief.")
        st.caption("Free self-service · Available to verified Advisory accounts · No separate approval")
        if st.button("Open Investment Decision Advisor", key="overview_investment",
                     use_container_width=True):
            navigate("decision")

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
