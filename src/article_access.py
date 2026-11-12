"""Time-limited registered-reader access for portfolio Articles.

This is a display entitlement. It must be checked at render time, never by
client-side CSS, scheduled jobs or a mutable 'locked' flag. The underlying
CMS API requires its own private-read redesign for strict content protection.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ARTICLE_KINDS = frozenset({
    "article", "point of view", "decision note", "field note", "framework",
})
EARLY_ACCESS_DURATION = timedelta(days=7)


def is_editorial_article(article) -> bool:
    """Exclude Briefings, Weekly AI and other formats."""
    return (
        str(getattr(article, "kind", "") or "").strip().casefold()
        in ARTICLE_KINDS
        and not str(getattr(article, "slug", "") or "").startswith("weekly-ai-")
    )


def first_published_at(article) -> datetime | None:
    """Use published_at, not updated_at: revisions do not restart the clock."""
    source = str(getattr(article, "published_at", "") or "").strip()
    if not source:
        return None
    try:
        parsed = datetime.fromisoformat(source.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        # Legacy CMS timestamps are normally offset-aware; interpret naive
        # legacy values as UTC rather than browser-local time.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def unlock_at(article) -> datetime | None:
    published = first_published_at(article)
    return published + EARLY_ACCESS_DURATION if published else None


def article_is_locked(article, *, now: datetime | None = None) -> bool:
    """Exactly 168 hours after first publication, access is public.

    Missing/malformed publication dates fail closed for editorial articles
    until CMS metadata is repaired. This prevents premature public exposure.
    """
    if not is_editorial_article(article):
        return False
    release = unlock_at(article)
    if release is None:
        return True
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    return clock.astimezone(timezone.utc) < release


def unlock_label(article) -> str:
    release = unlock_at(article)
    if not release:
        return "Publication date pending"
    local = release.astimezone(ZoneInfo("Europe/Stockholm"))
    return local.strftime("%-d %B %Y, %H:%M %Z")
