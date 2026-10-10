"""Weekly offer/start planning windows and an explicit evidence-quality index.

The event-time curve is uncalibrated; weekly values are scenario-derived masses,
NOT backtested personal probabilities. Calendar-week aggregation is derived from
the unchanged cumulative scenario curve, avoiding invented day-of-week effects.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import isfinite


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _iso_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _weekly_masses(day_masses: dict[date, float]) -> list[dict]:
    totals: dict[date, float] = defaultdict(float)
    for when, mass in day_masses.items():
        if mass > 0:
            totals[_iso_week_start(when)] += mass
    return [
        {"from": start.isoformat(),
         "to": (start + timedelta(days=6)).isoformat(),
         "model_week_pct": round(100 * _clamp(mass), 2)}
        for start, mass in sorted(totals.items())
    ]


def _daily_offer_masses(curve: list[dict], as_of: date) -> dict[date, float]:
    """Interpolate *within* existing weekly probability mass, no weekday claims."""
    rows = sorted((int(r["Days"]), float(r["Current pace"]))
                  for r in curve if "Days" in r and "Current pace" in r)
    if len(rows) < 2 or rows[0][0] != 0:
        return {}
    daily = {}
    for (start_day, start_probability), (end_day, end_probability) in zip(rows, rows[1:]):
        interval = end_day - start_day
        if interval <= 0:
            continue
        # Distribute the existing 7-day likelihood increase evenly across
        # that interval: do NOT infer Monday/Friday hiring preferences.
        daily_share = max(0.0, end_probability - start_probability) / interval
        for offset in range(start_day + 1, end_day + 1):
            daily[as_of + timedelta(days=offset)] = daily_share
    return daily


def peak_weeks(curve: list[dict], as_of: date, limit: int = 3) -> dict:
    """Top ISO weeks from the central offer scenario and a start-delay mixture."""
    if not curve:
        return {"offers": [], "starts": [], "offer_weeks": [], "start_weeks": []}
    offer_days = _daily_offer_masses(curve, as_of)
    if not offer_days:
        return {"offers": [], "starts": [], "offer_weeks": [], "start_weeks": []}
    # A provisional first-day delay of 21–56 days, peaking near 35 days.
    # This is a scenario assumption and is NOT fitted from job-start records.
    delays = [(d, max(0.01, 1 - abs(d - 35) / 21)) for d in range(21, 57)]
    total_weight = sum(weight for _, weight in delays)
    start_days = defaultdict(float)
    for offer_day, mass in offer_days.items():
        for lag, weight in delays:
            start_days[offer_day + timedelta(days=lag)] += mass * weight / total_weight
    offer_weeks = _weekly_masses(offer_days)
    start_weeks = _weekly_masses(start_days)
    ranked_offers = sorted(offer_weeks, key=lambda p: (-p["model_week_pct"], p["from"]))[:limit]
    ranked_starts = sorted(start_weeks, key=lambda p: (-p["model_week_pct"], p["from"]))[:limit]
    # Shares are model weights (not real population percentages).
    return {"offers": ranked_offers, "starts": ranked_starts,
            "offer_weeks": offer_weeks, "start_weeks": start_weeks,
            "start_delay": "21–56 days; weight highest near day 35"}


def reliability_index(sources: dict, stages: list[dict], drivers: dict) -> dict:
    """Transparent 0–100 evidence-coverage index, never 'chance of offer'.

    Until an independently backtested validation exists, cap the score at 55%.
    Offer counts alone do not establish accuracy.
    """
    def num(field: str) -> float:
        try:
            v = float(sources.get(field) or 0)
            return max(0., v) if isfinite(v) else 0.
        except (ValueError, TypeError):
            return 0.

    observed_offers = num("recorded_offer_events")
    advanced = sum(p.get("stage") in ("interview", "progression") for p in stages)
    recent = sum(int(p.get("age") or 0) <= 35 for p in stages)
    coverage = sources.get("event_coverage")
    try:
        coverage = min(1., max(0., float(coverage))) if coverage is not None else 0.
    except (TypeError, ValueError):
        coverage = 0.
    detail = {
        "Dated search events": 16 * min(1., num("primary_events") / 40),
        "Historical coverage": 10 * min(1., num("job_history_days") / 90),
        "Linked process coverage": 18 * coverage,
        "Documented interviews": 14 * min(1., advanced / 4),
        "Recruiter interactions": 12 * min(1., num("mature_with_human_contact") / 5),
        "Recent live processes": 12 * min(1., recent / 6),
        "Portfolio data coverage": 4 if (drivers.get("portfolio") or {}).get("qualified_actions_available") else 0,
        "Market data coverage": 4 if (drivers.get("market") or {}).get("indicators_reviewed", 0) >= 3 else 0,
        "Historical offer outcomes": 10 * min(1., observed_offers / 5),
    }
    score = round(min(sum(detail.values()), 55))
    grade = "Limited evidence" if score < 35 else ("Developing evidence" if score < 55 else "Useful evidence; not validated")
    return {"score_pct": score, "grade": grade,
            "components": {k: round(v, 1) for k, v in detail.items()},
            "calibrated": False,
            "definition": "Transparency score for documented evidence and coverage, not statistical forecast accuracy or the chance of receiving an offer."}
