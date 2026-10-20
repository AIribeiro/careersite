"""Non-scoring hiring-market shadow evaluation.

The primary v2 forecast is intentionally unaffected. Historical validation must
establish incremental predictive value before external observations can be scored.
Never treat contextual classifications or coverage as personal probabilities.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json

SHADOW_VERSION = "market-shadow-v1-context-only"
SOURCE_GROUPS = {
    "trr_professional_transitions": "Professional transitions",
    "brg_gothenburg_business_cycle": "Hiring environment",
    "scb_enterprise_ai_adoption": "Structural AI demand",
    "unionen_branschbarometern": "Hiring environment",
    "almega_services_indicator": "Hiring environment",
}
TARGET_SOURCE = "af_jobtech_target_demand"
TARGET_KEYS = {
    "jobtech_high_signal_target_ads_v1": "Sweden",
    "jobtech_high_signal_target_ads_vgr_v1": "Västra Götaland",
    "jobtech_high_signal_target_ads_stockholm_v1": "Stockholm",
    "jobtech_tier_a_ai_leadership_ads_v1": "Tier A, Sweden",
}
TIMING_FIELDS = ("offer_earliest", "offer_central", "offer_latest",
                 "start_earliest", "start_central", "start_latest")


def _date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if abs(result) < 1e15 and result == result else None
    except (TypeError, ValueError):
        return None


def _observed(row):
    return _date(row.get("period_end")) or _date(row.get("observation_date"))


def _released(row, as_of):
    """No hindsight: both source publication and first observation must be known."""
    released = _date(row.get("published_at"))
    first = _date(row.get("first_seen_at")) or _date(row.get("source_accessed_at"))
    observed = _observed(row)
    # Historical backfills with absent release dates are NOT usable as leading
    # evidence; their history may still be charted elsewhere.
    return bool(observed and observed <= as_of and first and first <= as_of
                and (str(row.get("source_registry_key")) == TARGET_SOURCE
                     or (released and released <= as_of))
                and (not _date(row.get("valid_until"))
                     or _date(row.get("valid_until")) >= as_of
                     or row.get("is_current") is False))


def _select(rows, as_of, registry):
    """Deduplicate revisions by series/period, without discarding historical periods."""
    active = {str(row.get("source_key")) for row in registry
              if row.get("active") is True}
    candidates = {}
    for row in rows:
        source = str(row.get("source_registry_key") or "")
        if source not in (set(SOURCE_GROUPS) | {TARGET_SOURCE}) or source not in active:
            continue
        if not _released(row, as_of):
            continue
        period = _observed(row).isoformat()
        slot = (source, str(row.get("indicator_key") or ""),
                str(row.get("sector") or ""), str(row.get("region") or ""), period)
        prev = candidates.get(slot)
        if prev is None or (bool(row.get("is_current")), str(row.get("last_confirmed_at") or ""),
                            str(row.get("updated_at") or ""), str(row.get("id") or "")) > (
                bool(prev.get("is_current")), str(prev.get("last_confirmed_at") or ""),
                str(prev.get("updated_at") or ""), str(prev.get("id") or "")):
            candidates[slot] = row
    return list(candidates.values())


def _series(rows, source, indicator, *, sector=None):
    records = [r for r in rows if r.get("source_registry_key") == source
               and r.get("indicator_key") == indicator
               and (sector is None or r.get("sector") == sector)
               and _number(r.get("metric_value")) is not None]
    return sorted(records, key=lambda r: (_observed(r), str(r.get("id") or "")))


def _metric(rows, source, indicator, *, sector=None):
    values = _series(rows, source, indicator, sector=sector)
    if not values:
        return None
    last = values[-1]
    old = values[-2] if len(values) > 1 else None
    new_value = _number(last.get("metric_value"))
    old_value = _number(old.get("metric_value")) if old else None
    return {
        "value": new_value, "previous": old_value,
        "change": (round(new_value - old_value, 3) if old_value is not None else None),
        "unit": last.get("metric_unit") or "",
        "observed": str(_observed(last)),
        "published": str(last.get("published_at") or ""),
        "source_url": last.get("source_url") or "",
        "source_key": last.get("source_key") or "",
        "id": last.get("id"),
        "history_count": len(values),
    }


def _signal(group, label, metric, interpretation, *, direction="mixed", independence="source"):
    if not metric:
        return None
    return {
        "group": group, "label": label, "metric": metric,
        "interpretation": interpretation, "direction": direction,
        "dependency_cluster": independence,
    }


def evaluate_market_shadow(market_rows, registry_rows, baseline, as_of):
    """Evaluate five registered source families without changing offer or start dates.

    A matching shadow *date* is a deliberate no-score safeguard, not proof that
    the market has no causal effect. It must never be described as a backtest.
    """
    as_of = _date(as_of)
    if not as_of:
        raise ValueError("A valid evaluation date is required.")
    market_rows = market_rows or []
    registry_rows = registry_rows or []
    eligible = _select(market_rows, as_of, registry_rows)
    registry = {r.get("source_key"): r for r in registry_rows}
    counts = {key: sum(r.get("source_registry_key") == key for r in eligible)
              for key in SOURCE_GROUPS}
    missing = [key for key in SOURCE_GROUPS
               if key not in registry or registry[key].get("active") is not True
               or counts[key] == 0]
    signals = []

    duration = _metric(eligible, "trr_professional_transitions", "trr_average_transition_days")
    employment = _metric(eligible, "trr_professional_transitions", "trr_new_employment")
    positive = _metric(eligible, "trr_professional_transitions", "trr_positive_exit_share")
    if duration:
        change = duration["change"]
        wording = ("Average TRR transition duration increased, a caution for planning "
                   "search length, not a Director-level duration estimate.") if change is not None and change > 0 else (
                   "TRR duration is contextual for white-collar workers, not a personal deadline.")
        signals.append(_signal("Professional transitions", "TRR transition duration",
                               duration, wording,
                               direction="negative" if change is not None and change > 0 else "undetermined"))
    if employment:
        signals.append(_signal("Professional transitions", "TRR new employment",
                               employment, "TRR-supported transitions measure a selected population; "
                               "quarterly throughput is not the individual's offer probability.",
                               direction="negative" if employment["change"] is not None and employment["change"] < 0 else "undetermined"))
    if positive:
        signals.append(_signal("Professional transitions", "TRR positive programme exits",
                               positive, "Positive exits include employment, self-employment "
                               "and education; not a direct employment rate."))

    service = _metric(eligible, "brg_gothenburg_business_cycle", "gothenburg_business_confidence_index", sector="services")
    manufacturing = _metric(eligible, "brg_gothenburg_business_cycle", "gothenburg_business_confidence_index", sector="manufacturing")
    for label, m in (("Göteborgsregionen services", service),
                     ("Göteborgsregionen manufacturing", manufacturing)):
        if m:
            signals.append(_signal("Hiring environment", label, m,
                                   "13-municipality business conditions, not an observed vacancy count; "
                                   "do not substitute for all Västra Götaland.",
                                   direction="positive" if m["change"] is not None and m["change"] > 0 else
                                   "negative" if m["change"] is not None and m["change"] < 0 else "undetermined",
                                   independence="brg_business_cycle"))
    ict_output = _metric(eligible, "almega_services_indicator", "ict_output_growth_yoy")
    ict_jobs = _metric(eligible, "almega_services_indicator", "ict_employment_growth_yoy")
    ict_loss = _metric(eligible, "almega_services_indicator", "ict_employment_change_yoy")
    for label, m, direction in (("ICT output growth", ict_output, "positive"),
                                 ("ICT employment growth", ict_jobs, "negative" if ict_jobs and ict_jobs["value"] < 0 else "undetermined"),
                                 ("ICT employment change", ict_loss, "negative" if ict_loss and ict_loss["value"] < 0 else "undetermined")):
        if m:
            signals.append(_signal("Hiring environment", label, m,
                                   "Almega release partly reuses SCB/KI; one dependent "
                                   "evidence cluster, not independent votes.",
                                   direction=direction, independence="almega_scb_ki"))
    ai_enterprise = _metric(eligible, "scb_enterprise_ai_adoption", "ai_using_enterprises_10plus_share")
    ai_large = _metric(eligible, "scb_enterprise_ai_adoption", "ai_using_large_enterprises_250plus_share")
    for label, m in (("Enterprise AI adoption (10+)", ai_enterprise),
                     ("Large-enterprise AI adoption (250+)", ai_large)):
        if m:
            signals.append(_signal("Structural AI demand", label, m,
                                   "Adoption measures usage, not advertised senior leadership vacancies.",
                                   direction="structural", independence="scb_ai_adoption"))
    unionen = [r for r in eligible if r.get("source_registry_key") == "unionen_branschbarometern"
               and str(r.get("metric_value_text") or "").strip()]
    if unionen:
        row = sorted(unionen, key=lambda r: _observed(r))[-1]
        signals.append({"group": "Hiring environment",
                        "label": "Unionen workplace survey",
                        "metric": {"value": None, "change": None,
                                   "observed": str(_observed(row)),
                                   "published": str(row.get("published_at") or ""),
                                   "source_url": row.get("source_url") or "",
                                   "source_key": row.get("source_key") or "", "id": row.get("id")},
                        "interpretation": str(row.get("metric_value_text")) +
                                          " Qualitative survey: no invented numerical hiring effect.",
                        "direction": "qualitative", "dependency_cluster": "unionen_survey"})

    # A full-month, vintage-visible JobTech snapshot only. Never compare a
    # partial-month count to a full month or interpret sparse regional counts
    # as a whole-market vacancy measure.
    jobtech = {}
    for indicator, place in TARGET_KEYS.items():
        rows = _series(eligible, TARGET_SOURCE, indicator)
        full = [r for r in rows if str(r.get("frequency") or "").lower() == "monthly"
                and _date(r.get("period_start")) and
                _date(r.get("period_start")).day == 1 and
                (_observed(r).replace(day=1) != _date(r.get("period_start")).replace(day=1)
                 or (_observed(r) + __import__("datetime").timedelta(days=1)).day == 1)
                and (r.get("raw_data") or {}).get("methodology_version") == "v1"]
        if full:
            top = full[-1]
            value = _number(top.get("metric_value"))
            jobtech[place] = {"value": value, "period_end": str(_observed(top)),
                              "first_seen": str(top.get("first_seen_at") or ""),
                              "sample_small": bool(value is not None and value < 10),
                              "status": "advertised-demand proxy, not all vacancies"}
    # No expansion of JobTech v1 feature definitions or auto-scoring.
    scenario = baseline.get("leading_stage_scenario") or {} if isinstance(baseline, dict) else {}
    timing = {k: scenario.get(k) for k in TIMING_FIELDS}
    signature_items = sorted((str(r.get("id")), str(r.get("source_key")),
                              str(r.get("updated_at") or ""), str(r.get("metric_value") or ""),
                              str(r.get("metric_value_text") or "")) for r in eligible)
    signature = hashlib.sha256(json.dumps(
        {"market": signature_items,
         "baseline": {"version": baseline.get("model_version"),
                      "scenario": timing,
                      "stages": baseline.get("stage_breakdown"),
                      "pipeline_index": baseline.get("portfolio_credibility_index")}}
        if isinstance(baseline, dict) else {"market": signature_items},
        sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()

    by_group = defaultdict(list)
    for signal in signals:
        by_group[signal["group"]].append(signal)
    contradictions = bool(ict_output and ict_jobs and ict_output["value"] > 0
                          and ict_jobs["value"] < 0)
    return {
        "version": SHADOW_VERSION, "as_of": as_of.isoformat(),
        "mode": "shadow_context_only", "validation": "not_backtested",
        "outlook": "Insufficient evidence", "external_contribution": "Unchanged (not scored)",
        "forecast_confidence": "Not empirically calibrated",
        "market_interpretation": ("Mixed: senior-relevant hiring signals do not corroborate "
                                  "a shorter time to an offer. No numerical recalibration justified."),
        "baseline_version": baseline.get("model_version") if isinstance(baseline, dict) else None,
        "baseline_timing": timing, "shadow_timing": dict(timing),
        "offer_date_delta_days": 0, "start_date_delta_days": 0,
        "delta_explanation": "Same dates by policy: no validated new coefficients. "
                             "A zero shadow delta is not a measured zero market effect.",
        "source_counts": counts, "missing_sources": missing,
        "observations_read": len(eligible),
        "signals": signals, "groups": dict(by_group),
        "jobtech": jobtech, "contradictory_output_employment": contradictions,
        "geography": {"Sweden": jobtech.get("Sweden"),
                      "Stockholm": jobtech.get("Stockholm"),
                      "Västra Götaland": jobtech.get("Västra Götaland"),
                      "Göteborgsregionen": {"services": service, "manufacturing": manufacturing,
                                            "geography_note": "BRG's 13 municipalities; no comparable city-specific JobTech series"}},
        "limitations": [
            "TRR transition outcomes cover a selected private-sector white-collar population.",
            "JobTech v1 captures advertised matched posts, not unadvertised vacancies; small VGR counts lack precision.",
            "Stockholm, Västra Götaland and Göteborgsregionen are distinct geographies.",
            "Almega's SCB/KI-derived estimates count as one dependent evidence cluster.",
            "Survey sentiment and SCB AI adoption do not imply a leadership opening.",
            "Only two TRR/BRG quarters, one Almega release and no confirmed offers: insufficient historical evidence to fit weights.",
        ],
        "promotion_allowed": False, "evidence_signature": signature,
    }
