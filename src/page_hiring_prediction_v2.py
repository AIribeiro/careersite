"""Owner-only interview-stage hiring forecast v2.

V2 is the primary hiring overview. Beta 4.3 remains available in historical
snapshots but is not a fallback masquerading as a current v2 prediction.
"""
from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from site_cms import _request_json, _rest_url

VERSION = "hiring-v2-stage-review-v1"  # Accepted historical stage model
CURRENT_VERSION = "hiring-v4-stage-review-market-live-v1"
SUPPORTED_VERSIONS = frozenset((VERSION, CURRENT_VERSION))
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
    if not isinstance(result, dict) or result.get("model_version") not in SUPPORTED_VERSIONS:
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



def _assessment_rows(access_token: str, prediction: dict) -> list[dict]:
    """Owner-only: link each reviewed interview to its exact opportunity ID."""
    if not access_token:
        return []
    assessments = _request_json(
        "GET", _rest_url(
            "careersite_interview_assessment_scores?"
            "select=review_id,status,source_basis,confidence,dimensions"
            "&status=in.(final,draft)&order=review_id.desc"
        ), token=access_token, timeout=18,
    )
    reviews = _request_json(
        "GET", _rest_url(
            "careersite_post_interview_reviews?"
            "select=id,opportunity_id,meeting_id,employer,role_title,interview_date,stage,review_status"
        ), token=access_token, timeout=18,
    )
    opportunities = _request_json(
        "GET", _rest_url(
            "careersite_recruiting_opportunities?"
            "select=id,forecast_process_key"
            "&forecast_process_key=not.is.null"
        ), token=access_token, timeout=18,
    )
    if not all(isinstance(values, list)
               for values in (assessments, reviews, opportunities)):
        raise RuntimeError("Interview assessment response is not a list.")
    by_review = {row["id"]: row for row in reviews}
    by_opportunity = {row["id"]: row.get("forecast_process_key")
                      for row in opportunities}
    by_process = {row.get("process_key"): row
                  for row in prediction.get("top_processes", [])}
    weights = {"mandate_fit": .25, "answer_evidence": .25,
               "interviewer_signal": .20, "objections_addressed": .20,
               "practical_feasibility": .10}
    rows = []
    for entry in assessments:
        review = by_review.get(entry.get("review_id"))
        if not review:
            continue
        dimensions = entry.get("dimensions") or {}
        if any(type(dimensions.get(k)) is not int or not 0 <= dimensions[k] <= 4
               for k in weights):
            continue
        process_key = by_opportunity.get(review.get("opportunity_id"))
        matched = by_process.get(process_key) if process_key else None
        final = (entry.get("status") == "final"
                 and review.get("review_status") == "reviewed")
        adjusted = float(matched.get("post_interview_delta_points") or 0) if matched else 0.
        stage = int(review.get("stage") or 0)
        weighted = round(25 * sum(dimensions[k] * w for k, w in weights.items()), 1)
        rows.append({
            "Employer / role": f"{review.get('employer') or 'Unlinked'} · {review.get('role_title') or 'Unknown role'}",
            "Interview": str(review.get("interview_date") or "Not established"),
            "Round": stage if stage else "Unknown",
            "Status": "Final · counted" if final and matched and
                      int(matched.get("post_interview_reviews_used") or 0) > 0
                      else ("Final · excluded" if final else "Draft · not counted"),
            "Quality": f"{sum(dimensions.values())}/20 ({weighted:.1f}/100)",
            "Evidence confidence": f"{float(entry.get('confidence') or 0)*100:.0f}%",
            "Forecast effect": f"{adjusted:+.1f} points" if final and matched else "None",
            "Process credibility": f"{float(matched['credibility_index']):.1f}/100"
                                    if matched else "Not in live shortlist",
        })
    return sorted(rows, key=lambda item:item["Interview"], reverse=True)

def _credibility_gradient_101() -> list[str]:
    """101 exact color stops: 0 green, 50 yellow, 100 red."""
    green = (22, 163, 74)
    yellow = (250, 204, 21)
    red = (220, 38, 38)
    colors = []
    for score in range(101):
        start, end, fraction = (
            (green, yellow, score / 50.0)
            if score <= 50 else
            (yellow, red, (score - 50) / 50.0)
        )
        rgb = tuple(round(a + (b - a) * fraction) for a, b in zip(start, end))
        colors.append("#{0:02x}{1:02x}{2:02x}".format(*rgb))
    return colors


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

    # Answer the user's timing question *before* showing diagnostic scores.
    # This scenario is conditioned on the leading process continuing successfully.
    st.subheader("When could I get my next job?")
    if scenario.get("start_central"):
        st.markdown(
            f"## Around {_pretty_date(scenario['start_central'])} "
            "— potential first day at work"
        )
        st.markdown(
            f"**Possible job offer: around "
            f"{_pretty_date(scenario.get('offer_central'))}.**"
        )
        if scenario.get("start_earliest") and scenario.get("start_latest"):
            st.caption(
                "Indicative start-date window: "
                f"{_pretty_date(scenario['start_earliest'])} – "
                f"{_pretty_date(scenario['start_latest'])}."
            )
    else:
        st.markdown("## No defensible start date yet")
        if scenario.get("window_state") == "expired_requires_new_employer_evidence":
            st.warning("The leading-process window has expired without a confirmed offer. "
                       "The model will not extend it indefinitely. "
                       "A new employer milestone is needed to establish a dated estimate.")
        else:
            st.caption("A timing scenario requires stronger verified interview evidence.")
    if scenario.get("timing_anchor"):
        remaining = scenario.get("days_to_offer")
        shift = scenario.get("calendar_shift_days")
        st.caption("Calendar anchor: verified milestone "+
                   _pretty_date(scenario.get("timing_anchor"))+
                   (f" · {remaining} calendar days until the conditional offer centre"
                    if remaining is not None else "")+
                   (f" · reassessed by {shift} days" if shift not in (None,0) else "")+
                   ". The countdown decreases daily while the central milestone remains "
                   "feasible; it does not restart automatically.")
        if scenario.get("window_state")=="overdue_reassessed_weekly":
            st.warning("Calendar reassessment: the original central offer window is "
                       "approaching or overdue. The planning date has advanced by "
                       "a bounded weekly step, not because an employer confirmed an offer.")
    st.caption(
        "Conditional stage-based planning estimate, **not a confirmed job, "
        "offer or statistically calibrated hiring probability**. "
        "The forecast will change as employers confirm or decline next steps."
    )
    st.markdown("**Offer and start — separate milestones**")

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
    st.caption(f"Relative strength of documented recruiting processes — not a "
               f"{index:.1f}% offer chance, evidence reliability percentage or "
               "forecast accuracy.")

    market = data.get("market_intelligence")
    if isinstance(market, dict) and market.get("status") == "active_in_production_not_shadow":
        st.caption(
            "Live market conditions: "
            + str(market.get("direction") or "mixed_stable").replace("_", " ")
            + f" · {int(market.get('signal_families_active') or 0)} scored source families"
            + f" · planning adjustment {int(data.get('market_adjustment_applied_days') or 0):+d} days."
            + " Directional planning evidence, not calibrated offer probabilities."
        )

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
        for position, process in enumerate(relevant, 1):
            score = max(0.0, min(100.0, float(process.get("credibility_index") or 0)))
            with st.container(border=True):
                st.markdown(f"#### {position}. {process['employer']}")
                st.caption(process["role"])
                st.markdown(f"**{_stage_title(process.get('stage'))}**")
                st.progress(score / 100, text=f"Evidence strength · {score:.1f} / 100")
                if process.get("next_interview"):
                    st.caption("Confirmed interview · " + _pretty_date(process["next_interview"]))
        st.caption("Higher scores mean stronger documented progression. "
                   "Scores reflect stage, role fit, evidence recency and finalized "
                   "interview reviews; they are not offer probabilities.")


    st.markdown("**Post-interview assessment impact**")
    st.caption("Assessment quality and employer progression are separate signals. "
               "Only finalized, evidence-backed assessments change the process score; "
               "drafts are retained for review but carry no forecast weight.")
    owner_session = st.session_state.get("cms_auth") or {}
    owner_token = str(owner_session.get("access_token") or "") if isinstance(owner_session, dict) else ""
    if owner_token:
        try:
            assessment_rows = _assessment_rows(owner_token, data)
            if assessment_rows:
                a, b, c = st.columns(3)
                a.metric("Assessed interviews", len(assessment_rows))
                b.metric("Finalized", sum("Final" in row["Status"] for row in assessment_rows))
                c.metric("Awaiting evidence", sum("Draft" in row["Status"] for row in assessment_rows))
                st.dataframe(assessment_rows, hide_index=True, width="stretch")
                st.caption("Evidence confidence describes source quality, not offer probability. "
                           "The forecast effect is aggregated at hiring-process level; "
                           "drafts and multiple interviews must not be added together.")
            else:
                st.caption("No scored interviews have been stored.")
        except (RuntimeError, TimeoutError, ValueError, PermissionError):
            st.warning("The stored assessment audit is temporarily unavailable. "
                       "The verified forecast above remains valid.")
    else:
        st.caption("Owner authentication is required to display interview assessments.")

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
        st.caption("Offer dates are now anchored to the observed employer milestone, "
                   "not recalculated as today plus a fixed number of days. "
                   "Elapsed days reduce remaining time. Near the original centre, "
                   "a bounded weekly reassessment applies; when the evidence window "
                   "expires, the model withholds the date instead of endlessly rolling it.")
        st.caption("Finalized post-interview reviews add or subtract at most eight "
                   "credibility points, moderated by evidence quality and confidence. "
                   "Draft reviews do not affect the model. Interview engagement is "
                   "not proof of an employer decision.")
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
                   "External market evidence is live but never replaces personal interview "
                   "outcomes. Model version: " + str(data.get("model_version") or VERSION) + ".")
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
