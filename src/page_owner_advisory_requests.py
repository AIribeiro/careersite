"""Owner-facing Advisory action inbox for client requests.

Only the verified owner token is passed here by the private Analytics workspace.
The request RPC independently checks owner identity before any write.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import streamlit as st

from site_cms import _request_json, _rest_url
from page_advisory_client_journey import STATUS, CLOSED

ACTIONS = {
    "review": "Mark under review",
    "ask_client": "Ask the client a question",
    "invite_discovery": "Propose a discovery conversation",
    "proposal": "Present proposed scope",
    "start": "Start agreed engagement",
    "complete": "Mark work completed",
    "close": "Close request",
    "decline": "Decline request",
    "reply": "Send an update (keep stage)",
    "plan": "Set next step and follow-up",
}
ACTIONS_FOR_STATUS = {
    "submitted": ("review","ask_client","invite_discovery","decline","reply","plan"),
    "reviewing": ("ask_client","invite_discovery","proposal","decline","close","reply","plan"),
    "awaiting_client": ("reply","invite_discovery","decline","close","plan"),
    "discovery": ("ask_client","proposal","start","decline","close","reply","plan"),
    "proposal": ("ask_client","start","decline","close","reply","plan"),
    "active": ("reply","complete","plan"),
    "completed": ("close","reply","plan"),
    "closed": ("reply","plan"),
    "declined": ("reply","plan"),
}


def _read_owner_requests(token: str) -> list[dict]:
    rows = _request_json(
        "GET",_rest_url("portfolio_advisory_requests?select=*&order=updated_at.desc&limit=500"),
        token=token,timeout=15,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Cannot load Advisory action queue")
    return rows


def read_request_history(token: str) -> list[dict]:
    rows=_request_json(
        "GET",_rest_url("portfolio_advisory_request_audit?select=*"
                        "&order=created_at.desc&limit=500"),
        token=token,timeout=15,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Cannot load Advisory request audit")
    return rows


def _read_thread(token: str,rid: str) -> list[dict]:
    rows = _request_json(
        "GET",_rest_url("portfolio_advisory_messages?select=*&request_id=eq."
                         +rid+"&order=created_at.desc,id.desc&limit=200"),
        token=token,timeout=15,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Cannot load Advisory conversation")
    return list(reversed(rows))


def _send_owner_action(token: str,rid: str,action: str,
                       message: str | None = None,
                       next_step: str | None = None,
                       follow_up: str | None = None) -> dict:
    if action not in ACTIONS:
        raise ValueError("Unsupported Advisory action")
    result = _request_json(
        "POST",_rest_url("rpc/portfolio_advisory_request_owner_action_v1"),
        token=token,timeout=15,
        payload={
            "p_request_id":rid,"p_action":action,
            "p_message":message,"p_next_step":next_step,
            "p_follow_up":follow_up,
        },
    )
    if not isinstance(result,dict) or result.get("id")!=rid:
        raise RuntimeError("The action was not confirmed")
    return result


def _client_waiting(req: dict) -> bool:
    if req.get("status") in CLOSED or req.get("status")=="awaiting_client":
        return False
    last_client=str(req.get("last_client_at") or "")
    last_owner=str(req.get("last_owner_at") or "")
    return bool(last_client) and (not last_owner or last_client>last_owner)


def _overdue(req: dict) -> bool:
    follow=str(req.get("follow_up_on") or "")
    local_today = datetime.now(ZoneInfo("Europe/Stockholm")).date()
    return bool(follow and follow[:10] <= local_today.isoformat()
                and req.get("status") not in CLOSED)


def _priority(req: dict) -> tuple:
    return (not _client_waiting(req),not _overdue(req),
            str(req.get("created_at") or ""))


def _request_owner_detail(token: str, req: dict, people: dict) -> None:
    """Render one workspace section; no stacked correspondence/approval forms."""
    from page_owner_advisory_conversation_ui import render_owner_conversation
    render_owner_conversation(token, req, people.get(str(req.get("user_id")), {}))


def render_advisory_action_inbox(token: str, people_list: list[dict],
                                 requests: list[dict] | None = None) -> None:
    """A compact action queue with the conversation kept in one selected case."""
    st.markdown("### Client conversations")
    st.caption("Prioritize responses, open a client thread and handle stage or access changes separately.")
    if requests is None:
        try:
            requests = _read_owner_requests(token)
        except (RuntimeError, TimeoutError, KeyError):
            st.error("The client conversation inbox could not be retrieved.")
            return
    waiting = [r for r in requests if _client_waiting(r)]
    overdue = [r for r in requests if _overdue(r)]
    awaiting = [r for r in requests if r.get("status") == "awaiting_client"]
    active = [r for r in requests if r.get("status") == "active"]
    a,b,c,d = st.columns(4)
    a.metric("Needs your reply", len(waiting))
    b.metric("Follow-ups due", len(overdue))
    c.metric("Awaiting client", len(awaiting))
    d.metric("Active engagements", len(active))
    if not requests:
        st.info("No Advisory requests yet. New client requests will appear here.")
        return

    people = {str(p["user_id"]): p for p in people_list}
    queues = {
        "needs_reply": ("Needs my reply", waiting),
        "follow_up": ("Follow-ups", overdue),
        "awaiting_client": ("Awaiting client", awaiting),
        "all": ("All conversations", sorted(requests, key=_priority)),
    }
    filter_key = "advisory_owner_inbox_filter"
    if st.session_state.get(filter_key) not in queues:
        st.session_state[filter_key] = "needs_reply" if waiting else "all"
    filter_id = st.pills(
        "Inbox filter", list(queues),
        format_func=lambda key: queues[key][0],
        selection_mode="single", required=True, key=filter_key,
        label_visibility="collapsed", width="stretch", wrap=False,
    )
    filtered = queues[filter_id][1]
    if not filtered:
        st.info("Nothing in this queue. Choose All conversations to review the full request history.")
        return

    ordered = sorted(filtered, key=_priority)
    ids = [str(r["id"]) for r in ordered]
    selected_key = "owner_advisory_request_id"
    if st.session_state.get(selected_key) not in ids:
        st.session_state[selected_key] = ids[0]
    by_id = {str(r["id"]): r for r in ordered}

    def _option(rid: str) -> str:
        req = by_id[rid]
        person = people.get(str(req.get("user_id")), {})
        client = (str(person.get("first_name") or person.get("email") or "Client"))
        label = STATUS.get(str(req.get("status") or "submitted"), STATUS["submitted"])[0]
        name = str(req.get("title") or "Advisory request")
        urgent = "REPLY NEEDED · " if _client_waiting(req) else ""
        return urgent + client + " — " + name[:66] + " · " + label

    st.selectbox(
        "Open client conversation", ids, key=selected_key,
        format_func=_option, help="Switch between requests without modifying their status.",
    )
    selected = str(st.session_state[selected_key])
    if selected in by_id:
        _request_owner_detail(token, by_id[selected], people)

    with st.expander("View queue details"):
        st.dataframe([{
            "Priority": ("Respond" if _client_waiting(r) else
                         "Follow-up" if _overdue(r) else
                         "Awaiting client" if r.get("status") == "awaiting_client"
                         else "On track"),
            "Client": str(people.get(str(r.get("user_id")), {}).get("email") or "Client"),
            "Request": str(r.get("title") or ""),
            "Stage": STATUS.get(str(r.get("status") or "submitted"), STATUS["submitted"])[0],
            "Follow-up": str(r.get("follow_up_on") or "")[:10],
            "Last client activity": str(r.get("last_client_at") or "")[:16],
        } for r in ordered], hide_index=True, use_container_width=True)
