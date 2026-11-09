"""Append contextual closing navigation to primary portfolio landing pages.

Do not attach the landing-page route index to individual Thinking articles or
the Weekly AI archive. Existing article-level navigation remains unchanged.
"""
from __future__ import annotations

from about_next_navigation import about_next_navigation

LANDING_PAGES = frozenset({"impact", "ai-data-governance", "thinking", "contact"})


def inject_portfolio_continuation(
    document: str, page: str, *, article_slug: str = "", weekly_archive: bool = False
) -> str:
    if page not in LANDING_PAGES:
        return document
    if page == "thinking" and (article_slug.strip() or weekly_archive):
        return document
    if "<main" not in document or "</main>" not in document:
        return document
    if 'class="about-next"' in document or 'data-analytics-section="site-writing-footer"' in document:
        return document
    index = document.rfind("</main>")
    return document[:index] + about_next_navigation(page) + document[index:]
