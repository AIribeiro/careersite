from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class ThinkingPublishingTests(unittest.TestCase):
    def test_registry_has_complete_unique_social_ready_metadata(self) -> None:
        from thinking_articles import (
            ARTICLES,
            article_app_url,
            article_share_url,
            article_social_image_url,
            article_url,
        )

        self.assertEqual(len(ARTICLES), 8)
        self.assertEqual(len({article.key for article in ARTICLES}), len(ARTICLES))
        self.assertEqual(len({article.slug for article in ARTICLES}), len(ARTICLES))

        for article in ARTICLES:
            with self.subTest(article=article.key):
                self.assertGreaterEqual(len(article.seo_description), 90)
                self.assertLessEqual(len(article.seo_description), 170)
                self.assertLessEqual(len(article.seo_title), 75)
                self.assertTrue(article.tags)
                self.assertTrue(article.published_iso.startswith("2026-"))
                self.assertTrue(article_url(article).endswith(f"/thinking/{article.slug}"))
                self.assertEqual(article_share_url(article), article_url(article))
                self.assertTrue(article_social_image_url(article).endswith(f"/social/{article.slug}.png"))
                self.assertIn(f"article={article.slug}", article_app_url(article))

    def test_legacy_article_slugs_resolve_to_canonical_metadata(self) -> None:
        from thinking_articles import ARTICLES, resolve_article

        for article in ARTICLES:
            self.assertIs(resolve_article(article.slug), article)
            for alias in article.aliases:
                with self.subTest(alias=alias):
                    self.assertIs(resolve_article(alias), article)

    def test_every_article_generates_valid_social_image_and_crawler_page(self) -> None:
        from thinking_articles import ARTICLES, article_app_url, article_social_image_url, article_url
        from thinking_social import ensure_article_social_assets

        for article in ARTICLES:
            with self.subTest(article=article.key):
                image_path, html_path = ensure_article_social_assets(article)
                self.assertTrue(image_path.exists())
                self.assertTrue(html_path.exists())
                self.assertGreater(image_path.stat().st_size, 40_000)

                with Image.open(image_path) as image:
                    self.assertEqual(image.format, "PNG")
                    self.assertEqual(image.size, (1200, 630))

                share_html = html_path.read_text(encoding="utf-8")
                self.assertIn('property="og:type" content="article"', share_html)
                self.assertIn('name="twitter:card" content="summary_large_image"', share_html)
                self.assertIn('property="article:published_time"', share_html)
                self.assertIn('type="application/ld+json"', share_html)
                self.assertIn(article_social_image_url(article), share_html)
                self.assertIn(article_url(article), share_html)
                self.assertIn(article_app_url(article).replace("&", "&amp;"), share_html)
                self.assertIn("window.location.replace", share_html)

    def test_article_metadata_share_controls_and_asgi_routes_are_wired(self) -> None:
        meta = (ROOT / "src/site_meta.py").read_text(encoding="utf-8")
        core = (ROOT / "src/thinking_core.py").read_text(encoding="utf-8")
        launcher = (ROOT / "app.py").read_text(encoding="utf-8")
        main = (ROOT / "main.py").read_text(encoding="utf-8")

        self.assertIn("inject_article_metadata", meta)
        self.assertIn("article:published_time", meta)
        self.assertIn("data-jair-article", meta)
        self.assertIn("data-copy-url", core)
        self.assertIn("linkedin.com/sharing/share-offsite", core)
        self.assertIn("twitter.com/intent/tweet", core)
        self.assertIn("mailto:?subject=", core)
        self.assertIn('Route("/thinking/{slug}"', launcher)
        self.assertIn('Route("/social/{slug}.png"', launcher)
        self.assertIn('Route("/sitemap.xml"', launcher)
        self.assertIn("st.App(", launcher)
        self.assertIn("ensure_all_article_social_assets", main)
        self.assertIn("ARTICLE_META.seo_title", main)


if __name__ == "__main__":
    unittest.main()
