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


def render_scorecard_analysis_approvals(
    token: str, people: list[dict],
) -> None:
    st.subheader("New Scorecard analysis requests")
    st.caption(
        "Approve each new analysis separately. Approval creates an empty, "
        "private Scorecard with its own revision history. Earlier analyses "
        "and existing access rights remain unchanged."
    )
    try:
        requests=read_owner_analysis_requests(token)
    except (RuntimeError,TimeoutError,ValueError,KeyError):
        st.error("The analysis approval queue could not be read.")
        return
    people_by_id={str(p.get("user_id")):p for p in people}
    pending=[r for r in requests if r.get("status")=="pending"]
    a,b,c=st.columns(3)
    a.metric("Awaiting decision",len(pending))
    b.metric("Approved analyses",sum(r.get("status")=="approved" for r in requests))
    c.metric("Declined / revoked",sum(r.get("status") in ("declined","revoked") for r in requests))
    if pending:
        for req in pending:
            rid=str(req["id"])
            person=people_by_id.get(str(req.get("user_id")),{})
            client=str(person.get("email") or "Verified Advisory client")
            with st.container(border=True):
                st.markdown("#### "+str(req.get("title") or "New analysis"))
                st.caption(client+" · Requested "+str(req.get("created_at") or "")[:16].replace("T"," "))
                st.markdown("**Portfolio decision:**")
                st.write(str(req.get("decision_context") or ""))
                st.markdown("**Desired outcome:**")
                st.write(str(req.get("expected_outcome") or ""))
                st.caption("Decision timeframe: "+str(req.get("decision_timing") or "Exploratory"))
                with st.form("scorecard_analysis_owner_decision_"+rid):
                    note=st.text_area(
                        "Decision note (visible to the client if declined)",
                        max_chars=1000,height=68,key="scorecard_owner_note_"+rid,
                    )
                    confirmed=st.checkbox(
                        "I have reviewed this request and approve another private, empty Scorecard.",
                        key="scorecard_owner_confirm_"+rid,
                    )
                    approve=st.form_submit_button(
                        "Approve and create new Scorecard",type="primary"
                    )
                    decline=st.form_submit_button("Decline this request")
                if approve or decline:
                    if approve and not confirmed:
                        st.error("Confirm approval before creating a new workspace.")
                    else:
                        try:
                            result=owner_analysis_action(
                                token,rid,"approve" if approve else "decline",note
                            )
                            st.session_state["scorecard_owner_analysis_flash"]=(
                                "Approved: a new empty workspace was created and verified. "
                                "The client can select it in their Advisory account. "
                                +str(result.get("notification_message") or "")
                                if approve else "New analysis request declined."
                            )
                            st.rerun()
                        except (RuntimeError,TimeoutError,ValueError,KeyError) as exc:
                            st.error(str(exc))
    else:
        st.info("No new Scorecard analyses are awaiting approval.")

    flash=st.session_state.pop("scorecard_owner_analysis_flash",None)
    if flash:
        st.success(str(flash))
    history=[r for r in requests if r.get("status")!="pending"]
    if history:
        st.markdown("#### Decision history and access controls")
        with st.expander("Previous analysis decisions ("+str(len(history))+")"):
            for req in history[:100]:
                rid=str(req["id"])
                client=str(people_by_id.get(str(req.get("user_id")),{}).get("email") or "")
                st.markdown(
                    "**"+str(req.get("title") or "Analysis")+"** · "
                    +str(req.get("status") or "").capitalize()
                )
                st.caption(client+" · "+str(req.get("decided_at") or "")[:16].replace("T"," "))
                if req.get("decision_note"):
                    st.caption("Decision note: "+str(req["decision_note"]))
                if req.get("status")=="approved":
                    notice_id=str(req.get("approval_notification_id") or "")
                    if notice_id:
                        try:
                            notices=_request_json(
                                "GET",_rest_url(
                                    "portfolio_advisory_approval_notifications?"
                                    "select=id,state,sent_at,error_category,attempts"
                                    "&id=eq."+quote(notice_id,safe="")+"&limit=1"
                                ),token=token,timeout=12,
                            )
                            notice=notices[0] if isinstance(notices,list) and notices else None
                        except (RuntimeError,TimeoutError,ValueError,KeyError):
                            notice=None
                        if notice:
                            state=str(notice.get("state") or "pending")
                            st.caption(
                                "Access email: "+(
                                    "Supabase Auth accepted the request"
                                    if state=="sent" else state.capitalize()
                                )
                            )
                            if state in ("pending","failed"):
                                if st.button(
                                    "Retry access email",
                                    key="scorecard_analysis_email_retry_"+rid,
                                ):
                                    try:
                                        result=deliver_approval_notice(token,notice_id)
                                        st.session_state["scorecard_owner_analysis_flash"]=(
                                            approval_notice_message(result)
                                        )
                                        st.rerun()
                                    except (RuntimeError,TimeoutError,ValueError,KeyError):
                                        st.error("Email delivery could not be confirmed.")
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
                                    "This analysis was revoked. Other Scorecards remain available."
                                )
                                st.rerun()
                            except (RuntimeError,TimeoutError,ValueError,KeyError):
                                st.error("Revocation could not be confirmed.")
                st.divider()
