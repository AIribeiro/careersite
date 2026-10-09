"""Exploratory Swedish market ↔ job-search/portfolio analytics.

Only independently observed market releases are paired with complete calendar
months. No interpolation, repeated snapshot filling or causal forecasting.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import math

from job_search_metrics import canonical_events, day
from portfolio_job_correlations import _daily_jobs, _pearson, _spearman, _site_features

OUTCOMES = {
    "applications": "Applications",
    "responses": "Inbound / two-way contacts",
    "interviews": "Completed interviews",
    "progression": "Explicit progression",
    "rejections": "Dated negative decisions",
    "portfolio_sessions": "Qualified portfolio sessions",
    "portfolio_engaged": "Engaged portfolio sessions",
    "portfolio_hiring_actions": "Hiring-related portfolio actions",
}
LAGS = (0, 1, 2, 3)  # Full calendar months after a released observation.
MIN_PAIRED = 12
MIN_REPEATED = 24


def _month(value: date) -> date:
    return value.replace(day=1)


def _next_month(value: date, n: int = 1) -> date:
    number = value.year * 12 + value.month - 1 + n
    return date(number // 12, number % 12 + 1, 1)


def _num(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _identity(row: dict) -> str:
    return str(row.get("series_key") or "|".join(str(row.get(x) or "").lower() for x in (
        "source_organization", "indicator_key", "frequency", "region",
        "sector", "role_family", "metric_unit",
    )))


def _available(row: dict) -> date | None:
    # Observations with no known release date must not be used in lead/lag tests.
    return day(row.get("published_at"))


def _deduplicate_market(rows: list[dict], today: date) -> dict[str, list[dict]]:
    selected = {}
    for item in rows:
        observed = day(item.get("period_end")) or day(item.get("observation_date"))
        if not observed or observed > today:
            continue
        key = (_identity(item), observed)
        previous = selected.get(key)
        rank = lambda r: (str(r.get("last_confirmed_at") or ""), str(r.get("updated_at") or ""), int(r.get("id") or 0))
        if previous is None or rank(item) > rank(previous):
            selected[key] = item
    groups = defaultdict(list)
    for (series, _), row in selected.items():
        groups[series].append(row)
    return {key: sorted(group, key=lambda r: str(r.get("period_end") or r.get("observation_date")))
            for key, group in groups.items()}


def _full_job_months(jobs: list[dict], today: date) -> tuple[dict[date,dict], list[date]]:
    dated = [day(r.get("event_date")) for r in canonical_events(jobs)]
    dated = [d for d in dated if d and d < today]
    if not dated:
        return {}, []
    # Earliest imported event is not necessarily the start of search history.
    # Exclude its month to avoid assuming missing earlier events are zeros.
    cursor = _next_month(_month(min(dated)))
    final = _month(today)  # Exclude the current incomplete month.
    all_months = []
    while cursor < final:
        all_months.append(cursor)
        cursor = _next_month(cursor)
    daily = _daily_jobs(jobs, today - timedelta(days=1))
    by_month = {d: {key: 0 for key in OUTCOMES} for d in all_months}
    for d, signals in daily.items():
        if _month(d) in by_month:
            for key in ("applications", "responses", "interviews", "progression", "rejections"):
                by_month[_month(d)][key] += int(signals.get(key, 0))
    return by_month, all_months


def _add_portfolio(monthly: dict[date,dict], site_payload: dict | None) -> dict:
    if not site_payload:
        return {"first": None, "end": None, "complete_months": 0, "complete_days": 0}
    site, _, coverage = _site_features(site_payload)
    if not site:
        return {"first": None, "end": None, "complete_months": 0, "complete_days": 0}
    first, last = min(site), max(site)
    complete = 0
    for month, counts in monthly.items():
        if month < first or _next_month(month) - timedelta(days=1) > last:
            continue
        # Do not treat a mid-month telemetry start as zero traffic.
        if month < first:
            continue
        complete += 1
        cursor = month
        while cursor < _next_month(month):
            observed = site.get(cursor, {})
            counts["portfolio_sessions"] += int(observed.get("sessions", 0))
            counts["portfolio_engaged"] += int(observed.get("engaged_10s", 0))
            counts["portfolio_hiring_actions"] += int(observed.get("hiring_actions", 0))
            cursor += timedelta(days=1)
    return {"first": first, "end": last, "complete_months": complete,
            "complete_days": coverage.get("coverage", 0)}


def _bh(rows: list[dict]) -> None:
    ordered = sorted((r for r in rows if r.get("p") is not None), key=lambda r: r["p"])
    smallest = 1.0
    for i in range(len(ordered) - 1, -1, -1):
        smallest = min(smallest, ordered[i]["p"] * len(ordered) / (i + 1))
        ordered[i]["q"] = round(smallest, 6)


def _screen(x: list[float], y: list[float]) -> dict:
    n = len(x)
    distinct = len(set(x))
    active = sum(v > 0 for v in y)
    result = {"n": n, "active": active, "distinct_x": distinct,
              "r": None, "rho": None, "p": None, "q": None,
              "early_r": None, "late_r": None, "diff_r": None,
              "drop_peak_r": None, "status": "Insufficient history"}
    if n < MIN_PAIRED or distinct < 4 or active < 5:
        return result
    r, rho = _pearson(x, y), _spearman(x, y)
    if r is None or rho is None:
        return result
    half = n // 2
    peak = max(range(n), key=lambda i: abs(x[i] - sum(x) / n))
    result.update(r=r, rho=rho,
                  early_r=_pearson(x[:half], y[:half]) if half >= 6 else None,
                  late_r=_pearson(x[half:], y[half:]) if n - half >= 6 else None,
                  drop_peak_r=_pearson(x[:peak] + x[peak+1:], y[:peak] + y[peak+1:]))
    # A difference check reduces spurious common-level trend discoveries.
    dx = [b-a for a,b in zip(x,x[1:])]
    dy = [b-a for a,b in zip(y,y[1:])]
    result["diff_r"] = _pearson(dx,dy)
    z = math.atanh(max(-.999999, min(.999999, r))) * math.sqrt(n-3)
    result["p"] = math.erfc(abs(z)/math.sqrt(2))
    return result


def _classify(row: dict) -> str:
    r = row["r"]
    if r is None:
        return "Insufficient history"
    matching = lambda v, threshold: v is not None and r*v > 0 and abs(v) >= threshold
    if abs(r) < .45 or not matching(row["rho"], .35) or not matching(row["drop_peak_r"], .30):
        return "Weak / unstable"
    if row["n"] >= MIN_REPEATED and row["q"] is not None and row["q"] <= .05 and (
        matching(row["early_r"], .2) and matching(row["late_r"], .2)
        and matching(row["diff_r"], .2) and row["active"] >= 9
    ):
        return "Repeated association"
    if row["n"] >= MIN_PAIRED and abs(r) >= .55 and matching(row["diff_r"], .15):
        return "Worth monitoring"
    return "Weak / unstable"


def analyze_market(rows: list[dict], jobs: list[dict], site_payload: dict | None,
                   today: date | None = None) -> dict:
    today = today or date.today()
    groups = _deduplicate_market(rows, today)
    latest = [g[-1] for g in groups.values() if g]
    latest.sort(key=lambda r: (_num(r.get("relevance_score")) or 0), reverse=True)
    monthly, complete_months = _full_job_months(jobs, today)
    portfolio = _add_portfolio(monthly, site_payload)
    trends = []
    for series, history in groups.items():
        quantitative = [r for r in history if _num(r.get("metric_value")) is not None]
        if len(quantitative) >= 2:
            before, now = quantitative[-2:]
            trends.append({"Indicator": now.get("indicator_name") or now.get("indicator_key"),
                           "Previous": _num(before.get("metric_value")),
                           "Latest": _num(now.get("metric_value")),
                           "Change": round(_num(now.get("metric_value")) - _num(before.get("metric_value")), 3),
                           "Unit": now.get("metric_unit"), "Periods": len(quantitative),
                           "Period": str(now.get("period_label") or now.get("observation_date"))})
    tested = []
    # Each x observation is used once. A release date is required for exposure
    # to prevent look-ahead. Different indicators/units are never combined.
    for series, history in groups.items():
        # Compare the reported source metric AND the distinct subjective score
        # as separate hypotheses, never as interchangeable units.
        for value_type, field in (("Source metric", "metric_value"),
                                  ("Analyst score", "signal_score")):
            available = []
            for row in history:
                val, published = _num(row.get(field)), _available(row)
                if val is None or published is None or published > today:
                    continue
                available.append((_month(published), val))
            releases = {}
            for released, val in available:
                releases[released] = val
            for outcome in OUTCOMES:
                if outcome.startswith("portfolio_") and portfolio["complete_months"] == 0:
                    continue
                for lag in LAGS:
                    # Lag 0 is the FIRST WHOLE MONTH after publication. Never
                    # match an outcome month containing pre-release activity.
                    target = lambda release: _next_month(release, lag + 1)
                    paired = [(m, x, monthly[target(m)][outcome])
                              for m,x in sorted(releases.items())
                              if target(m) in monthly and
                              (not outcome.startswith("portfolio_") or
                               target(m) >= portfolio["first"])]
                    x = [float(a) for _,a,_ in paired]
                    y = [float(b) for _,_,b in paired]
                    result = _screen(x,y)
                    result.update(series_key=series, indicator=history[-1].get("indicator_name") or
                                  history[-1].get("indicator_key"), outcome=outcome,
                                  value_type=value_type, lag_months=lag,
                                  pairs=[p[0].isoformat() for p in paired],
                                  source=history[-1].get("source_organization"))
                    tested.append(result)
    _bh(tested)
    for candidate in tested:
        candidate["status"] = _classify(candidate)
    order = {"Repeated association": 0, "Worth monitoring": 1,
             "Weak / unstable": 2, "Insufficient history": 3}
    tested.sort(key=lambda r: (order[r["status"]], -(abs(r["r"]) if r["r"] is not None else 0), -r["n"]))
    return {
        "latest": latest, "groups": groups, "trends": trends,
        "checks": tested, "findings": [r for r in tested if r["status"] in
                                    ("Repeated association", "Worth monitoring")],
        "coverage": {"indicators": len(groups), "observations": sum(map(len,groups.values())),
                     "repeat_series": sum(len(g) >= 2 for g in groups.values()),
                     "job_full_months": len(complete_months),
                     "portfolio_full_months": portfolio["complete_months"],
                     "portfolio_days": portfolio["complete_days"],
                     "tested": sum(r["p"] is not None for r in tested),
                     "qualified": sum(r["status"] == "Repeated association" for r in tested)},
        "monthly": [{"Month": m.isoformat(), **values} for m,values in sorted(monthly.items())],
        "portfolio": portfolio,
    }
