"""Regression checks for portfolio page size and Thinking document structure."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import site_media  # Bind public asset URLs before page imports.
from site_cms import CmsArticle, inject_cms_landing
from thinking_landing import landing
from thinking_weekly_brief import _edition_cover_html


class PortfolioPerformanceTests(unittest.TestCase):
    def test_photographs_and_badges_use_cacheable_urls(self):
        for url in (
            site_media.hero,
            site_media.thinking,
            site_media.panel_dialogue,
            site_media.brand_icon,
            site_media.openai_ai_leadership,
        ):
            self.assertTrue(url.startswith("/media/"), url[:80])
            self.assertIn("?v=", url)
            self.assertIn("&w=", url)
            self.assertNotIn("data:image", url)
        self.assertIn("&w=160", site_media.brand_icon)

    def test_thinking_catalogue_keeps_one_correct_anchor_in_main(self):
        article = CmsArticle(
            id="sample", title="A decision worth examining",
            slug="a-decision-worth-examining", status="published",
            kind="Point of view", category="Enterprise AI",
            published_at="2026-10-15T00:00:00+00:00",
        )
        with patch("site_cms.fetch_published_articles", return_value=(article,)), \
             patch("site_cms._public_reads_or_none", return_value={}):
            output = inject_cms_landing(landing())

        self.assertEqual(output.count('id="thinking-articles"'), 1)
        self.assertEqual(output.count('id="articles-catalog"'), 1)
        self.assertLess(output.index("<nav"), output.index('id="thinking-articles"'))
        self.assertLess(output.index('id="thinking-briefings"'), output.index('id="thinking-articles"'))
        self.assertLess(output.index('id="thinking-articles"'), output.index("Longer perspectives"))
        self.assertIn('data-hq-event="cms_article_open"', output)
        self.assertLess(len(output.encode("utf-8")), 300_000)
        self.assertNotIn("data:image/jpeg;base64,", output)

    def test_weekly_cover_does_not_embed_png_bytes(self):
        output = _edition_cover_html("weekly-ai-2026-10-30")
        self.assertIn('/weekly-ai-cover/weekly-ai-2026-10-30.png', output)
        self.assertNotIn("base64,", output)


if __name__ == "__main__":
    unittest.main()
