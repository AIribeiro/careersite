"""Regression coverage for the published faster-business article short links."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_shortlinks import expand_shortlink, short_article_link


class FasterBusinessShortLinkTests(unittest.TestCase):
    def test_channel_links_are_distinct_and_fully_attributed(self):
        slug = "ai-can-make-every-team-faster-and-still-leave-the-business-slow"
        expected = {
            "linkedin": ("fl", "social"),
            "x": ("fx", "social"),
            "threads": ("ft", "social"),
            "facebook": ("ff", "social"),
            "whatsapp": ("fw", "messaging"),
        }
        for channel, (code, medium) in expected.items():
            with self.subTest(channel=channel):
                self.assertEqual(
                    short_article_link(slug, channel),
                    f"https://airibeiro.github.io/careersite/go/{code}/",
                )
                self.assertEqual(expand_shortlink(code), {
                    "page": "thinking",
                    "article": slug,
                    "source": channel,
                    "role": "article",
                    "utm_source": channel,
                    "utm_medium": medium,
                    "utm_campaign": "thinking",
                    "utm_content": slug,
                })


if __name__ == "__main__":
    unittest.main()
