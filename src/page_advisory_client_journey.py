"""Client-facing Advisory service journey: registered account to a specific request.

Authentication and service entitlement are handled by the parent account page.
Every request and reply is stored in Supabase with independent RLS.
"""
from __future__ import annotations

from html import escape
from urllib.parse import quote
import streamlit as st

from site_cms import _request_json, _rest_url

STATUS = {
    "submitted": ("Request received", "Your request is recorded. Jair can now review it and respond in this space."),
    "reviewing": ("Under review", "Your request is being considered. Watch this space for the next question or proposal."),
    "awaiting_client": ("Your input is needed", "Please read the latest message and reply so the conversation can continue."),
    "discovery": ("Discovery discussion", "Clarify the decision, context and a useful way of working."),
    "proposal": ("Scope under discussion", "Review the proposed approach and respond before any commercial commitment."),
    "active": ("Engagement underway", "The agreed advisory work is in progress. Follow the messages and next steps."),
    "completed": ("Outcome delivered — review & handover", "Review the outcome, raise final questions and reply before the request is closed."),
    "closed": ("Conversation closed", "This request is closed. You can begin another discussion when needed."),
    "declined": ("Unable to proceed", "This request is closed without an engagement. You may start another request."),
}
CLOSED = {"closed", "declined"}


def _client_requests(token: str, uid: str) -> list[dict]:
    result = _request_json(
        "GET",
        _rest_url("portfolio_advisory_requests?select=*&user_id=eq."
                  + quote(uid, safe="") + "&order=created_at.desc&limit=50"),
        token=token, timeout=12,
    )
    if not isinstance(result, list):
        raise RuntimeError("Unexpected Advisory request response")
    return result


def _request_messages(token: str, uid: str, rid: str) -> list[dict]:
    result = _request_json(
        "GET", _rest_url("portfolio_advisory_messages?select=sender,body,created_at,id"
                         "&user_id=eq." + quote(uid,safe="") +
                         "&request_id=eq." + quote(rid,safe="") +
                         "&order=created_at.asc,id.asc&limit=100"),
        token=token, timeout=12,
    )
    if not isinstance(result, list):
        raise RuntimeError("Unexpected Advisory conversation response")
    return result


def _create_request(token: str, uid: str, fields: dict) -> None:
    title = str(fields.get("title") or "").strip()
    outcome = str(fields.get("desired_outcome") or "").strip()
    context = str(fields.get("business_context") or "").strip()
    if len(title)<8 or len(outcome)<20:
        raise ValueError("Please provide a short decision title and the outcome you want to achieve.")
    if len(context)>3000:
        raise ValueError("Please shorten the business context.")
    payload = {
        "user_id":uid,
        "title":title,"desired_outcome":outcome,"business_context":context,
        "decision_timing":fields["decision_timing"],
        "contact_preference":fields["contact_preference"],
    }
    returned = _request_json(
        "POST", _rest_url("portfolio_advisory_requests"),
        token=token,payload=payload,prefer="return=representation",timeout=15,
    )
    if not isinstance(returned,list) or not returned:
        raise RuntimeError("The request was not confirmed by the server.")


def _reply(token: str, uid: str, rid: str, body: str) -> None:
    message = str(body or "").strip()
    if len(message)<2 or len(message)>4000:
        raise ValueError("Write a message between 2 and 4,000 characters.")
    rows=_request_json(
        "POST",_rest_url("portfolio_advisory_messages"),
        token=token,payload={
            "request_id":rid,"user_id":uid,"sender":"client","body":message,
        },
        prefer="return=representation",timeout=15,
    )
    if not isinstance(rows,list) or not rows:
        raise RuntimeError("The reply was not confirmed by the server.")


def _display_conversation(token: str, uid: str, req: dict) -> None:
    rid=str(req["id"])
    state=str(req.get("status") or "submitted")
    title,desc=STATUS.get(state,STATUS["submitted"])
    st.markdown("### " + str(req.get("title") or "Your advisory request"))
    st.caption("Submitted " + str(req.get("created_at") or "")[:10] +
               " · " + str(req.get("decision_timing") or ""))
    st.info("**" + title + "** — " + desc)
    if req.get("next_step"):
        st.markdown("**Your next step**")
        st.write(str(req["next_step"]))
    elif state=="submitted":
        st.write("Your request is under review. No advisory discussion has been confirmed yet.")

    with st.expander("The request you submitted"):
        st.write("**Decision or business outcome:**")
        st.write(str(req.get("desired_outcome") or ""))
        if req.get("business_context"):
            st.write("**Background:**")
            st.write(str(req["business_context"]))
        st.caption("Preferred contact: " + str(req.get("contact_preference") or "Email"))
    st.markdown("#### Your conversation")
    messages=_request_messages(token,uid,rid)
    if not messages:
        st.caption("No messages yet. Responses from Jair will appear here.")
    for msg in messages:
        with st.chat_message("assistant" if msg.get("sender")=="advisor" else "user"):
            st.caption("Jair Ribeiro · Advisory" if msg.get("sender")=="advisor" else "You")
            st.write(str(msg.get("body") or ""))
            st.caption(str(msg.get("created_at") or "")[:16].replace("T"," "))
    if state not in CLOSED:
        with st.form("advisory_client_reply_"+rid,clear_on_submit=True):
            response=st.text_area(
                "Reply to Jair or provide more context",
                max_chars=4000,height=120,
                placeholder="Answer the question or share what would help move this forward.",
                help="Keep sensitive client data and confidential material out of this form.",
            )
            sent=st.form_submit_button("Send my response",type="primary")
        if sent:
            try:
                _reply(token,uid,rid,response)
                st.success("Your response was delivered to the private Advisory workspace.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except (RuntimeError,TimeoutError,KeyError):
                st.error("Your response could not be saved. Please try again.")
    else:
        st.caption("This discussion is closed. Start a new request for a new decision.")


def _request_form(token: str,uid: str,profile: dict) -> None:
    st.html("""<section class="advisory-portal-intro">
<p style="color:#a5643f;font-size:11px;letter-spacing:.14em;font-weight:800">YOUR FIRST STEP</p>
<h2>What decision do you need help with?</h2>
<p>Describe the business question and the outcome you need. Requests are
reviewed individually for relevance and availability. Selected discussions
are pro-bono and focused on a defined decision.</p>
</section>""")
    st.html("""<div class="advisory-process-guide">
<div style="font-size:11px;font-weight:800;letter-spacing:.14em;color:#a5643f;margin-bottom:14px">WHAT HAPPENS NEXT</div>
<div class="advisory-process-steps">
<div><strong>01 · Your question</strong><span>Tell me the decision and desired outcome.</span></div>
<div><strong>02 · My assessment</strong><span>I review it and respond in this private space.</span></div>
<div><strong>03 · If selected</strong><span>Agree the question and scope of a free discussion.</span></div>
<div><strong>04 · Delivery &amp; close</strong><span>If engaged, we track the agreed work and its conclusion.</span></div>
</div></div>""")
    with st.form("advisory_client_new_request",clear_on_submit=False):
        title=st.text_input(
            "The decision or challenge *",max_chars=160,
            placeholder="e.g. Which AI initiatives should we invest in next?",
        )
        outcome=st.text_area(
            "What do you need to decide or achieve? *",height=126,max_chars=2000,
            placeholder="Describe the outcome, why it matters, and what is blocking the decision.",
        )
        context=st.text_area(
            "Relevant context (optional)",height=105,max_chars=3000,
            placeholder="Business situation, existing work, stakeholders or constraints.",
            help="No confidential documents, personal data or credentials.",
        )
        a,b=st.columns(2)
        with a:
            horizon=st.selectbox(
                "Decision timing",["Exploratory","Within 30 days","1–3 months","3–6 months"],
                index=0,
            )
        with b:
            contact=st.selectbox("Preferred first contact",["Email","Video call"])
        acknowledged=st.checkbox(
            "I understand this free request is assessed individually and does not guarantee a pro-bono discussion."
        )
        submit=st.form_submit_button("Send my advisory request",type="primary",
                                     use_container_width=True)
    if submit:
        if not acknowledged:
            st.error("Please acknowledge the nature of the initial request.")
        else:
            try:
                _create_request(token,uid,{
                    "title":title,"desired_outcome":outcome,
                    "business_context":context,"decision_timing":horizon,
                    "contact_preference":contact,
                })
                st.success("Request received. Your private advisory conversation is now open.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except (RuntimeError,TimeoutError,KeyError):
                st.error("Your request could not be submitted. Check whether another request is already open.")


def render_advisory_client_journey(session: dict,user: dict,profile: dict) -> None:
    token=str(session["access_token"])
    uid=str(user["id"])
    name=str(profile.get("first_name") or "there")
    st.markdown("## Welcome, " + name + ".")
    st.html("""<div class="advisory-portal-badge">
<strong>Your Advisory account is active.</strong> You can now describe a
specific business decision for individual review. Pro-bono discussions are
selective, not automatically booked. Your free Reader Library remains available.
</div>""")
    try:
        requests=_client_requests(token,uid)
    except (RuntimeError,TimeoutError,KeyError):
        st.error("We could not retrieve your advisory conversations. Please try again.")
        return
    current=next((x for x in requests if str(x.get("status")) not in CLOSED),None)
    if current is None:
        _request_form(token,uid,profile)
    else:
        _display_conversation(token,uid,current)
    if requests and current is None:
        st.divider()
        st.caption("Previous requests are available below.")
    prior=[x for x in requests if current is None or x["id"]!=current["id"]]
    if prior:
        with st.expander("Previous advisory requests"):
            chosen=st.selectbox(
                "Review a previous discussion",
                [str(x["id"]) for x in prior],
                format_func=lambda rid: next((str(x.get("title")) for x in prior
                                              if str(x["id"])==rid),rid),
                key="advisory_prior_request",
            )
            target=next((x for x in prior if str(x["id"])==chosen),None)
            if target:
                _display_conversation(token,uid,target)
    st.divider()
    a,b=st.columns([1,2])
    with a:
        if st.button("Open my Premium Reader library",use_container_width=True):
            st.query_params.clear()
            st.query_params["page"]="readers"
            st.rerun()
    with b:
        st.caption("Every request is reviewed individually. Selected discussions are pro-bono "
                   "and free of charge; scope and timing depend on availability.")
