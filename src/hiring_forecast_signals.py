"""Bounded, explainable *heuristic* adjustments to future hiring opportunities.

These coefficients are editorial planning assumptions, not empirical causal
effects. Only future application opportunities are adjusted; ongoing
interviews never get retroactive boosts. Missing, stale and low-volume
signals remain neutral.
"""
from __future__ import annotations

from datetime import date, timedelta
import math

from job_search_metrics import day
from jobtech_demand_forecast import analyze_jobtech_demand, jobtech_lag_diagnostics

PORTFOLIO_CAP = 0.12
PORTFOLIO_GENERAL_CAP = 0.09
CV_ATTRIBUTION_CAP = 0.03
MARKET_CAP = 0.18
MARKET_NOWCAST_CAP = 0.035
COMBINED_MIN = 0.78
COMBINED_MAX = 1.28
# Each selected topic gets ONE source to avoid double counting similar studies.
MARKET_TOPICS = (
    ("it_tech_demand", ("employment_outlook_it_tech",), 0.050, "IT and technology hiring outlook"),
    ("consulting_demand", ("employment_outlook_services_consulting",), 0.035, "Services and consulting hiring outlook"),
    ("regional_outlook", ("employment_outlook_net_vgr",), 0.035, "Västra Götaland hiring outlook"),
    ("regional_vacancies", ("new_vacancies_arbetsformedlingen",), 0.045, "New vacancies in Västra Götaland"),
    ("tech_hiring", ("tech_hiring_regime", "tech_vacancies"), 0.025, "Technology hiring conditions"),
    ("services_employment", ("services_pmi_employment_below_50_streak",
                             "services_employment_expectations_3m"), 0.040, "Services employment plans"),
    ("regional_redundancy", ("redundancy_notices",), 0.035, "Regional redundancy notices"),
    ("large_employers", ("large_employer_staff_replacement_stance",), 0.025, "Large employers' hiring stance"),
    ("regional_recovery", ("vgr_recovery_timing", "labour_market_recovery_regime"), 0.030, "Regional recovery outlook"),
    ("target_data_it_demand", ("data_it_active_job_ads",), 0.045, "Active Data/IT vacancy demand"),
    ("employment_expectations", ("employment_expectations_3m",
                                  "manufacturing_employment_expectations_3m"), 0.045,
     "Near-term employment expectations"),
    ("services_cycle", ("services_confidence", "services_pmi"), 0.035,
     "Services business-cycle conditions"),
    ("macro_growth", ("gdp_growth_forecast", "gdp_growth_qoq"), 0.025,
     "Swedish growth outlook"),
    ("unemployment_outlook", ("unemployment_rate_forecast",
                              "harmonised_unemployment_rate"), 0.030,
     "Swedish unemployment outlook"),
)

JOBTECH_MTD_PAIRS = (
    ("jobtech_tier_a_ai_leadership_ads_mtd_v1",
     "jobtech_tier_a_ai_leadership_ads_v1", .45),
    ("jobtech_high_signal_target_ads_mtd_v1",
     "jobtech_high_signal_target_ads_v1", .30),
    ("jobtech_high_signal_target_ads_stockholm_mtd_v1",
     "jobtech_high_signal_target_ads_stockholm_v1", .15),
    ("jobtech_high_signal_target_ads_vgr_mtd_v1",
     "jobtech_high_signal_target_ads_vgr_v1", .10),
)


def _number(raw: object, default: float = 0.0) -> float:
    try:
        value = float(raw)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _growth(cur: int, prior: int, *, threshold: int = 6) -> float:
    """0..1 only for convincing growth above a real baseline."""
    if prior < threshold or cur <= prior:
        return 0.0
    growth = (cur - prior) / max(prior, 1)
    return _bounded(growth / 0.75, 0, 1)


def _driver(label: str, effect: float, current: int | None = None,
            previous: int | None = None, detail: str = "",
            **other) -> dict:
    return {
        "label": label, "effect": round(effect, 5),
        "current": current, "previous": previous, "detail": detail, **other,
    }


def _daily_sums(rows: list[dict], keys: tuple[str, ...]) -> dict[str, int]:
    return {k: sum(max(0, int(_number(r.get(k)))) for r in rows) for k in keys}


def portfolio_adjustment(site_model: dict | None, actions: dict | None,
                         as_of: date) -> dict:
    """Growth in verified portfolio sessions + distinct CV/contact actions.

    Daily session data excludes current partial day. Actions must be returned
    from an owner-only, quality-screened aggregate with matching dates.
    """
    series = (site_model or {}).get("site_daily") or []
    per_day = {day(r.get("Date")): r for r in series
               if day(r.get("Date")) and day(r["Date"]) < as_of}
    end = as_of - timedelta(days=1)
    # Compare equal, complete periods only. Early V5 tracking can start
    # with short 6–7-day comparisons but gets proportionally less weight.
    comparison_days = next(
        (n for n in (28, 14, 7, 6)
         if all(end - timedelta(days=i) in per_day for i in range(2 * n))),
        0,
    )
    recent_days = [end - timedelta(days=i) for i in range(comparison_days - 1, -1, -1)]
    previous_days = [end - timedelta(days=i) for i in range(
        2 * comparison_days - 1, comparison_days - 1, -1)]
    reliability = math.sqrt(comparison_days / 28.0) if comparison_days else 0.0
    drivers = []
    values = {
        "qualified": (0, 0), "engaged": (0, 0), "readers": (0, 0),
        "cv_downloads": (0, 0), "contact_clicks": (0, 0),
    }
    if comparison_days and all(d in per_day for d in recent_days + previous_days):
        recent = [per_day[d] for d in recent_days]
        before = [per_day[d] for d in previous_days]
        keys = ("sessions", "engaged_10s", "article_readers",
                "multi_page_visitors", "impact_visitors", "governance_visitors")
        r, p = _daily_sums(recent, keys), _daily_sums(before, keys)
        values["qualified"] = (r["sessions"], p["sessions"])
        values["engaged"] = (r["engaged_10s"], p["engaged_10s"])
        deep_r = r["article_readers"] + r["multi_page_visitors"] + r["impact_visitors"] + r["governance_visitors"]
        deep_p = p["article_readers"] + p["multi_page_visitors"] + p["impact_visitors"] + p["governance_visitors"]
        # An individual may appear in several deep-behavior buckets.
        # These are a directional index, not a visitor headcount.
        values["readers"] = (deep_r, deep_p)
        drivers.extend([
            _driver("Qualified visitors", reliability * 0.035 * _growth(
                r["sessions"],p["sessions"],threshold=max(4,round(12*comparison_days/28))),
                    r["sessions"],p["sessions"],"Change in quality-filtered visits"),
            _driver("Engaged readers", reliability * 0.025 * _growth(
                r["engaged_10s"],p["engaged_10s"],threshold=max(3,round(8*comparison_days/28))),
                    r["engaged_10s"],p["engaged_10s"],"Engaged visitor sessions"),
            _driver("Deeper exploration", reliability * 0.025 * _growth(
                deep_r,deep_p,threshold=max(3,round(6*comparison_days/28))),
                    deep_r,deep_p,"Article, evidence and multi-page interest (overlapping sessions)"),
        ])

    # Do not compare 56-day counts to partial months or stale sessions.
    # The owner action RPC includes the current partial day so CV/contact
    # actions are reflected on the next five-minute Overview refresh.
    # The visitor growth comparison remains based on *complete* days.
    action_end = as_of if actions and actions.get("includes_partial_today") else end
    expected_recent = (action_end - timedelta(days=27)).isoformat()
    expected_prior = (action_end - timedelta(days=55)).isoformat()
    valid_actions = bool(actions and actions.get("recent_from") == expected_recent
                         and actions.get("previous_from") == expected_prior
                         and actions.get("through") == action_end.isoformat()
                         and actions.get("quality_checked") is True)
    if valid_actions:
        cv = actions.get("cv_download_sessions") or {}
        clicks = actions.get("contact_click_sessions") or {}
        cr, cp = max(0,int(_number(cv.get("recent")))), max(0,int(_number(cv.get("previous"))))
        er, ep = max(0,int(_number(clicks.get("recent")))), max(0,int(_number(clicks.get("previous"))))
        values["cv_downloads"], values["contact_clicks"] = (cr,cp), (er,ep)
        # Small, quality-filtered actions are stronger than generic reach,
        # yet cannot create a large forecast shift from one isolated click.
        full_actions_baseline = all(
            end - timedelta(days=i) in per_day for i in range(56)
        )
        cv_effect = 0.0 if cr == 0 else min(0.025, 0.006 * cr) + (
            0.006 if full_actions_baseline and cr >= 2 and cr > cp else 0.0)
        contact_effect = 0.0 if er == 0 else min(0.025, 0.006 * er) + (
            0.006 if full_actions_baseline and er >= 2 and er > ep else 0.0)
        drivers.extend([
            _driver("CV downloads", min(0.031,cv_effect), cr, cp,
                    "Distinct qualified sessions with CV downloads"),
            _driver("Contact actions", min(0.031,contact_effect), er, ep,
                    "Distinct qualified sessions clicking email or LinkedIn"),
        ])
    # CV-origin scoring is a reserved part of the existing 12% portfolio
    # budget, never an additional 12% nor a direct hiring probability.
    # The SQL counts each qualified CV session once, assigning a single
    # highest-quality tier: action > role > tag > variant > parent.
    cv_attribution = (actions or {}).get("cv_attribution") if valid_actions else None
    tiers = {key: max(0, int(_number((cv_attribution or {}).get(key))))
             for key in ("parent_recent","parent_previous","base_only",
                         "variants","roles","tags","actions")}
    attribution_valid = bool(
        isinstance(cv_attribution,dict)
        and cv_attribution.get("classification") == "exclusive_highest_quality_tier"
        and cv_attribution.get("tracking") == "qualified_engaged_sessions"
        and sum(tiers[k] for k in ("base_only","variants","roles","tags","actions"))
        <= tiers["parent_recent"]
    )
    if attribution_valid:
        reach = tiers["parent_recent"]
        # Two qualified, engaged, CV-sourced sessions are the minimum.
        # No assumed growth until both periods have adequate V5 history.
        parent_effect = (min(0.012, 0.004 + 0.001 * reach) if reach >= 2 else 0.0)
        growth_effect = (min(0.003, 0.003 * _growth(
            reach, tiers["parent_previous"], threshold=5))
            if comparison_days == 28 else 0.0)
        # All tiers below are mutually exclusive counts, already disjoint
        # from the baseline-only group. A source cannot claim several tier
        # bonuses through a single CV session.
        drivers.extend([
            _driver("Qualified CV parent channel",parent_effect+growth_effect,
                    tiers["parent_recent"],tiers["parent_previous"],
                    "Engaged, quality-screened sessions from CV attribution"),
            _driver("Specific CV source variants",min(0.006,0.003*tiers["variants"]),
                    tiers["variants"],None,"Explicit CV variant source, e.g. cv_recruiter"),
            _driver("Target-role CV referrals",min(0.008,0.004*tiers["roles"]),
                    tiers["roles"],None,"Explicit senior AI/data leadership role attribution"),
            _driver("Relevant CV campaign tags",min(0.005,0.0025*tiers["tags"]),
                    tiers["tags"],None,"Explicit AI/data/recruitment-oriented campaign tags"),
            _driver("CV-origin hiring actions",min(0.005,0.0025*tiers["actions"]),
                    tiers["actions"],None,"CV-origin sessions with a verified contact/CV action"),
        ])
    cv_drivers = drivers[-5:] if attribution_valid else []
    attribution_effect = (min(CV_ATTRIBUTION_CAP,
                             sum(d["effect"] for d in cv_drivers))
                          if attribution_valid else 0.0)
    general_effect = min(PORTFOLIO_GENERAL_CAP,
                         sum(d["effect"] for d in drivers[:-5] if attribution_valid)
                         if attribution_valid else sum(d["effect"] for d in drivers))
    total = min(PORTFOLIO_CAP, general_effect + attribution_effect)
    return {"effect": round(total,5), "drivers":drivers,
            "general_effect":round(general_effect,5),
            "cv_attribution_effect":round(attribution_effect,5),
            "cv_attribution_available":attribution_valid,
            "cv_attribution_tiers":tiers if attribution_valid else {},
            "cv_attribution_cap":CV_ATTRIBUTION_CAP,
            "values":values,"qualified_actions_available":valid_actions,
            "daily_history_available":len(drivers) >= 3,
            "comparison_days":comparison_days,
            "full_action_baseline":comparison_days == 28,
            "category":"portfolio","cap":PORTFOLIO_CAP}


def _days_in_month(d: date) -> int:
    next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (next_month - timedelta(days=1)).day


def _jobtech_mtd_nowcast(by_key: dict[str, dict], as_of: date) -> dict:
    """Pro-rate current-month official target-role demand against last month.

    This is deliberately a small nowcast. It reacts before month-end without
    pretending that a partial month is a completed observation.
    """
    components = []
    weighted = 0.0
    weight_used = 0.0
    for mtd_key, prior_key, weight in JOBTECH_MTD_PAIRS:
        mtd = by_key.get(mtd_key)
        prior = by_key.get(prior_key)
        if not mtd or not prior:
            continue
        observed = day(mtd.get("observation_date"))
        prior_observed = day(prior.get("observation_date"))
        if not observed or not prior_observed or observed.year != as_of.year or observed.month != as_of.month:
            continue
        previous_month = (as_of.replace(day=1) - timedelta(days=1))
        if prior_observed.year != previous_month.year or prior_observed.month != previous_month.month:
            continue
        cur = _number(mtd.get("metric_value"), -1)
        prev = _number(prior.get("metric_value"), -1)
        if cur < 0 or prev <= 0:
            continue
        elapsed_fraction = _bounded(observed.day / _days_in_month(observed), .05, 1.0)
        expected_to_date = prev * elapsed_fraction
        # +2 shrinkage stabilizes small-count regional baskets.
        pace_score = math.tanh(math.log((cur + 2) / (expected_to_date + 2)) / math.log(2))
        confidence = _bounded(_number(mtd.get("confidence_score"), 70) / 100, 0, 1)
        relevance = _bounded(_number(mtd.get("relevance_score"), 80) / 100, 0, 1)
        sample_quality = min(1.0, math.sqrt((cur + expected_to_date) / 12.0))
        maturity = math.sqrt(elapsed_fraction)
        quality = confidence * relevance * sample_quality * maturity
        contribution = weight * pace_score * quality
        weighted += contribution
        weight_used += weight
        components.append({
            "key": mtd_key,
            "current_mtd": int(cur),
            "previous_month": int(prev),
            "expected_to_date": round(expected_to_date, 2),
            "pace_score": round(pace_score, 4),
            "quality": round(quality, 4),
            "weight": weight,
        })
    score = weighted / weight_used if weight_used else 0.0
    effect = _bounded(score * .055, -MARKET_NOWCAST_CAP, MARKET_NOWCAST_CAP)
    if abs(effect) < .0001:
        effect = 0.0
    return {
        "effect": round(effect, 5),
        "score": round(score, 5),
        "cap": MARKET_NOWCAST_CAP,
        "components": components,
        "status": ("Active current-month JobTech nowcast" if components
                   else "No eligible current-month JobTech nowcast"),
    }


def market_adjustment(market_model: dict | None, as_of: date,
                      *, job_records: list[dict] | None = None,
                      jobtech_config: dict | None = None) -> dict:
    """De-duplicated market factors plus bounded target-role JobTech demand."""
    rows = (market_model or {}).get("latest") or []
    by_key = {}
    for r in rows:
        key = r.get("indicator_key")
        observed = day(r.get("observation_date"))
        published = day(r.get("published_at")) or day(r.get("first_seen_at"))
        if not key or not observed or not published or observed > as_of or published > as_of:
            continue
        if r.get("is_current") is False:
            continue
        expiry = day(r.get("valid_until"))
        if expiry and expiry < as_of:
            continue
        existing = by_key.get(key)
        if existing is None or observed > day(existing["observation_date"]):
            by_key[key] = r
    jobtech = analyze_jobtech_demand(market_model, as_of, jobtech_config)
    jobtech["lag_screen"] = jobtech_lag_diagnostics(market_model, job_records or [], as_of)
    drivers = []
    for topic, keys, max_weight, description in MARKET_TOPICS:
        # Priority list: one specific indicator per topic, never stack
        # multiple highly correlated releases or duplicate observations.
        signal = next((by_key[k] for k in keys if k in by_key), None)
        if not signal:
            continue
        score = _number(signal.get("signal_score"), default=float("nan"))
        if not math.isfinite(score):
            direction = str(signal.get("direction") or "").lower()
            score = {"positive":0.45,"negative":-0.45}.get(direction,0)
        score = _bounded(score, -1, 1)
        # Scores are analyst interpretations. Confidence and relevance are
        # used as reliability filters/attenuators, not probabilistic priors.
        confidence = _number(signal.get("confidence_score"),65)
        relevance = _number(signal.get("relevance_score"),70)
        if confidence < 50 or relevance < 65:
            continue
        reliability = _bounded(confidence / 100, 0, 1) * _bounded(relevance / 100, 0, 1)
        published = day(signal.get("published_at")) or day(signal.get("first_seen_at"))
        age = (as_of - published).days
        # React immediately to fresh releases and fade old observations faster.
        freshness = math.exp(-max(0, age) / 75.0)
        leading = bool(signal.get("is_leading_indicator"))
        lag = int(_number(signal.get("expected_lag_days"), 0))
        lead_boost = 1.0
        if leading and 0 < lag <= 45:
            lead_boost = 1.25
        elif leading and lag <= 90:
            lead_boost = 1.12
        region = str(signal.get("region") or "").casefold()
        sector = str(signal.get("sector") or "").casefold()
        role_family = str(signal.get("role_family") or "").casefold()
        specificity = 1.0
        if "enterprise_ai_data_leadership" in role_family:
            specificity *= 1.08
        if "västra götaland" in region or "stockholm" in region:
            specificity *= 1.08
        if "ai/data" in sector or "ai leadership" in sector or "data/it" in sector:
            specificity *= 1.10
        effect = max_weight * score * reliability * freshness * lead_boost * specificity
        # JobTech replaces some of the generic positive AI/tech-demand proxy,
        # while genuine negative employment pressures remain untouched.
        # Its four nested series already share ONE combined JobTech factor.
        if jobtech["effect"] and effect > 0 and topic in (
            "it_tech_demand", "tech_hiring", "regional_outlook"
        ):
            effect *= 0.50
        if abs(effect) < 0.0001:
            continue
        drivers.append(_driver(description, effect,
                               detail=str(signal.get("indicator_name") or topic),
                               key=signal.get("indicator_key"), topic=topic,
                               release_date=published.isoformat(),
                               observed_date=str(signal.get("observation_date")),
                               source=signal.get("source_organization") or "",
                               source_url=signal.get("source_url") or "",
                               freshness=round(freshness,4),
                               leading=leading, expected_lag_days=lag,
                               specificity=round(specificity,4)))
    if jobtech["effect"]:
        drivers.append(_driver(
            "JobTech target-role hiring demand", jobtech["effect"],
            detail=jobtech["status"], key="jobtech_high_signal_target_ads_v1",
            topic="target_role_demand", release_date=jobtech["first_recorded_at"],
            observed_date=jobtech["latest_month"],
            source="Arbetsförmedlingen JobTech", source_url="",
        ))
    nowcast = _jobtech_mtd_nowcast(by_key, as_of)
    if nowcast["effect"]:
        drivers.append(_driver(
            "JobTech current-month target-role nowcast", nowcast["effect"],
            detail=nowcast["status"], key="jobtech_target_role_mtd_nowcast_v1",
            topic="target_role_nowcast", release_date=as_of.isoformat(),
            observed_date=as_of.isoformat(), source="Arbetsförmedlingen JobTech",
            source_url="", components=nowcast["components"],
        ))

    raw_total = sum(d["effect"] for d in drivers)
    positive_topics = sum(d["effect"] > .002 for d in drivers)
    negative_topics = sum(d["effect"] < -.002 for d in drivers)
    dominant = max(positive_topics, negative_topics)
    opposing = min(positive_topics, negative_topics)
    corroboration = 1.0
    if dominant >= 3 and dominant - opposing >= 2:
        corroboration = min(1.18, 1.0 + .04 * (dominant - 2))
    total = _bounded(raw_total * corroboration, -MARKET_CAP, MARKET_CAP)
    drivers.sort(key=lambda d:abs(d["effect"]),reverse=True)
    return {"effect":round(total,5),"drivers":drivers,"category":"market",
            "cap":MARKET_CAP,"indicators_reviewed":len(by_key),
            "jobtech":jobtech,"nowcast":nowcast,
            "corroboration_multiplier":round(corroboration,4),
            "raw_effect":round(raw_total,5)}


def forecast_drivers(site_model: dict | None, actions: dict | None,
                     market_model: dict | None, as_of: date, *,
                     jobs: list[dict] | None = None,
                     jobtech_config: dict | None = None) -> dict:
    portfolio = portfolio_adjustment(site_model, actions, as_of)
    market = market_adjustment(market_model, as_of, job_records=jobs,
                               jobtech_config=jobtech_config)
    return {
        "portfolio":portfolio, "market":market,
        "combined_multiplier":round(
            _bounded(1 + portfolio["effect"] + market["effect"], COMBINED_MIN, COMBINED_MAX), 5),
    }
