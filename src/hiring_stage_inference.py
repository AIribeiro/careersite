"""Evidence-based naming of the current hiring stage, independent of employer.

The scored forecast stage is intentionally not replaced here: this resolves
human-facing labels and source state without inventing an interview or offer.
The mailbox is read by an authorized ingestion workflow, not by Streamlit.
"""
from __future__ import annotations

from datetime import date
import re


def _norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold().replace("-", " ")).strip()


def _day(value: object) -> str:
    v = str(value or "")[:10]
    try:
        return date.fromisoformat(v).isoformat()
    except (ValueError, TypeError):
        return ""


def classify_stage(text: str, *, meeting_type: str = "", interviewer_role: str = "") -> str | None:
    """Return a controlled display label, never arbitrary text from an email."""
    value = _norm(text)
    role = _norm(interviewer_role)
    kind = _norm(meeting_type)
    if ("culture fit" in value or "cultural fit" in value
            or "culture interview" in value or "values interview" in value):
        return "Final culture fit interview" if re.search(r"\\bfinal\\b", value) else "Culture fit interview"
    if re.search(r"\b(case study|case interview|business case|take home case)\b", value):
        return "Case interview"
    if "technical interview" in value or "technical assessment" in value:
        return "Technical interview"
    if "panel interview" in value or "interview panel" in value or "panel" in role:
        return "Panel interview"
    if "partner interview" in value:
        return "Partner interview"
    if "competence interview" in value or "competency interview" in value:
        return "Competence interview"
    if "stakeholder interview" in value:
        return "Stakeholder interview"
    if "hiring manager" in value or kind == "hiring_manager":
        return "Hiring manager interview"
    if ("recruiter screening" in value or "screening interview" in value
            or "talent acquisition interview" in value or kind == "recruiter_screening"):
        return "Recruiter screening"
    if "chief ai officer" in role:
        return "Chief AI Officer interview"
    if re.search(r"\bfinal (round|interview|stage)\b", value):
        return "Final interview"
    if "third interview" in value or "third round" in value:
        return "Third interview"
    if "second interview" in value or "second round" in value or "2nd stage" in value:
        return "Second interview"
    if "interview" in value or kind == "interview":
        return "Interview"
    return None


def resolve_stage(*, forecast_stage: str = "", outcome: str = "",
                  attended: list[dict] | None = None,
                  scheduled: list[dict] | None = None,
                  signals: list[dict] | None = None,
                  today: str | None = None) -> dict:
    """Resolve specific stage from newest attributable progression after last held round.

    Order: recruiter-confirmed progression > explicit calendar stage > next
    scheduled meeting > last confirmed attended meeting > generic forecast.
    Conditional stages and assessments are never promoted into booked interviews.
    """
    now = _day(today) or date.today().isoformat()
    outcome_norm = _norm(outcome)
    if outcome_norm in ("rejected", "withdrawn", "closed"):
        return {"label": outcome_norm.capitalize(), "state": "closed",
                "source": "employer outcome", "date": None, "confidence": "high"}
    if outcome_norm == "offer" or forecast_stage == "verified_offer":
        return {"label": "Offer received", "state": "confirmed",
                "source": "verified offer", "date": None, "confidence": "high"}

    held = sorted((m for m in attended or []
                   if isinstance(m, dict) and m.get("attendance") == "attended"
                   and _day(m.get("scheduled_date")) <= now),
                  key=lambda r: _day(r.get("scheduled_date")))
    latest_held = _day(held[-1].get("scheduled_date")) if held else ""
    planned = sorted((m for m in scheduled or []
                      if isinstance(m, dict) and m.get("attendance") == "unverified"
                      and _day(m.get("scheduled_date")) >= latest_held
                      and m.get("meeting_type") != "networking"),
                     key=lambda r: _day(r.get("scheduled_date")))
    planned_next = next((m for m in planned if _day(m.get("scheduled_date")) >= now), None)
    planned_any = planned_next or (planned[-1] if planned else None)
    choices = []
    for s in signals or []:
        if not isinstance(s, dict) or s.get("kind") != "stage_progression":
            continue
        when = _day(s.get("anchor_date"))
        if not when or when <= latest_held:
            continue
        label = classify_stage(str(s.get("event_label") or ""))
        raw = _norm(s.get("event_label"))
        if not label or not any(w in raw for w in ("invit", "schedul", "confirm", "next stage", "advance", "progress")):
            continue
        kind = _norm(s.get("source_kind"))
        strength = 3 if kind in ("outlook", "gmail") else 2 if kind == "calendar" else 1
        choices.append((when, strength, label, s))
    if choices:
        _, strength, label, signal = max(choices, key=lambda p: (p[0], p[1]))
        appointment = _day(planned_any.get("scheduled_date")) if planned_any else ""
        # A recruiter option window is NOT a booked date. Only meeting evidence
        # or an explicitly recorded confirmed appointment establishes booking.
        status = "scheduled" if appointment and appointment >= now else (
            "attendance_unverified" if appointment else "invited"
        )
        return {"label": label, "state": status,
                "date": appointment or None,
                "source": str(signal.get("source_kind") or "evidence"),
                "confidence": "high" if strength >= 3 else "moderate",
                "evidence_date": _day(signal.get("anchor_date"))}

    if planned_any:
        label = classify_stage(
            str(planned_any.get("title") or ""), meeting_type=str(planned_any.get("meeting_type") or ""),
            interviewer_role=str(planned_any.get("interviewer_role") or ""),
        ) or "Interview"
        appointment = _day(planned_any.get("scheduled_date"))
        return {"label": label,
                "state": "scheduled" if appointment >= now else "attendance_unverified",
                "date": appointment, "source": "calendar",
                "confidence": "moderate"}
    if held:
        meeting = held[-1]
        label = classify_stage(str(meeting.get("title") or ""),
                               meeting_type=str(meeting.get("meeting_type") or ""),
                               interviewer_role=str(meeting.get("interviewer_role") or "")) or "Interview"
        return {"label": f"{label} completed", "state": "completed",
                "date": _day(meeting.get("scheduled_date")), "source": "attendance evidence",
                "confidence": "moderate"}
    fallback = {
        "application_only": "Application submitted",
        "human_response": "Recruiter response received",
        "first_interview_scheduled": "First interview scheduled",
        "first_interview_completed": "First interview completed",
        "subsequent_interview_scheduled": "Subsequent interview scheduled",
        "subsequent_interview_completed": "Subsequent interview completed",
    }
    return {"label": fallback.get(forecast_stage, "Stage not verified"),
            "state": "inferred", "date": None, "source": "forecast",
            "confidence": "low"}
