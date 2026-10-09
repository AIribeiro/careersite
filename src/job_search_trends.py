"""Evidence-based job search trends, independent of Streamlit and data access.

All event series use deduplicated primary records and exact linked processes.
Official point-in-time snapshots are deliberately handled separately.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from job_search_metrics import canonical_events, completed_interview, day, norm, process_key, rejection_event


SERIES = (
    "Applications",
    "Inbound / two-way contacts",
    "Completed interviews",
    "Explicit negative decisions",
)
SNAPSHOT_METRICS = (
    ("Confirmed application submissions", "Applications"),
    ("Explicit negative decisions", "Negative decisions"),
    ("Conservative active/unresolved working figure", "Active / unresolved minimum"),
)


def _signal(row):
    if row.get("is_application"):
        yield SERIES[0]
    if row.get("is_human_interaction") and norm(row.get("interaction_direction")) in {"inbound", "two_way"}:
        yield SERIES[1]
    if completed_interview(row):
        yield SERIES[2]
    if rejection_event(row):
        yield SERIES[3]


def _period(d: date, cadence: str) -> date:
    return d.replace(day=1) if cadence == "Month" else d - timedelta(days=d.weekday())


def _next_period(d: date, cadence: str) -> date:
    if cadence == "Week":
        return d + timedelta(days=7)
    return d.replace(year=d.year + 1, month=1) if d.month == 12 else d.replace(month=d.month + 1)


def _window_counts(events, first: date, last: date) -> dict[str, int]:
    signals = {label: set() for label in SERIES}
    for row in events:
        d = day(row.get("event_date"))
        key = process_key(row)
        if d is None or key is None or not first <= d <= last:
            continue
        for label in _signal(row):
            signals[label].add(key)
    return {label: len(signals[label]) for label in SERIES}


def _time_series(events, start: date, end: date, cadence: str) -> list[dict]:
    counts = defaultdict(lambda: {label: set() for label in SERIES})
    for row in events:
        d = day(row.get("event_date"))
        key = process_key(row)
        if d is None or key is None or not start <= d <= end:
            continue
        bucket = _period(d, cadence)
        for label in _signal(row):
            counts[bucket][label].add(key)

    series = []
    cursor = _period(start, cadence)
    while cursor <= end:
        for label in SERIES:
            series.append({
                "Date": cursor.isoformat(),
                "Measure": label,
                "Processes": len(counts[cursor][label]),
            })
        cursor = _next_period(cursor, cadence)
    return series


def _cohorts(events, start: date, end: date, maturity_days: int) -> dict:
    groups = defaultdict(list)
    for row in events:
        key = process_key(row)
        if key:
            groups[key].append(row)

    buckets = defaultdict(lambda: {
        "Applications": 0,
        "Matured": 0,
        "Pending maturation": 0,
        "Contact within 28d": 0,
        "Interview within 28d": 0,
    })
    for rows in groups.values():
        application_dates = [
            d for r in rows if r.get("is_application")
            if (d := day(r.get("event_date"))) is not None and d <= end
        ]
        if not application_dates:
            continue
        applied = min(application_dates)
        if not start <= applied <= end:
            continue
        item = buckets[applied.replace(day=1).isoformat()]
        item["Applications"] += 1
        if (end - applied).days < maturity_days:
            item["Pending maturation"] += 1
            continue
        item["Matured"] += 1
        deadline = applied + timedelta(days=maturity_days)
        within = [r for r in rows if (d := day(r.get("event_date"))) is not None and applied <= d <= deadline]
        if any(r.get("is_human_interaction") and norm(r.get("interaction_direction")) in {"inbound", "two_way"} for r in within):
            item["Contact within 28d"] += 1
        if any(completed_interview(r) for r in within):
            item["Interview within 28d"] += 1

    result = []
    for month, item in sorted(buckets.items()):
        matured = item["Matured"]
        result.append({
            "Month": month,
            **item,
            "Contact %": round(item["Contact within 28d"] * 100 / matured, 1) if matured else None,
            "Interview %": round(item["Interview within 28d"] * 100 / matured, 1) if matured else None,
        })
    return {
        "rows": result,
        "matured": sum(row["Matured"] for row in result),
        "pending": sum(row["Pending maturation"] for row in result),
        "contacted": sum(row["Contact within 28d"] for row in result),
        "interviewed": sum(row["Interview within 28d"] for row in result),
    }


def _snapshots(records, end: date) -> dict:
    dated = defaultdict(dict)
    for row in records:
        d = day(row.get("snapshot_date"))
        if row.get("record_type") != "snapshot_metric" or d is None or d > end:
            continue
        name = row.get("metric_name")
        if name not in dict(SNAPSHOT_METRICS) or row.get("metric_value") is None:
            continue
        try:
            number = int(float(row["metric_value"]))
        except (TypeError, ValueError):
            continue
        # The latest primary version of each metric wins, not a sum across sheets.
        previous = dated[d].get(name)
        if previous is None or (str(row.get("updated_at") or ""), str(row.get("id") or "")) > previous[0]:
            dated[d][name] = ((str(row.get("updated_at") or ""), str(row.get("id") or "")), number)

    days = sorted(dated, reverse=True)
    if not days:
        return {"current_date": None, "previous_date": None, "metrics": []}
    latest, preceding = days[0], (days[1] if len(days) > 1 else None)
    result = []
    for name, label in SNAPSHOT_METRICS:
        now = dated[latest].get(name)
        before = dated[preceding].get(name) if preceding else None
        current = now[1] if now else None
        previous = before[1] if before else None
        result.append({
            "Label": label,
            "Current": current,
            "Previous": previous,
            "Delta": current - previous if current is not None and previous is not None else None,
        })
    return {
        "current_date": latest.isoformat(),
        "previous_date": preceding.isoformat() if preceding else None,
        "metrics": result,
    }


def analyze_trends(records, start: date, end: date, employer: str = "All employers", window_days: int = 28) -> dict:
    if start > end or window_days < 1:
        raise ValueError("Invalid reporting period.")

    canonical = canonical_events(records)
    if employer != "All employers":
        canonical = [r for r in canonical if r.get("employer") == employer]
    events = [r for r in canonical if (d := day(r.get("event_date"))) is not None and d <= end]

    recent_start = end - timedelta(days=window_days - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)
    baseline_available = start <= previous_start
    current_complete = start <= recent_start

    recent = _window_counts(events, max(recent_start, start), end)
    previous = _window_counts(events, previous_start, previous_end) if baseline_available else None
    coverage = {
        "recent_dated": sum(max(recent_start, start) <= day(r["event_date"]) <= end for r in events),
        "previous_dated": sum(previous_start <= day(r["event_date"]) <= previous_end for r in events) if baseline_available else None,
        "undated": sum(day(r.get("event_date")) is None for r in canonical),
        "linked_dated": sum(process_key(r) is not None for r in events),
        "all_dated": len(events),
    }
    return {
        "recent_start": recent_start,
        "previous_start": previous_start,
        "previous_end": previous_end,
        "window_days": window_days,
        "current_complete": current_complete,
        "baseline_available": baseline_available,
        "recent": recent,
        "previous": previous,
        "coverage": coverage,
        "weekly": _time_series(events, start, end, "Week"),
        "monthly": _time_series(events, start, end, "Month"),
        "cohorts": _cohorts(events, start, end, maturity_days=28),
        "snapshots": _snapshots(records, end) if employer == "All employers" else None,
    }
