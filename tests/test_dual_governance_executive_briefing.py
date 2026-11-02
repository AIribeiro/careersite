from __future__ import annotations

import unittest
from types import SimpleNamespace

from data_vs_ai_governance_briefing import DUAL_GOV_CSS, dual_governance_briefing_article
from page_executive_briefings import DUAL_GOV_SLUG, _briefing_catalog_art


class DualGovernanceExecutiveBriefingTests(unittest.TestCase):
    def make_article(self):
        return SimpleNamespace(
            title="Data Governance vs AI Governance: Two Controls, One Business Decision",
            subtitle="Evidence, ownership and permission to act",
            excerpt="A joint decision test",
            content_html="<h2>Full original perspective</h2><p>Field-informed anonymized service example.</p>",
            published_at="",
            published_label="",
            read_minutes=8,
        )

    def test_reader_keeps_full_cms_content_visible(self):
        html = dual_governance_briefing_article(
            self.make_article(), "", "", "", "", "", "",
        )
        self.assertIn("Full original perspective", html)
        self.assertIn("Field-informed anonymized service example.", html)
        self.assertIn("Two evidence streams. One approval.", html)
        self.assertIn("Should this workflow be allowed to operate?", html)
        self.assertIn("Proceed · Restrict · Test · Stop", html)
        self.assertIn('href="?page=contact"', html)
        self.assertIn("data-analytics-section", html)
        self.assertNotIn('<details class="briefing-reader-detail"', html)

    def test_mobile_reader_and_unique_collection_art(self):
        self.assertIn("@media(max-width:650px)", DUAL_GOV_CSS)
        art = _briefing_catalog_art(DUAL_GOV_SLUG)
        self.assertIn("BUSINESS RELEASE GATE", art)
        self.assertIn("DATA<br>FITNESS", art)
        self.assertIn("AI<br>ASSURANCE", art)

    def test_no_employer_references_or_borrowed_six_row_visual(self):
        html = dual_governance_briefing_article(
            self.make_article(), "", "", "", "", "", "",
        )
        self.assertNotIn("Six differences", html)
        self.assertNotIn("Volvo", html)
        self.assertNotIn("MSX", html)


if __name__ == "__main__":
    unittest.main()
