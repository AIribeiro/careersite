"""Pure evidence-aware recruiting journey calculations.

A calendar invite is a planned milestone, never attendance proof. Dates from
estimated application evidence cannot be used for precise elapsed-day KPIs.
Separate opportunity identities prevent employer-level accidental merges.
"""
from __future__ import annotations

from datetime import date, datetime
from statistics import median
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Stockholm")
MEETING_TYPES = {"interview", "recruiter_screening", "hiring_manager"}
STATUS_LABELS = {
    "attended": "Completed · confirmed",
    "unverified": "Calendar evidence only",
    "cancelled": "Cancelled",
    "no_show": "Did not take place",
}


def as_day(value) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(TZ).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def elapsed(start, end, *, reliable=True) -> int | None:
    a, b = as_day(start), as_day(end)
    if not a or not b or b < a or not reliable:
        return None
    return (b - a).days


def application_reliable(opportunity: dict) -> bool:
    return bool(opportunity.get("application_date")) and opportunity.get(
        "application_date_basis"
    ) in ("confirmed_submission", "candidate_reported")


def stage_label(row: dict) -> str:
    kind = row.get("meeting_type")
    prefix = {
        "recruiter_screening": "Recruiter screening",
        "hiring_manager": "Hiring leader interview",
        "interview": "Interview",
        "networking": "Introduction",
    }.get(kind, "Meeting")
    stage = row.get("stage")
    return f"Round {stage} · {prefix}" if stage else f"{prefix} · round not verified"


def meeting_state(row: dict, now: datetime) -> str:
    attendance = row.get("attendance")
    if attendance in ("attended", "cancelled", "no_show"):
        return STATUS_LABELS[attendance]
    scheduled = as_day(row.get("scheduled_date"))
    raw = row.get("starts_at")
    if raw:
        try:
            timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if timestamp.tzinfo and timestamp.astimezone(TZ) >= now:
                return "Scheduled · upcoming"
        except ValueError:
            pass
    if scheduled and scheduled > now.date():
        return "Scheduled · upcoming"
    if scheduled == now.date() and not raw:
        return "Scheduled today · time unknown"
    return "Past invitation · not attendance-verified"


def _chronological(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda r: (as_day(r.get("scheduled_date")) or date.max,
                       str(r.get("starts_at") or ""), r.get("id") or 0),
    )


def journey(opportunity: dict, meetings: list[dict], now: datetime) -> dict:
    """Return milestones without presuming a round occurred or offer exists.

    Elapsed days are calendar days; an application timestamp of unknown,
    imputed or estimated origin never generates an exact elapsed KPI.
    """
    meetings = _chronological([
        row for row in meetings
        if row.get("opportunity_id") == opportunity.get("id")
    ])
    applied = as_day(opportunity.get("application_date"))
    reliable = application_reliable(opportunity)
    offer = as_day(opportunity.get("offer_date"))
    decision = as_day(opportunity.get("decision_date"))
    events = []
    if applied:
        events.append({
            "kind": "application", "date": applied, "label": "Application recorded",
            "state": "Confirmed submission" if opportunity.get("application_date_basis") ==
            "confirmed_submission" else "Reported / estimated date",
            "source": opportunity.get("application_evidence") or "Date evidence not recorded",
            "round": None,
        })
    for meeting in meetings:
        day = as_day(meeting.get("scheduled_date"))
        if not day:
            continue
        events.append({
            "kind": "meeting", "date": day, "label": stage_label(meeting),
            "state": meeting_state(meeting, now),
            "source": meeting.get("source_kind") or "Not specified",
            "round": meeting.get("stage"),
            "meeting_id": meeting.get("id"),
            "attendance": meeting.get("attendance"),
        })
    if decision:
        events.append({
            "kind": "decision", "date": decision,
            "label": "Employer decision" if opportunity.get("outcome") != "rejected" else "Employer rejection",
            "state": opportunity.get("outcome") or "Unknown",
            "source": opportunity.get("decision_evidence") or "Source unknown", "round": None,
        })
    if offer:
        events.append({
            "kind": "offer", "date": offer, "label": "Offer received",
            "state": "Offer evidenced",
            "source": opportunity.get("offer_evidence") or "Source unknown", "round": None,
        })
    order = {"application": 0, "meeting": 1, "decision": 2, "offer": 3}
    events.sort(key=lambda r: (r["date"], order[r["kind"]], r.get("meeting_id") or 0))
    prev = None
    for event in events:
        event["from_application"] = elapsed(applied, event["date"], reliable=reliable)
        event["from_previous"] = elapsed(prev, event["date"]) if prev else None
        event["to_offer"] = (
            elapsed(event["date"], offer)
            if offer and event["kind"] in ("meeting", "application") else None
        )
        # A confirmed past interview and a planned invitation are distinct.
        event["confirmed"] = event["kind"] == "meeting" and event.get("attendance") == "attended"
        prev = event["date"]
    meeting_events = [e for e in events if e["kind"] == "meeting"
                      and e.get("attendance") not in ("cancelled", "no_show")]
    by_round = {}
    for event in meeting_events:
        if event.get("round") and event["round"] not in by_round:
            by_round[event["round"]] = event
    confirmed = [e for e in meeting_events if e["confirmed"]]
    first_confirmed = next(
        (e for e in confirmed if e.get("round") == 1), None
    ) or (confirmed[0] if confirmed and all(e.get("round") is None for e in confirmed) else None)
    return {
        "opportunity": opportunity,
        "meetings": meetings,
        "events": events,
        "by_round": by_round,
        "meeting_events": meeting_events,
        "confirmed": confirmed,
        "application_date": applied,
        "application_reliable": reliable,
        "offer_date": offer,
        "decision_date": decision,
        "first_confirmed": first_confirmed,
        "days_to_first_confirmed": (
            elapsed(applied, first_confirmed["date"], reliable=reliable)
            if first_confirmed else None
        ),
        "days_application_to_offer": elapsed(applied, offer, reliable=reliable),
        "days_application_to_decision": elapsed(applied, decision, reliable=reliable),
        "days_decision_after_latest_confirmed": (
            elapsed(confirmed[-1]["date"], decision)
            if decision and confirmed else None
        ),
    }


def cohort_metrics(journeys: list[dict]) -> dict:
    """Aggregate only verified attendance + credible application chronology."""
    first_durations = [j["days_to_first_confirmed"] for j in journeys
                       if j["days_to_first_confirmed"] is not None
                       and j["opportunity"].get("application_date_basis") == "confirmed_submission"]
    offer_durations = [j["days_application_to_offer"] for j in journeys
                       if j["days_application_to_offer"] is not None
                       and j["opportunity"].get("application_date_basis") == "confirmed_submission"]
    adjacent = []
    for j in journeys:
        by_round = {e["round"]: e for e in j["confirmed"] if e.get("round")}
        for ordinal in sorted(by_round):
            if ordinal + 1 in by_round:
                days = elapsed(by_round[ordinal]["date"], by_round[ordinal + 1]["date"])
                if days is not None:
                    adjacent.append(days)
    return {
        "processes": len(journeys),
        "multi_round_processes": sum(
            len({e.get("round") for e in j["meeting_events"] if e.get("round")}) > 1
            for j in journeys
        ),
        "completed_interviews": sum(len(j["confirmed"]) for j in journeys),
        "median_days_to_first": median(first_durations) if first_durations else None,
        "first_sample": len(first_durations),
        "median_days_between_completed_rounds": median(adjacent) if adjacent else None,
        "round_sample": len(adjacent),
        "median_days_to_offer": median(offer_durations) if offer_durations else None,
        "offer_sample": len(offer_durations),
        "offers_recorded": sum(bool(j["offer_date"]) for j in journeys),
    }


def comparison_rows(journeys: list[dict]) -> list[dict]:
    result = []
    for j in journeys:
        op = j["opportunity"]
        applied = j["application_date"]
        basis = op.get("application_date_basis")
        def round_metric(n):
            event = j["by_round"].get(n)
            if not event:
                return "—"
            days = event.get("from_application")
            if days is None:
                return "Date unknown"
            suffix = "held" if event["confirmed"] else "planned" if event["state"].startswith("Scheduled") else "unverified"
            return f"{days} d · {suffix}"
        result.append({
            "Role": op.get("role_title") or "Unknown",
            "Employer": op.get("employer") or "Unknown",
            "Applied": str(applied) if applied else "Not evidenced",
            "Round 1": round_metric(1),
            "Round 2": round_metric(2),
            "Highest round": max(j["by_round"]) if j["by_round"] else "Not recorded",
            "Interviews confirmed": len(j["confirmed"]),
            "Application → offer": (
                f"{j['days_application_to_offer']} d"
                if j["days_application_to_offer"] is not None else "—"
            ),
            "Outcome": str(op.get("outcome") or "unknown").replace("_", " ").title(),
            "Basis": basis,
        })
    return result
