"""Premium Reader policy for the latest published Weekly AI edition.

Only the newest *published* Weekly AI issue is exclusive to registered readers.
It remains Premium until the next Weekly AI issue is actually published,
including across calendar weeks, delayed releases and year boundaries.
Earlier editions are permanently open. This follows the publication catalogue,
not the local clock, scheduled job, slug age or a mutable lock flag.
"""
from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from site_cms import CmsArticle


def latest_weekly_ai_slug(published: Iterable["CmsArticle"]) -> str | None:
    """Use the existing official weekly archive ordering and deduplication."""
    from thinking_weekly_brief import sorted_editions
    editions = sorted_editions(list(published))
    return str(editions[0].slug) if editions else None


def weekly_ai_is_premium(
    article: "CmsArticle", *, published: Iterable["CmsArticle"] | None = None
) -> bool:
    """Read-only entitlement: latest published weekly issue, regardless of week.

    For catalogue/archive/library renderers, supply the already fetched set.
    Direct individual readers use the cached public CMS publication metadata.
    If that lookup fails or is empty, fail closed for a published Weekly AI
    rather than exposing an edition whose place in the catalogue is unknown.
    """
    from thinking_weekly_brief import is_weekly_brief
    if not is_weekly_brief(article) or str(article.status).casefold() != "published":
        return False
    if published is None:
        from site_cms import fetch_published_articles
        try:
            published = fetch_published_articles()
        except (RuntimeError, ValueError, TimeoutError):
            return True
    latest = latest_weekly_ai_slug(published)
    if latest is None:
        return True
    return str(article.slug) == latest
