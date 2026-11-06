"""Public-safe, aggregate attribution analysis for Advanced Insights.

The reporting RPC already contains first-touch source + role tags and a
separate content campaign cohort. This module *does not infer visitor jobs*
and never emits arbitrary campaign names or source strings into public UI.

Only a finite set of editorial/portfolio distribution tags is displayable.
Unknown and potentially sensitive tags are grouped rather than published.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlsplit
import re

from portfolio_legacy_signal_model import n, percentage, channel_label


_ROLE_LABELS = {
    "article": "Articles",
    "weeklyai": "Weekly AI",
    "executivebriefings": "Executive Briefings",
    "dailyquote": "Daily AI perspective",
    "profile": "Profile & portfolio",
    "aienthusiast": "AI Enthusiast newsletter",
    "ai_leadership": "AI leadership",
    "enterprise_ai_leadership": "Enterprise AI leadership",
    "microsoft-leadership-innovation-specialization": "Credentials feature",
}
_CAMPAIGN_LABELS = {
    "linkedin_launch": "Portfolio launch",
    "thinking": "Thinking articles",
    "dailyquote": "Daily AI perspective",
    "introduction": "Introduction outreach",
    "weekly_ai_archive": "Weekly AI archive",
    "weekly_ai_launch": "Weekly AI launch",
    "facebook_groups": "Facebook communities",
    "executive_briefings": "Executive Briefings",
    "ai_adoption_process_improvement": "AI adoption & process design",
    "hbr_business_savvy_2026": "Business leadership article",
    "governance-comment": "AI governance discussion",
    "aienthusiast": "AI Enthusiast newsletter",
    "article": "Article promotion",
    "profile": "Portfolio profile",
    "microsoft-leadership-innovation-specialization": "Credentials feature",
}
_WEEKLY = re.compile(
    r"^weekly_ai_(20\d{2})_w(0[1-9]|[1-4]\d|5[0-3])(?:_(friday|wednesday|monday|tuesday|thursday))?$"
)
_PRIVATE_HINTS = re.compile(
    r"(?:@|https?://|utm_|token|secret|linkedin\.com/in/|recruiter|candidate|interview|application_|hiring|\+46|\b[a-f0-9]{20,}\b)",
    re.IGNORECASE,
)


def role_tag(value: object) -> str:
    """Public category of the LINK, never a person or occupational role."""
    raw = str(value or "").strip().lower()
    if raw in ("", "none", "unknown", "untagged", "null"):
        return "No role tag"
    return _ROLE_LABELS.get(raw, "Other editorial tags")


def campaign_tag(value: object) -> str:
    """Safe editorial campaign label; no arbitrary user-entered identifiers."""
    raw = str(value or "").strip().lower()
    if raw in ("", "none", "unknown", "untagged", "null", "(none)"):
        return "No campaign tag"
    if _PRIVATE_HINTS.search(raw):
        return "Other tagged campaigns"
    if raw in _CAMPAIGN_LABELS:
        return _CAMPAIGN_LABELS[raw]
    match = _WEEKLY.fullmatch(raw)
    if match:
        year, week, weekday = match.groups()
        return f"Weekly AI · {year} W{week}" + (
            f" {weekday.title()}" if weekday else ""
        )
    return "Other tagged campaigns"


def _cohort(rows: object, *, label_key: str, mapper, metrics: tuple[str, ...]) -> list[dict]:
    if not isinstance(rows, list):
        return []
    grouped = defaultdict(lambda: {metric: 0 for metric in metrics})
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = mapper(row.get(label_key))
        for field in metrics:
            grouped[label][field] += n(row.get(field))
    return [
        {"Label": label, **values}
        for label, values in sorted(
            grouped.items(),
            key=lambda pair: (-pair[1].get("sessions", 0), pair[0]),
        )
        if values.get("sessions", 0) > 0
    ]


def role_cohorts(traffic_attribution: object) -> list[dict]:
    """Mutually exclusive traffic RPC source/role cohorts."""
    return _cohort(
        traffic_attribution,
        label_key="attribution_role",
        mapper=role_tag,
        metrics=("sessions", "engaged_sessions", "article_sessions",
                 "impact_sessions", "cv_sessions"),
    )


def channel_role_cohorts(rows: object) -> list[dict]:
    """Traffic-source × link-purpose co-occurrence, never visitor job roles."""
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        channel = channel_label(row.get("attribution_source"))
        purpose = role_tag(row.get("attribution_role"))
        key = (channel, purpose)
        if key not in grouped:
            grouped[key] = {"Channel": channel, "Link purpose": purpose,
                            "sessions": 0, "engaged_sessions": 0}
        grouped[key]["sessions"] += n(row.get("sessions"))
        grouped[key]["engaged_sessions"] += n(row.get("engaged_sessions"))
    return [
        record for record in sorted(
            grouped.values(),
            key=lambda record: (-record["sessions"], record["Channel"], record["Link purpose"]),
        )
        if record["sessions"] > 0
    ]


def campaign_cohorts(content_campaigns: object) -> list[dict]:
    """Content RPC campaign cohorts; never merge with traffic RPC sessions."""
    return _cohort(
        content_campaigns,
        label_key="campaign",
        mapper=campaign_tag,
        metrics=("sessions", "engaged_sessions", "reader_sessions",
                 "cv_sessions", "contact_sessions"),
    )


def campaign_channel_cohorts(rows: object) -> list[dict]:
    """Aggregated channel × approved campaign, to show attribution context."""
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        channel = channel_label(row.get("channel"))
        campaign = campaign_tag(row.get("campaign"))
        key = (channel, campaign)
        if key not in grouped:
            grouped[key] = {"Channel": channel, "Campaign": campaign, "sessions": 0,
                            "reader_sessions": 0, "engaged_sessions": 0}
        for name in ("sessions", "reader_sessions", "engaged_sessions"):
            grouped[key][name] += n(row.get(name))
    return [
        record for record in sorted(
            grouped.values(),
            key=lambda record: (-record["sessions"], record["Channel"], record["Campaign"]),
        ) if record["sessions"] > 0
    ]


_REFERRERS = {
    "linkedin.com": "LinkedIn",
    "lnkd.in": "LinkedIn",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "threads.net": "Threads",
    "t.co": "X",
    "x.com": "X",
    "google.com": "Google Search",
    "bing.com": "Bing",
    "chatgpt.com": "ChatGPT",
}


def referrer_origin(value: object) -> str:
    """Coarse referral hosts. Arbitrary domains are not publicized."""
    host = str(value or "").strip().lower()
    if host in ("", "unknown", "direct/unknown", "(direct)", "none"):
        return "No referrer recorded"
    if "://" in host:
        host = urlsplit(host).hostname or ""
    host = host.split(":", 1)[0].removeprefix("www.").removeprefix("m.")
    for known, label in _REFERRERS.items():
        if host == known or host.endswith("." + known):
            return label
    return "Other referrers"


def referrer_cohorts(rows: object) -> list[dict]:
    return _cohort(rows, label_key="referrer_host",
                   mapper=referrer_origin, metrics=("sessions",))


def tag_coverage(cohorts: list[dict], unknown_label: str) -> tuple[int, int]:
    """Measured tagged count and denominator in one collector only."""
    total = sum(n(row.get("sessions")) for row in cohorts)
    missing = sum(n(row.get("sessions")) for row in cohorts
                  if row.get("Label") == unknown_label)
    return max(0, total - missing), total


def meaningful_rate(row: dict, numerator: str, *, minimum: int = 20) -> float | None:
    sessions = n(row.get("sessions"))
    return percentage(row.get(numerator), sessions) if sessions >= minimum else None
