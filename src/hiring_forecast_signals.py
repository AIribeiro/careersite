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

PORTFOLIO_CAP = 0.12
MARKET_CAP = 0.12
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
    ("regional_recovery", ("vgr_recovery_timing",), 0.025, "Regional recovery outlook"),
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
    total = min(PORTFOLIO_CAP, sum(d["effect"] for d in drivers))
    return {"effect": round(total,5), "drivers":drivers,
            "values":values,"qualified_actions_available":valid_actions,
            "daily_history_available":len(drivers) >= 3,
            "comparison_days":comparison_days,
            "full_action_baseline":comparison_days == 28,
            "category":"portfolio","cap":PORTFOLIO_CAP}


def market_adjustment(market_model: dict | None, as_of: date) -> dict:
    """Directional score per distinct, relevant, independently released topic."""
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
        # Fresh monthly and quarterly releases contribute more; old material
        # fades rather than influencing the forecast indefinitely.
        freshness = math.exp(-max(0, age - 35) / 180.0)
        effect = max_weight * score * reliability * freshness
        if abs(effect) < 0.0001:
            continue
        drivers.append(_driver(description, effect,
                               detail=str(signal.get("indicator_name") or topic),
                               key=signal.get("indicator_key"), topic=topic,
                               release_date=published.isoformat(),
                               observed_date=str(signal.get("observation_date")),
                               source=signal.get("source_organization") or "",
                               source_url=signal.get("source_url") or ""))
    total = _bounded(sum(d["effect"] for d in drivers),-MARKET_CAP, MARKET_CAP)
    drivers.sort(key=lambda d:abs(d["effect"]),reverse=True)
    return {"effect":round(total,5),"drivers":drivers,"category":"market",
            "cap":MARKET_CAP,"indicators_reviewed":len(by_key)}


def forecast_drivers(site_model: dict | None, actions: dict | None,
                     market_model: dict | None, as_of: date) -> dict:
    portfolio = portfolio_adjustment(site_model, actions, as_of)
    market = market_adjustment(market_model, as_of)
    return {
        "portfolio":portfolio, "market":market,
        "combined_multiplier":round(
            _bounded(1 + portfolio["effect"] + market["effect"], 0.82, 1.24), 5),
    }
