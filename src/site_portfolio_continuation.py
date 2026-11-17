"""Attach the common contextual navigation to every public portfolio route.

Individual articles retain their editorial related-reading sections. The shared
three-card navigator follows those sections and precedes the site-wide footer.
Explicit renderers using the same component are left intact.
"""
from __future__ import annotations

from about_next_navigation import _PAGE_COPY, portfolio_next_navigation

LANDING_PAGES = frozenset(_PAGE_COPY)


def inject_portfolio_continuation(
    document: str, page: str, *, article_slug: str = "", weekly_archive: bool = False
) -> str:
    """Insert exactly one relevant closing navigator before the document footer.

    Article slugs and archive flags are accepted for backwards compatibility.
    All rendered article, briefing, archive and service pages now participate.
    """
    if page not in LANDING_PAGES or "<main" not in document or "</main>" not in document:
        return document
    if (
        'class="about-next portfolio-next"' in document
        or f'data-analytics-section="{page}-next-destinations"' in document
    ):
        return document
    index = document.rfind("</main>")
    return document[:index] + portfolio_next_navigation(page) + document[index:]
