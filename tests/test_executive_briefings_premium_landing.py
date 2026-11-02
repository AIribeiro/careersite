"""Contract tests for the executive briefing collection's editorial landing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from page_executive_briefings import executive_briefings
from briefings_landing_premium import PREMIUM_BRIEFINGS_CSS


def article(slug: str, date: str, title: str):
    return SimpleNamespace(
        slug=slug,
        title=title,
        subtitle="A decision-focused briefing",
        excerpt="A decision-focused briefing",
        published_at=date,
        published_label="2 Nov 2026",
        read_minutes=7,
    )


def render(articles):
    with (
        patch("page_executive_briefings.published_briefings", return_value=articles),
        patch("page_executive_briefings.nav", return_value=""),
        patch("page_executive_briefings.footer", return_value=""),
        patch("page_executive_briefings.contact_block", return_value=""),
        patch("page_executive_briefings.article_relative_url",
              side_effect=lambda a: f"?page=briefing&article={a.slug}"),
    ):
        return executive_briefings().rsplit("</style>", 1)[-1]


class PremiumBriefingsLandingTest(unittest.TestCase):
    def test_latest_is_featured_and_every_publication_has_one_url(self):
        older = article("ai-governance-explained-to-executives", "2026-10-30", "Governance")
        newest = article("eu-ai-act-what-executives-must-decide", "2026-11-02", "EU AI Act")
        other = article("seven-questions-for-better-ai-decisions", "2026-10-31", "Questions")
        page = render((older, other, newest))

        self.assertEqual(page.count('class="briefings-library-card"'), 3)
        self.assertEqual(page.count('data-hq-event="briefings_featured_open"'), 1)
        self.assertEqual(page.count('data-hq-event="briefings_article_open"'), 2)
        self.assertEqual(page.count('href="?page=briefing&amp;article='), 3)
        feature = page.split('<div class="be-feature">', 1)[1].split("</div></a></div>", 1)[0]
        self.assertIn("EU AI Act", feature)
        self.assertNotIn("<svg", page)
        self.assertNotIn("<img", page)
        self.assertIn('id="briefings-library"', page)
        self.assertIn("03 PUBLISHED BRIEFINGS", page)

    def test_escapes_cms_titles_and_does_not_inline_article_bodies(self):
        data = (article("some-article", "2026-11-02", "<script>alert(1)</script>"),)
        page = render(data)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertEqual(page.count('class="briefings-library-card"'), 1)

    def test_empty_state_still_has_a_useful_page(self):
        page = render(())
        self.assertIn("The library is being prepared.", page)
        self.assertEqual(page.count('class="briefings-library-card"'), 0)
        self.assertIn("00 PUBLISHED BRIEFINGS", page)
        self.assertIn("Executive AI Briefings", page)

    def test_mobile_and_reduced_motion_rules_have_first_party_fallback(self):
        self.assertIn("@media(max-width:740px)", PREMIUM_BRIEFINGS_CSS)
        self.assertIn("@media(prefers-reduced-motion:reduce)", PREMIUM_BRIEFINGS_CSS)
        self.assertIn(".site .be-collection .briefings-library-grid", PREMIUM_BRIEFINGS_CSS)
        self.assertNotIn("@import", PREMIUM_BRIEFINGS_CSS)
        self.assertNotIn("<script", PREMIUM_BRIEFINGS_CSS)
        self.assertNotIn("url(http", PREMIUM_BRIEFINGS_CSS)


if __name__ == "__main__":
    unittest.main()
