"""Owner-only interview-stage hiring forecast v2.

V2 is the primary hiring overview. Beta 4.3 remains available in historical
snapshots but is not a fallback masquerading as a current v2 prediction.
"""
from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from site_cms import _request_json, _rest_url

VERSION = "hiring-v2-stage-evidence-provisional"
STAGE_NAMES = {
    "verified_offer": "Verified offer",
    "subsequent_interview_completed": "Subsequent interview completed",
    "subsequent_interview_scheduled": "Second interview scheduled",
    "first_interview_completed": "First interview completed",
    "first_interview_scheduled": "First interview scheduled",
    "human_response": "Recruiter / human response",
    "application_only": "Application, no verified response",
}


def validate_prediction_v2(result: object) -> dict:
    if not isinstance(result, dict) or result.get("model_version") != VERSION:
        raise ValueError("The hiring v2 model did not return a valid versioned forecast.")
    if not isinstance(result.get("cohort"), dict) or not isinstance(
        result.get("top_processes"), list
    ):
        raise ValueError("Hiring v2 response lacks the required pipeline evidence.")
    index = result.get("portfolio_credibility_index")
    if index is None or not 0 <= float(index) <= 100:
        raise ValueError("Hiring v2 credibility score is missing or out of range.")
    return result


def fetch_hiring_prediction_v2(access_token: str) -> dict:
    """Read the owner's private Supabase RPC. Never query as anon."""
    if not access_token:
        raise ValueError("An owner access token is required.")
    response = _request_json(
        "POST", _rest_url("rpc/careersite_hiring_prediction_v2"),
        token=access_token, payload={}, timeout=25,
    )
    return validate_prediction_v2(response)


def _pretty_date(value: str | None) -> str:
    if not value:
        return "Not established"
    try:
        return date.fromisoformat(value).strftime("%d %b %Y")
    except (TypeError, ValueError):
        return "Not established"


def _stage_title(stage: str | None) -> str:
    return STAGE_NAMES.get(stage or "", (stage or "Unverified").replace("_", " ").capitalize())


def _live_opportunities(data: dict) -> list[dict]:
    """Only verified or human-engaged processes, not application-volume noise."""
    return [
        p for p in data.get("top_processes", [])
        if p.get("stage") not in (None, "application_only")
        and p.get("status") not in ("employer_rejection", "stale_unknown", "closed_unreconciled")
    ]


def render_hiring_prediction_v2(data: dict) -> dict:
    data = validate_prediction_v2(data)
    cohort = data["cohort"]
    scenario = data.get("leading_stage_scenario") or {}
    index = float(data["portfolio_credibility_index"])

    st.subheader("When might I get an offer?")
    st.caption("Hiring Prediction v2 · verified interview stages and employer evidence. "
               "Dates are conditional planning scenarios, not calibrated hiring probabilities.")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.caption("Leading-process offer scenario")
            st.markdown(f"### {_pretty_date(scenario.get('offer_central'))}")
            st.caption("Indicative midpoint, conditional on progressing through interviews.")
    with right:
        with st.container(border=True):
            st.caption("Leading-process start scenario")
            st.markdown(f"### {_pretty_date(scenario.get('start_central'))}")
            st.caption("Illustrative start date after an offer, not a confirmed first day.")

    st.markdown(f"**Pipeline credibility: {index:.1f} / 100**")
    st.progress(index / 100)
    st.caption("Relative strength of documented recruiting processes — **not** "
               "a {index:.1f}% offer chance, evidence reliability percentage or forecast accuracy."
               .replace("{index:.1f}", f"{index:.1f}"))

    live = _live_opportunities(data)
    if live:
        top = live[0]
        st.markdown(f"**Strongest verified route:** {top['employer']} — "
                    f"{top['role']} ({_stage_title(top.get('stage')).lower()}).")
        if top.get("next_interview"):
            st.caption(f"Next confirmed interview: {_pretty_date(top['next_interview'])}. "
                       "A scheduled interview is not counted as completed.")
    else:
        st.info("No confirmed active interview or human-response process is available.")

    relevant = [p for p in live if float(p.get("credibility_index") or 0) >= 10][:7]
    if relevant:
        st.markdown("**Where current opportunities stand**")
        chart_data = [{
            "Process": f"{p['employer']} · {p['role'][:35]}",
            "Credibility": float(p.get("credibility_index") or 0),
            "Stage": _stage_title(p.get("stage")),
        } for p in reversed(relevant)]
        chart = (alt.Chart(alt.Data(values=chart_data))
                 .mark_bar(cornerRadiusEnd=4)
                 .encode(
                     y=alt.Y("Process:N", sort=None, title=None),
                     x=alt.X("Credibility:Q", title="Relative credibility index",
                             scale=alt.Scale(domain=[0, 100])),
                     tooltip=["Process:N", "Stage:N",
                              alt.Tooltip("Credibility:Q", format=".1f")],
                 ).properties(height=max(150, len(chart_data) * 39)))
        st.altair_chart(chart, width="stretch")
        st.caption("Scores use the highest documented process stage, senior role-fit "
                   "category and evidence recency. They are **not** offer probabilities.")

    st.markdown("**What the evidence says**")
    if cohort.get("subsequent_stage_v2", 0):
        st.caption(f"{cohort['subsequent_stage_v2']} process(es) have a confirmed "
                   "subsequent-interview milestone.")
    if cohort.get("scheduled_first_v2", 0):
        st.caption(f"{cohort['scheduled_first_v2']} process(es) have a scheduled "
                   "first interview that has not been recorded as completed.")
    st.caption(f"{cohort.get('stale_not_rejected',0)} applications have aged without "
               "a known employer decision; they contribute no active forecast weight "
               "and are **not** classified as rejections.")
    if cohort.get("reconciled_active"):
        st.caption(f"{cohort['reconciled_active']} older closed/unreconciled "
                   "status(es) were overridden by newer confirmed progression evidence.")

    if scenario:
        with st.expander("Offer and start timing — conditional scenario"):
            st.markdown(f"**Offer window:** {_pretty_date(scenario.get('offer_earliest'))} "
                        f"to {_pretty_date(scenario.get('offer_latest'))}.")
            st.markdown(f"**Potential start window:** "
                        f"{_pretty_date(scenario.get('start_earliest'))} "
                        f"to {_pretty_date(scenario.get('start_latest'))}.")
            st.caption("These are illustrative stage durations for the leading process. "
                       "They depend on successful interviews, hiring decisions and "
                       "start-date arrangements; there are not enough historical "
                       "offers to establish a calibrated personal probability.")

    with st.expander("How v2 is calculated and what remains uncertain"):
        st.markdown("**Verified stage → role alignment → freshness → credibility.**")
        st.caption("Initial stage weights: application 0.05; verified human contact "
                   "0.15; first interview scheduled 0.22; first interview completed "
                   "0.45; subsequent interview scheduled 0.58; subsequent interview "
                   "completed 0.65; verified offer 0.95. These are provisional scoring "
                   "coefficients, **not** observed conversion rates.")
        st.caption("Confirmed employer advancement provides a small bonus. Ageing "
                   "reduces confidence. Rejections and verified exclusions receive "
                   "zero active credit; stale silence is not a confirmed rejection.")
        st.caption("Sweden-wide leadership mandates remain addressable: Gothenburg "
                   "is the preferred base, Stockholm is not automatically penalized, "
                   "business travel is acceptable and family relocation is conditional "
                   "on a sufficiently strong opportunity.")
        st.caption(f"Audited processes: {cohort.get('total',0)} · "
                   f"active scored: {cohort.get('eligible_scored',0)} · "
                   f"verified offers: {cohort.get('offers',0)}. "
                   "Market data is contextual, not substituted for personal interview "
                   "outcomes. Model version: " + VERSION + ".")
        with st.container():
            details = [{
                "Employer": p.get("employer"),
                "Role": p.get("role"),
                "Verified stage": _stage_title(p.get("stage")),
                "Last progression": p.get("last_progress") or "Undated",
                "Next interview": p.get("next_interview") or "Not confirmed",
                "Credibility index": float(p.get("credibility_index") or 0),
            } for p in data.get("top_processes", [])]
            if details:
                st.dataframe(details, hide_index=True, width="stretch")

    return data
