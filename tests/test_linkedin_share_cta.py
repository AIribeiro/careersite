from __future__ import annotations

from html import unescape
from urllib.parse import parse_qs, urlparse
import re
import unittest

from thinking_articles import ARTICLES
from thinking_core import X_CARD_VERSION, _share_footer


class SocialShareCtaTests(unittest.TestCase):
    def test_every_article_cta_passes_full_pages_url_to_linkedin_feed(self) -> None:
        for article in ARTICLES:
            with self.subTest(article=article.slug):
                rendered = unescape(_share_footer(article.key))
                match = re.search(
                    r'href="([^"]+)"[^>]+data-share-target="([^"]+)"[^>]+data-hq-event="article_share_linkedin"',
                    rendered,
                )
                self.assertIsNotNone(match)
                href, target = match.groups()

                parsed_target = urlparse(target)
                self.assertEqual(parsed_target.scheme, "https")
                self.assertEqual(parsed_target.netloc, "airibeiro.github.io")
                self.assertEqual(
                    parsed_target.path,
                    f"/careersite/thinking/{article.slug}/",
                )
                self.assertEqual(parse_qs(parsed_target.query).get("source"), ["linkedin"])

                parsed = urlparse(href)
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.netloc, "www.linkedin.com")
                self.assertEqual(parsed.path, "/feed/")

                params = parse_qs(parsed.query)
                self.assertEqual(params.get("shareActive"), ["true"])
                self.assertEqual(params.get("shareUrl"), [target])
                self.assertIn(f"/thinking/{article.slug}/", params["shareUrl"][0])

    def test_every_article_x_cta_uses_fresh_x_specific_pages_url(self) -> None:
        for article in ARTICLES:
            with self.subTest(article=article.slug):
                rendered = unescape(_share_footer(article.key))
                match = re.search(
                    r'href="([^"]+)"[^>]+data-share-target="([^"]+)"[^>]+data-hq-event="article_share_x"',
                    rendered,
                )
                self.assertIsNotNone(match)
                href, target = match.groups()

                parsed_target = urlparse(target)
                self.assertEqual(parsed_target.netloc, "airibeiro.github.io")
                self.assertEqual(
                    parsed_target.path,
                    f"/careersite/thinking/{article.slug}/",
                )
                target_params = parse_qs(parsed_target.query)
                self.assertEqual(target_params.get("source"), ["x"])
                self.assertEqual(target_params.get("v"), [X_CARD_VERSION])

                parsed = urlparse(href)
                self.assertEqual(parsed.netloc, "twitter.com")
                self.assertEqual(parsed.path, "/intent/tweet")
                params = parse_qs(parsed.query)
                self.assertEqual(params.get("url"), [target])
                self.assertEqual(params.get("text"), [article.social_title])

    def test_legacy_share_offsite_launcher_is_not_used(self) -> None:
        for article in ARTICLES:
            rendered = _share_footer(article.key)
            self.assertNotIn("linkedin.com/sharing/share-offsite", rendered)


if __name__ == "__main__":
    unittest.main()
