"""Minimal authenticated first-value measurement for two member journeys.

Only fixed milestone names and a Supabase Auth UUID are stored, once per
member/experience/milestone. Database timestamps and elapsed time are
generated server-side from genuine Reader/Advisory registration records.
Never send titles, prompts, decisions, profile text, URLs or device metadata.
The write is best effort and must never block access to the actual service.
"""
from __future__ import annotations

from statistics import median

from site_cms import _request_json, _rest_url

MILESTONES = frozenset({
    ("reader", "first_full_read"),
    ("advisory", "first_assessment"),
    ("advisory", "first_personal_request"),
})


def record_first_value(token: str, uid: str, journey: str, milestone: str) -> bool:
    """Best-effort deduplicated server milestone after a successful user action."""
    if (journey, milestone) not in MILESTONES:
        raise ValueError("Unsupported onboarding milestone.")
    if not token or not uid:
        raise ValueError("Verified member session required.")
    try:
        _request_json(
            "POST", _rest_url(
                "portfolio_onboarding_milestones?"
                "on_conflict=user_id,journey,milestone"
            ),
            token=token,
            payload={
                "user_id": uid, "journey": journey, "milestone": milestone,
            },
            prefer="resolution=ignore-duplicates,return=minimal",
            timeout=6,
        )
        return True
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        # Measurement is not a condition for reading or receiving a decision.
        return False


def owner_first_value_summary(
    reader_profiles: list[dict], advisory_profiles: list[dict],
    milestones: list[dict],
) -> dict[str, object]:
    """Aggregate only; the owner screen never renders per-member timings."""
    reader_ids = {
        str(r.get("user_id"))
        for r in reader_profiles if r.get("user_id")
    }
    advisory_ids = {
        str(r.get("user_id"))
        for r in advisory_profiles
        if r.get("user_id") and r.get("account_status") == "active"
    }
    good: dict[tuple[str, str], dict[str, dict]] = {}
    for item in milestones:
        if not isinstance(item, dict):
            continue
        journey, event = item.get("journey"), item.get("milestone")
        if (journey, event) not in MILESTONES:
            continue
        uid = str(item.get("user_id") or "")
        allowed = reader_ids if journey == "reader" else advisory_ids
        if uid not in allowed:
            continue
        good.setdefault((journey, event), {})[uid] = item

    def values(journey: str, event: str) -> list[int]:
        result: list[int] = []
        for row in good.get((journey, event), {}).values():
            try:
                val = int(row.get("elapsed_seconds"))
            except (ValueError, TypeError):
                continue
            if 0 <= val <= 315360000:
                result.append(val)
        return result

    reader_times = values("reader", "first_full_read")
    advisory_times = values("advisory", "first_assessment")
    return {
        "reader_registrations": len(reader_ids),
        "advisory_registrations": len(advisory_ids),
        "reader_first_reads": len(good.get(("reader", "first_full_read"), {})),
        "advisory_first_assessments": len(good.get(("advisory", "first_assessment"), {})),
        "advisory_personal_requests": len(good.get(("advisory", "first_personal_request"), {})),
        "reader_median_seconds": median(reader_times) if reader_times else None,
        "advisory_median_seconds": median(advisory_times) if advisory_times else None,
    }


def duration_label(value: float | None) -> str:
    if value is None:
        return "Not enough data"
    seconds = max(0, round(float(value)))
    if seconds < 60:
        return "Under 1 min"
    if seconds < 3600:
        return f"{round(seconds / 60)} min"
    if seconds < 86400:
        return f"{round(seconds / 3600, 1)} h"
    return f"{round(seconds / 86400, 1)} days"
