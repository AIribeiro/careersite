"""Owner-only approval and revocation for one-session rollout decision advisory."""
from __future__ import annotations

import streamlit as st
from site_cms import _request_json, _rest_url

def _current(token: str, request_id: str) -> dict | None:
    rows = _request_json(
        "GET", _rest_url("portfolio_advisory_rollout_access?select=id,status,"
                         "approved_at,updated_at,request_id"
                         "&request_id=eq." + request_id + "&limit=1"),
        token=token, timeout=12)
    if not isinstance(rows,list):
        raise RuntimeError("Rollout entitlement unavailable")
    return rows[0] if rows else None

def _action(token: str, request_id: str, action: str) -> dict:
    if action not in ("approve","revoke"):
        raise ValueError("Invalid rollout entitlement action")
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_rollout_owner_action_v1"),
        token=token, payload={"p_request_id":request_id,"p_action":action},timeout=15)
    if not isinstance(result,dict) or result.get("status") not in ("active","revoked"):
        raise RuntimeError("Rollout entitlement not confirmed")
    return result

def render_owner_rollout_access(token: str, req: dict, requested: bool=False) -> None:
    rid=str(req.get("id") or "")
    stage=str(req.get("status") or "")
    if not rid:
        return
    try:
        record = _current(token,rid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("Unable to verify this client's rollout entitlement.")
        return
    if not requested and record is None:
        return
    st.markdown("#### Enterprise AI Rollout Advisor · Individual access")
    st.caption("A one-session executive decision service. Registration is not an entitlement.")
    if record:
        st.write("**Access:** "+str(record.get("status") or "")+
                 " · Approved: "+str(record.get("approved_at") or "")[:10])
    if stage=="active" and (record is None or record.get("status")!="active"):
        with st.form("rollout_owner_approve_"+rid):
            confirmed=st.checkbox(
                "I confirm this individual pro-bono service access has been reviewed "
                "and the information boundaries are agreed.")
            submitted=st.form_submit_button("Enable Rollout Advisor",type="primary")
        if submitted:
            if not confirmed:
                st.warning("Explicit approval is required.")
            else:
                try:
                    _action(token,rid,"approve")
                    st.success("Rollout Advisor access enabled and audited.")
                    st.rerun()
                except (ValueError,RuntimeError,TimeoutError,KeyError):
                    st.error("Rollout approval could not be confirmed.")
    elif record and record.get("status")=="active":
        if stage not in ("active","completed"):
            st.warning("This entitlement is automatically blocked while the engagement is inactive.")
        with st.form("rollout_owner_revoke_"+rid):
            confirmed=st.checkbox("I understand access will end immediately; "
                                  "previous decision briefs remain preserved.")
            submitted=st.form_submit_button("Revoke Rollout Advisor access")
        if submitted:
            if not confirmed:
                st.warning("Confirm the revocation.")
            else:
                try:
                    _action(token,rid,"revoke")
                    st.success("Rollout access revoked.")
                    st.rerun()
                except (ValueError,RuntimeError,TimeoutError,KeyError):
                    st.error("Rollout revocation could not be confirmed.")
    elif record is None:
        st.caption("Service approval becomes available after the agreed Advisory "
                   "engagement reaches the active stage.")
