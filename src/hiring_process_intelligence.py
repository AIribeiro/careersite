"""Employer-process evidence, role alignment and stale-application discipline.

These are *planning* features: stage evidence affects the model through the
existing stage-specific offer curves. Role fit and inferred company interest
stay explanatory unless an explicit, source-backed hard constraint exists.
No general sentiment or job-title keyword is a measured offer probability.
"""
from __future__ import annotations

from datetime import date
from math import exp
import re

from job_search_metrics import day, norm, process_key, progression, scheduled_interview, completed_interview

MODEL_POLICY = "process-evidence-v1"
MATERIAL_UPDATES = ("interview_invitation", "interview_scheduled", "hiring_manager_email",
                    "recruiter_invitation", "reference_check", "interview_completed")

def employer_update(row: dict) -> bool:
    direction = norm(row.get("interaction_direction"))
    if direction not in ("inbound", "two_way"):
        return False
    if row.get("response_received") is True or row.get("is_human_interaction"):
        return True
    if norm(row.get("interaction_type")) in MATERIAL_UPDATES:
        return True
    return bool(progression(row) or scheduled_interview(row))

def _field(row: dict, field: str):
    raw = row.get("raw_data") if isinstance(row.get("raw_data"), dict) else {}
    return row.get(field) if row.get(field) not in (None, "") else raw.get(field)

def role_alignment(role: str, rows: list[dict]) -> dict:
    """Minimum effective taxonomy, with *explicit* qualification gates only."""
    text = norm(role)
    primary = bool(re.search(
        r"\bai\b|artificial intelligence|genai|data.*analytics|"
        r"data.*governance|analytics.*leader|intelligent automation",
        text,
    ))
    strategic = bool(re.search(
        r"\b(head|director|lead|vp|vice president|chief|principal|senior manager)\b"
        r"|ai strategist|ai-strateg|ai-ansvarig",
        text,
    ))
    implementation_dominant = bool(re.search(
        r"machine learning engineer|data scientist|data engineer|"
        r"software developer|full.stack engineer|scrum master|"
        r"technical product owner|data analyst",
        text,
    ))
    attrs = {}
    for r in rows:
        for k in ("compensation_fit", "language_requirements_fit",
                  "mandate_quality", "executive_sponsorship", "relocation_feasible"):
            value = _field(r,k)
            if value is not None:
                attrs[k] = str(value).strip().lower()
    excluded = any(attrs.get(k) in ("no","incompatible","below_floor","not_feasible")
                   for k in ("compensation_fit","language_requirements_fit"))
    return {
        "category": ("strong_target" if primary and strategic and not implementation_dominant
                     else "adjacent_or_mixed" if primary and not implementation_dominant
                     else "outside_primary_target"),
        "explicit_hard_constraint": excluded,
        "recorded_requirements": attrs,
        "numeric_offer_effect": 0,
        "reason": ("Explicit language/pay incompatibility" if excluded else
                   "Scope and selection fit require employer-specific verification"),
    }

def process_health(rows: list[dict], as_of: date, stage: str,
                   stage_day: date, state: str) -> dict:
    """Decay abandoned application-only paths; never reset stage clock on followup.

    Do not treat lack of response as a rejection. The value is a conservative
    opportunity-planning discount, not measured failure probability.
    """
    employer_days = [day(r.get("event_date")) for r in rows
                     if employer_update(r) and day(r.get("event_date"))
                     and day(r.get("event_date")) <= as_of]
    last_employer = max(employer_days) if employer_days else None
    if stage not in ("application", "conversation"):
        # Interviewed or advanced processes remain individually visible;
        # date distribution is still based on time in the latest stage.
        freshness = 1.0
    elif stage == "conversation":
        # Some delay is normal after authentic two-way contact.
        anchor = last_employer or stage_day
        inactive_days = max(0, (as_of - anchor).days)
        freshness = exp(-max(0, inactive_days - 45) / 75)
    else:
        inactive_days = max(0, (as_of - (last_employer or stage_day)).days)
        # No reply beyond 30 days is uncertainty, not proof of closure.
        freshness = exp(-max(0, inactive_days - 30) / 45)
    details = []
    for r in rows:
        if day(r.get("event_date")) and day(r["event_date"]) <= as_of:
            details.append(norm(_field(r,"stage_outcome") or
                                _field(r,"activity") or ""))
    verified_pause = any(re.search(
        r"\b(?:hiring|recruitment|requisition)\s+"
        r"(?:frozen|freeze|paused|on hold)\b",x) for x in details)
    if verified_pause:
        freshness *= 0.2
    return {
        "freshness_weight":round(max(.04, min(1., freshness)), 4),
        "last_employer_update":last_employer.isoformat() if last_employer else None,
        "days_since_employer_update": (as_of-last_employer).days if last_employer else None,
        "documented_pause":verified_pause,
        "status": ("documented_hiring_pause" if verified_pause
                   else "stale_application" if stage=="application" and freshness<.50
                   else "active_employer_contact" if last_employer else "unverified"),
    }

def process_intelligence(rows: list[dict], as_of: date, stage: str,
                         stage_day: date, state: str, role: str) -> dict:
    health=process_health(rows,as_of,stage,stage_day,state)
    fit=role_alignment(role,rows)
    # Do not award a discretionary employer 'enthusiasm' bonus for nonverbal
    # sentiment. Documented next rounds are already counted in stage.
    return {"health":health,"fit":fit,
            "evidence_confidence":("employer_confirmed" if health["last_employer_update"]
                                   else "application_only"),
            "employer_investment_status":("not_documented" if not health["documented_pause"]
                                          else "documented_pause"),
            "numeric_fit_effect":0}
