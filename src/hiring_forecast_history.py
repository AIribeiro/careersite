"""Immutable owner-only forecast history: evidence stability vs real accuracy.

No raw job applications, contact details, or visit telemetry are persisted.
The earliest complete daily run is retained; a later refresh never overwrites
past forecasts. A 55/100 evidence score is not 55% observed prediction accuracy.
"""
from __future__ import annotations
from datetime import date
from hashlib import sha256
import json

from site_cms import _request_json, _rest_url

TABLE="careersite_hiring_forecast_history"

def build_snapshot(result: dict, source_signatures: dict[str,str]) -> dict:
    if result.get("status") not in ("scenario","no_median"):
        raise ValueError("Only complete computed forecasts may be archived.")
    sources=result["sources"]
    windows=result.get("windows") or {}
    offer=windows.get("offers") or []
    start=windows.get("starts") or []
    payload={
        "forecast_day": result["as_of"],
        "model_version": result["version"],
        "central_offer_date": (result.get("crossings") or {}).get("Current pace"),
        "top_offer_week":offer[0]["from"] if offer else None,
        "top_start_week":start[0]["from"] if start else None,
        "evidence_index":int((result.get("reliability") or {}).get("score_pct") or 0),
        "official_application_total":sources.get("official_application_total"),
        "linked_application_processes":sources.get("linked_application_processes"),
        "process_stage_counts":sources.get("stage_counts") or {},
        "opportunity_market_effect":(result.get("drivers") or {}).get("market",{}).get("effect"),
        "opportunity_portfolio_effect":(result.get("drivers") or {}).get("portfolio",{}).get("effect"),
        "modelled_90d":result.get("modelled_90d"),
        "expected_start_days":result.get("start_window") or {},
        "source_signature":sha256(json.dumps(source_signatures,sort_keys=True).encode()).hexdigest(),
    }
    return payload

def record_daily_first(access_token: str, result: dict, signatures: dict[str,str]) -> bool:
    """Private PostgreSQL RLS insertion; uniqueness keeps first run immutable."""
    if not access_token or not signatures.get("jobs"):
        return False
    payload=build_snapshot(result,signatures)
    _request_json("POST",_rest_url(
        TABLE+"?on_conflict=owner_user_id,forecast_day,model_version"
    ),token=access_token,payload=payload,
       prefer="resolution=ignore-duplicates,return=minimal",timeout=20)
    return True

def build_v2_snapshot(result: dict, source_signatures: dict[str, str]) -> dict:
    """Archive the v2 stage scenario without inventing offer probabilities."""
    if result.get("model_version") != "hiring-v2-stage-evidence-provisional":
        raise ValueError("Only a verified stage-model v2 result may be archived.")
    s = result.get("leading_stage_scenario") or {}
    cohort = result.get("cohort") or {}
    return {
        "forecast_day": result["as_of"],
        "model_version": result["model_version"],
        "central_offer_date": s.get("offer_central"),
        "top_offer_week": s.get("offer_central"),
        "top_start_week": s.get("start_central"),
        "evidence_index": round(float(result.get("portfolio_credibility_index") or 0)),
        "official_application_total": None,
        "linked_application_processes": cohort.get("total"),
        "process_stage_counts": {
            "stages": result.get("stage_breakdown") or {},
            "cohort": cohort,
            "model_notes": "Uncalibrated interview-stage credibility; not hiring probability",
        },
        "opportunity_market_effect": None,
        "opportunity_portfolio_effect": None,
        "modelled_90d": None,
        "expected_start_days": {
            "from": s.get("start_earliest"),
            "central": s.get("start_central"),
            "to": s.get("start_latest"),
            "conditional_scenario": True,
        },
        "source_signature": sha256(json.dumps(
            source_signatures, sort_keys=True, default=str).encode()).hexdigest(),
    }


def record_v2_daily_first(access_token: str, result: dict,
                          signatures: dict[str, str]) -> bool:
    """Keep the first owner-only v2 snapshot for each day, without overwriting beta."""
    if not access_token or not signatures.get("v2"):
        return False
    payload = build_v2_snapshot(result, signatures)
    _request_json("POST", _rest_url(
        TABLE + "?on_conflict=owner_user_id,forecast_day,model_version"
    ), token=access_token, payload=payload,
       prefer="resolution=ignore-duplicates,return=minimal", timeout=20)
    return True


def publish_v2_timing(access_token: str, result: dict) -> bool:
    """Publish the six scenario dates only; all process records stay private."""
    if not access_token or result.get("model_version") != "hiring-v2-stage-evidence-provisional":
        return False
    scenario = result.get("leading_stage_scenario") or {}
    fields = ("offer_central", "offer_earliest", "offer_latest",
              "start_central", "start_earliest", "start_latest")
    if any(not scenario.get(k) for k in fields):
        return False
    payload = {"id": 1, "model_version": result["model_version"],
               "as_of": result["as_of"],
               **{k: scenario[k] for k in fields}}
    _request_json(
        "POST", _rest_url("careersite_public_hiring_timing_v2?on_conflict=id"),
        token=access_token, payload=payload,
        prefer="resolution=merge-duplicates,return=minimal", timeout=20,
    )
    return True


def previous_forecasts(access_token: str, limit: int=15) -> list[dict]:
    if not access_token:
        return []
    n=max(1,min(90,int(limit)))
    data=_request_json("GET",_rest_url(
        f"{TABLE}?select=forecast_day,model_version,central_offer_date,"
        "top_offer_week,top_start_week,evidence_index,observed_at"
        f"&order=observed_at.desc&limit={n}"
    ),token=access_token,timeout=15)
    return data if isinstance(data,list) else []

def stability_summary(history: list[dict],
                      model_version: str | None = None) -> dict:
    """Compare comparable dates *within* a single model version.

    Switching from beta 4.3 to stage-v2 is not a forecast-date movement.
    """
    versions = sorted({r.get("model_version") for r in history
                       if r.get("model_version")})
    selected = model_version or (
        "hiring-v2-stage-evidence-provisional"
        if "hiring-v2-stage-evidence-provisional" in versions
        else (versions[-1] if versions else None)
    )
    rows = [r for r in history
            if r.get("central_offer_date") and r.get("forecast_day")
            and r.get("model_version") == selected]
    # Multiple versions recorded on one day may not be compared.
    dated = {}
    for r in sorted(rows, key=lambda x: x.get("observed_at") or ""):
        dated.setdefault(r["forecast_day"], r)
    rows = sorted(dated.values(), key=lambda x: x["forecast_day"])
    base = {
        "historical_accuracy_pct": None,
        "history_count": len(history),
        "model_version": selected,
        "comparable_count": len(rows),
        "model_versions": len(versions),
    }
    if len(rows) < 2:
        return {
            **base, "status": "Awaiting two dates from the same model",
            "shift_days": None,
        }
    last, prior = rows[-1], rows[-2]
    shift = (date.fromisoformat(last["central_offer_date"]) -
             date.fromisoformat(prior["central_offer_date"])).days
    return {
        **base, "status": "Within-model forecast stability; accuracy not validated",
        "shift_days": shift,
        "latest_day": last["forecast_day"],
        "previous_day": prior["forecast_day"],
    }
