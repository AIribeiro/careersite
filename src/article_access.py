"""Registered-reader policy for published editorial Articles.

A full Article is public only after BOTH events have happened:
(1) at least 168 hours have elapsed since its first publication; and
(2) a newer editorial Article has actually been published.

The latest published Article remains Premium even when older than seven
days. When a newer edition appears, the previous one opens immediately if
already seven days old, otherwise at its own seven-day threshold.

This controls website rendering, not authorization of the public CMS API.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

ARTICLE_KINDS = frozenset({
    "article", "point of view", "decision note", "field note", "framework",
})
EARLY_ACCESS_DURATION = timedelta(days=7)


def is_editorial_article(article) -> bool:
    """Only Articles and editorial subtypes; never Briefings or Weekly AI."""
    return (
        str(getattr(article, "kind", "") or "").strip().casefold()
        in ARTICLE_KINDS
        and not str(getattr(article, "slug", "") or "").startswith("weekly-ai-")
    )


def first_published_at(article) -> datetime | None:
    """The original publication date, not the mutable revision timestamp."""
    source = str(getattr(article, "published_at", "") or "").strip()
    if not source:
        return None
    try:
        parsed = datetime.fromisoformat(source.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def unlock_at(article) -> datetime | None:
    """Earliest possible public date; NOT a promise of automatic release."""
    published = first_published_at(article)
    return published + EARLY_ACCESS_DURATION if published else None


def latest_editorial_article_slug(published: Iterable) -> str | None:
    """Newest actually published editorial item across all Article subtypes.

    Use the canonical original publication timestamp; a metadata edit or a
    featured flag must not cause an older piece to become the 'latest'.
    Slugs settle ties deterministically. Malformed dates never make an item
    'newer', but such an item's own content is kept Premium.
    """
    eligible = [
        item for item in published
        if is_editorial_article(item)
        and str(getattr(item, "status", "") or "").casefold() == "published"
        and first_published_at(item) is not None
        and str(getattr(item, "slug", "") or "")
    ]
    if not eligible:
        return None
    newest = max(
        eligible,
        key=lambda item: (first_published_at(item), str(item.slug)),
    )
    return str(newest.slug)


def _published_catalogue(published: Iterable | None) -> Iterable | None:
    if published is not None:
        return published
    from site_cms import fetch_published_articles
    try:
        return fetch_published_articles()
    except (RuntimeError, ValueError, TimeoutError):
        return None


def article_is_locked(
    article, *, now: datetime | None = None, published: Iterable | None = None
) -> bool:
    """True if fewer than seven days old OR still the latest published Article.

    Publication catalogue errors fail closed for an eligible article after
    seven days: never assume a successor has been published. Separate
    Executive AI Briefings retain their own permanent registered gate.
    """
    if not is_editorial_article(article):
        return False
    if str(getattr(article, "status", "") or "").casefold() != "published":
        return False
    release = unlock_at(article)
    if release is None:
        return True
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    if clock.astimezone(timezone.utc) < release:
        return True
    catalogue = _published_catalogue(published)
    if catalogue is None:
        return True
    newest_slug = latest_editorial_article_slug(catalogue)
    if not newest_slug:
        return True
    return newest_slug == str(article.slug)


def public_access_explanation(article) -> str:
    """Truthful for both reasons a published Article might still be Premium."""
    return (
        "The full article becomes public after its first seven days "
        "and once a newer Article has been published."
    )


def unlock_label(article) -> str:
    """Date when an older superseded Article can become public."""
    from zoneinfo import ZoneInfo
    release = unlock_at(article)
    if not release:
        return "Publication date pending"
    local = release.astimezone(ZoneInfo("Europe/Stockholm"))
    return local.strftime("%-d %B %Y, %H:%M %Z")
