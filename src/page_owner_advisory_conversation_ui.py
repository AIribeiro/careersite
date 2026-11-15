"""Owner side of the Advisory two-way correspondence workspace.

A quick reply never changes the request stage. Management decisions use the
existing owner-only RPC; approvals remain in their existing service workflows.
"""
from __future__ import annotations

from datetime import date
from html import escape

import streamlit as st

from page_advisory_client_journey import STATUS, CLOSED
from page_advisory_thread_ui import (
    CSS as THREAD_CSS, render_thread, render_casebar, render_notice,
    pretty_date,
)

OWNER_CORRESPONDENCE_VERSION = "owner_dialogue_20261115"

OWNER_CSS = """
<style>
.owner-dialogue{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
 color:#192f44;margin:8px 0 22px}
.owner-dialogue *{box-sizing:border-box}
.owner-dialogue .hero{background:linear-gradient(130deg,#0e2136,#253c51);color:#fefbf8;
 padding:clamp(22px,3.2vw,38px);border-bottom:4px solid #b68060}
.owner-dialogue .eyebrow{font:800 10px/1.45 Arial,sans-serif;letter-spacing:.17em;
 text-transform:uppercase;color:#e6b18c}
.owner-dialogue h2{font:500 clamp(26px,3.2vw,40px)/1.16 Georgia,serif;
 color:#fff;letter-spacing:-.025em;margin:10px 0 12px;overflow-wrap:anywhere}
.owner-dialogue .hero p{font:13px/1.65 Arial,sans-serif;color:#d6dfe7;margin:0}
.owner-dialogue .section{margin:20px 0 12px}
.owner-dialogue .section h3{font:500 25px/1.2 Georgia,serif;color:#172e43;margin:7px 0}
.owner-dialogue .section p{font:13px/1.6 Arial,sans-serif;color:#536779;margin:0}
.owner-dialogue .detail{background:#fffdfa;border:1px solid #e1d9ce;
 padding:17px 20px;margin:9px 0;overflow-wrap:anywhere}
.owner-dialogue .detail strong{font:800 11px/1.5 Arial,sans-serif;color:#9c6443;
 text-transform:uppercase;letter-spacing:.09em}
.owner-dialogue .detail p{font:13px/1.75 Arial,sans-serif;color:#30465a;
 white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0 0}
@media(max-width:720px),(max-device-width:720px){
 .owner-dialogue .hero{padding:24px 19px}
}
</style>
"""


def _s(value: object, limit: int = 4000) -> str:
    return escape(str(value if value is not None else "")[:limit], quote=True)


def _section(kicker: str, title: str, summary: str = "") -> None:
    st.html(OWNER_CSS + '<section class="owner-dialogue"><div class="section">'
            '<span style="font-size:10px;font-weight:800;letter-spacing:.14em;'
            'text-transform:uppercase;color:#a36c46">' + _s(kicker) + '</span>'
            '<h3>' + _s(title) + '</h3>'
            + ('<p>' + _s(summary) + '</p>' if summary else '') +
            '</div></section>')


def _context(req: dict, person: dict) -> None:
    fields = [
        ("Business decision", req.get("desired_outcome") or "Not specified"),
        ("Context", req.get("business_context") or "No additional context was provided"),
        ("Decision timing", req.get("decision_timing") or "Not specified"),
        ("Preferred first contact", req.get("contact_preference") or "Not specified"),
    ]
    st.html(
        OWNER_CSS + '<div class="owner-dialogue">' +
        "".join('<div class="detail"><strong>' + _s(label) + '</strong><p>' +
                _s(value, 3200) + '</p></div>' for label, value in fields) +
        '</div>'
    )


@st.fragment(run_every="45s")
def _live_owner_thread(token: str, rid: str, client_name: str) -> None:
    """Only the thread refreshes, not management controls or unsent drafts."""
    from page_owner_advisory_requests import _read_thread
    try:
        current = _read_thread(token, rid)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.caption("The message feed is temporarily unavailable. Refresh the request to retry.")
        return
    with st.container(height=470, border=True, key="owner_advisory_thread"):
        render_thread(current, viewer="advisor", client_name=client_name, limit=200)


def _conversation(token: str, req: dict, person: dict, messages: list[dict]) -> None:
    from page_owner_advisory_requests import (
        _send_owner_action, _client_waiting, _overdue,
    )
    rid = str(req["id"])
    stage = str(req.get("status") or "submitted")
    client_name = str(person.get("first_name") or person.get("email") or "Client")
    if st.session_state.pop("owner_message_sent_" + rid, False):
        st.success("Reply saved to the client's private conversation.")
    if _client_waiting(req):
        render_notice("Client response waiting", "The client has written since your last reply. Review the latest message and respond.")
    elif stage == "awaiting_client":
        render_notice("Waiting for client", "Your question is with the client. You may send an update if needed.")
    elif _overdue(req):
        render_notice("Follow-up due", "Your follow-up date has been reached. Review the agreed next step.")
    if req.get("next_step"):
        render_notice("Client-facing next step", req["next_step"])

    left, right = st.columns([3, 1], vertical_alignment="bottom")
    with left:
        _section("Client dialogue", "Conversation", "Replies are saved to the same private thread the client sees.")
    with right:
        if st.button("Refresh thread", key="owner_thread_refresh_" + rid, use_container_width=True):
            st.rerun()
    _live_owner_thread(token, rid, client_name)
    st.caption("New messages are checked automatically while the owner workspace is open.")

    with st.expander("View the client's original request"):
        _context(req, person)

    draft_key = "owner_reply_draft_" + rid
    if st.session_state.pop("owner_reply_clear_" + rid, False):
        st.session_state[draft_key] = ""
    _section("Message composer", "Reply to " + client_name,
             "Send a message without changing the engagement stage, next step or access permissions.")
    with st.form("owner_quick_reply_" + rid, clear_on_submit=False):
        message = st.text_area(
            "Private reply", key=draft_key, height=124, max_chars=4000,
            placeholder="Write your response to the client…",
            help="This is an in-portal message, not an email or meeting invitation.",
        )
        sent = st.form_submit_button("Send reply", type="primary", use_container_width=True)
    if stage in CLOSED:
        st.caption("This request is closed. A reply can be sent as a final update, but the client cannot respond here.")
    else:
        st.caption("The client can see this reply in their Advisory account. Email alerts are not implied.")
    if sent:
        if len(message.strip()) < 2:
            st.error("Write a message before sending.")
        else:
            try:
                _send_owner_action(token, rid, "reply", message=message.strip())
                st.session_state["owner_reply_clear_" + rid] = True
                st.session_state["owner_message_sent_" + rid] = True
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.error("The reply was not saved. Your draft remains available for retry.")


def _management(token: str, req: dict, person: dict) -> None:
    from page_owner_advisory_requests import (
        ACTIONS, ACTIONS_FOR_STATUS, _send_owner_action, _overdue,
    )
    rid = str(req["id"])
    stage = str(req.get("status") or "submitted")
    _section("Engagement administration", "Request decisions and follow-up",
             "Status changes are separate from messages. Confirm the scope before starting an engagement.")
    _context(req, person)
    label, explanation = STATUS.get(stage, STATUS["submitted"])
    render_notice("Current stage · " + label, explanation)
    if req.get("next_step"):
        render_notice("Current next step", req["next_step"])
    if _overdue(req):
        st.warning("The follow-up date has been reached.")
    choices = tuple(x for x in ACTIONS_FOR_STATUS.get(stage, ("plan",)) if x != "reply")
    if not choices:
        st.info("No additional stage transitions are available for this request.")
        return
    action = st.selectbox(
        "Management action", choices, format_func=lambda x: ACTIONS[x],
        key="owner_stage_action_" + rid,
    )
    with st.form("owner_manage_request_" + rid, clear_on_submit=False):
        st.caption("A state change may update what the client sees. This is not a booking or contract.")
        msg = st.text_area(
            "Message to client (required for major decisions)",
            max_chars=4000, height=115,
            placeholder="Explain the decision or proposed next step.",
        )
        next_step = st.text_input(
            "Client-facing next step (optional)", max_chars=1000,
            placeholder=str(req.get("next_step") or "Leave blank to retain the suggested next step."),
        )
        follow = req.get("follow_up_on")
        try:
            initial_date = date.fromisoformat(str(follow)[:10]) if follow else None
        except ValueError:
            initial_date = None
        day = st.date_input("Follow-up date (private planning)",
                            value=initial_date, format="YYYY-MM-DD")
        confirmed = (
            st.checkbox("The client and I have agreed scope, terms and permission to begin.")
            if action == "start" else False
        )
        submit = st.form_submit_button("Confirm management action", type="primary",
                                       use_container_width=True)
    if submit:
        if action == "start" and not confirmed:
            st.error("Confirm the agreed scope and terms before starting the engagement.")
        elif action in ("ask_client","invite_discovery","proposal","start","complete","decline") and len(msg.strip()) < 10:
            st.error("A meaningful client-facing message is required for this decision.")
        else:
            try:
                _send_owner_action(
                    token, rid, action,
                    message=msg.strip() or None,
                    next_step=next_step.strip() or None,
                    follow_up=day.isoformat() if day else None,
                )
                st.success("The request decision was saved.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.error("This change was not saved. Review the action and retry.")


def _access(token: str, req: dict, messages: list[dict]) -> None:
    _section("Service permissions", "Approved services and access requests",
             "Access decisions are controlled separately from correspondence and the engagement stage.")
    from page_owner_advisory_operations import render_service_access_for_request
    render_service_access_for_request(token, req)
    from page_advisory_rollout import REQUEST_MARKER, REQUEST_TITLE
    rollout_requested = (
        str(req.get("title") or "").casefold() == REQUEST_TITLE.casefold()
        or any(m.get("sender") == "client" and
               REQUEST_MARKER in str(m.get("body") or "")
               for m in messages)
    )
    from page_owner_advisory_rollout import render_owner_rollout_access
    render_owner_rollout_access(token, req, rollout_requested)
    if str(req.get("title") or "").casefold() == "ai portfolio prioritization scorecard — access request" or any(
        m.get("sender") == "client" and
        "AI PORTFOLIO SCORECARD ACCESS REQUEST" in str(m.get("body") or "")
        for m in messages
    ):
        st.info("Scorecard access was requested. Review pro-bono eligibility and enable the relevant service separately.")


def render_owner_conversation(token: str, req: dict, person: dict) -> None:
    """One private case and one focused activity at a time."""
    from page_owner_advisory_requests import _read_thread
    rid = str(req["id"])
    stage = str(req.get("status") or "submitted")
    status, _ = STATUS.get(stage, STATUS["submitted"])
    try:
        messages = _read_thread(token, rid)
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        st.error("The conversation could not be retrieved. Replies are disabled until it loads.")
        return
    label = str(person.get("first_name") or person.get("email") or "Client")
    metadata = " · ".join(str(x) for x in (
        person.get("email") or "",
        person.get("organization") or "",
    ) if x)
    st.html(
        OWNER_CSS + THREAD_CSS +
        '<section class="owner-dialogue"><div class="hero">'
        '<span class="eyebrow">Executive advisory · Owner workspace</span>'
        '<h2>' + _s(req.get("title") or "Advisory request", 160) + '</h2>'
        '<p>' + _s(label) +
        (' · ' + _s(metadata, 240) if metadata else '') +
        '</p></div></section>'
    )
    from page_owner_advisory_requests import _client_waiting
    render_casebar(status, req.get("created_at"), len(messages),
                   needs_response=_client_waiting(req))
    sections = ("conversation", "management", "access")
    keys = {
        "conversation": "Conversation & reply",
        "management": "Manage request",
        "access": "Service access",
    }
    key = "owner_dialogue_section_" + rid
    if st.session_state.get(key) not in sections:
        st.session_state[key] = "conversation"
    section = st.pills(
        "Request workspace", sections, format_func=lambda v: keys[v],
        selection_mode="single", required=True,
        label_visibility="collapsed", key=key,
        width="stretch", wrap=False,
    )
    if section == "conversation":
        _conversation(token, req, person, messages)
    elif section == "management":
        _management(token, req, person)
    else:
        _access(token, req, messages)
