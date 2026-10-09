"""Experimental offer-date scenario model for the private Analytics Overview.

This is an assumption-led forecasting aid, NOT a calibrated probability model.
No employer decision, ATS feed, or applicant-level market probability is inferred.
Only primary job events control the numerical curve; public market and anonymous
portfolio metrics remain contextual until independent predictive validation.
"""
from __future__ import annotations

from datetime import date, timedelta
from math import exp, isfinite
from statistics import median

from job_search_metrics import analyze, canonical_events, completed_interview, day, offer

MODEL_VERSION = "hiring-beta-1"
HORIZON_DAYS = 365
STAGES = {
    # Illustrative conditional offer assumptions; NOT derived from population studies.
    "progression": (0.32, 38),
    "interview": (0.18, 58),
    "conversation": (0.065, 83),
    "application": (0.012, 115),
}
SCENARIOS = {"Conservative": 0.55, "Current pace": 1.0, "Faster conversion": 1.5}


def _bounded(number: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, number))


def _cdf(days: float, characteristic_days: float) -> float:
    if days <= 0:
        return 0.0
    return 1 - exp(-((days / characteristic_days) ** 1.6))


def _crossing(curve: list[dict], key: str, threshold: float = 0.5) -> date | None:
    return next((day(row["Date"]) for row in curve if row[key] >= threshold), None)


def _process_stage(p: dict) -> str | None:
    if p.get("Progressed"):
        return "progression"
    if p.get("Completed interview"):
        return "interview"
    if p.get("Human") or p.get("Human events", 0) > 0:
        return "conversation"
    if p.get("Applied"):
        return "application"
    return None


def forecast_hiring(
    jobs: list[dict], as_of: date, *,
    market_model: dict | None = None,
    portfolio_correlation: dict | None = None,
    hiring_quality: dict | None = None,
) -> dict:
    """Return a transparent offer forecast conditional on recorded search pace.

    Curve = independent open-process scenario hazards + expected new application
    arrivals (Poisson approximation). An illustrative likelihood is assigned to
    each stage. Nothing here has been validated against individual offer outcomes.
    """
    events = [r for r in canonical_events(jobs)
              if day(r.get("event_date")) and day(r["event_date"]) <= as_of]
    dates = [day(r["event_date"]) for r in events]
    first = min(dates) if dates else None
    report = analyze(jobs, first or as_of, as_of, False)
    known_offers = sum(offer(r) for r in events)
    active = []
    for p in report["processes"]:
        if p["State"] == "Closed / paused":
            continue
        stage = _process_stage(p)
        age = p.get("Days since event")
        if not stage or age is None or age > 150:
            continue
        # An unresolved process is not a verified live opening.
        # Old or unknown-status processes receive progressively less weight.
        status_weight = 1.0 if p["State"] == "Active documented" else 0.38
        freshness = exp(-max(0, age - 21) / 70)
        weight = status_weight * freshness
        if weight >= 0.035:
            active.append({"stage": stage, "weight": round(weight, 5),
                           "age": age, "state": p["State"]})

    last28 = sum(bool(r.get("is_application")) and
                 as_of - timedelta(days=27) <= day(r["event_date"]) <= as_of
                 for r in events)
    prior28 = sum(bool(r.get("is_application")) and
                  as_of - timedelta(days=55) <= day(r["event_date"]) < as_of - timedelta(days=27)
                  for r in events)
    # Smooth the observed application flow; cap the contribution of high volume.
    daily_rate = _bounded((0.7 * last28 + 0.3 * prior28) / 28.0, 0.0, 0.75)
    search_days = (as_of - first).days + 1 if first else 0

    # A demonstrated conversation stage is useful leading evidence, but without
    # offer outcomes it does not identify an individual offer conversion rate.
    mature = [p for p in report["processes"] if p.get("Applied")
              and (as_of - p["Applied"]).days >= 28]
    contacted = sum(bool(p.get("Human") or p.get("Human events", 0))
                    for p in mature)
    contact_rate = contacted / len(mature) if len(mature) >= 8 else None

    market_coverage = (market_model or {}).get("coverage") or {}
    confirmed_market = [
        r for r in (market_model or {}).get("findings", [])
        if r.get("status") == "Repeated association"
        and r.get("outcome") in ("responses", "interviews", "progression")
    ]
    confirmed_portfolio = [
        r for r in (portfolio_correlation or {}).get("ranked", [])
        if r.get("status") == "Repeated association"
        and r.get("outcome") in ("responses", "interviews", "progression")
    ]
    quality = (hiring_quality or {}).get("quality_summary") or {}
    source_state = {
        "primary_events": len(events),
        "recorded_offer_events": known_offers,
        "tracked_processes": len(report["processes"]),
        "live_or_recent_unresolved_processes": len(active),
        "applications_last_28d": last28,
        "applications_previous_28d": prior28,
        "mature_applied_processes": len(mature),
        "mature_with_human_contact": contacted,
        "contact_rate": contact_rate,
        "job_history_days": search_days,
        "qualified_portfolio_sessions_30d": int(quality.get("analysis_eligible_sessions") or 0),
        "portfolio_hiring_intent_actions_30d": int(quality.get("hiring_intent_sessions") or 0),
        "portfolio_repeated_associations": len(confirmed_portfolio),
        "market_indicator_series": int(market_coverage.get("indicators") or 0),
        "market_observations": int(market_coverage.get("observations") or 0),
        "market_repeated_associations": len(confirmed_market),
    }
    result = {"version": MODEL_VERSION, "as_of": as_of.isoformat(),
              "sources": source_state, "active_stages": active,
              "curve": [], "crossings": {}, "confidence": "Low",
              "limitations": [
                  "Offer-conversion assumptions are illustrative, not learned from past offers.",
                  "Portfolio analytics are anonymous and cannot identify employers or prove recruitment impact.",
                  "Swedish market releases describe general demand, not your personal offer odds.",
                  "Assumes similar application pace; hiring decisions, pauses and search changes are unknown.",
              ]}
    if known_offers:
        result["status"] = "offer_recorded"
        return result
    if len(events) < 8 or (not active and last28 + prior28 < 3):
        result["status"] = "insufficient"
        return result

    # Sparse history precludes honest confidence intervals. Alternate curves
    # vary the uncalibrated priors; they are sensitivity cases, not percentiles.
    curve = []
    for t in range(0, HORIZON_DAYS + 1, 7):
        entry = {"Date": (as_of + timedelta(days=t)).isoformat(), "Days": t}
        for name, factor in SCENARIOS.items():
            no_offer = 1.0
            for p in active:
                p_final, characteristic = STAGES[p["stage"]]
                chance = _bounded(p_final * factor * p["weight"] *
                                  _cdf(t, characteristic), 0.0, 0.96)
                no_offer *= (1 - chance)
            # New applications are future arrivals, each with time-to-decision.
            # Numerical integration uses weekly bins; exact day-level precision
            # would suggest more certainty than this model can support.
            if daily_rate:
                expected = 0.0
                for age in range(7, t + 1, 7):
                    expected += (7 * daily_rate * STAGES["application"][0] *
                                 factor * _cdf(age, STAGES["application"][1]))
                no_offer *= exp(-expected)
            entry[name] = round(_bounded(1 - no_offer, 0.0, 1.0), 4)
        curve.append(entry)

    result["curve"] = curve
    result["crossings"] = {name: (
        _crossing(curve, name).isoformat() if _crossing(curve, name) else None
    ) for name in SCENARIOS}
    # At least one active process or sustained flow is required for a date.
    result["status"] = "scenario" if result["crossings"]["Current pace"] else "no_median"
    result["confidence"] = "Low — uncalibrated" if not known_offers else "Limited"
    result["modelled_90d"] = next(
        (r["Current pace"] for r in curve if r["Days"] >= 91), None)
    result["modelled_180d"] = next(
        (r["Current pace"] for r in curve if r["Days"] >= 182), None)
    return result
