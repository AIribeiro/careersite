"""Portfolio campaign link integrity, truthfulness and CMS sharing."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse
import inspect
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from site_campaign_links import (
    CHANNEL_MEDIA, canonical_channel, make_distribution_link,
)


class AttributionLinkTests(unittest.TestCase):
    def test_channels_have_canonical_names_and_media(self):
        self.assertEqual(canonical_channel("LiNkEdIn"), "linkedin")
        self.assertEqual(canonical_channel("thre"), "threads")
        self.assertEqual(canonical_channel("twitter"), "x")
        self.assertEqual(canonical_channel("fb"), "facebook")
        self.assertIn("whatsapp", CHANNEL_MEDIA)
        with self.assertRaises(ValueError):
            canonical_channel("unknown")

    def test_article_tracking_preserves_original_permalink_and_creates_all_tags(self):
        base = "https://jairribeiro-ai.streamlit.app/thinking/ai-portfolio"
        url = make_distribution_link(
            base, channel="LinkedIn", campaign="thinking",
            content="ai-portfolio",
        )
        parsed = urlparse(url)
        self.assertEqual(parsed.path, "/thinking/ai-portfolio")
        params = parse_qs(parsed.query)
        for name, value in (
            ("source", "linkedin"), ("utm_source", "linkedin"),
            ("utm_medium", "social"), ("utm_campaign", "thinking"),
            ("utm_content", "ai-portfolio"),
        ):
            self.assertEqual(params[name], [value])

    def test_weekly_ai_and_portfolio_targets_keep_selection(self):
        url = make_distribution_link(
            "https://jairribeiro-ai.streamlit.app/?page=thinking&weekly_ai=archive",
            channel="whatsapp", campaign="weekly_ai_2026_w42",
        )
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["page"], ["thinking"])
        self.assertEqual(params["weekly_ai"], ["archive"])
        self.assertEqual(params["utm_medium"], ["messaging"])

    def test_replace_stale_tags_without_duplicate_conflicting_sources(self):
        base = ("https://jairribeiro-ai.streamlit.app/?page=thinking"
                "&article=my-article&source=thre&role=dailyquote"
                "&utm_source=x&utm_campaign=old&utm_content=old")
        url = make_distribution_link(
            base, channel="facebook", campaign="dailyquote",
            content="my-article",
        )
        parts = parse_qs(urlparse(url).query)
        self.assertEqual(parts["source"], ["facebook"])
        self.assertEqual(parts["utm_source"], ["facebook"])
        self.assertEqual(parts["utm_campaign"], ["dailyquote"])
        self.assertEqual(parts["utm_content"], ["my-article"])
        self.assertNotIn("role", parts)
        for key in ("source", "utm_source", "utm_campaign", "utm_content"):
            self.assertEqual(len(parts[key]), 1)
        self.assertEqual(parts["article"], ["my-article"])

    def test_reject_malicious_external_or_personalized_link_destinations(self):
        for target in (
            "https://example.com/",
            "http://jairribeiro-ai.streamlit.app/",
            "https://jairribeiro-ai.streamlit.app.evil.test/",
            "https://user@jairribeiro-ai.streamlit.app/",
            "https://jairribeiro-ai.streamlit.app/admin",
        ):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    make_distribution_link(target, channel="linkedin",
                                           campaign="thinking")
        with self.assertRaises(ValueError):
            make_distribution_link(
                "https://jairribeiro-ai.streamlit.app/",
                channel="linkedin", campaign="user@example.com")

    def test_automated_social_share_controls_are_channel_tagged(self):
        from site_cms import CmsArticle, _share_footer
        from thinking_core import _share_footer as bundled_footer
        from thinking_articles import ARTICLES

        cms = CmsArticle()
        cms.slug = "ai-portfolio"
        cms.title = "AI Portfolio"
        cms.status = "published"
        rendered = _share_footer(cms)
        self.assertIn("utm_source%3Dlinkedin", rendered)
        self.assertIn("utm_source%3Dx", rendered)
        self.assertIn("source%3Demail", rendered)
        self.assertIn('data-copy-url=', rendered)
        self.assertNotIn('data-copy-url="https://jairribeiro-ai.streamlit.app/thinking/ai-portfolio?source=', rendered)
        bundled = bundled_footer(ARTICLES[0].key)
        self.assertIn("utm_source%3Demail", bundled)

    def test_linkedin_share_offsite_uses_crawlable_cms_article_permalink(self):
        from html import unescape
        import re
        from site_cms import CmsArticle, _share_footer
        from site_campaign_links import linkedin_share_url
        from thinking_articles import ARTICLES
        from thinking_core import _share_footer as bundled_footer

        slug = "ai-is-entering-the-management-layer-leadership-has-to-catch-up"
        markup = _share_footer(CmsArticle(
            title="AI Is Entering the Management Layer", slug=slug,
            status="published",
        ))
        match = re.search(r'href="([^"]+)"[^>]+data-hq-event="article_share_linkedin"', markup)
        self.assertIsNotNone(match, "CMS article must render a LinkedIn sharing anchor")
        parsed = urlparse(unescape(match.group(1)))
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "www.linkedin.com")
        self.assertEqual(parsed.path, "/sharing/share-offsite/")
        self.assertEqual(set(parse_qs(parsed.query)), {"url"})
        target = urlparse(parse_qs(parsed.query)["url"][0])
        self.assertEqual(target.netloc, "jairribeiro-ai.streamlit.app")
        self.assertEqual(target.path, f"/thinking/{slug}")
        inner = parse_qs(target.query)
        self.assertEqual(inner["utm_source"], ["linkedin"])
        self.assertEqual(inner["utm_medium"], ["social"])
        self.assertEqual(inner["utm_campaign"], ["thinking"])
        self.assertEqual(inner["utm_content"], [slug])
        self.assertNotIn("/feed/", markup)
        # Copied links remain clean permalink URLs, not tagged by assumption.
        self.assertIn(f'data-copy-url="https://jairribeiro-ai.streamlit.app/thinking/{slug}"', markup)

        bundled = bundled_footer(ARTICLES[0].key)
        match = re.search(r'href="([^"]+)"[^>]+data-share-target="([^"]+)"[^>]+data-hq-event="article_share_linkedin"', bundled)
        self.assertIsNotNone(match)
        target = parse_qs(urlparse(unescape(match.group(1))).query)["url"][0]
        self.assertEqual(target, unescape(match.group(2)))
        self.assertIn("airibeiro.github.io/careersite/thinking/", target)
        self.assertNotIn("/feed/", bundled)

        with self.assertRaises(ValueError):
            linkedin_share_url("https://malicious.example/steal")
        with self.assertRaises(ValueError):
            linkedin_share_url("http://jairribeiro-ai.streamlit.app/")

    def test_private_cms_has_generator_not_public_analytics(self):
        import page_admin
        source = inspect.getsource(page_admin._dashboard)
        self.assertIn("_distribution_links(articles)", source)
        self.assertIn("cms_edit_id", source)
        from page_analytics_v2 import _VIEWS
        self.assertNotIn("CMS", list(_VIEWS.values()))


if __name__ == "__main__":
    unittest.main()
