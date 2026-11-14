"""Reusable, optional client feedback at real Executive Advisory interaction stages.

Only verified members can submit, via an ownership-checked Supabase RPC. One
record per service/stage/engagement avoids repeated surveys on every page view.
Feedback never gates registration, assessment results, recommendations, or export.
"""
from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from site_cms import _request_json, _rest_url


SCORECARD_SERVICE = "ai_portfolio_prioritization_scorecard"
ADVISORY_SERVICE = "executive_advisory"

STAGE_QUESTIONS = {
    "registration_access": (
        "Registration and access",
        "Was registration and account access clear and straightforward?",
    ),
    "assessment_completion": (
        "Assessment completion",
        "Were the assessment questions relevant and easy to answer?",
    ),
    "executive_recommendation": (
        "Decision Usefulness",
        "Did the Scorecard's suggested actions make your next decision clearer?",
    ),
    "report_download": (
        "Report usefulness",
        "Could you use the exported Scorecard summary in a real business decision?",
    ),
    "personal_advisory": (
        "Advisory experience",
        "How satisfied were you with the advisory support and outcome?",
    ),
}


def read_member_feedback(token: str, uid: str) -> list[dict]:
    if not token or not uid:
        raise ValueError("An authenticated Advisory account is required")
    rows = _request_json(
        "GET",
        _rest_url(
            "portfolio_advisory_interaction_feedback?"
            "select=id,service_key,stage,request_id,scorecard_id,rating,created_at"
            "&user_id=eq." + quote(uid, safe="") + "&order=created_at.desc&limit=200"
        ),
        token=token,
        timeout=11,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Feedback state unavailable")
    return rows


def already_recorded(rows: list[dict], service_key: str, stage: str,
                     request_id: str | None = None,
                     scorecard_id: str | None = None) -> bool:
    for row in rows:
        if row.get("service_key") != service_key or row.get("stage") != stage:
            continue
        if str(row.get("request_id") or "") != str(request_id or ""):
            continue
        if str(row.get("scorecard_id") or "") != str(scorecard_id or ""):
            continue
        return True
    return False


def submit_feedback(token: str, service_key: str, stage: str, rating: int,
                    comment: str = "", followup_answer: str = "",
                    contact_ok: bool = False, request_id: str | None = None,
                    scorecard_id: str | None = None) -> str:
    if stage not in STAGE_QUESTIONS:
        raise ValueError("Unrecognized feedback stage")
    if service_key not in (ADVISORY_SERVICE, SCORECARD_SERVICE):
        raise ValueError("Unrecognized advisory service")
    if type(rating) is not int or not 1 <= rating <= 5:
        raise ValueError("Please select a rating between 1 and 5")
    if len(comment) > 800 or len(followup_answer) > 800:
        raise ValueError("Please shorten your optional comment")
    result = _request_json(
        "POST",
        _rest_url("rpc/portfolio_advisory_feedback_submit_v1"),
        token=token, timeout=12,
        payload={
            "p_service_key": service_key,
            "p_stage": stage,
            "p_request_id": request_id,
            "p_scorecard_id": scorecard_id,
            "p_rating": rating,
            "p_comment": comment.strip(),
            "p_followup_answer": followup_answer.strip(),
            "p_contact_ok": bool(contact_ok),
        },
    )
    if not isinstance(result, dict) or result.get("status") not in (
        "recorded", "already_recorded"
    ):
        raise RuntimeError("Feedback was not confirmed")
    return str(result["status"])


def render_optional_feedback(
    token: str, uid: str, service_key: str, stage: str, *,
    request_id: str | None = None, scorecard_id: str | None = None,
    feedback_rows: list[dict] | None = None,
) -> None:
    """Only a collapsed, contextual prompt; safe to omit when unavailable."""
    if not token or not uid or stage not in STAGE_QUESTIONS:
        return
    if feedback_rows is None:
        try:
            feedback_rows = read_member_feedback(token, uid)
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            return  # Never interrupt the actual Advisory interaction.
    suffix = scorecard_id or request_id or "onboarding"
    key = service_key + "_" + stage + "_" + suffix
    if already_recorded(feedback_rows, service_key, stage, request_id, scorecard_id):
        if st.session_state.pop("feedback_recently_recorded_" + key, False):
            st.caption("Thank you. Your optional feedback has been recorded.")
        return

    title, question = STAGE_QUESTIONS[stage]
    with st.expander(title + " · Optional feedback", expanded=False):
        st.caption(
            "One brief rating helps improve the service. You can skip this. "
            "Feedback is private and never required to continue."
        )
        rating = st.radio(
            question,
            options=[1, 2, 3, 4, 5],
            index=None, horizontal=True,
            help="1 = not at all · 5 = completely",
            key="feedback_rating_" + key,
        )
        with st.form("feedback_form_" + key):
            comment = st.text_area(
                "Optional comment",
                max_chars=800, height=68,
                placeholder="What worked, or what should be clearer?",
            )
            followup = ""
            contact_ok = False
            if rating is not None and rating <= 3:
                followup = st.text_area(
                    "What would make this more useful? (optional)",
                    max_chars=800, height=66,
                )
                contact_ok = st.checkbox(
                    "I am comfortable being contacted about this feedback",
                    value=False,
                )
            submit = st.form_submit_button(
                "Send optional feedback", disabled=rating is None,
            )
        if submit and rating is not None:
            try:
                submit_feedback(
                    token, service_key, stage, int(rating),
                    comment, followup, contact_ok,
                    request_id=request_id, scorecard_id=scorecard_id,
                )
                st.session_state["feedback_recently_recorded_" + key] = True
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.caption(
                    "Feedback could not be saved. Your Advisory work is unaffected."
                )
