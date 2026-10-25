"""Regression coverage for the Thinking highlight and six-item article catalogue."""
from __future__ import annotations

import re
import unittest
from unittest.mock import patch

from site_cms import CmsArticle, inject_cms_landing


def articles():
    return tuple(
        CmsArticle(
            id=f"id-{i:02}",
            slug=f"article-{i:02}",
            title=f"Article {i:02}",
            subtitle="An operating perspective.",
            excerpt="A practical enterprise AI decision.",
            kind="Article",
            category="Enterprise AI",
            status="published",
            published_at=f"2026-10-{i:02}T09:00:00+00:00",
            read_minutes=4,
        )
        for i in range(1, 16)
    )


DOCUMENT = (
    '<nav>Navigation</nav><main><section class="pagehero">Thinking hero</section>'
    '<section class="section white"><div class="container"><div class="head">'
    '<div><p class="eyebrow">Selected writing</p><h2>Explore the articles.</h2></div>'
    '</div><div class="recent-grid">Legacy list</div></div></section>'
    '<section class="section paper">Following section</section></main>'
)


class ThinkingCatalogPaginationTests(unittest.TestCase):
    def render(self, page):
        with patch("site_cms.fetch_published_articles", return_value=articles()), \
             patch("site_cms._public_reads_or_none", return_value={"article-15": 100}), \
             patch("thinking_core.query_value", return_value=str(page)):
            return inject_cms_landing(DOCUMENT)

    @staticmethod
    def card_slugs(rendered):
        return re.findall(
            r'data-hq-event="cms_article_open" data-hq-content-slug="([^"]+)"',
            rendered,
        )

    def test_highlight_immediately_precedes_six_article_grid(self):
        page = self.render(1)
        title = page.index("Articles I believe are worth your time.")
        highlight = page.index('class="cms-thinking-highlight"')
        grid = page.index('<div class="recent-grid">', highlight)
        self.assertLess(title, highlight)
        self.assertLess(highlight, grid)
        self.assertIn('data-hq-event="thinking_highlight_open"', page)
        self.assertIn('data-hq-content-slug="article-15"', page)
        self.assertEqual(len(self.card_slugs(page)), 6)
        self.assertNotIn("article-15", self.card_slugs(page))

    def test_catalog_pages_do_not_repeat_or_omit_articles(self):
        pages = [self.render(p) for p in (1, 2, 3)]
        slugs = [self.card_slugs(page) for page in pages]
        self.assertEqual([len(x) for x in slugs], [6, 6, 2])
        all_cards = [slug for group in slugs for slug in group]
        self.assertEqual(len(all_cards), len(set(all_cards)))
        self.assertEqual(set(all_cards), {f"article-{i:02}" for i in range(1, 15)})
        self.assertIn("Showing 7–12 of 14 articles", pages[1])
        self.assertIn("Showing 13–14 of 14 articles", pages[2])

    def test_navigation_is_shareable_and_accessible(self):
        page = self.render(2)
        self.assertIn('?page=thinking&amp;articles_page=3#articles-catalog', page)
        self.assertIn('?page=thinking&amp;articles_page=1#articles-catalog', page)
        self.assertIn('aria-label="Article pages"', page)
        self.assertIn('aria-current="page">2</span>', page)
        self.assertIn('data-hq-event="thinking_catalog_page"', page)

    def test_invalid_or_stale_page_numbers_are_safe(self):
        self.assertEqual(self.card_slugs(self.render("not-a-number")), self.card_slugs(self.render(1)))
        self.assertEqual(self.card_slugs(self.render(-9)), self.card_slugs(self.render(1)))
        self.assertEqual(self.card_slugs(self.render(999)), self.card_slugs(self.render(3)))

    def test_incoming_query_parameter_is_used_without_override(self):
        with patch("site_cms.fetch_published_articles", return_value=articles()), \
             patch("site_cms._public_reads_or_none", return_value={"article-15": 100}), \
             patch("thinking_core.query_value", return_value="2") as query:
            rendered = inject_cms_landing(DOCUMENT)
        query.assert_called_once_with("articles_page")
        self.assertIn("Showing 7–12 of 14 articles", rendered)


if __name__ == "__main__":
    unittest.main()
