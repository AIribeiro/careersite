"""Hiring Predictor Beta v3.1: transparent, evidence-sensitive *planning* scenarios.

No personal offer probabilities are calibrated: this individual's history has no
observed offers. Dates are conditional illustrations, never statistical forecasts.
An observed contact rate affects future application-funnel assumptions.
Selected portfolio engagement and independent Swedish labour-market indicators
pragmatically shift future opportunities using capped, disclosed heuristic
weights; these are not proof of causality.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import exp
import re

from job_search_metrics import (
    analyze, canonical_events, completed_interview, day, offer, process_key,
    progression,
)
from hiring_forecast_signals import forecast_drivers
from hiring_forecast_windows import peak_weeks, reliability_index

MODEL_VERSION = "hiring-beta-3.2"
HORIZON_DAYS = 364
SCENARIOS = {"Conservative": 0.55, "Current pace": 1.0, "Faster conversion": 1.5}
# Purely illustrative offer propensity *given each hiring stage*, NOT observed
# Sweden-wide or applicant-specific base rates.
STAGES = {
    "progression": (0.32, 42),
    "interview": (0.18, 63),
    "conversation": (0.065, 91),
    "application": (0.012, 126),
}
MATURE_DAYS = 35
MODEL_MAX_APPLICATIONS_PER_WEEK = 5.25
START_DELAY_DAYS = (21, 56)


def _bounded(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def _cdf(days: float, scale: int) -> float:
    """Illustrative elapsed-time response profile."""
    return 0.0 if days <= 0 else 1.0 - exp(-((days / scale) ** 1.6))


def _stage_evidence(row: dict) -> str | None:
    """Only documented two-way contact counts as a conversation.

    Scheduled interviews and outbound follow-ups alone are *not* completed
    interviews or replies. A completed-interview status is accepted only on a
    dated event carrying an interview flag.
    """
    if progression(row):
        return "progression"
    status = str(row.get("status") or "").casefold()
    activity = str(row.get("activity") or "").casefold()
    if completed_interview(row) or (row.get("is_interview") and
            (re.search(r"interview\s+(completed|held|conducted)", status) or
             re.search(r"interview\s+(completed|held|conducted)", activity))):
        return "interview"
    direction = str(row.get("interaction_direction") or "").casefold()
    if row.get("is_human_interaction") and (
        direction in ("inbound", "two_way") or row.get("response_received") is True
    ):
        return "conversation"
    if row.get("is_application"):
        return "application"
    return None


def _stage_for_process(rows: list[dict]) -> tuple[str, date] | None:
    """Strongest recorded stage, dated at that stage rather than the last follow-up."""
    stage_rank = {stage: rank for rank, stage in
                  enumerate(("application", "conversation", "interview", "progression"))}
    selected = []
    for row in rows:
        stage = _stage_evidence(row)
        when = day(row.get("event_date"))
        if stage and when:
            selected.append((stage_rank[stage], when, stage))
    if not selected:
        return None
    _, when, stage = max(selected, key=lambda item: (item[0], item[1]))
    return stage, when


def _as_of_events(jobs: list[dict], as_of: date) -> list[dict]:
    return [r for r in canonical_events(jobs)
            if day(r.get("event_date")) and day(r["event_date"]) <= as_of]


def _official_application_total(jobs: list[dict], as_of: date) -> int | None:
    snapshots = [r for r in jobs if r.get("record_type") == "snapshot_metric"
                 and r.get("metric_name") == "Confirmed application submissions"
                 and day(r.get("snapshot_date"))
                 and day(r["snapshot_date"]) <= as_of
                 and r.get("metric_value") is not None]
    if not snapshots:
        return None
    latest = max(snapshots, key=lambda r: (str(r.get("snapshot_date")), int(r.get("id") or 0)))
    try:
        total = int(float(latest["metric_value"]))
        return total if total >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _crossing(curve: list[dict], scenario: str, threshold: float = 0.5) -> str | None:
    return next((r["Date"] for r in curve if r[scenario] >= threshold), None)


def _remaining_offer_chance(p_offer: float, stage_age: int,
                            future_days: int, scale: int) -> float:
    """Chance of an offer in the next period, conditional on no earlier offer.

    Accounts for a stage already being several weeks old, unlike the v1 model
    which incorrectly restarted the hiring clock after every follow-up.
    """
    earlier = _cdf(stage_age, scale)
    later = _cdf(stage_age + future_days, scale)
    denominator = max(1e-9, 1.0 - p_offer * earlier)
    return _bounded(p_offer * max(0.0, later - earlier) / denominator, 0.0, 0.99)


def forecast_hiring(
    jobs: list[dict], as_of: date, *,
    market_model: dict | None = None,
    portfolio_correlation: dict | None = None,
    hiring_quality: dict | None = None,
    portfolio_actions: dict | None = None,
) -> dict:
    events = _as_of_events(jobs, as_of)
    dates = [day(r["event_date"]) for r in events]
    first = min(dates) if dates else None
    report = analyze(jobs, first or as_of, as_of, False)
    grouped = defaultdict(list)
    for r in events:
        key = process_key(r)
        if key is not None:
            grouped[key].append(r)
    recorded_offers = sum(offer(r) for r in events)

    # Event-linked application processes are a subset of the official
    # application snapshot. Never equate the two or synthesize missing events.
    processes = report["processes"]
    applied = [p for p in processes if p.get("Applied")]
    recent_start = as_of - timedelta(days=27)
    prior_start = as_of - timedelta(days=55)
    last28 = sum(recent_start <= p["Applied"] <= as_of for p in applied)
    prior28 = sum(prior_start <= p["Applied"] < recent_start for p in applied)

    mature = [p for p in applied if (as_of - p["Applied"]).days >= MATURE_DAYS]
    contact_count = 0
    for p in mature:
        group = grouped.get(process_key({"employer": p["Employer"], "role": p["Role"]}), [])
        if any(_stage_evidence(e) in ("conversation", "interview", "progression")
               and day(e.get("event_date")) >= p["Applied"] for e in group):
            contact_count += 1
    observed_contact_rate = contact_count / len(mature) if len(mature) >= 8 else None
    # Stable Beta-style shrinkage: 2 contacts out of 10 hypothetical mature
    # applications. This is an explicitly disclosed smoothing assumption.
    effective_contact_rate = (contact_count + 2) / (len(mature) + 10)
    new_application_offer_rate = _bounded(
        0.002 + 0.06 * effective_contact_rate, 0.005, 0.035
    )
    raw_weekly_pace = 7 * (0.55 * last28 + 0.45 * prior28) / 28
    assumed_weekly_pace = min(MODEL_MAX_APPLICATIONS_PER_WEEK, raw_weekly_pace)
    daily_rate = assumed_weekly_pace / 7

    open_stages = []
    for p in processes:
        if p["State"] == "Closed / paused":
            continue
        key = process_key({"employer": p["Employer"], "role": p["Role"]})
        stage_info = _stage_for_process(grouped.get(key, []))
        if stage_info is None:
            continue
        stage, stage_date = stage_info
        age = (as_of - stage_date).days
        if age > 180:
            continue
        # Unresolved is not verified active; short-lived unknown histories
        # must contribute less than employer-acknowledged active processes.
        weight = 1.0 if p["State"] == "Active documented" else 0.35
        if weight:
            open_stages.append({"stage": stage, "age": age,
                                "weight": weight, "state": p["State"],
                                "stage_date": stage_date.isoformat()})

    coverage = (market_model or {}).get("coverage") or {}
    stable_market = [r for r in (market_model or {}).get("findings", [])
                     if r.get("status") == "Repeated association"
                     and r.get("outcome") in ("responses", "interviews", "progression")]
    stable_portfolio = [r for r in (portfolio_correlation or {}).get("ranked", [])
                        if r.get("status") == "Repeated association"
                        and r.get("outcome") in ("responses", "interviews", "progression")]
    quality = (hiring_quality or {}).get("quality_summary") or {}
    drivers = forecast_drivers(portfolio_correlation, portfolio_actions, market_model, as_of)
    official = _official_application_total(jobs, as_of)
    event_coverage = (len(applied) / official) if official else None
    sources = {
        "primary_events": len(events),
        "recorded_offer_events": recorded_offers,
        "tracked_processes": len(processes),
        "live_or_recent_unresolved_processes": len(open_stages),
        "applications_last_28d": last28,
        "applications_previous_28d": prior28,
        "linked_application_processes": len(applied),
        "official_application_total": official,
        "event_coverage": event_coverage,
        "mature_applied_processes": len(mature),
        "mature_with_human_contact": contact_count,
        "contact_rate": observed_contact_rate,
        "adjusted_contact_rate": effective_contact_rate,
        "assumed_weekly_pace": round(assumed_weekly_pace, 2),
        "new_application_offer_assumption": round(new_application_offer_rate, 4),
        "job_history_days": (as_of - first).days + 1 if first else 0,
        "qualified_portfolio_sessions_30d": int(quality.get("analysis_eligible_sessions") or 0),
        "portfolio_hiring_intent_actions_30d": int(quality.get("hiring_intent_sessions") or 0),
        "portfolio_repeated_associations": len(stable_portfolio),
        "market_indicator_series": int(coverage.get("indicators") or 0),
        "market_observations": int(coverage.get("observations") or 0),
        "market_repeated_associations": len(stable_market),
    }
    evidence = reliability_index(sources, open_stages, drivers)
    result = {
        "version": MODEL_VERSION, "as_of": as_of.isoformat(), "sources": sources,
        "active_stages": open_stages, "curve": [], "crossings": {},
        "reliability": evidence,
        "windows": {"offers": [], "starts": [], "offer_weeks": [], "start_weeks": []},
        "confidence": "Early estimate", "status": "insufficient",
        "drivers": drivers,
        "limitations": [
            "Qualified CV-origin traffic, source variants, target-role tags and associated recruitment campaigns receive bounded positive planning weights; they do not identify visitors.",
            "Specific Swedish job-market signals can help or hurt future opportunity estimates; their weights are heuristic, not proven effects.",
            "Only new opportunities—not hiring decisions already under way—receive portfolio/market adjustments.",
            "Offer rates and decision times remain assumptions, not calibrated personal probabilities.",
            "A formal offer and a first day of work are different events.",
        ],
    }
    # Historical offers are not evidence of being hired today. A previous
    # declined or closed offer must not permanently disable future forecasts.
    live_processes = {
        process_key({"employer": p["Employer"], "role": p["Role"]})
        for p in processes if p["State"] != "Closed / paused"
    }
    open_offer = any(
        offer(event) and process_key(event) in live_processes
        and (as_of - day(event.get("event_date"))).days <= 90
        for event in events
    )
    if open_offer:
        result["status"] = "offer_recorded"
        return result
    if len(events) < 8 or not first or (not open_stages and last28 + prior28 < 3):
        return result

    def _scenario_curve(portfolio_effect: float, market_effect: float) -> list[dict]:
        """Same base model, independently switching heuristics on and off."""
        opportunity_factor = _bounded(1.0 + portfolio_effect + market_effect, 0.82, 1.24)
        curve = []
        for t in range(0, HORIZON_DAYS + 1, 7):
            row = {"Date": (as_of + timedelta(days=t)).isoformat(), "Days": t}
            for label, multiplier in SCENARIOS.items():
                no_offer = 1.0
                for p in open_stages:
                    p_offer, scale = STAGES[p["stage"]]
                    chance = p["weight"] * _remaining_offer_chance(
                        _bounded(p_offer * multiplier, 0.0, 0.95),
                        p["age"], t, scale,
                    )
                    no_offer *= 1 - chance
                expected_new_offers = 0.0
                for elapsed in range(7, t + 1, 7):
                    expected_new_offers += (
                        7 * daily_rate * new_application_offer_rate * multiplier
                        * opportunity_factor
                        * _cdf(elapsed, STAGES["application"][1])
                    )
                no_offer *= exp(-expected_new_offers)
                row[label] = round(_bounded(1 - no_offer, 0.0, 1.0), 4)
            curve.append(row)
        return curve

    port = drivers["portfolio"]["effect"]
    market = drivers["market"]["effect"]
    curve = _scenario_curve(port, market)
    baseline_curve = _scenario_curve(0.0, 0.0)
    portfolio_curve = _scenario_curve(port, 0.0)
    market_curve = _scenario_curve(0.0, market)
    reference = {
        "base": _crossing(baseline_curve, "Current pace"),
        "portfolio_only": _crossing(portfolio_curve, "Current pace"),
        "market_only": _crossing(market_curve, "Current pace"),
        "combined": _crossing(curve, "Current pace"),
    }
    reference["portfolio_days"] = (
        (day(reference["portfolio_only"]) - day(reference["base"])).days
        if reference["portfolio_only"] and reference["base"] else None
    )
    reference["market_days"] = (
        (day(reference["market_only"]) - day(reference["base"])).days
        if reference["market_only"] and reference["base"] else None
    )
    reference["combined_days"] = (
        (day(reference["combined"]) - day(reference["base"])).days
        if reference["combined"] and reference["base"] else None
    )
    result["comparison"] = reference
    result["curve"] = curve
    result["windows"] = peak_weeks(curve, as_of)
    result["crossings"] = {label: _crossing(curve, label) for label in SCENARIOS}
    result["status"] = "scenario" if result["crossings"]["Current pace"] else "no_median"
    central = result["crossings"].get("Current pace")
    if central:
        offer_day = day(central)
        result["start_window"] = {
            "from": (offer_day + timedelta(days=START_DELAY_DAYS[0])).isoformat(),
            "to": (offer_day + timedelta(days=START_DELAY_DAYS[1])).isoformat(),
        }
    result["modelled_90d"] = next((r["Current pace"] for r in curve if r["Days"] >= 91), None)
    result["modelled_180d"] = next((r["Current pace"] for r in curve if r["Days"] >= 182), None)
    return result
