"""Private hiring-market shadow comparison and audit trail for Analytics."""
from __future__ import annotations

from datetime import date

import streamlit as st

from hiring_market_shadow import evaluate_market_shadow, SHADOW_VERSION, SOURCE_GROUPS
from site_cms import _request_json, _rest_url

TABLE = "careersite_hiring_market_shadow_history"


def fetch_market_registry(token: str) -> list[dict]:
    if not token:
        raise PermissionError("Owner access required for source registry.")
    rows = _request_json(
        "GET", _rest_url("job_market_source_registry?"
                         "select=source_key,source_name,active,last_observation_date,"
                         "last_success_at,next_expected_release_at,refresh_cadence,geography_scope"
                         "&limit=100"),
        token=token, timeout=20)
    if not isinstance(rows, list):
        raise RuntimeError("Source registry response not available.")
    return rows


def historical_shadow(token: str, limit: int = 12) -> list[dict]:
    if not token:
        raise PermissionError("Owner access required.")
    result = _request_json("GET", _rest_url(
        f"{TABLE}?select=forecast_day,baseline_model_version,baseline_offer_central,"
        "baseline_start_central,shadow_offer_central,shadow_start_central,"
        "outlook,source_signature,evidence,created_at"
        f"&order=created_at.desc&limit={max(1, min(int(limit), 30))}"
    ), token=token, timeout=15)
    if not isinstance(result, list):
        raise RuntimeError("Unexpected shadow history.")
    return result


def record_shadow(token: str, evaluation: dict) -> None:
    """Append a distinct evidence state; never touch production forecast tables."""
    if not token or evaluation.get("mode") != "shadow_context_only":
        raise ValueError("Private context-only shadow evaluation required.")
    if not evaluation.get("observations_read") or not evaluation.get("baseline_version"):
        return  # Do not record a missing feed as a confirmed zero/unchanged market.
    baseline = evaluation.get("baseline_timing") or {}
    shadow = evaluation.get("shadow_timing") or {}
    payload = {
        "forecast_day": evaluation["as_of"],
        "baseline_model_version": evaluation["baseline_version"],
        "shadow_model_version": SHADOW_VERSION,
        "baseline_offer_central": baseline.get("offer_central"),
        "baseline_start_central": baseline.get("start_central"),
        "shadow_offer_central": shadow.get("offer_central"),
        "shadow_start_central": shadow.get("start_central"),
        "outlook": evaluation["outlook"],
        "scoring_status": "context_only",
        "source_signature": evaluation["evidence_signature"],
        "evidence": evaluation,
    }
    _request_json(
        "POST",
        _rest_url(TABLE+"?on_conflict=owner_user_id,forecast_day,"
                  "baseline_model_version,source_signature"),
        token=token, payload=payload,
        prefer="resolution=ignore-duplicates,return=minimal", timeout=18)


def _date(value):
    if not value:
        return "Not established"
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d %b %Y")
    except ValueError:
        return "Not established"


def _change_message(evaluation: dict, historical: list[dict] | None) -> str:
    history = historical or []
    prior = next((h for h in history
                  if h.get("source_signature") != evaluation.get("evidence_signature")), None)
    if not prior:
        return ("First observed shadow evidence state; a before/after accuracy "
                "comparison is not yet possible.")
    previous = prior.get("evidence") or {}
    old_signals = {
        (s.get("group"), s.get("label")): (s.get("metric") or {})
        for s in previous.get("signals", []) if isinstance(s, dict)}
    changed = []
    for signal in evaluation.get("signals", []):
        key = (signal.get("group"), signal.get("label"))
        metric = signal.get("metric") or {}
        old = old_signals.get(key)
        if old is None or (old.get("value"),old.get("observed")) != (
                metric.get("value"),metric.get("observed")):
            changed.append(signal.get("label"))
    pipeline_changed = ((prior.get("baseline_offer_central") !=
                         evaluation.get("baseline_timing", {}).get("offer_central")) or
                        (prior.get("baseline_start_central") !=
                         evaluation.get("baseline_timing", {}).get("start_central")))
    if changed:
        return ("Updated market evidence: " + ", ".join(changed[:5]) +
                (" and others." if len(changed) > 5 else ".") +
                (" The production scenario also changed through the personal pipeline."
                 if pipeline_changed else " No market-scoring date change."))
    if pipeline_changed:
        return ("Personal pipeline timing changed since the prior shadow comparison; "
                "external features still have no scoring influence.")
    return "Source records changed without a qualifying numeric or period change; no forecast effect."


def render_market_shadow(evaluation: dict, *, compact: bool = False,
                         history: list[dict] | None = None) -> None:
    """Render source-linked evidence, without implying calibrated offer likelihood."""
    st.subheader("External market evidence · shadow evaluation")
    st.caption("Production hiring forecast versus an expanded contextual reading. "
               "New external source weights are **not active**.")
    a,b,c = st.columns(3)
    a.metric("Hiring outlook", evaluation.get("outlook", "Insufficient evidence"))
    b.metric("External forecast effect", "No adjustment")
    c.metric("Forecast calibration", "Not validated")
    st.write(evaluation.get("market_interpretation") or "")
    st.caption("The two versions show identical dates **by design**, not because the "
               "market has been proven to have zero effect. Offer probabilities and "
               "employment-start probabilities are not estimated from this backfill.")
    base = evaluation.get("baseline_timing") or {}
    if base.get("offer_central") or base.get("start_central"):
        st.caption("Current pipeline-only conditional dates: "
                   f"offer {_date(base.get('offer_central'))} "
                   f"({_date(base.get('offer_earliest'))} – "
                   f"{_date(base.get('offer_latest'))}); "
                   f"start {_date(base.get('start_central'))} "
                   f"({_date(base.get('start_earliest'))} – "
                   f"{_date(base.get('start_latest'))}). "
                   "The shadow has retained the same windows.")
    st.caption("Since previous shadow evaluation: " + _change_message(evaluation, history))
    count = sum(evaluation.get("source_counts", {}).values())
    st.caption(f"{count} verified observations across "
               f"{len(SOURCE_GROUPS)-len(evaluation.get('missing_sources',[]))}/5 "
               "new source families, including retained historical periods. "
               "Missing and overdue releases are not treated as zero.")
    if evaluation.get("missing_sources"):
        st.warning("Unavailable or inactive registered sources: " +
                   ", ".join(evaluation["missing_sources"]) +
                   ". This reduces interpretive coverage.")
    if evaluation.get("contradictory_output_employment"):
        st.info("Contradictory ICT signals: production is growing while ICT "
                "employment is shrinking. Higher output cannot be assumed "
                "to create more senior hiring opportunities.")

    with st.expander("Geography: Sweden, Stockholm, Västra Götaland and Göteborgsregionen",
                     expanded=not compact):
        geo = evaluation.get("geography") or {}
        rows = []
        for name in ("Sweden","Stockholm","Västra Götaland"):
            matched = geo.get(name)
            rows.append({"Geography":name,
                         "Target-role ads · last complete month":
                             (int(matched["value"]) if matched and matched.get("value") is not None else None),
                         "Observed through":matched.get("period_end") if matched else None,
                         "Interpretation":("Very small regional count; high uncertainty"
                                           if matched and matched.get("sample_small") else
                                           "JobTech matched advertisements, not all opportunities")})
        st.dataframe(rows, hide_index=True, width="stretch")
        brg = geo.get("Göteborgsregionen") or {}
        service, manufacturing = brg.get("services"), brg.get("manufacturing")
        if service and manufacturing:
            service_change = (f"{service['change']:+g}" if service['change'] is not None
                              else "not yet comparable")
            manufacturing_change = (
                f"{manufacturing['change']:+g}" if manufacturing['change'] is not None
                else "not yet comparable")
            st.caption("Göteborgsregionen (13 municipalities), separate from VGR: "
                       f"services confidence {service['value']:g} "
                       f"(quarter-on-quarter {service_change}); "
                       f"manufacturing {manufacturing['value']:g} "
                       f"({manufacturing_change}). "
                       "Business confidence is not a count of vacancies.")
        st.caption("Never sum or equate the nested national, Stockholm and VGR counts. "
                   "No Göteborg-specific senior JobTech count is asserted.")

    with st.expander("Evidence by factor · sources and measurement",
                     expanded=not compact):
        rows = []
        for group in ("Target-role demand","Hiring environment",
                      "Professional transitions","Structural AI demand"):
            if group == "Target-role demand":
                for location, item in (evaluation.get("jobtech") or {}).items():
                    rows.append({"Factor":group,"Indicator":f"JobTech · {location}",
                                 "Latest":item.get("value"),"Change":None,
                                 "Observation":item.get("period_end"),"Reference":None,
                                 "Interpretation":item.get("status")})
                continue
            for item in evaluation.get("groups",{}).get(group,[]):
                metric = item.get("metric") or {}
                rows.append({"Factor":group,"Indicator":item.get("label"),
                             "Latest":metric.get("value"),"Change":metric.get("change"),
                             "Observation":metric.get("observed"),
                             "Reference":metric.get("source_url"),
                             "Interpretation":item.get("interpretation")})
        if rows:
            st.dataframe(rows,hide_index=True,width="stretch",
                         column_config={"Reference":st.column_config.LinkColumn("Source publication")},
                         column_order=["Factor","Indicator","Latest","Change",
                                       "Observation","Reference","Interpretation"])
        st.caption("Observed values and deltas have their original units; the columns "
                   "are not comparable scores. Almega and its underlying SCB/KI "
                   "indicators share one dependence cluster, not independent votes.")
        for note in evaluation.get("limitations",[]):
            st.caption("• "+note)
        st.caption("Validation gate: time-ordered historical testing of calibration, "
                   "offer timing error, stability and uncertainty coverage. Until it "
                   "passes, any expanded weighted forecast remains disabled.")
