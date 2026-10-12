"""Public, anonymized planning projection derived from the Hiring Predictor Beta.

This is NOT the detailed owner predictor: only 30-day stage-age buckets,
summarized application/contact counts and public market/portfolio signals are
available. Employer identities and process-level records remain private.
The deterministic curve uses the same stage assumptions and weekly-window
calculator as the full Beta, with explicit coarsening uncertainty.
"""
from __future__ import annotations

from datetime import date, timedelta
from math import exp

from hiring_predictor import (
    HORIZON_DAYS, SCENARIOS, STAGES, MODEL_MAX_APPLICATIONS_PER_WEEK,
    _bounded, _cdf, _remaining_offer_chance, MODEL_VERSION,
)
from hiring_forecast_windows import peak_weeks
from hiring_forecast_signals import portfolio_adjustment, market_adjustment
from portfolio_job_correlations import _site_features


def forecast_public_hiring(
    aggregate: dict, portfolio: dict | None = None,
    market_signals: list[dict] | None = None,
) -> dict:
    """Return dates and non-calibrated scenario weights, never employer detail."""
    today=date.fromisoformat(str(aggregate["as_of"]))
    stats=aggregate.get("summary") or {}
    entries=aggregate.get("stage_buckets") or []
    strategy=aggregate.get("strategy_context") or {}
    strategy_features=strategy.get("features") or {}
    strategy_context={
        "records_used": max(0,int(strategy.get("records_used") or 0)),
        "critical_records": max(0,int(strategy.get("critical_records") or 0)),
        "high_records": max(0,int(strategy.get("high_records") or 0)),
        "features": {
            key: bool(strategy_features.get(key))
            for key in (
                "conversion_funnel_focus",
                "human_access_priority",
                "role_positioning_calibrated",
                "seniority_calibrated",
                "interview_compression_risk_tracked",
                "evidence_quality_control",
                "targeted_application_strategy",
            )
        },
        "effect": 0.0,
        "usage": (
            "qualitative calibration and guardrails only; no direct probability "
            "multiplier until outcome history supports calibration"
        ),
    }
    if stats.get("currently_offered"):
        return {"status":"offer_recorded","as_of":today.isoformat()}
    recent=max(0,int(stats.get("recent_applications") or 0))
    prior=max(0,int(stats.get("prior_applications") or 0))
    mature=max(0,int(stats.get("matured_applications") or 0))
    contacted=max(0,min(mature,int(stats.get("mature_contacts") or 0)))
    pace=min(MODEL_MAX_APPLICATIONS_PER_WEEK,
             7*(.55*recent+.45*prior)/28)
    baseline_contact=(contacted+2)/(mature+10)
    future_app_offer_rate=_bounded(.002+.06*baseline_contact,.005,.035)
    binned=[]
    for entry in entries:
        name=str(entry.get("stage") or "")
        if name not in STAGES:
            continue
        n=max(0,min(1000,int(entry.get("n") or 0)))
        age_bucket=max(0,min(5,int(entry.get("age_month_index") or 0)))
        weight=float(entry.get("stage_weight") or 0)
        if weight not in (.35,1.0):
            continue
        if n:
            binned.append({"stage":name,"n":n,"age_days":age_bucket*30+14,"weight":weight})
    if not binned and recent+prior <3:
        return {"status":"insufficient","as_of":today.isoformat()}
    site_effect=0.0
    site_history_days=0
    if portfolio:
        site, _, coverage = _site_features(portfolio)
        site_history_days=int(coverage.get("coverage") or 0)
        if site:
            model={"site_daily":[{"Date":d.isoformat(),**row}
                                 for d,row in sorted(site.items())]}
            site_effect=portfolio_adjustment(model,None,today)["effect"]
    market_drivers=market_adjustment({"latest":market_signals or []},today)
    market_effect=market_drivers["effect"]
    opportunity_factor=_bounded(1+site_effect+market_effect,.78,1.28)
    curve=[]
    for t in range(0,HORIZON_DAYS+1,7):
        line={"Date":(today+timedelta(days=t)).isoformat(),"Days":t}
        for label,multiplier in SCENARIOS.items():
            no_offer=1.0
            for entry in binned:
                p_offer,scale=STAGES[entry["stage"]]
                stage_chance=entry["weight"] * _remaining_offer_chance(
                    _bounded(p_offer*multiplier,0.0,.95),
                    entry["age_days"],t,scale
                )
                no_offer *= (1-stage_chance)**entry["n"]
            new_offers=0.0
            for elapsed in range(7,t+1,7):
                new_offers+=(
                    pace*future_app_offer_rate*multiplier
                    *opportunity_factor
                    *_cdf(elapsed,STAGES["application"][1])
                )
            no_offer *= exp(-new_offers)
            line[label]=round(_bounded(1-no_offer,0,1),4)
        curve.append(line)
    windows=peak_weeks(curve,today)
    return {
        "status":"scenario",
        "as_of":today.isoformat(),
        "method":"coarsened-process-stages-public-planning-v1",
        "model_family":MODEL_VERSION,
        "windows":windows,
        "curve":curve,
        "weekly_application_pace":round(pace,2),
        "recent_applications":recent,
        "prior_applications":prior,
        "stage_sessions":sum(x["n"] for x in binned),
        "market_effect":market_effect,
        "portfolio_effect":site_effect,
        "strategy_effect":0.0,
        "strategy_context":strategy_context,
        "site_history_days":site_history_days,
        "market_indicators":market_drivers.get("indicators_reviewed",0),
        "evidence":"Limited: no personally validated offer probabilities; stage ages grouped in 30-day buckets. Current strategy records are used qualitatively, not as an uncalibrated probability multiplier.",
    }
