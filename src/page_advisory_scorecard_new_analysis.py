"""Separate approval for each additional AI Portfolio Scorecard analysis.

A member with at least one active, approved Scorecard can request another
private analysis. Requesting does not create or grant a workspace.
"""
from __future__ import annotations

from urllib.parse import quote
import streamlit as st
from site_cms import _request_json, _rest_url


def read_analysis_requests(token: str, uid: str) -> list[dict]:
    rows = _request_json(
        "GET",
        _rest_url(
            "portfolio_advisory_scorecard_analysis_requests?"
            "select=id,title,decision_context,expected_outcome,decision_timing,"
            "status,decision_note,created_at,decided_at"
            "&user_id=eq." + quote(uid, safe="") + "&order=created_at.desc&limit=100"
        ),
        token=token, timeout=12,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Analysis request state is unavailable")
    return rows


def submit_new_analysis(token: str, anchor_scorecard_id: str,
                        title: str, context: str, outcome: str,
                        timing: str) -> dict:
    title = str(title or "").strip()
    context = str(context or "").strip()
    outcome = str(outcome or "").strip()
    if not (10 <= len(title) <= 140):
        raise ValueError("Give this analysis a title of 10–140 characters.")
    if not (20 <= len(context) <= 1800):
        raise ValueError("Describe the portfolio decision in 20–1,800 characters.")
    if not (10 <= len(outcome) <= 800):
        raise ValueError("Describe the expected outcome in 10–800 characters.")
    if timing not in ("This month", "1–3 months", "Exploratory"):
        raise ValueError("Choose a valid decision timeframe.")
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_scorecard_analysis_request_v1"),
        token=token, timeout=15,
        payload={
            "p_anchor_scorecard_id":anchor_scorecard_id,
            "p_title":title,
            "p_context":context,
            "p_outcome":outcome,
            "p_timing":timing,
        },
    )
    if not isinstance(result,dict) or result.get("status") != "pending" or not result.get("id"):
        raise RuntimeError("Analysis request was not confirmed")
    return result


def render_new_analysis_request(token: str, uid: str, anchor_scorecard_id: str) -> None:
    """Small, unobtrusive control on the authenticated Scorecard page."""
    try:
        requests = read_analysis_requests(token, uid)
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        st.caption("New analysis requests are temporarily unavailable. Your current workspace is unaffected.")
        return

    pending = next((r for r in requests if r.get("status")=="pending"),None)
    if pending:
        st.info(
            "**New analysis pending individual approval** — "
            + str(pending.get("title") or "Scorecard request")
            + ". Your current Scorecard remains available."
        )
    else:
        key="scorecard_new_analysis_open_"+uid
        if st.button(
            "Request a new Scorecard analysis",
            key="scorecard_new_analysis_button_"+uid,
            help="Start a separate analysis. Your existing initiative portfolio and reports are preserved.",
        ):
            st.session_state[key] = True
        if st.session_state.get(key,False):
            st.markdown("#### New Scorecard analysis request")
            st.caption(
                "Each analysis is reviewed individually. Once approved, a new "
                "empty workspace will appear here; previous work is never reset. "
                "Do not include confidential business information."
            )
            with st.form("scorecard_new_analysis_request_form_"+uid):
                title=st.text_input(
                    "Analysis title *", max_chars=140,
                    placeholder="For example: Customer operations AI investment review",
                )
                context=st.text_area(
                    "What portfolio decision do you need to make? *",
                    max_chars=1800,height=95,
                    placeholder="Describe the competing opportunities, constraints and business decision.",
                )
                outcome=st.text_area(
                    "What outcome should this analysis support? *",
                    max_chars=800,height=72,
                    placeholder="For example: a shortlist with clear next actions and investment conditions.",
                )
                timing=st.selectbox(
                    "Decision timeframe", ("This month","1–3 months","Exploratory"),
                )
                submitted=st.form_submit_button("Submit for individual approval",type="primary")
            if submitted:
                try:
                    submit_new_analysis(token,anchor_scorecard_id,title,context,outcome,timing)
                    st.session_state[key]=False
                    st.session_state["scorecard_new_analysis_flash_"+uid]=(
                        "New analysis requested. A separate empty Scorecard will be "
                        "created only after individual approval."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except (RuntimeError, TimeoutError, KeyError):
                    st.error(
                        "The request could not be confirmed. Refresh to check "
                        "whether one is pending before trying again."
                    )
    flash=st.session_state.pop("scorecard_new_analysis_flash_"+uid,None)
    if flash:
        st.success(str(flash))

    history=[r for r in requests if r.get("status")!="pending"]
    if history:
        with st.expander("Previous analysis access decisions",expanded=False):
            for item in history[:12]:
                status=str(item.get("status") or "").capitalize()
                st.caption(
                    f"{str(item.get('title') or 'Analysis')} · {status} · "
                    f"{str(item.get('created_at') or '')[:10]}"
                )
                if item.get("status")=="declined" and item.get("decision_note"):
                    st.caption("Response: "+str(item["decision_note"]))
