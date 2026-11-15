from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_social_http import (
    PAGE_META, SITE_IMAGE, homepage_social_html, is_social_crawler,
)


class NativeStreamlitSocialPreviewTests(unittest.TestCase):
    def test_root_html_exposes_full_crawler_visible_og(self):
        document = homepage_social_html("home")
        self.assertIsNotNone(document)
        self.assertIn('<meta property="og:image" content="' + SITE_IMAGE + '">', document)
        self.assertIn('property="og:image:width" content="1200"', document)
        self.assertIn('property="og:image:height" content="630"', document)
        self.assertIn('name="twitter:card" content="summary_large_image"', document)
        self.assertIn('rel="image_src"', document)
        self.assertIn('property="og:site_name" content="Jair Ribeiro"', document)
        self.assertIn('rel="canonical" href="https://jairribeiro.com/"', document)
        self.assertNotIn("<iframe", document)
        self.assertNotIn("<script", document)

    def test_public_page_metadata_is_distinct(self):
        home = homepage_social_html("home")
        for page in ("advisory", "thinking", "briefings", "ai-data-governance"):
            with self.subTest(page=page):
                html = homepage_social_html(page)
                self.assertNotEqual(html, home)
                self.assertIn("og:image", html)
                self.assertIn("?page=" + page, html)

    def test_social_crawlers_only(self):
        for agent in ("LinkedInBot/1.0", "facebookexternalhit/1.1", "Twitterbot/1.0", "Slackbot-LinkExpanding", "WhatsApp/2.0"):
            self.assertTrue(is_social_crawler(agent), agent)
        for agent in ("Mozilla/5.0 Safari/605", "Googlebot/2.1", ""):
            self.assertFalse(is_social_crawler(agent), agent)

    def test_private_and_member_routes_not_in_public_metadata(self):
        for page in ("readers", "readers-admin", "analytics", "admin", "owner", "login", "advisory-admin"):
            self.assertNotIn(page, PAGE_META)
            self.assertIsNone(homepage_social_html(page))


if __name__ == "__main__":
    unittest.main()
