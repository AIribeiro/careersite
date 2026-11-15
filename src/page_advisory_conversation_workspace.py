"""Private executive correspondence workspace, styled after the Rollout Advisor.

Request ownership and authorization remain in the existing Supabase RLS-backed
request/message endpoints. This module changes presentation and navigation only.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from page_advisory_client_journey import (
    CLOSED, STATUS, _client_requests, _request_messages, _reply,
)
from site_assets import ADVISORY_EMAIL

SECTIONS = ("overview", "correspondence", "request", "history")
SECTION_LABELS = {
    "overview": "Conversation overview",
    "correspondence": "Messages & reply",
    "request": "Original request",
    "history": "All conversations",
}

# Action labels describe the *stored* request state. They do not claim that a
# message was read, a meeting was scheduled, or a service was approved.
STATE_GUIDANCE = {
    "submitted": "Your request has been received. No reply is required while it awaits review.",
    "reviewing": "Your request is under review. You can add context, but no response is required unless you are asked.",
    "awaiting_client": "Your response is requested. Read the correspondence and reply with the information needed.",
    "discovery": "Use the correspondence to clarify the decision, scope and what support would be useful.",
    "proposal": "Review the proposed scope and respond with questions or a decision. No engagement is agreed automatically.",
    "active": "Follow the agreed next steps in the messages. You can ask questions or provide updates here.",
    "completed": "Review the delivered outcome and raise any final questions before the conversation is closed.",
    "closed": "This conversation is closed and remains available for reference.",
    "declined": "This request will not proceed. Its correspondence remains available for reference.",
}

WORKSPACE_CSS = r"""
<style>
.cv-workspace{color:#182e43;max-width:1120px;margin:5px 0 22px}
.cv-workspace *{box-sizing:border-box}
.cv-workspace .eyebrow{display:block;font:800 10px/1.45 Arial,sans-serif;
 text-transform:uppercase;letter-spacing:.17em;color:#a36c46}
.cv-workspace .hero{background:linear-gradient(130deg,#0e2136,#253c51);
 padding:clamp(25px,4vw,43px);color:#fdfbf8;border-bottom:4px solid #b68060}
.cv-workspace .hero .eyebrow{color:#e6b18c}
.cv-workspace .hero h2{font:500 clamp(30px,3.7vw,44px)/1.13 Georgia,serif;
 letter-spacing:-.03em;color:#fff;margin:10px 0 12px;overflow-wrap:anywhere}
.cv-workspace .hero p{font-size:14px;line-height:1.7;color:#d8e0e7;
 max-width:740px;margin:0}
.cv-workspace .summarybar{display:flex;flex-wrap:wrap;gap:9px 23px;
 padding:14px 19px;background:#f8f4ec;border:1px solid #e0d7ca;border-top:0}
.cv-workspace .summarybar span{font:700 11px/1.55 Arial,sans-serif;
 color:#415367}
.cv-workspace .section-head{margin:24px 0 15px}
.cv-workspace .section-head h3{font:500 clamp(24px,2.8vw,33px)/1.2 Georgia,serif;
 letter-spacing:-.02em;color:#182d42;margin:6px 0 8px}
.cv-workspace .section-head p{max-width:780px;color:#5a6d7d;
 font-size:13px;line-height:1.65;margin:0}
.cv-workspace .decision{background:#fffdfa;border:1px solid #d9d5cd;
 border-left:5px solid #b07751;padding:clamp(20px,3vw,29px);margin:12px 0 15px}
.cv-workspace .decision h3{font:500 clamp(24px,2.9vw,33px)/1.18 Georgia,serif;
 color:#19314a;margin:8px 0 10px}
.cv-workspace .decision p{font-size:14px;color:#3a5266;
 line-height:1.72;max-width:820px;margin:0 0 12px}
.cv-workspace .decision p:last-child{margin-bottom:0}
.cv-workspace .nextstep{background:#f7f3ec;border:1px solid #e1d7c8;
 padding:18px 21px;margin:14px 0}
.cv-workspace .nextstep strong{display:block;color:#213b52;
 font-size:13px;margin:6px 0}
.cv-workspace .nextstep p{font-size:13px;line-height:1.68;
 color:#465b6e;margin:0;white-space:pre-wrap;overflow-wrap:anywhere}
.cv-workspace .three-col{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:12px;margin:16px 0 19px}
.cv-workspace .three-col article{background:#fffdfa;
 border:1px solid #ddd7cc;padding:20px;min-width:0}
.cv-workspace .three-col strong{display:block;font:500 19px/1.3 Georgia,serif;
 color:#193047;margin:8px 0}
.cv-workspace .three-col p{font:13px/1.65 Arial,sans-serif;
 color:#52677a;margin:0;overflow-wrap:anywhere}
.cv-workspace .message{max-width:93%;background:#fffdfa;border:1px solid #dcd7ce;
 border-left:4px solid #b6825f;padding:19px 22px;margin:13px auto 13px 0;
 box-shadow:0 3px 15px rgba(14,33,54,.025)}
.cv-workspace .message--client{margin-left:auto;margin-right:0;
 background:#f4f6f6;border-left-color:#8397a3}
.cv-workspace .message .meta{display:flex;flex-wrap:wrap;
 justify-content:space-between;gap:6px 15px;margin-bottom:12px}
.cv-workspace .message .meta strong{font-size:12px;color:#203b52}
.cv-workspace .message .meta time{font-size:11px;color:#66788b}
.cv-workspace .message .body{font:14px/1.75 Arial,sans-serif;
 white-space:pre-wrap;overflow-wrap:anywhere;color:#293f54}
.cv-workspace .empty{background:#fffdfa;border:1px solid #ddd7cc;
 padding:24px;color:#546879;font-size:13px;line-height:1.7}
.cv-workspace .detail{background:#fffdfa;border:1px solid #ded7cc;
 padding:22px 25px;margin:14px 0}
.cv-workspace .detail strong{display:block;font:800 11px/1.5 Arial,sans-serif;
 color:#9f6a46;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px}
.cv-workspace .detail p{font:14px/1.75 Arial,sans-serif;
 color:#294357;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}
.cv-workspace .footnote{color:#6c7b88;font-size:12px;
 line-height:1.6;margin:15px 0}
.st-key-native_advisory_content [data-testid="stPills"] button{white-space:nowrap}
@media(max-width:720px),(max-device-width:720px){
 .cv-workspace .three-col{grid-template-columns:1fr}
 .cv-workspace .three-col article{padding:16px}
 .cv-workspace .message,.cv-workspace .message--client{max-width:100%;padding:16px}
 .cv-workspace .summarybar{gap:7px 15px}
 .cv-workspace .detail{padding:18px}
 .cv-workspace .hero{padding:26px 20px}
}
</style>
"""


def _s(value: object, limit: int = 4000) -> str:
    return escape(str(value if value is not None else "")[:limit], quote=True)


def _day(value: object) -> str:
    raw = str(value or "")[:10]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return raw or "Not available"


def _moment(value: object) -> str:
    raw = str(value or "")
    return (_day(raw) + (" · " + raw[11:16] if len(raw) >= 16 else ""))


def _go(section: str) -> None:
    if section in SECTIONS:
        st.query_params["conversation_section"] = section
        st.rerun()


def _tab_changed() -> None:
    current = st.session_state.get("advisory_conversation_section")
    if current in SECTIONS:
        st.query_params["conversation_section"] = current


def _open_request(rid: str) -> None:
    """Switch selected request without losing the authenticated Streamlit session."""
    st.query_params["request"] = rid
    st.query_params["conversation_section"] = "overview"
    st.rerun()


def _navigation() -> str:
    current = str(st.query_params.get("conversation_section") or "overview").lower()
    if current not in SECTIONS:
        current = "overview"
    if st.session_state.get("advisory_conversation_section") != current:
        st.session_state["advisory_conversation_section"] = current
    st.pills(
        "Conversation sections", SECTIONS,
        format_func=lambda section: SECTION_LABELS[section],
        selection_mode="single", required=True,
        key="advisory_conversation_section",
        on_change=_tab_changed, label_visibility="collapsed",
        wrap=False, width="stretch",
    )
    return current


def _header(req: dict, message_count: int) -> None:
    state = str(req.get("status") or "submitted")
    status, _ = STATUS.get(state, STATUS["submitted"])
    st.html(
        WORKSPACE_CSS +
        '<div class="cv-workspace"><div class="hero">'
        '<span class="eyebrow">Private executive advisory · Selected conversation</span>'
        '<h2>' + _s(req.get("title") or "Advisory request", 160) + '</h2>'
        '<p>One place to follow your request, review the correspondence '
        'and see what happens next.</p></div>'
        '<div class="summarybar">'
        '<span>STATUS · ' + _s(status) + '</span>'
        '<span>SUBMITTED · ' + _s(_day(req.get("created_at"))) + '</span>'
        '<span>MESSAGES · ' + str(message_count) + '</span>'
        '</div></div>'
    )


def _section(title: str, headline: str, description: str) -> None:
    st.html(
        '<div class="cv-workspace"><div class="section-head">'
        '<span class="eyebrow">' + _s(title) + '</span>'
        '<h3>' + _s(headline) + '</h3>'
        '<p>' + _s(description) + '</p></div></div>'
    )


def _overview(req: dict, messages: list[dict]) -> None:
    state = str(req.get("status") or "submitted")
    title, _ = STATUS.get(state, STATUS["submitted"])
    guidance = STATE_GUIDANCE.get(state, STATE_GUIDANCE["submitted"])
    _section("Current position", "Where this request stands",
             "See the confirmed status and the next useful action before reviewing the full discussion.")
    st.html(
        '<div class="cv-workspace"><div class="decision">'
        '<span class="eyebrow">Current request status</span>'
        '<h3>' + _s(title) + '</h3><p>' + _s(guidance) + '</p>'
        '</div></div>'
    )
    next_step = str(req.get("next_step") or "").strip()
    if next_step:
        st.html(
            '<div class="cv-workspace"><div class="nextstep">'
            '<span class="eyebrow">Next step recorded for this request</span>'
            '<strong>From your advisory record</strong><p>' +
            _s(next_step, 1800) + '</p></div></div>'
        )
    last = messages[-1] if messages else None
    last_sender = ("Jair Ribeiro · Advisory" if last and last.get("sender") == "advisor"
                   else "You" if last else "No messages yet")
    last_moment = _moment(last.get("created_at")) if last else "Awaiting first message"
    timing = str(req.get("decision_timing") or "Not specified")
    st.html(
        '<div class="cv-workspace"><div class="three-col">'
        '<article><span class="eyebrow">01 · Decision context</span>'
        '<strong>What this is about</strong><p>' +
        _s(req.get("desired_outcome") or req.get("title") or "See original request", 260) +
        '</p></article>'
        '<article><span class="eyebrow">02 · Activity</span>'
        '<strong>' + _s(last_sender) + '</strong><p>Last message: ' +
        _s(last_moment) + '</p></article>'
        '<article><span class="eyebrow">03 · Decision timing</span>'
        '<strong>' + _s(timing) + '</strong>'
        '<p>Your stated decision horizon, not a promised response date.</p></article>'
        '</div></div>'
    )
    if last:
        preview = str(last.get("body") or "").strip()
        st.html(
            '<div class="cv-workspace"><div class="nextstep">'
            '<span class="eyebrow">Latest message · ' + _s(last_sender) + '</span>'
            '<p>' + _s(preview[:360] + ("…" if len(preview) > 360 else "")) +
            '</p></div></div>'
        )
    a, b = st.columns(2)
    with a:
        label = ("Read and respond" if state == "awaiting_client"
                 else "Open correspondence")
        if st.button(label, key="cv_open_messages", type="primary",
                     use_container_width=True):
            _go("correspondence")
    with b:
        if st.button("Review original request", key="cv_open_request",
                     use_container_width=True):
            _go("request")
    st.caption("Replies are kept within this request. Service approvals and "
               "engagement agreements are handled separately.")


def _correspondence(token: str, uid: str, req: dict, messages: list[dict]) -> None:
    _section("Private correspondence", "Messages and responses",
             "A chronological record of your advisory discussion. Your reply is stored with this request.")
    if not messages:
        st.html('<div class="cv-workspace"><div class="empty">'
                'No messages yet. When the discussion begins, messages will appear here.'
                '</div></div>')
    else:
        cards = []
        for msg in messages:
            advisor = msg.get("sender") == "advisor"
            label = "Jair Ribeiro · Advisory" if advisor else "You"
            klass = "message" if advisor else "message message--client"
            cards.append(
                '<article class="' + klass + '">'
                '<div class="meta"><strong>' + _s(label) + '</strong>'
                '<time>' + _s(_moment(msg.get("created_at"))) + '</time></div>'
                '<div class="body">' + _s(msg.get("body")) + '</div>'
                '</article>'
            )
        st.html('<div class="cv-workspace">' + "".join(cards) + '</div>')
    rid = str(req["id"])
    state = str(req.get("status") or "submitted")
    if state not in CLOSED:
        _section("Your response", "Reply to this request",
                 "Add a question, answer or relevant update. Avoid personal or confidential client data.")
        with st.form("advisory_client_reply_" + rid, clear_on_submit=True):
            response = st.text_area(
                "Your message", max_chars=4000, height=145,
                placeholder="Write your reply or the additional context needed to move the discussion forward.",
                help="Do not submit credentials, confidential documents or sensitive personal information.",
            )
            sent = st.form_submit_button(
                "Send private response", type="primary", use_container_width=True,
            )
        if sent:
            try:
                _reply(token, uid, rid, response)
                st.success("Your response was saved to this advisory conversation.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except (RuntimeError, TimeoutError, KeyError):
                st.error("Your response could not be saved. Please retry.")
    else:
        st.info("This conversation is closed. Its messages remain available to read.")
    if state in ("active", "completed") and any(
        msg.get("sender") == "advisor" for msg in messages
    ):
        from page_advisory_service_feedback import (
            ADVISORY_SERVICE, render_optional_feedback,
        )
        render_optional_feedback(
            token, uid, ADVISORY_SERVICE, "personal_advisory", request_id=rid,
        )


def _request_details(req: dict) -> None:
    _section("Original request", "What you submitted",
             "The initial decision question, outcome and context, preserved separately from later messages.")
    fields = (
        ("Decision or desired outcome", req.get("desired_outcome") or "Not provided"),
        ("Business context", req.get("business_context") or "No additional context provided"),
        ("Decision timing", req.get("decision_timing") or "Not specified"),
        ("Preferred first contact", req.get("contact_preference") or "Not specified"),
    )
    st.html(
        '<div class="cv-workspace">' +
        "".join(
            '<section class="detail"><strong>' + _s(label) + '</strong>'
            '<p>' + _s(value, 3200) + '</p></section>'
            for label, value in fields
        ) +
        '<p class="footnote">Submitted ' + _s(_day(req.get("created_at"))) +
        '. This is the original submission; later changes and responses appear '
        'under Messages &amp; reply.</p></div>'
    )
    if st.button("Go to correspondence", type="primary", key="cv_request_messages"):
        _go("correspondence")


def _history(requests: list[dict], selected_id: str) -> None:
    _section("Conversation history", "All your advisory requests",
             "Reopen any past discussion, including completed and closed requests. "
             "Each conversation retains its own status, original request and messages.")
    for index, req in enumerate(requests):
        rid = str(req["id"])
        title, _ = STATUS.get(str(req.get("status") or "submitted"), STATUS["submitted"])
        selected_label = " · Currently selected" if rid == selected_id else ""
        st.html(
            '<div class="cv-workspace"><div class="detail">'
            '<span class="eyebrow">Request ' + str(index + 1) + selected_label + '</span>'
            '<h3 style="font:500 23px/1.3 Georgia,serif;color:#193047;margin:10px 0">'
            + _s(req.get("title") or "Advisory request", 180) + '</h3>'
            '<p><strong style="display:inline;font-size:12px;color:#9f6a46;'
            'letter-spacing:0;text-transform:none;margin:0">' + _s(title) +
            '</strong> · Submitted ' + _s(_day(req.get("created_at"))) +
            ' · ' + _s(req.get("decision_timing") or "Timing not specified") +
            '</p>'
            '<p style="margin-top:10px">' + _s(
                req.get("desired_outcome") or "Decision details in the original request", 260
            ) + '</p></div></div>'
        )
        if st.button("Open this conversation", key="cv_history_" + rid,
                     type="primary" if rid == selected_id else "secondary"):
            _open_request(rid)
    st.caption("Only requests connected to your verified Advisory account are shown.")


def render_conversation_workspace(session: dict, user: dict) -> None:
    """Render one selected case and one focused section, never a long all-in-one feed."""
    token, uid = str(session["access_token"]), str(user["id"])
    st.html(WORKSPACE_CSS)
    try:
        requests = _client_requests(token, uid)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("Your advisory conversations could not be retrieved. Please retry.")
        return
    if not requests:
        _section("Private correspondence", "Your conversations",
                 "Submitted advisory requests and their private replies will appear here.")
        st.info("No conversations yet. Submit an advisory request to get started.")
        if st.button("Create an advisory request", type="primary", key="cv_new_request"):
            from page_advisory_member_experience import navigate
            navigate("requests")
        return

    ids = [str(r["id"]) for r in requests]
    query_id = str(st.query_params.get("request") or "")
    selected_id = query_id if query_id in ids else ids[0]
    target = next(r for r in requests if str(r["id"]) == selected_id)
    try:
        messages = _request_messages(token, uid, selected_id)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("The selected conversation could not be loaded. Please retry.")
        return
    _header(target, len(messages))
    section = _navigation()
    if section == "overview":
        _overview(target, messages)
    elif section == "correspondence":
        _correspondence(token, uid, target, messages)
    elif section == "request":
        _request_details(target)
    else:
        _history(requests, selected_id)
    st.caption("Private advisory correspondence · Support: " + ADVISORY_EMAIL)
