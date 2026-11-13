"""Owner-facing Advisory action inbox for client requests.

Only the verified owner token is passed here by the private Analytics workspace.
The request RPC independently checks owner identity before any write.
"""
from __future__ import annotations

from datetime import date
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
    "plan": "Update next step and follow-up",
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


def _read_thread(token: str,rid: str) -> list[dict]:
    rows = _request_json(
        "GET",_rest_url("portfolio_advisory_messages?select=*&request_id=eq."
                         +rid+"&order=created_at.asc,id.asc&limit=250"),
        token=token,timeout=15,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Cannot load Advisory conversation")
    return rows


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
    return bool(follow and follow[:10]<=date.today().isoformat()
                and req.get("status") not in CLOSED)


def _priority(req: dict) -> tuple:
    return (not _client_waiting(req),not _overdue(req),
            str(req.get("created_at") or ""))


def _request_owner_detail(token: str,req: dict,people: dict) -> None:
    rid=str(req["id"])
    stage=str(req.get("status") or "submitted")
    label,desc=STATUS.get(stage,STATUS["submitted"])
    person=people.get(str(req.get("user_id")), {})
    st.markdown("### "+str(req.get("title") or "Executive advisory request"))
    st.caption(str(person.get("email") or "Unknown account")
               +" · "+label+" · Submitted "+str(req.get("created_at") or "")[:10])
    st.write("**Decision/outcome:** "+str(req.get("desired_outcome") or ""))
    if req.get("business_context"):
        st.write("**Context:** "+str(req.get("business_context")))
    st.write("**Timing:** "+str(req.get("decision_timing") or "")+
             " · **Preferred contact:** "+str(req.get("contact_preference") or "Email"))
    if _client_waiting(req):
        st.warning("Action required: the client has submitted information not yet answered.")
    elif stage=="awaiting_client":
        st.info("Waiting for the client to answer your question.")
    if _overdue(req):
        st.warning("Follow-up date reached. Review the next step.")
    if req.get("next_step"):
        st.markdown("**Client sees as next step:**")
        st.write(str(req["next_step"]))

    st.markdown("#### Conversation history")
    try:
        messages=_read_thread(token,rid)
    except (RuntimeError,TimeoutError,KeyError):
        st.error("Could not load the message history.")
        messages=[]
    if not messages:
        st.caption("No messages yet. Your first response establishes the advisory conversation.")
    for msg in messages:
        with st.chat_message("assistant" if msg.get("sender")=="advisor" else "user"):
            st.caption("You · Advisor" if msg.get("sender")=="advisor" else
                       str(person.get("first_name") or "Client") + " · Client")
            st.write(str(msg.get("body") or ""))
            st.caption(str(msg.get("created_at") or "")[:16].replace("T"," "))

    st.markdown("#### Take the next step")
    choices=ACTIONS_FOR_STATUS.get(stage,("reply","plan"))
    with st.form("advisory_owner_request_action_"+rid):
        action=st.selectbox(
            "Your action",choices,format_func=lambda x:ACTIONS[x],
        )
        st.caption("Changing the stage is a deliberate decision. A submitted request is not a booking, contract or paid client.")
        message=st.text_area(
            "Message visible to client",
            max_chars=4000,height=120,
            placeholder="Explain the decision, question, proposed conversation or outcome.",
        )
        next_step=st.text_input(
            "Clear next step visible to client (optional)",
            value=str(req.get("next_step") or ""),
            max_chars=1000,
        )
        day=st.date_input("Your follow-up date (for planning)",
                          value=date.fromisoformat(str(req["follow_up_on"])[:10])
                          if req.get("follow_up_on") else None,format="YYYY-MM-DD")
        confirmed=False
        if action=="start":
            confirmed=st.checkbox(
                "I have separately agreed the advisory scope, terms and permission to begin with the client."
            )
        submitted=st.form_submit_button("Save and update the client",type="primary")
    if submitted:
        if action=="start" and not confirmed:
            st.error("Confirm that the engagement has been agreed before marking it active.")
        elif action in ("ask_client","invite_discovery","proposal","start","complete","decline") and len(message.strip())<10:
            st.error("A meaningful client-facing message is required for this step.")
        elif action=="reply" and len(message.strip())<2:
            st.error("Write a message before sending an update.")
        else:
            try:
                _send_owner_action(
                    token,rid,action,
                    message=message.strip() if message.strip() else None,
                    next_step=next_step.strip() if next_step.strip() else None,
                    follow_up=day.isoformat() if day else None,
                )
                st.success("Saved and added to the private client journey.")
                st.rerun()
            except (RuntimeError,TimeoutError,ValueError,KeyError):
                st.error("The action was not saved. Review the stage and retry.")

    st.caption(
        "This is an in-portal response. The client can see the update after opening "
        "their Advisory account. A separate email or meeting invitation must be sent "
        "through your usual channel when required."
    )


def render_advisory_action_inbox(token: str,people_list: list[dict]) -> None:
    st.markdown("### Client requests & next actions")
    st.caption(
        "An active account is not an engagement. When a client submits an actual "
        "business question, it appears here for review and follow-up."
    )
    try:
        requests=_read_owner_requests(token)
    except (RuntimeError,TimeoutError,KeyError):
        st.error("Unable to load the Advisory request inbox.")
        return
    waiting=[x for x in requests if _client_waiting(x)]
    overdue=[x for x in requests if _overdue(x)]
    awaiting=[x for x in requests if x.get("status")=="awaiting_client"]
    active=[x for x in requests if x.get("status")=="active"]
    a,b,c,d=st.columns(4)
    a.metric("Needs your response",len(waiting))
    b.metric("Follow-ups due",len(overdue))
    c.metric("Awaiting client",len(awaiting))
    d.metric("Active engagements",len(active))
    if not requests:
        st.info(
            "No formal Advisory requests yet. A completed registration confirms "
            "account access, but does not automatically open a client engagement. "
            "New clients are now invited to submit their first business request."
        )
        return
    people={str(x["user_id"]):x for x in people_list}
    ordered=sorted(requests,key=_priority)
    st.dataframe([{
        "Priority":"Respond" if _client_waiting(r) else
                   "Follow-up" if _overdue(r) else
                   "Await client" if r.get("status")=="awaiting_client" else "On track",
        "Client":str(people.get(str(r.get("user_id")),{}).get("email") or "Unknown"),
        "Decision":str(r.get("title") or ""),
        "Stage":STATUS.get(str(r.get("status")),STATUS["submitted"])[0],
        "Follow-up":str(r.get("follow_up_on") or ""),
        "Last client activity":str(r.get("last_client_at") or "")[:16],
    } for r in ordered],hide_index=True,use_container_width=True)
    selected=st.selectbox(
        "Open a request to act on",
        [str(x["id"]) for x in ordered],
        format_func=lambda rid: next(
            (str(people.get(str(x.get("user_id")),{}).get("email") or "Client")
             +" — "+str(x.get("title") or "Request")
             for x in ordered if str(x["id"])==rid),rid
        ),
        key="owner_advisory_request_id",
    )
    req=next((r for r in ordered if str(r["id"])==selected),None)
    if req:
        _request_owner_detail(token,req,people)
