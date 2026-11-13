"""Pure, privacy-safe calculations for public portfolio intelligence.

All inputs are aggregate report objects supplied by approved anonymous RPCs.
No visitor IDs, exact source tags, campaign names or recruiting data are
required or emitted. Inferences remain conditional on coverage and sample.
"""
from __future__ import annotations

from datetime import date, timedelta


CHANNEL_METRICS = (
    "sessions", "engaged_sessions", "home_sessions", "impact_sessions",
    "article_sessions", "cv_sessions", "email_sessions", "linkedin_sessions",
)


def n(value: object) -> int:
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError, OverflowError):
        return 0


def percentage(numerator: object, denominator: object) -> float | None:
    top, bottom = n(numerator), n(denominator)
    if bottom <= 0 or top > bottom:
        return None
    return round(100 * top / bottom, 1)


def channel_label(label: object) -> str:
    """Discard the exact source string, including potential role/campaign tags."""
    source = str(label or "").strip().lower().split("?", 1)[0].split("&", 1)[0]
    if any(tag in source for tag in ("linkedin", "lnkd.in")):
        return "LinkedIn"
    if source in ("cv", "resume", "résumé", "curriculum-vitae") or source.startswith("cv-"):
        return "CV distribution"
    if any(tag in source for tag in ("google", "bing", "duckduckgo", "search")):
        return "Search"
    if any(tag in source for tag in ("newsletter", "email", "outlook", "gmail")):
        return "Email / newsletter"
    if source in ("facebook", "fb") or "facebook" in source:
        return "Facebook"
    if source in ("threads", "thre") or "threads" in source:
        return "Threads"
    if source in ("x", "twitter") or "x.com" in source or "twitter" in source:
        return "X"
    if source in ("whatsapp", "wa") or "whatsapp" in source:
        return "WhatsApp"
    if "chatgpt.com" in source or source in ("chatgpt", "openai"):
        return "AI assistants"
    if source == "application":
        return "Application links"
    if source == "reddit" or "reddit" in source:
        return "Reddit"
    if source in ("social", "bluesky") or any(
        tag in source for tag in ("bluesky", "instagram")
    ):
        return "Other social"
    if source in ("", "direct", "direct/unknown", "unattributed", "unknown",
                  "none", "(direct)"):
        return "Direct / unattributed"
    return "Other sources"


def channel_rollup(rows: object) -> list[dict]:
    """Roll up disjoint first-touch source/role cohorts without exposing labels."""
    grouped: dict[str, dict] = {}
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        group = channel_label(row.get("attribution_source"))
        agg = grouped.setdefault(group, {"Channel": group, **{key: 0 for key in CHANNEL_METRICS}})
        for key in CHANNEL_METRICS:
            agg[key] += n(row.get(key))
    output = []
    for row in grouped.values():
        sessions = row["sessions"]
        if not sessions:
            continue
        output.append({
            **row,
            "Session share": None,
            "Engagement rate": percentage(row["engaged_sessions"], sessions),
            "Article reach": percentage(row["article_sessions"], sessions),
            "CV reach": percentage(row["cv_sessions"], sessions),
        })
    return sorted(output, key=lambda row: (-row["sessions"], row["Channel"]))


def device_comparison(rows: object) -> list[dict]:
    results = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        sessions = n(row.get("sessions"))
        if not sessions:
            continue
        try:
            avg_pages = float(row.get("avg_pages") or 0)
        except (TypeError, ValueError):
            avg_pages = 0
        results.append({
            "Device": str(row.get("device_type") or "Unknown").title(),
            "Sessions": sessions,
            "Engaged": n(row.get("engaged_sessions")),
            "Engagement rate": percentage(row.get("engaged_sessions"), sessions),
            "Avg recorded pages": round(max(0.0, avg_pages), 2),
        })
    return sorted(results, key=lambda r: (-r["Sessions"], r["Device"]))


def seven_day_comparison(rows: object, *, today: date, window: str,
                         period_since: object = None) -> dict | None:
    """Two fully completed 7-day spans; never compare against today's partial day."""
    if window not in ("all", "this_year", "this_month", "30d", "90d", "365d"):
        return None
    start = today - timedelta(days=14)
    try:
        if period_since and date.fromisoformat(str(period_since)[:10]) > start:
            return None
    except ValueError:
        return None
    counted: dict[date, int] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        try:
            day = date.fromisoformat(str(row.get("day", ""))[:10])
        except ValueError:
            continue
        if start <= day < today:
            counted[day] = n(row.get("sessions"))
    if not counted or min(counted) > start:
        return None
    previous = sum(value for day, value in counted.items() if day < today - timedelta(days=7))
    recent = sum(value for day, value in counted.items() if day >= today - timedelta(days=7))
    return {
        "recent": recent, "previous": previous,
        "recent_start": today - timedelta(days=7),
        "previous_start": start,
        "previous_end": today - timedelta(days=8),
        "recent_end": today - timedelta(days=1),
        "change_pct": round(100 * (recent - previous) / previous, 1) if previous >= 20 else None,
    }


def _finding(title: str, evidence: str, meaning: str, next_check: str) -> dict:
    return {"title": title, "evidence": evidence, "meaning": meaning, "next_check": next_check}


def traffic_findings(data: dict, *, today: date, window: str) -> list[dict]:
    """Descriptive signals only; guard small samples and incompatible measures."""
    totals = data.get("totals") or {}
    sessions = n(totals.get("sessions"))
    if sessions == 0:
        return [_finding("No recorded sessions in this period", "0 sessions",
                         "This is not evidence that nobody visited; coverage may vary.",
                         "Choose a wider reporting period before interpreting traffic.")]
    findings = []
    channels = channel_rollup(data.get("attribution", []))
    direct = next((r for r in channels if r["Channel"] == "Direct / unattributed"), None)
    if direct and sessions >= 50:
        rate = percentage(direct["sessions"], sessions)
        if rate is not None and rate >= 35:
            findings.append(_finding(
                "Origin is uncertain for a substantial share of visits",
                f"{direct['sessions']:,} of {sessions:,} sessions ({rate:.1f}%) grouped as direct / unattributed",
                "This is a tracking-coverage limitation, not proof that visitors typed the URL.",
                "Check tagging consistency on LinkedIn, newsletters and shared portfolio links.",
            ))
    period = seven_day_comparison(data.get("daily", []), today=today, window=window,
                                  period_since=data.get("period_since"))
    if period and min(period["recent"], period["previous"]) >= 20:
        delta = period["change_pct"]
        if delta is not None and abs(delta) >= 15:
            findings.append(_finding(
                "Recorded weekly traffic moved " + ("up" if delta > 0 else "down"),
                f"{period['recent']:,} vs {period['previous']:,} sessions over two complete 7-day windows ({delta:+.1f}%)",
                "A traffic change does not establish its cause or imply a matching change in qualified attention.",
                "Compare publication and outreach timing with the same completed-day windows.",
            ))
    unknown = n(totals.get("unconfirmed_duration_sessions"))
    if sessions >= 30 and (percentage(unknown, sessions) or 0) >= 20:
        findings.append(_finding(
            "Active-time coverage is incomplete",
            f"{unknown:,} of {sessions:,} sessions ({percentage(unknown,sessions):.1f}%) have unconfirmed duration",
            "The available active-time average represents recorded browser activity, not verified dwell time for every visitor.",
            "Compare outcomes only among appropriately measured cohorts; retain the unconfirmed group.",
        ))
    devices = device_comparison(data.get("devices", []))
    meaningful = [d for d in devices if d["Sessions"] >= 50 and d["Engagement rate"] is not None]
    if len(meaningful) >= 2:
        strongest = max(meaningful, key=lambda d: d["Engagement rate"])
        weakest = min(meaningful, key=lambda d: d["Engagement rate"])
        if strongest["Engagement rate"] - weakest["Engagement rate"] >= 10:
            findings.append(_finding(
                "Recorded engagement differs by device",
                f"{strongest['Device']}: {strongest['Engagement rate']:.1f}% (n={strongest['Sessions']:,}); "
                f"{weakest['Device']}: {weakest['Engagement rate']:.1f}% (n={weakest['Sessions']:,})",
                "The groups can contain different sources and automation mixes; this is not a causal device effect.",
                "Inspect page speed and article accessibility on the weaker device before drawing conclusions.",
            ))
    single = n(totals.get("single_page_sessions"))
    if sessions >= 50 and (percentage(single, sessions) or 0) >= 70:
        findings.append(_finding(
            "Most recorded sessions show only one page",
            f"{single:,} of {sessions:,} sessions ({percentage(single,sessions):.1f}%) are single-page observations",
            "Single-page observation is not a validated bounce rate; legacy links and recording coverage influence this measure.",
            "Cross-check confirmed onward journeys and article recommendations before redesigning navigation.",
        ))
    contacts = n(totals.get("contact_channel_sessions"))
    cvs = n(totals.get("cv_sessions"))
    if sessions >= 30 and (contacts or cvs):
        findings.append(_finding(
            "Direct actions are measurable but sparse",
            f"{contacts:,} contact-channel and {cvs:,} CV-opening sessions out of {sessions:,} recorded sessions",
            "These independent measures can overlap and do not prove hiring intent.",
            "Check CTA visibility and confirmed click-to-destination paths without treating small counts as rates.",
        ))
    return findings[:7]
