"""Current-week Premium Reader policy for Weekly AI.

The editorial ISO week in the Europe/Stockholm calendar is authoritative.
An edition unlocks automatically for anonymous visitors at local Monday
00:00 after the ISO week it covers. Old weeks never relock when a new
edition has not yet been published.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def _stockholm_today(now: datetime | date | None = None) -> date:
    if now is None:
        return datetime.now(STOCKHOLM).date()
    if isinstance(now, datetime):
        if now.tzinfo is None:
            # Explicitly interpret legacy naïve timestamps as UTC.
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        return now.astimezone(STOCKHOLM).date()
    return now


def weekly_ai_is_premium(article, *, now: datetime | date | None = None) -> bool:
    """Only an edition covering the current ISO week is members-only."""
    from thinking_weekly_brief import edition_week, is_weekly_brief
    if not is_weekly_brief(article):
        return False
    year, week, _, _ = edition_week(article)
    current_year, current_week, _ = _stockholm_today(now).isocalendar()
    return (year, week) == (current_year, current_week)


def weekly_ai_public_from(article) -> date:
    """Local Monday after the edition's covered week (not a rolling 7 days)."""
    from thinking_weekly_brief import edition_week
    from datetime import timedelta
    _, _, monday, _ = edition_week(article)
    return monday + timedelta(days=7)
