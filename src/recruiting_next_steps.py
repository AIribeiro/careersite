"""Evidence-first hiring process next-step planner (no calibrated offer probabilities).

Four evidence types are intentionally distinct:
1. Calendar events establish scheduled meetings, NOT that they happened.
2. Recruiter-indicated response windows are not guaranteed.
3. Heuristic windows are a planning aid learned from this candidate's sparse
   historical transitions and employer decisions, NOT confidence intervals.
4. Candidate follow-up dates are recommended actions, NOT company commitments.

All events are tied to opportunity IDs. Expired windows are not slid into the
future to create the appearance of activity. No inference creates an offer.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from statistics import median

from recruiting_journeys import as_day, MEETING_TYPES

MODEL_VERSION = "recruiter-next-step-planner-v1.0"
LABELS = {
    "confirmed": "Confirmed appointment",
    "indicated": "Employer-indicated reply",
    "estimated": "Historical timing estimate",
    "action": "Your follow-up checkpoint",
}


def working_day_on_or_after(value: date) -> date:
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def working_days_after(day: date, n: int) -> date:
    value = day
    for _ in range(max(0, n)):
        value += timedelta(days=1)
        value = working_day_on_or_after(value)
    return value


def _nearest_rank(values: list[int], p: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    position = max(0, min(len(ordered) - 1, round(p * (len(ordered) - 1))))
    return ordered[position]


def timing_sample(opportunities: list[dict], meetings: list[dict],
                  signals: list[dict]) -> dict:
    """Use actual elapsed days; never import external market rates as facts."""
    meetings_by_op: dict[int, list[dict]] = {}
    for m in meetings:
        if m.get("opportunity_id") is not None and m.get("attendance") == "attended":
            meetings_by_op.setdefault(int(m["opportunity_id"]), []).append(m)
    decision_lags: list[int] = []
    next_stage_lags: list[int] = []
    for opp in opportunities:
        decision = as_day(opp.get("decision_date"))
        held = sorted(
            (as_day(m.get("scheduled_date")) for m in
             meetings_by_op.get(int(opp["id"]), [])
             if as_day(m.get("scheduled_date"))),
        )
        if decision and held and decision >= held[-1]:
            decision_lags.append((decision - held[-1]).days)
        # A completed interview to next completed interview is a transition
        # observation, not a prediction that future processes will progress.
        distinct = sorted(set(
            (int(m["stage"]), as_day(m.get("scheduled_date")))
            for m in meetings_by_op.get(int(opp["id"]), [])
            if m.get("stage") and as_day(m.get("scheduled_date"))
        ))
        if len(distinct) >= 2:
            for i in range(1, len(distinct)):
                if distinct[i][0] == distinct[i-1][0] + 1:
                    next_stage_lags.append((distinct[i][1] - distinct[i-1][1]).days)
    for s in signals:
        if s.get("kind") != "stage_progression":
            continue
        day = as_day(s.get("anchor_date"))
        held = [
            as_day(m.get("scheduled_date"))
            for m in meetings_by_op.get(int(s["opportunity_id"]), [])
            if as_day(m.get("scheduled_date")) and
            as_day(m.get("scheduled_date")) < day
        ] if day else []
        if held:
            next_stage_lags.append((day - max(held)).days)
    # Events from the same process may be genuinely distinct: invite date
    # versus subsequent actual second interview. Count each kind separately.
    values = sorted(n for n in decision_lags + next_stage_lags if n >= 0)
    return {
        "n": len(values), "decision_n": len(decision_lags),
        "progression_n": len(next_stage_lags),
        "minimum": min(values) if values else None,
        "lower": _nearest_rank(values, 0.25),
        "typical": median(values) if values else None,
        "upper": _nearest_rank(values, 0.75),
        "maximum": max(values) if values else None,
        "model_version": MODEL_VERSION,
    }


def _item(opp: dict, kind: str, label: str, start: date,
          end: date, *, evidence: str, conditional: str = "",
          next_action: bool = False) -> dict:
    if end < start:
        raise ValueError("Next-step end predates start")
    return {
        "opportunity_id": int(opp["id"]),
        "employer": opp["employer"],
        "role": opp["role_title"],
        "kind": kind,
        "label": label,
        "start": start,
        "end": end,
        "evidence": evidence,
        "conditional": conditional,
        "candidate_action": next_action,
        "type_label": LABELS[kind],
        "model_version": MODEL_VERSION,
    }


def make_plan(opportunities: list[dict], meetings: list[dict],
              signals: list[dict], today: date) -> dict:
    history = timing_sample(opportunities, meetings, signals)
    lo = max(3, history["lower"] or 7)
    hi = max(lo + 7, history["upper"] or 21)
    typical = int(round(history["typical"] or 14))
    signal_by_op: dict[int, list[dict]] = {}
    meetings_by_op: dict[int, list[dict]] = {}
    for s in signals:
        signal_by_op.setdefault(int(s["opportunity_id"]), []).append(s)
    for m in meetings:
        if m.get("opportunity_id") is not None:
            meetings_by_op.setdefault(int(m["opportunity_id"]), []).append(m)

    items: list[dict] = []
    active: list[dict] = []
    watch: list[dict] = []
    for op in opportunities:
        outcome = op.get("outcome")
        op_id = int(op["id"])
        opmeet = meetings_by_op.get(op_id, [])
        if outcome not in ("in_progress",):
            if outcome == "unknown":
                watch.append(op)
            continue
        active.append(op)
        future = sorted(
            (m for m in opmeet
             if as_day(m.get("scheduled_date")) and
             as_day(m.get("scheduled_date")) >= today
             and m.get("attendance") not in ("attended", "cancelled", "no_show")
             and m.get("meeting_type") in MEETING_TYPES),
            key=lambda m: as_day(m["scheduled_date"]),
        )
        held = sorted(
            (m for m in opmeet if m.get("attendance") == "attended"
             and as_day(m.get("scheduled_date"))),
            key=lambda m: as_day(m["scheduled_date"]),
        )
        promise = next(
            (s for s in sorted(signal_by_op.get(op_id, []),
                               key=lambda s: s.get("anchor_date") or "", reverse=True)
             if s.get("kind") == "employer_response_window"
             and s.get("window_start") and s.get("window_end")),
            None,
        )
        referral = next((s for s in signal_by_op.get(op_id, [])
                         if s.get("kind") == "referral_intent"), None)
        # Planned appointment is the only exact company meeting shown.
        for appointment in future:
            day = as_day(appointment["scheduled_date"])
            items.append(_item(
                op, "confirmed",
                f"Round {appointment['stage']} interview" if appointment.get("stage")
                else "Recruiting meeting",
                day, day,
                evidence=(appointment.get("evidence_note") or
                          "Outlook calendar: appointment only, not completion"),
                conditional="The meeting is booked, but has not yet occurred.",
            ))

        if promise:
            start, end = as_day(promise["window_start"]), as_day(promise["window_end"])
            if end >= today:
                items.append(_item(
                    op, "indicated", promise["event_label"], start, end,
                    evidence=promise["source_reference"],
                    conditional="A recruiter indication, not a guaranteed reply or new interview.",
                ))
            else:
                # Keep an overdue commitment visible; never move the window.
                items.append(_item(
                    op, "indicated", "Unconfirmed past reply window",
                    start, end, evidence=promise["source_reference"],
                    conditional="This window has elapsed without a recorded reply; verify status.",
                ))
            checkpoint = working_day_on_or_after(end + timedelta(days=1))
            items.append(_item(
                op, "action", "Check in if no recruiter reply",
                checkpoint, checkpoint, evidence=promise["source_reference"],
                conditional="Do not contact sooner unless the employer initiates.",
                next_action=True,
            ))
        elif future:
            last_future = as_day(future[-1]["scheduled_date"])
            if last_future:
                items.append(_item(
                    op, "estimated", "Possible feedback after scheduled interview",
                    working_day_on_or_after(last_future + timedelta(days=lo)),
                    working_day_on_or_after(last_future + timedelta(days=hi)),
                    evidence=(f"Within-person historical transitions, n={history['n']}: "
                              f"middle observed range {lo}–{hi} calendar days. "
                              "Not an empirically calibrated probability interval."),
                    conditional="Only relevant if the scheduled interview actually takes place.",
                ))
                checkpoint = working_days_after(last_future, 5)
                items.append(_item(
                    op, "action", "Check in after interview if no update",
                    checkpoint, checkpoint,
                    evidence="Standard candidate planning checkpoint: five weekdays after a held interview.",
                    conditional="Only if the meeting took place and the recruiter gave no later date.",
                    next_action=True,
                ))
        elif held:
            last = as_day(held[-1]["scheduled_date"])
            if last:
                start = working_day_on_or_after(last + timedelta(days=lo))
                end = working_day_on_or_after(last + timedelta(days=hi))
                items.append(_item(
                    op, "estimated",
                    "Possible feedback or next-stage invitation",
                    start, end,
                    evidence=(f"Within-person historical transitions, n={history['n']}: "
                              f"middle observed range {lo}–{hi} calendar days. "
                              "Outcomes cannot be inferred."),
                    conditional=("If shortlisted, may prompt a further interview; "
                                 "the interview itself is not booked."),
                ))
                checkpoint = working_days_after(last, 5)
                items.append(_item(
                    op, "action", "Check in if no update",
                    checkpoint, checkpoint,
                    evidence="Five-weekday follow-up planning rule, not a recruiter promise.",
                    next_action=True,
                ))
        elif referral:
            anchor = as_day(referral.get("anchor_date"))
            start, end = working_days_after(anchor, 5), working_days_after(anchor, 10)
            items.append(_item(
                op, "action",
                "Ask for status of separate AI role referral",
                start, end, evidence=referral.get("source_reference") or "",
                conditional="No interview or reply date has been promised for this separate vacancy.",
                next_action=True,
            ))
        else:
            # Application only: no scientifically supported employer milestone.
            applied = as_day(op.get("application_date"))
            if applied:
                due = working_days_after(applied, 10)
                items.append(_item(
                    op, "action", "Verify application status",
                    due, due,
                    evidence="Candidate follow-up after ten weekdays, not employer forecast.",
                    next_action=True,
                ))

    items.sort(key=lambda i: (i["start"], {"confirmed": 0, "indicated": 1,
                                          "estimated": 2, "action": 3}[i["kind"]],
                              i["employer"]))
    return {
        "items": items,
        "active": active,
        "watch": watch,
        "historical": history,
        "as_of": today,
        "version": MODEL_VERSION,
    }
