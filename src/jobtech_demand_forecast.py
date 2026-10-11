"""Official JobTech v1 advertised-demand momentum for the personal hiring beta.

Only completed publication months, official JobTech target-title basket v1, and
evidence already recorded by the analysis date are eligible. The four baskets
are related/subset views, not four independent vacancy populations. Coefficients
are disclosed heuristic planning weights, NOT empirical hiring probabilities.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import exp, isfinite, log, sqrt, tanh

from job_search_metrics import canonical_events, completed_interview, day, offer, progression

JOBTECH_KEYS = {
    "tier_a": "jobtech_tier_a_ai_leadership_ads_v1",
    "national": "jobtech_high_signal_target_ads_v1",
    "stockholm": "jobtech_high_signal_target_ads_stockholm_v1",
    "vgr": "jobtech_high_signal_target_ads_vgr_v1",
}
# These values are intentionally easy to alter via the *config* argument.
DEFAULT_CONFIG = {
    "basket_version": "v1",
    "weights": {"tier_a": .45, "national": .30, "stockholm": .15, "vgr": .10},
    "components": {"month_over_month": .45, "three_month_trend": .30,
                   "trailing_baseline": .25},
    "small_sample_reference": 12,
    "unconfirmed_effect_cap": .012,
    "confirmed_effect_cap": .040,
    "freshness_grace_days": 50,
    "freshness_decay_days": 90,
    "minimum_history_months": 4,
}
LAG_WINDOWS = {
    "opportunities_discovered": (0, 14),
    "applications": (0, 21),
    "employer_interactions": (7, 30),
    "interviews": (14, 45),
    "offers": (30, 75),
}
MIN_LAG_PAIRS = 12
MIN_STABLE_PAIRS = 24


def _date(value) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _month_end(d: date) -> date:
    next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _valid_number(value) -> int | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(x) or x < 0 or int(x) != x:
        return None
    return int(x)


def _clamp(value: float, a=-1., b=1.) -> float:
    return min(b, max(a, value))


def _profile(market_model: dict | None, as_of: date, config: dict) -> tuple[dict, list]:
    """Return eligible immutable monthly rows and quality alerts.

    Historical rows can have is_current=False and must be retained. first_seen
    is the earliest credible availability for this archive: the 2026 history
    was added October 11, not known in July.
    """
    rows = []
    for history in (market_model or {}).get("groups", {}).values():
        rows.extend(history)
    if not rows:
        rows = list((market_model or {}).get("latest") or [])
    selected = {}
    alerts = []
    for row in rows:
        key = row.get("indicator_key")
        if key not in JOBTECH_KEYS.values():
            continue
        first = _date(row.get("first_seen_at")) or _date(row.get("source_accessed_at"))
        published = _date(row.get("published_at"))
        available = max(x for x in (first, published) if x is not None) if (first or published) else None
        end = _date(row.get("period_end"))
        start = _date(row.get("period_start"))
        count = _valid_number(row.get("metric_value"))
        raw = row.get("raw_data") or {}
        version = str(raw.get("methodology_version") or "")
        registry = row.get("source_registry_key")
        if (not first or not available or available > as_of or not end or
                end > as_of or not start or start.day != 1 or
                _month_end(start) != end or
                str(row.get("frequency") or "").lower() != "monthly" or
                count is None or version != config["basket_version"] or
                registry != "af_jobtech_target_demand"):
            alerts.append(f"Excluded incomplete, unavailable or incompatible record: {key}")
            continue
        if raw.get("date_semantics") not in (None, "publication month"):
            alerts.append(f"Excluded non-publication-month record: {key}")
            continue
        if key == JOBTECH_KEYS["national"]:
            sources = {str(item).casefold() for item in
                       (raw.get("query_sources") or [])}
            methodology = str(row.get("methodology_note") or "").casefold()
            if (not {"historical ads", "jobsearch"}.issubset(sources)
                    or "deduplicat" not in methodology):
                alerts.append("National JobTech v1 lacks verified active + "
                              "historical union/dedup provenance")
                continue
        slot = (key, start)
        # Duplicate monthly observations with conflicting totals: do not
        # silently replace history, or fabricate growth from a revision.
        if slot in selected:
            before = selected[slot]
            if before.get("conflict"):
                continue
            if count != before["count"]:
                alerts.append(f"Conflicting JobTech snapshots: {key} {start:%Y-%m}")
                selected[slot] = {"conflict": True}
            continue
        selected[slot] = {
            "key": key, "month": start, "period_end": end,
            "count": count, "first_seen_at": first.isoformat(),
            "source": row.get("source_organization") or "Arbetsförmedlingen JobTech",
            "confidence": _clamp(float(row.get("confidence_score") or 75) / 100, 0, 1),
            "relevance": _clamp(float(row.get("relevance_score") or 85) / 100, 0, 1),
        }
    grouped = defaultdict(list)
    for (key, _), row in selected.items():
        if row.get("conflict"):
            grouped[key] = []
            continue
        grouped[key].append(row)
    for key, history in grouped.items():
        grouped[key] = sorted(history, key=lambda item: item["month"])
    return grouped, alerts


def _series_momentum(history: list[dict], config: dict):
    if len(history) < config["minimum_history_months"]:
        return None
    last4 = history[-4:]
    for before, after in zip(last4, last4[1:]):
        bm, am = before["month"], after["month"]
        if (am.year * 12 + am.month) - (bm.year * 12 + bm.month) != 1:
            return None
    old, prev, current = last4[0]["count"], last4[-2]["count"], last4[-1]["count"]
    baseline = sum(r["count"] for r in last4[:-1]) / 3
    # log ratios are bounded: +100% and -50% yield symmetric effects,
    # and no tiny-denominator percentage can dominate the score.
    transform = lambda a, b: tanh(log((a + 2) / (b + 2)) / log(2))
    components = {
        "month_over_month": transform(current, prev),
        "three_month_trend": transform(current, old),
        "trailing_baseline": transform(current, baseline),
    }
    momentum = sum(components[k] * config["components"][k] for k in components)
    denominator = config["small_sample_reference"]
    sample_quality = min(1., sqrt((current + prev) / 2 / denominator))
    quality = sample_quality * last4[-1]["confidence"] * last4[-1]["relevance"]
    return {
        "month": last4[-1]["month"].strftime("%Y-%m"),
        "value": current, "previous": prev,
        "three_month_start": old,
        "trailing_baseline": round(baseline, 2),
        "month_over_month": round((current - prev) / prev, 3) if prev else None,
        "momentum": round(momentum, 5),
        "quality": round(quality, 5),
        "components": {k: round(v, 5) for k, v in components.items()},
        "history": [{"month": r["month"].strftime("%Y-%m"), "count": r["count"]}
                    for r in history],
        "source": last4[-1]["source"],
    }


def analyze_jobtech_demand(market_model: dict | None, as_of: date,
                           config: dict | None = None) -> dict:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    cfg["weights"] = {**DEFAULT_CONFIG["weights"], **(config or {}).get("weights", {})}
    cfg["components"] = {**DEFAULT_CONFIG["components"], **(config or {}).get("components", {})}
    if any(v < 0 for v in cfg["weights"].values()) or abs(sum(cfg["weights"].values()) - 1) > .0001:
        raise ValueError("JobTech series weights must be positive and sum to 1.")
    if any(v < 0 for v in cfg["components"].values()) or abs(sum(cfg["components"].values()) - 1) > .0001:
        raise ValueError("JobTech momentum components must sum to 1.")
    groups, alerts = _profile(market_model, as_of, cfg)
    families = {name: _series_momentum(groups.get(key, []), cfg)
                for name, key in JOBTECH_KEYS.items()}
    available = {name: row for name, row in families.items() if row}
    # If the primary Tier A national or the broader national basket is absent,
    # do not extrapolate from Stockholm/VGR as though it were national demand.
    sufficient = bool(families["tier_a"] and families["national"])
    if sufficient:
        nation = {r["month"]:r["count"] for r in
                  groups.get(JOBTECH_KEYS["national"], [])}
        for family in ("tier_a", "stockholm", "vgr"):
            for observation in groups.get(JOBTECH_KEYS[family], []):
                national_count = nation.get(observation["month"])
                if national_count is not None and observation["count"] > national_count:
                    sufficient = False
                    alerts.append("JobTech v1 subset exceeds national total: "
                                  + family + " " + observation["month"].isoformat())
    score = sum(cfg["weights"][name] * row["momentum"] * row["quality"]
                for name, row in available.items()) if sufficient else 0.
    # Require October (or later) *completed*, consecutive-month confirmation
    # before the strong September rebound gets the larger factor budget.
    tier_history = groups.get(JOBTECH_KEYS["tier_a"], [])
    national_history = groups.get(JOBTECH_KEYS["national"], [])
    confirmed = False
    if sufficient and len(tier_history) >= 5 and len(national_history) >= 5:
        tier, nat = tier_history[-1], national_history[-1]
        prior_tier, prior_nat = tier_history[-2], national_history[-2]
        confirmed = (
            tier["month"] >= date(2026, 10, 1)
            and tier["month"] == nat["month"]
            and tier["count"] >= .85 * prior_tier["count"]
            and nat["count"] >= .85 * prior_nat["count"]
            and tier["count"] >= tier_history[-3]["count"]
            and nat["count"] >= national_history[-3]["count"]
        )
    period = max((row["month"] for row in available.values()), default=None)
    last_period_end = _month_end(date.fromisoformat(period + "-01")) if period else None
    age = (as_of - last_period_end).days if last_period_end else 0
    freshness = (exp(-max(0, age - cfg["freshness_grace_days"]) /
                     cfg["freshness_decay_days"]) if period else 0.)
    max_effect = (cfg["confirmed_effect_cap"] if confirmed
                  else cfg["unconfirmed_effect_cap"])
    effect = _clamp(score * max_effect * freshness, -max_effect, max_effect)
    if abs(effect) < .00001:
        effect = 0.
    return {
        "status": "October+ confirmed" if confirmed else (
            "Early rebound; awaiting next complete month" if sufficient else "Not enough comparable history"),
        "effect": round(effect, 5),
        "score": round(score, 5), "freshness": round(freshness, 4),
        "confirmed": confirmed, "cap": max_effect,
        "methodology": cfg["basket_version"], "families": families,
        "history_months": len(tier_history), "latest_month": period,
        "first_recorded_at": max((row["first_seen_at"] for row in tier_history
                                  if row["month"].strftime("%Y-%m") == period),
                                 default=None),
        "source": "Arbetsförmedlingen JobTech Historical Ads + JobSearch",
        "alerts": alerts[:8],
        "configuration": {"weights": cfg["weights"], "components": cfg["components"]},
        "monthly_history": {name: row["history"] for name, row in available.items()},
    }


def jobtech_lag_diagnostics(market_model: dict | None, jobs: list[dict],
                            as_of: date) -> dict:
    """Prospective, pre-registered lag tests, gated on independent observation count.

    June–September 2026 months were first SEEN October 11, so they cannot
    backtest contemporaneous June/July applications. Never backdate the release
    just because the underlying advertisement month is earlier.
    """
    groups, _ = _profile(market_model, as_of, DEFAULT_CONFIG)
    months = groups.get(JOBTECH_KEYS["tier_a"], [])
    # Eligibility requires data actually known before the outcome window.
    # Last outcome day must also have elapsed; missing outcomes are not zeros
    # when the candidate's tracking history is incomplete.
    # Only genuinely observed monthly releases (not a multi-month backfill)
    # enter prospective tests. Late first-seen dates make the historical
    # observation unavailable for contemporaneous hiring-outcome validation.
    clean = [r for r in months
             if r["period_end"] <= _date(r["first_seen_at"])
             <= r["period_end"] + timedelta(days=15)]
    checks = []
    events = [r for r in canonical_events(jobs) if day(r.get("event_date")) and
              day(r["event_date"]) <= as_of]
    for name, (begin, finish) in LAG_WINDOWS.items():
        eligible = [r for r in clean
                    if (_date(r["first_seen_at"]) + timedelta(days=finish)) <= as_of]
        outcome_days = []
        series = []
        if len(eligible) >= MIN_LAG_PAIRS:
            for obs in eligible:
                # Date the completed count became observable is the earliest
                # valid start of its prospective predictor/outcome window.
                anchor = _date(obs["first_seen_at"])
                start = anchor + timedelta(days=begin)
                end = anchor + timedelta(days=finish)
                observed = set()
                for e in events:
                    timestamp = day(e["event_date"])
                    if not start <= timestamp <= end:
                        continue
                    if name == "applications" and e.get("is_application"):
                        observed.add(e.get("logical_event_key") or str(e.get("id")))
                    elif name == "employer_interactions" and e.get("is_human_interaction") and str(e.get("interaction_direction") or "").lower() in ("inbound","two_way"):
                        observed.add(e.get("logical_event_key") or str(e.get("id")))
                    elif name == "interviews" and completed_interview(e):
                        observed.add(e.get("logical_event_key") or str(e.get("id")))
                    elif name == "offers" and offer(e):
                        observed.add(e.get("logical_event_key") or str(e.get("id")))
                    elif name == "opportunities_discovered" and str(e.get("event_type") or "").lower() in ("opportunity_discovered","vacancy_discovered","job_researched"):
                        observed.add(e.get("logical_event_key") or str(e.get("id")))
                outcome_days.append(len(observed))
                series.append(obs["count"])
        # A 12-month sample is exploratory ONLY; 24 and stable two-half
        # correlations plus outcome coverage are required for repeated evidence.
        result = {
            "outcome": name, "lag_days": [begin, finish],
            "eligible_observations": len(eligible),
            "status": "Insufficient prospective history",
            "correlation": None,
        }
        if len(series) >= MIN_LAG_PAIRS and len(set(series)) >= 4 and sum(n > 0 for n in outcome_days) >= 5:
            from portfolio_job_correlations import _pearson, _spearman
            coefficient = _pearson(series, outcome_days)
            rank = _spearman(series, outcome_days)
            stable = False
            if len(series) >= MIN_STABLE_PAIRS and coefficient is not None and rank is not None:
                split = len(series) // 2
                early = _pearson(series[:split], outcome_days[:split])
                late = _pearson(series[split:], outcome_days[split:])
                stable = bool(early is not None and late is not None and
                              coefficient * early > 0 and coefficient * late > 0
                              and abs(coefficient) >= .45 and abs(rank) >= .35)
            result["correlation"] = round(coefficient, 3) if coefficient is not None else None
            result["status"] = ("Worth monitoring (unadjusted exploratory)" if not stable
                                else "Repeated direction; needs external validation")
        checks.append(result)
    repeated = [r for r in checks
                if r["status"] == "Repeated direction; needs external validation"
                and r["correlation"] is not None]
    strongest = max(repeated, key=lambda row: abs(row["correlation"]), default=None)
    status = ("Repeated exploratory lag: " + strongest["outcome"]
              if strongest else "Waiting for prospective outcome history")
    return {"status": status,
            "eligible_months": len(clean), "tests": checks,
            "strongest_lag": strongest,
            "note": "Prospectively strongest lag is descriptive only; no JobTech-to-personal-offer causal multiplier is learned without independent validation."}
