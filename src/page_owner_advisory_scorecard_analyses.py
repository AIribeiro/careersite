"""Private owner queue for additional AI Portfolio Scorecard analyses.

Approvals create an independent, empty, individually authorized workspace.
The original Scorecard and earlier analyses are never reset or duplicated.
"""
from __future__ import annotations

from urllib.parse import quote
import streamlit as st
from site_cms import _request_json, _rest_url
from advisory_approval_email import deliver_approval_notice, approval_notice_message


def read_owner_analysis_requests(token: str) -> list[dict]:
    result = _request_json(
        "GET", _rest_url(
            "portfolio_advisory_scorecard_analysis_requests?"
            "select=id,user_id,anchor_scorecard_id,request_id,title,"
            "decision_context,expected_outcome,decision_timing,status,"
            "decision_note,created_at,decided_at,decided_by,approval_notification_id"
            "&order=created_at.desc&limit=500"
        ),token=token,timeout=14,
    )
    if not isinstance(result,list):
        raise RuntimeError("Scorecard analysis approvals could not be loaded")
    return result


def owner_analysis_action(token: str, analysis_id: str,
                          action: str, note: str = "") -> dict:
    if action not in ("approve","decline","revoke"):
        raise ValueError("Unsupported analysis approval action")
    if len(note)>1000:
        raise ValueError("Decision note exceeds 1000 characters")
    result = _request_json(
        "POST",_rest_url("rpc/portfolio_advisory_scorecard_analysis_owner_v1"),
        token=token,timeout=16,
        payload={"p_analysis_id":analysis_id,"p_action":action,"p_note":note},
    )
    expected={"approve":"approved","decline":"declined","revoke":"revoked"}[action]
    if not isinstance(result,dict) or result.get("status") != expected:
        raise RuntimeError("Approval action was not confirmed")
    if action=="approve":
        workspace_id=str(result.get("workspace_id") or "")
        if not workspace_id:
            raise RuntimeError("Approval response contains no workspace")
        rows=_request_json(
            "GET",_rest_url(
                "portfolio_advisory_scorecards?"
                "select=id,user_id,status,revision,payload,analysis_request_id"
                "&analysis_request_id=eq."+quote(analysis_id,safe="")+"&limit=1"
            ),token=token,timeout=12,
        )
        if (not isinstance(rows,list) or len(rows)!=1
            or str(rows[0].get("id"))!=workspace_id
            or rows[0].get("status")!="active"
            or str(rows[0].get("analysis_request_id"))!=analysis_id
            or not isinstance(rows[0].get("payload"),dict)
            or rows[0]["payload"].get("initiatives")!=[]
            or rows[0].get("revision")!=0):
            raise RuntimeError(
                "Approval was recorded, but the new empty workspace "
                "could not be independently verified. Refresh the queue."
            )
        notification_id=str(result.get("notification_id") or "")
        if notification_id and not result.get("unchanged"):
            try:
                delivery=deliver_approval_notice(token,notification_id)
                result["notification_message"]=approval_notice_message(delivery)
            except (RuntimeError,TimeoutError,ValueError,KeyError):
                result["notification_message"]=(
                    "Access was approved, but email delivery was not confirmed. "
                    "The notification can be retried in the approval history."
                )
        elif not notification_id:
            result["notification_message"]=(
                "Workspace created; no access email event was returned."
            )
    return result


def _client_name(req: dict, people: dict[str,dict]) -> str:
    person=people.get(str(req.get("user_id")),{})
    name=" ".join(filter(None,(
        str(person.get("first_name") or "").strip(),
        str(person.get("last_name") or "").strip(),
    )))
    return name or str(person.get("email") or "Verified Advisory client")


def _request_detail(req: dict, people: dict[str,dict]) -> None:
    st.markdown("### "+str(req.get("title") or "Portfolio assessment"))
    st.caption(
        _client_name(req,people)+" · "
        +str(people.get(str(req.get("user_id")),{}).get("email") or "")
        +" · Requested "+str(req.get("created_at") or "")[:10]
    )
    st.markdown("**Decision to be supported**")
    st.write(str(req.get("decision_context") or "No decision context recorded."))
    st.markdown("**Expected outcome**")
    st.write(str(req.get("expected_outcome") or "No outcome recorded."))
    st.caption(
        "Requested timeframe: "+str(req.get("decision_timing") or "Exploratory")
        +" · Approval status: "+str(req.get("status") or "pending").title()
    )


def _email_status(token: str, req: dict) -> None:
    rid=str(req.get("id") or "")
    notice_id=str(req.get("approval_notification_id") or "")
    if not notice_id:
        st.caption("No access email event was recorded for this analysis.")
        return
    try:
        rows=_request_json(
            "GET",_rest_url(
                "portfolio_advisory_approval_notifications?"
                "select=id,state,sent_at,error_category,attempts"
                "&id=eq."+quote(notice_id,safe="")+"&limit=1"
            ),token=token,timeout=12,
        )
        notice=rows[0] if isinstance(rows,list) and rows else None
    except (RuntimeError,TimeoutError,ValueError,KeyError):
        notice=None
    if not notice:
        st.caption("Email delivery status is temporarily unavailable.")
        return
    status=str(notice.get("state") or "pending")
    st.caption(
        "Supabase access email · "
        +("Accepted by provider" if status=="sent" else status.title())
        +(f" · Attempts: {notice.get('attempts') or 0}" if status!="sent" else "")
    )
    if status in ("pending","failed"):
        if st.button("Retry access email",key="scorecard_analysis_email_retry_"+rid):
            try:
                outcome=deliver_approval_notice(token,notice_id)
                st.session_state["scorecard_owner_analysis_flash"]=approval_notice_message(outcome)
                st.rerun()
            except (RuntimeError,TimeoutError,ValueError,KeyError):
                st.error("Delivery was not confirmed. Access remains approved.")


def _active_workspace_summary(token: str, req: dict) -> None:
    rid=str(req.get("id") or "")
    try:
        rows=_request_json(
            "GET",_rest_url(
                "portfolio_advisory_scorecards?"
                "select=id,revision,payload,updated_at,status,approved_at"
                "&analysis_request_id=eq."+quote(rid,safe="")+"&limit=1"
            ),token=token,timeout=12,
        )
        record=rows[0] if isinstance(rows,list) and rows else None
    except (RuntimeError,TimeoutError,ValueError,KeyError):
        record=None
    if record is None:
        st.warning("The approved workspace could not be verified.")
        return
    payload=record.get("payload") if isinstance(record.get("payload"),dict) else {}
    initiatives=payload.get("initiatives") if isinstance(payload.get("initiatives"),list) else []
    c1,c2,c3=st.columns(3)
    c1.metric("Recorded initiatives",len(initiatives))
    c2.metric("Saved revision",record.get("revision") or 0)
    c3.metric("Workspace state",str(record.get("status") or "").title())
    st.caption(
        "Approved "+str(record.get("approved_at") or "")[:10]
        +" · Last saved "+str(record.get("updated_at") or "")[:16].replace("T"," ")
    )
    if initiatives:
        with st.expander("Initiative register · "+str(len(initiatives))+" items"):
            st.dataframe(
                [{
                    "Initiative":str(x.get("name") or "Not named"),
                    "Business owner":str(x.get("owner") or "Not assigned"),
                    "Stage":str(x.get("stage") or "Not recorded"),
                    "Control":str(x.get("gate") or "Not assessed"),
                } for x in initiatives if isinstance(x,dict)],
                hide_index=True,use_container_width=True,
            )
    else:
        st.info("This analysis is approved but the client has not entered initiatives yet.")


def render_scorecard_analysis_approvals(token: str, people: list[dict]) -> None:
    """Owner-facing navigation: one approval, one client, one decision at a time."""
    st.subheader("Scorecard service management")
    st.caption(
        "Review new client decisions individually, inspect approved workspaces "
        "and see the approval history. Each new workspace remains independent."
    )
    try:
        requests=read_owner_analysis_requests(token)
    except (RuntimeError,TimeoutError,ValueError,KeyError):
        st.error("Analysis approvals are temporarily unavailable.")
        return
    people_by_id={str(p.get("user_id")):p for p in people}
    pending=[r for r in requests if r.get("status")=="pending"]
    approved=[r for r in requests if r.get("status")=="approved"]
    a,b,c=st.columns(3)
    a.metric("Awaiting review",len(pending))
    b.metric("Approved",len(approved))
    c.metric("Declined / revoked",sum(r.get("status") in ("declined","revoked") for r in requests))
    flash=st.session_state.pop("scorecard_owner_analysis_flash",None)
    if flash:
        st.success(str(flash))
    mode=st.segmented_control(
        "Management section",
        ("Approval queue","Approved analyses","Decision history"),
        default="Approval queue",
        key="scorecard_owner_analysis_mode",
    )

    if mode=="Approval queue":
        if not pending:
            st.info("No new Scorecard analyses are awaiting approval.")
            return
        st.markdown("#### Review a request")
        choices={str(r["id"]):r for r in pending}
        rid=st.selectbox(
            "Pending request",list(choices),
            format_func=lambda val:(
                str(choices[val].get("title") or "Analysis")+" · "
                +_client_name(choices[val],people_by_id)
            ),key="scorecard_owner_pending_choice"
        )
        req=choices[rid]
        with st.container(border=True):
            _request_detail(req,people_by_id)
            st.caption(
                "Approval creates an independent empty Scorecard; it does not copy, "
                "reset or authorize spending from an existing portfolio."
            )
            with st.form("scorecard_analysis_owner_decision_"+rid):
                note=st.text_area(
                    "Decision note (shown if declined)",max_chars=1000,height=80,
                    key="scorecard_owner_note_"+rid,
                )
                confirmed=st.checkbox(
                    "I have reviewed the request and approve a separate Scorecard.",
                    key="scorecard_owner_confirm_"+rid,
                )
                left,right=st.columns(2)
                with left:
                    approve=st.form_submit_button(
                        "Approve and create new Scorecard",type="primary",
                        use_container_width=True
                    )
                with right:
                    decline=st.form_submit_button(
                        "Decline request",use_container_width=True
                    )
            if approve or decline:
                if approve and not confirmed:
                    st.error("Explicit approval is required.")
                else:
                    try:
                        result=owner_analysis_action(
                            token,rid,"approve" if approve else "decline",note
                        )
                        st.session_state["scorecard_owner_analysis_flash"]=(
                            "New Scorecard created and verified. "
                            +str(result.get("notification_message") or "")
                            if approve else "Request declined. The decision is recorded."
                        )
                        st.rerun()
                    except (RuntimeError,TimeoutError,ValueError,KeyError) as exc:
                        st.error(str(exc))
        return

    if mode=="Approved analyses":
        if not approved:
            st.info("No additional analyses have been approved.")
            return
        choices={str(r["id"]):r for r in approved}
        rid=st.selectbox(
            "Select approved analysis",list(choices),
            format_func=lambda val:(
                str(choices[val].get("title") or "Analysis")+" · "
                +_client_name(choices[val],people_by_id)
            ),key="scorecard_owner_approved_choice",
        )
        req=choices[rid]
        _request_detail(req,people_by_id)
        st.divider()
        st.markdown("#### Workspace contents")
        _active_workspace_summary(token,req)
        st.markdown("#### Client notification")
        _email_status(token,req)
        with st.expander("Revoke this individual analysis",expanded=False):
            st.caption(
                "Revoking this analysis prevents access while preserving the saved "
                "record. Other approved analyses are unaffected."
            )
            with st.form("scorecard_analysis_revoke_"+rid):
                confirm=st.checkbox(
                    "Revoke only this analysis (retain saved work).",
                    key="scorecard_analysis_revoke_ack_"+rid,
                )
                submit=st.form_submit_button("Revoke this workspace")
            if submit:
                if not confirm:
                    st.error("Confirm the individual revocation.")
                else:
                    try:
                        owner_analysis_action(token,rid,"revoke")
                        st.session_state["scorecard_owner_analysis_flash"]=(
                            "The selected analysis was revoked; other workspaces are unchanged."
                        )
                        st.rerun()
                    except (RuntimeError,TimeoutError,ValueError,KeyError):
                        st.error("Revocation could not be confirmed.")
        return

    st.markdown("#### Analysis decision history")
    if not requests:
        st.info("There are no additional analysis requests in the history.")
        return
    st.dataframe(
        [{
            "Requested":str(r.get("created_at") or "")[:10],
            "Analysis":str(r.get("title") or ""),
            "Client":_client_name(r,people_by_id),
            "Status":str(r.get("status") or "").title(),
            "Decided":str(r.get("decided_at") or "")[:10],
        } for r in requests],
        hide_index=True,use_container_width=True
    )
    by_id={str(r["id"]):r for r in requests}
    selected=st.selectbox(
        "Inspect historical request",list(by_id),
        format_func=lambda val:(
            str(by_id[val].get("title") or "Analysis")+" · "
            +str(by_id[val].get("status") or "").title()
        ),key="scorecard_owner_history_choice",
    )
    with st.container(border=True):
        _request_detail(by_id[selected],people_by_id)
        if by_id[selected].get("decision_note"):
            st.markdown("**Recorded decision note**")
            st.write(str(by_id[selected]["decision_note"]))
        st.caption(
            "History records the individual access decision. The client's "
            "separate Scorecard contains the assessment and formal decision record."
        )
