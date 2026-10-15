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

def previous_forecasts(access_token: str, limit: int=15) -> list[dict]:
    if not access_token:
        return []
    n=max(1,min(90,int(limit)))
    data=_request_json("GET",_rest_url(
        f"{TABLE}?select=forecast_day,model_version,central_offer_date,"
        "top_offer_week,top_start_week,evidence_index,observed_at"
        f"&order=forecast_day.desc&limit={n}"
    ),token=access_token,timeout=15)
    return data if isinstance(data,list) else []

def stability_summary(history: list[dict]) -> dict:
    """No actual offer labels => do not report a fake backtest accuracy."""
    rows=[r for r in history if r.get("central_offer_date") and r.get("forecast_day")]
    if len(rows)<2:
        return {"status":"Awaiting comparable forecast history",
                "historical_accuracy_pct":None,"shift_days":None,
                "history_count":len(history)}
    rows=sorted(rows,key=lambda r:r["forecast_day"])
    last=rows[-1]; prior=rows[-2]
    shift=(date.fromisoformat(last["central_offer_date"])-
           date.fromisoformat(prior["central_offer_date"])).days
    return {"status":"Forecast stability only, accuracy not validated",
            "historical_accuracy_pct":None,"shift_days":shift,
            "history_count":len(history),
            "latest_day":last["forecast_day"],
            "previous_day":prior["forecast_day"]}
