from __future__ import annotations

from html import unescape
from urllib.parse import parse_qs, urlparse
import re
import unittest

from thinking_articles import ARTICLES
from thinking_core import _share_footer


class LinkedInShareCtaTests(unittest.TestCase):
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

                expected_target = (
                    f"https://airibeiro.github.io/careersite/thinking/{article.slug}/"
                )
                self.assertEqual(target, expected_target)

                parsed = urlparse(href)
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.netloc, "www.linkedin.com")
                self.assertEqual(parsed.path, "/feed/")

                params = parse_qs(parsed.query)
                self.assertEqual(params.get("shareActive"), ["true"])
                self.assertEqual(params.get("shareUrl"), [expected_target])
                self.assertIn(f"/thinking/{article.slug}/", params["shareUrl"][0])

    def test_legacy_share_offsite_launcher_is_not_used(self) -> None:
        for article in ARTICLES:
            rendered = _share_footer(article.key)
            self.assertNotIn("linkedin.com/sharing/share-offsite", rendered)


if __name__ == "__main__":
    unittest.main()
