"""Adaptive, privacy-preserving comparison of portfolio traffic and recruitment events.

Statistical associations are exploratory ecological (day-level) comparisons,
never visitor -> employer attribution and never evidence of causation.
No UI, database access, user secrets, or shared mutable model state lives here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import math
import re

from job_search_metrics import (
    canonical_events, completed_interview, day, norm, process_key, progression,
    rejection_event,
)

FEATURES = {
    "sessions": "Qualified portfolio sessions",
    "engaged_10s": "Engaged sessions (10s+)",
    "cv_link_visitors": "CV-linked sessions",
    "linkedin_visitors": "LinkedIn-sourced sessions",
    "social_visitors": "Other social sessions",
    "article_readers": "Article reading sessions",
    "impact_visitors": "Leadership Impact visits",
    "certification_visitors": "Certification visits",
    "governance_visitors": "AI Governance visits",
    "multi_page_visitors": "Multi-page journeys",
    "hiring_actions": "Direct hiring-related actions",
}
OUTCOMES = {
    "applications": "Applications submitted",
    "responses": "Inbound / two-way contacts",
    "interviews": "Completed interviews",
    "progression": "Explicit next-stage progression",
    "rejections": "Explicit negative decisions",
}
LAGS = {
    "same_day": (0, 0, "Same day"),
    "before_1_3": (1, 3, "Preceding 1–3 days"),
    "before_4_7": (4, 7, "Preceding 4–7 days"),
}
# Two hypotheses from the initial 2026-10-09 investigation. Re-evaluated
# every run; they do not automatically receive a positive assessment.
ANCHORS = (("cv_link_visitors", "applications", "same_day"),
           ("cv_link_visitors", "responses", "same_day"))
MIN_DISCOVERY_SESSIONS = 15
MIN_DISCOVERY_ACTIVE_DAYS = 4
MIN_EXPLORATORY_DAYS = 10
MIN_STATISTICAL_DAYS = 42
MAX_HISTORY_DAYS = 365


def _pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n != len(y) or n < 3:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    if vx < 1e-10 or vy < 1e-10:
        return None
    return max(-1.0, min(1.0, sum((a-mx)*(b-my) for a,b in zip(x,y)) / math.sqrt(vx*vy)))


def _ranks(v: list[float]) -> list[float]:
    ordered = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    cursor = 0
    while cursor < len(v):
        end = cursor + 1
        while end < len(v) and v[ordered[end]] == v[ordered[cursor]]:
            end += 1
        average_rank = (cursor + 1 + end) / 2
        for i in ordered[cursor:end]:
            out[i] = average_rank
        cursor = end
    return out


def _spearman(x: list[float], y: list[float]) -> float | None:
    return _pearson(_ranks(x), _ranks(y))


def _p_screen(r: float | None, n: int) -> float | None:
    """Approximate two-sided Fisher-z screen, not a causal/independence claim."""
    if r is None or n < MIN_STATISTICAL_DAYS:
        return None
    z = math.atanh(max(-.999999, min(.999999, r))) * math.sqrt(n-3)
    return math.erfc(abs(z)/math.sqrt(2))


def _bh_pvalues(results: list[dict]) -> None:
    eligible = sorted(
        [row for row in results if row["p"] is not None],
        key=lambda r: r["p"],
    )
    # BH across every eligible discovered feature/outcome/lag, not only top hits.
    m = len(eligible)
    correction = 1.0
    for i in range(m-1, -1, -1):
        correction = min(correction, eligible[i]["p"] * m/(i+1))
        eligible[i]["q"] = round(correction, 6)


def _daily_jobs(records: list[dict], as_of: date) -> dict[date, dict[str, int]]:
    signals = defaultdict(lambda: {key: set() for key in OUTCOMES})
    for row in canonical_events(records):
        d = day(row.get("event_date"))
        key = process_key(row)
        if d is None or d > as_of or key is None:
            continue
        if row.get("is_application"):
            signals[d]["applications"].add(key)
        if row.get("is_human_interaction") and norm(row.get("interaction_direction")) in ("inbound","two_way"):
            signals[d]["responses"].add(key)
        if completed_interview(row):
            signals[d]["interviews"].add(key)
        if progression(row):
            signals[d]["progression"].add(key)
        if rejection_event(row):
            signals[d]["rejections"].add(key)
    return {d: {key: len(v) for key, v in row.items()} for d,row in signals.items()}


def _site_features(raw: dict) -> tuple[dict[date, dict[str,int]], dict[str,str], dict]:
    """Zero-fill recorded days; exclude partial rollout day and malformed rows."""
    earliest = day(raw.get("first_day"))
    latest = day(raw.get("through"))
    rollout = raw.get("tracking_since")
    rollout_date = day(rollout)
    # Tracking began partway through first day, which must not be interpreted
    # as a full-day zero or compared to a complete weekday.
    if earliest and rollout_date and earliest <= rollout_date:
        start = rollout_date + timedelta(days=1)
    else:
        start = earliest
    if not start or not latest or latest < start:
        return {}, dict(FEATURES), {"first": start, "end": latest, "coverage": 0}

    max_start = latest - timedelta(days=MAX_HISTORY_DAYS-1)
    start = max(start, max_start)
    dates = []
    current = start
    while current <= latest:
        dates.append(current)
        current += timedelta(days=1)
    dayset = set(dates)

    features = dict(FEATURES)
    series = {d: {label: 0 for label in FEATURES} for d in dates}
    for record in raw.get("daily", []):
        d = day(record.get("d"))
        if d not in dayset:
            continue
        for label in FEATURES:
            value = record.get(label, 0)
            try:
                series[d][label] = max(0, int(value or 0))
            except (ValueError, TypeError):
                pass

    for source_field, prefix, pattern in (
        ("pages", "page", r"^[a-z0-9][a-z0-9_-]{0,59}$"),
        ("sources", "source", r"^[a-z0-9][a-z0-9_.+%-]{0,47}$"),
    ):
        groups = defaultdict(lambda: defaultdict(int))
        for record in raw.get(source_field, []):
            d = day(record.get("d"))
            value = str(record.get("name") or "").casefold()
            if d not in dayset or not re.fullmatch(pattern, value):
                continue
            if source_field == "sources" and value in ("streamlit","unknown","direct/unknown","other/invalid","application"):
                continue
            try:
                n = int(record.get("sessions") or 0)
            except (ValueError, TypeError):
                continue
            groups[value][d] = max(0, n)
        for name, counts in groups.items():
            if sum(counts.values()) < MIN_DISCOVERY_SESSIONS or sum(n>0 for n in counts.values()) < MIN_DISCOVERY_ACTIVE_DAYS:
                continue
            label = f"{prefix}:{name}"
            features[label] = f"{'Page' if prefix == 'page' else 'Source'}: {name.replace('_',' ')}"
            for d, val in counts.items():
                series[d][label] = val
            for d in dates:
                series[d].setdefault(label, 0)

    return series, features, {"first": start, "end": latest, "coverage": len(dates)}


def _aligned_values(
    site: dict[date,dict[str,int]], jobs: dict[date,dict[str,int]],
    x_key: str, y_key: str, lag: tuple[int,int,str],
) -> tuple[list[date],list[float],list[float]]:
    start, end = min(site), max(site)
    offset_min,offset_max,_ = lag
    days, x, y = [], [], []
    d = start + timedelta(days=offset_max)
    while d <= end:
        exposure = sum(site[d-timedelta(days=offset)].get(x_key,0)
                       for offset in range(offset_min,offset_max+1))
        outcome = jobs.get(d, {}).get(y_key, 0)
        days.append(d)
        x.append(float(exposure))
        y.append(float(outcome))
        d += timedelta(days=1)
    return days,x,y


def _test_one(
    site: dict, jobs: dict, feature: str, outcome: str, lag_id: str,
    window: int | None = None,
) -> dict:
    days,x,y = _aligned_values(site,jobs,feature,outcome,LAGS[lag_id])
    if window:
        days, x, y = days[-window:],x[-window:],y[-window:]
    n = len(days)
    rx = sum(v > 0 for v in x)
    ry = sum(v > 0 for v in y)
    correlation = _pearson(x,y) if n >= MIN_EXPLORATORY_DAYS and rx >= 3 and ry >= 3 else None
    rank_r = _spearman(x,y) if correlation is not None else None
    weekday = [i for i,d in enumerate(days) if d.weekday() < 5]
    weekday_r = _pearson([x[i] for i in weekday],[y[i] for i in weekday]) if len(weekday)>=9 else None
    # Recheck without the day of maximum exposure; vulnerable to a single
    # publication, mass application burst or campaign launch.
    pos = x.index(max(x)) if x else None
    no_peak = _pearson(x[:pos]+x[pos+1:],y[:pos]+y[pos+1:]) if pos is not None and n>=14 else None
    mid = n//2
    before = _pearson(x[:mid],y[:mid]) if mid>=14 else None
    after = _pearson(x[mid:],y[mid:]) if n-mid>=14 else None
    return {
        "feature":feature,"outcome":outcome,"lag":lag_id,"n":n,
        "exposure_days":rx,"outcome_days":ry,
        "r":correlation,"rho":rank_r,"weekday_r":weekday_r,
        "without_peak_r":no_peak,"early_r":before,"later_r":after,
        "p":_p_screen(correlation,n) if rx>=7 and ry>=7 else None,
        "q":None,
        "from":days[0].isoformat() if days else None,
        "through":days[-1].isoformat() if days else None,
    }


def _same_direction(first: float | None, second: float | None, minimum: float = 0.0) -> bool:
    return first is not None and second is not None and abs(second)>=minimum and first*second>0


def _classify(result: dict) -> str:
    r = result["r"]
    if r is None:
        return "Too sparse"
    if result["n"] < MIN_STATISTICAL_DAYS:
        return "Early observation"
    steady = (
        abs(r)>=.35 and result["exposure_days"]>=7 and result["outcome_days"]>=7
        and _same_direction(r,result["rho"],.20)
        and _same_direction(r,result["weekday_r"],.15)
        and _same_direction(r,result["without_peak_r"],.20)
    )
    if not steady:
        return "Unstable / weak"
    confirmed = (
        result["n"]>=84 and result["exposure_days"]>=14 and result["outcome_days"]>=12
        and abs(r)>=.4 and result["q"] is not None and result["q"]<=.05
        and _same_direction(r,result["early_r"],.20)
        and _same_direction(r,result["later_r"],.20)
    )
    return "Repeated association" if confirmed else "Worth monitoring"


def analyze_portfolio_job_correlations(site_payload: dict, job_records: list[dict]) -> dict:
    site,features,quality = _site_features(site_payload)
    if not site:
        return {"coverage": quality, "results": [], "anchors": [], "ranked": [],
                "features": features, "outcomes": dict(OUTCOMES),
                "job_daily": {}, "site_daily": [], "discovered": [],
                "notice": "No complete, quality-filtered V5 days available."}
    job = _daily_jobs(job_records, max(site))
    candidate_results = [
        _test_one(site,job,feature,outcome,lag_id)
        for feature in features
        for outcome in OUTCOMES
        for lag_id in LAGS
    ]
    _bh_pvalues(candidate_results)
    for result in candidate_results:
        result["status"] = _classify(result)
    ordering = {"Repeated association":0,"Worth monitoring":1,"Early observation":2,
                "Unstable / weak":3,"Too sparse":4}
    ranked = sorted(
        [r for r in candidate_results if r["r"] is not None],
        key=lambda r:(ordering[r["status"]],-abs(r["r"]),-r["n"]),
    )
    anchors = [next((r for r in candidate_results if (r["feature"],r["outcome"],r["lag"])==tuple(key)),None)
               for key in ANCHORS]
    emerging = [r for r in ranked if r["feature"] not in dict(FEATURES)
                and r["status"] in ("Repeated association","Worth monitoring")]
    history = [{"Date": d.isoformat(),**counts} for d,counts in sorted(site.items())]
    return {
        "coverage":quality,"results":candidate_results,"anchors":[r for r in anchors if r],
        "ranked":ranked,"discovered":emerging,"features":features,
        "outcomes":dict(OUTCOMES),"site_daily":history,"job_daily":job,
        "total_tests":len(candidate_results),
        "tested":sum(r["p"] is not None for r in candidate_results),
        "top_status":next((r["status"] for r in ranked
                           if r["status"] in ("Repeated association","Worth monitoring")),None),
        "notice":None,
    }
