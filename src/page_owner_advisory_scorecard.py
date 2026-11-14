"""Owner-only controls for approving and revoking individual Scorecard workspaces."""
from __future__ import annotations

import streamlit as st

from site_cms import _request_json, _rest_url


def _current(token: str,request_id: str) -> dict | None:
    rows = _request_json(
        "GET", _rest_url("portfolio_advisory_scorecards?select=id,status,revision,"
                        "approved_at,updated_at,request_id,payload"
                        "&request_id=eq." + request_id + "&limit=1"),
        token=token, timeout=12,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Cannot read Scorecard entitlement")
    return rows[0] if rows else None


def _action(token: str,request_id: str,action: str) -> dict:
    if action not in ("approve","revoke"):
        raise ValueError("Unsupported entitlement action")
    result = _request_json(
        "POST",_rest_url("rpc/portfolio_advisory_scorecard_owner_action_v1"),
        token=token,payload={"p_request_id":request_id,"p_action":action},timeout=15
    )
    if not isinstance(result,dict) or result.get("status") not in ("active","revoked"):
        raise RuntimeError("Scorecard access action was not confirmed")
    return result


def render_scorecard_owner_access(token: str,req: dict) -> None:
    rid=str(req.get("id") or "")
    stage=str(req.get("status") or "")
    if not rid:
        return
    st.markdown("#### AI Portfolio Scorecard · Individual access")
    st.caption("This is a separate, on-demand pro-bono service. "
               "Registration alone never grants a Scorecard workspace.")
    try:
        record=_current(token,rid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("Unable to read the client's Scorecard access state.")
        return
    if record:
        st.write("**Entitlement:** "+str(record.get("status") or "")+
                 " · **Revision:** "+str(record.get("revision") or 0))
        st.caption("Approved: "+str(record.get("approved_at") or "")[:16].replace("T"," ")+
                   " · Last edited: "+str(record.get("updated_at") or "")[:16].replace("T"," "))
        payload=record.get("payload") if isinstance(record.get("payload"),dict) else {}
        initiatives=payload.get("initiatives") if isinstance(payload.get("initiatives"),list) else []
        st.caption(str(len(initiatives))+" initiative(s) recorded. "
                   "The advisor can review the client's evidence during the engagement.")
    if stage=="active" and (record is None or record.get("status")!="active"):
        with st.form("scorecard_owner_approve_"+rid):
            st.info("Approve only for a selected client whose pro-bono Advisory "
                    "scope and information boundaries have already been agreed.")
            confirmed=st.checkbox("I approve individual access to the AI Portfolio "
                                  "Prioritization Scorecard for this active engagement.")
            submitted=st.form_submit_button("Enable client workspace",type="primary")
        if submitted:
            if not confirmed:
                st.error("Explicit approval is required.")
            else:
                try:
                    _action(token,rid,"approve")
                    st.success("Individual Scorecard access enabled.")
                    st.rerun()
                except (ValueError,RuntimeError,TimeoutError,KeyError):
                    st.error("Approval could not be confirmed; check the request stage.")
    elif record and record.get("status")=="active":
        if stage not in ("active","completed"):
            st.warning("The entitlement record exists, but this Advisory request is no "
                       "longer active or completed. Client access is automatically blocked.")
        with st.form("scorecard_owner_revoke_"+rid):
            confirmed=st.checkbox("I understand this immediately prevents client access "
                                  "without deleting their stored decision work.")
            submitted=st.form_submit_button("Revoke Scorecard access")
        if submitted:
            if not confirmed:
                st.error("Confirm the revocation.")
            else:
                try:
                    _action(token,rid,"revoke")
                    st.success("Scorecard entitlement revoked.")
                    st.rerun()
                except (ValueError,RuntimeError,TimeoutError,KeyError):
                    st.error("The revocation could not be confirmed.")
    elif record is None:
        st.caption("Available to activate only after this request becomes an active, "
                   "agreed pro-bono Advisory engagement.")
