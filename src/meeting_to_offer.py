"""Evidence-led, reusable Meetings-to-Offer (MTO) planning estimator.

This module contains NO employer-specific cases or calibrated offer probabilities.
It estimates the number of candidate interview meetings on the route to a
potential offer decision, conditional on the employer continuing the process.
Only confirmed attendance contributes to the completed meeting count.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

METHOD_VERSION = "mto-v2-evidence-authority-20261030"


@dataclass(frozen=True)
class MTOEstimate:
    total_low: int
    total_high: int
    remaining_low: int | None
    remaining_high: int | None
    confidence: str
    evidence_level: str
    explanation: str
    version: str = METHOD_VERSION


def _prior(role: str, process: dict[str, Any]) -> tuple[int, int, str]:
    title = role.casefold()
    employment = str(process.get("employment_type") or "").casefold()
    if any(t in f"{title} {employment}" for t in ("contract", "interim", "temporary assignment", "freelance")):
        return 2, 3, "contract / interim assignment"
    if any(t in title for t in ("chief ", "ceo", "cfo", "cto", "cio", "cdo", "president", "executive vice president")):
        return 4, 6, "executive role"
    if any(t in title for t in ("director", "head of", "vice president", " vp ", "global head")):
        return 3, 5, "senior functional leadership"
    if any(t in title for t in ("manager", "lead", "principal", "product owner", "senior")):
        return 3, 4, "manager / senior specialist / functional lead"
    return 2, 4, "general experienced hire"


def _authority(meeting: dict[str, Any]) -> str:
    """Explicit authority is preferred; a title alone never proves final sign-off."""
    label = str(meeting.get("decision_authority") or "").strip().casefold().replace("-", "_")
    if label in {
        "final_decision_maker", "functional_owner", "executive_sponsor",
        "hiring_manager", "stakeholder", "recruiter",
    }:
        return label
    title = str(meeting.get("interviewer_role") or "").casefold()
    kind = str(meeting.get("meeting_type") or "").casefold()
    if any(w in title for w in ("recruit", "talent acquisition", "sourcer", "hr screening")) or kind == "recruiter_screening":
        return "recruiter"
    if "hiring manager" in title or kind == "hiring_manager":
        return "hiring_manager"
    if any(w in title for w in ("chief ", " ceo", " cto", " cfo", " cio", " cdo", "chief executive")):
        return "executive_sponsor"
    if any(w in title for w in ("partner", "director", "vice president", "head of", "panel", "stakeholder")):
        return "stakeholder"
    return "unknown"


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = int(value)
        return result if 0 <= result <= 30 else None
    except (ValueError, TypeError, OverflowError):
        return None


def estimate_mto(
    process: dict[str, Any],
    completed: int | None = None,
    meetings: list[dict[str, Any]] | None = None,
    employer_plan: dict[str, Any] | None = None,
) -> MTOEstimate:
    """Estimate total and remaining meeting ranges for ANY requisition.

    Inputs: role, completed distinct attended meetings, optional attendee-role
    evidence, optional confirmed employer recruiting plan. No interview outcome,
    favourable feedback or hiring forecast score is treated as a meeting.
    """
    low, high, family = _prior(str(process.get("role") or ""), process)
    plan = employer_plan if employer_plan is not None else process
    source_type = str(plan.get("mto_source_type") or "").casefold().strip()
    confirmed = source_type == "employer_confirmed"
    plan_total_low = _int_or_none(plan.get("mto_total_min"))
    plan_total_high = _int_or_none(plan.get("mto_total_max"))
    plan_rem_low = _int_or_none(plan.get("mto_remaining_min"))
    plan_rem_high = _int_or_none(plan.get("mto_remaining_max"))
    if plan_total_low is not None and plan_total_high is not None and plan_total_low > plan_total_high:
        plan_total_low = plan_total_high = None
    if plan_rem_low is not None and plan_rem_high is not None and plan_rem_low > plan_rem_high:
        plan_rem_low = plan_rem_high = None

    if completed is None:
        # Counts are unknown, not zero. A confirmed employer total can still
        # provide a total estimate without fabricating the remaining count.
        if confirmed and plan_total_low is not None and plan_total_high is not None:
            low, high = plan_total_low, plan_total_high
        return MTOEstimate(
            total_low=low, total_high=high,
            remaining_low=None, remaining_high=None,
            confidence="high" if confirmed and plan_total_low is not None else "low",
            evidence_level="employer_confirmed" if confirmed and plan_total_low is not None else "role_baseline",
            explanation=(
                f"Role baseline: {family}; employer-confirmed total applied. "
                if confirmed and plan_total_low is not None else
                f"Role baseline: {family}; no verified meeting count available. "
            ) + "Remaining meetings cannot be calculated until attendance is reconciled.",
        )

    completed = max(0, int(completed))
    evidence = meetings or []
    # The caller supplies attended records. Still reject unverified/cancelled
    # records if this estimator is reused directly by a different caller.
    authorities = [
        _authority(row) for row in evidence
        if isinstance(row, dict)
        and str(row.get("attendance") or "attended").casefold() == "attended"
        and str(row.get("meeting_type") or "").casefold() != "networking"
    ]
    has = set(authorities)
    remaining_low = max(0, low - completed)
    remaining_high = max(0, high - completed)
    level = "role_baseline"
    decision_reason = "No confirmed final decision-maker or employer-specific sequence."

    if "final_decision_maker" in has:
        remaining_low, remaining_high = 0, 1
        level = "decision_authority"
        decision_reason = "An explicitly identified final decision-maker has been interviewed; a final administrative/stakeholder meeting remains possible."
    elif "functional_owner" in has:
        remaining_low, remaining_high = 0, 1
        level = "decision_authority"
        decision_reason = "The accountable functional executive has been interviewed; decision now or one further round is plausible, not confirmed."
    elif "executive_sponsor" in has:
        remaining_low, remaining_high = 0, min(2, max(1, remaining_high))
        level = "decision_authority"
        decision_reason = "A senior executive has been interviewed, but their final decision rights are unverified."
    elif "hiring_manager" in has and "stakeholder" in has:
        remaining_low, remaining_high = 1, min(2, max(2, remaining_high))
        level = "stakeholder_progression"
        decision_reason = "The hiring manager and another stakeholder/panel have already met the candidate."
    elif "hiring_manager" in has:
        remaining_low = min(1, remaining_low)
        remaining_high = min(3, max(1, remaining_high))
        level = "stakeholder_progression"
        decision_reason = "The hiring manager has been interviewed; a further stakeholder/final round may follow."
    elif "recruiter" in has:
        remaining_low = max(1, remaining_low)
        remaining_high = max(remaining_low, remaining_high)
        level = "recruiter_only"
        decision_reason = "A recruiter conversation alone does not establish hiring-manager or decision-maker approval."
    elif completed:
        level = "count_only"
        if completed >= high:
            remaining_high = max(1, remaining_high)
        decision_reason = "Completed rounds are verified, but interviewer decision authority is not established."

    # A future interview date is confirmed on the live forecast, not completed.
    if process.get("next_interview"):
        remaining_low = max(1, remaining_low)
        remaining_high = max(1, remaining_high)
        decision_reason += " A forthcoming interview is scheduled, not yet completed."

    # Only an employer-confirmed, role-specific sequence can override the
    # generic estimator. Other process notes remain nonbinding context.
    if confirmed:
        if plan_total_low is not None and plan_total_high is not None:
            remaining_low = max(0, plan_total_low - completed)
            remaining_high = max(remaining_low, plan_total_high - completed)
            level = "employer_confirmed"
            decision_reason = "Employer-confirmed total interview plan takes precedence."
        elif plan_rem_low is not None and plan_rem_high is not None:
            remaining_low, remaining_high = plan_rem_low, plan_rem_high
            level = "employer_confirmed"
            decision_reason = "Employer-confirmed remaining interview plan takes precedence."
        if process.get("next_interview"):
            remaining_low = max(1, remaining_low)
            remaining_high = max(remaining_low, remaining_high)

    remaining_high = max(remaining_low, remaining_high)
    total_low, total_high = completed + remaining_low, completed + remaining_high
    confidence = (
        "high" if level == "employer_confirmed"
        else "moderate" if level == "decision_authority" and completed >= 2
        else "moderate" if level == "stakeholder_progression" and completed >= 2
        else "low"
    )
    return MTOEstimate(
        total_low=total_low, total_high=total_high,
        remaining_low=remaining_low, remaining_high=remaining_high,
        confidence=confidence, evidence_level=level,
        explanation=(
            f"Role baseline: {family} ({low}–{high} meetings). "
            f"{completed} distinct meeting(s) recorded as attended. "
            f"{decision_reason} "
            "Conditional meetings-to-decision range, not an offer likelihood."
        ),
    )
