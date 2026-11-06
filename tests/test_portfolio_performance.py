"""Regression checks for portfolio page size and Thinking document structure."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import site_media  # Bind public asset URLs before page imports.
from site_cms import CmsArticle, inject_cms_landing, reader_header_image_src
from thinking_landing import landing
from thinking_weekly_brief import _edition_cover_html, _weekly_header_image_uri
from page_home_featured import HomeArticlePreview, home_featured_article


class PortfolioPerformanceTests(unittest.TestCase):
    def test_photographs_and_badges_use_browser_accessible_urls(self):
        for url in (
            site_media.hero,
            site_media.thinking,
            site_media.panel_dialogue,
            site_media.brand_icon,
            site_media.openai_ai_leadership,
        ):
            self.assertTrue(url.startswith("https://raw.githubusercontent.com/AIribeiro/careersite/main/images/"), url[:100])
            self.assertIn("?v=", url)
            self.assertNotIn("data:image", url)
        self.assertTrue(
            "profile_red_bg.jpg.jpg?v=" in site_media.brand_icon
            or "profile_red_bg.jpg.jpg.160.webp?v=" in site_media.brand_icon
        )
        self.assertNotIn("&w=", site_media.brand_icon)
        self.assertNotIn("/portfolio-image/", site_media.hero)

    def test_optimized_photography_is_reliable_and_bounded(self):
        from pathlib import Path
        from PIL import Image
        root = Path(__file__).resolve().parents[1]
        original = root / "images" / "profile_red_bg.jpg.jpg"
        optimized = root / "images" / "optimized" / "profile_red_bg.jpg.jpg.160.webp"
        if optimized.exists():
            self.assertLess(optimized.stat().st_size, original.stat().st_size)
            with Image.open(optimized) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertLessEqual(image.width, 160)
            self.assertIn("optimized/profile_red_bg.jpg.jpg.160.webp?v=", site_media.brand_icon)
        else:
            self.assertIn("profile_red_bg.jpg.jpg?v=", site_media.brand_icon)

    def test_thinking_catalogue_keeps_one_correct_anchor_in_main(self):
        article = CmsArticle(
            id="sample", title="A decision worth examining",
            slug="a-decision-worth-examining", status="published",
            kind="Point of view", category="Enterprise AI",
            published_at="2026-10-15T00:00:00+00:00",
        )
        another = CmsArticle(
            id="another", title="Another article",
            slug="another-article", status="published",
            kind="Article", category="Enterprise AI",
            published_at="2026-10-10T00:00:00+00:00",
        )
        with patch("site_cms.fetch_published_articles", return_value=(article, another)), \
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
        self.assertIn('/weekly-ai-cover/weekly-ai-2026-10-30.png?v=', output)
        self.assertNotIn('/app/static/weekly-ai/', output)
        self.assertNotIn("base64,", output)
        self.assertEqual(_weekly_header_image_uri(), "/weekly-ai-cover/evergreen.webp")

    def test_home_feature_uses_premium_fallback_for_unreliable_social_route(self):
        preview = HomeArticlePreview(
            slug="example", title="Example article", deck="A summary.",
            kind_topic="Point of view · Enterprise AI",
            published_label="4 Nov 2026", read_minutes=3, href="?page=thinking&article=example",
            image_url="https://jairribeiro-ai.streamlit.app/social/example.png",
            image_alt="Example cover",
        )
        with patch("page_home_featured.current_home_article", return_value=preview):
            html = home_featured_article()
        self.assertIn('class="home-featured-art-fallback"', html)
        self.assertNotIn('src="https://jairribeiro-ai.streamlit.app/social/example.png"', html)

    def test_reader_preserves_one_original_bundled_webp_without_media_route(self):
        article = CmsArticle(slug="example", title="Example")
        with patch("site_cms.bundled_header_bytes", return_value=b"RIFFtestWEBP"):
            url = reader_header_image_src(article)
        self.assertTrue(url.startswith("data:image/webp;base64,"))
        self.assertNotIn("/cms-header/", url)


if __name__ == "__main__":
    unittest.main()
