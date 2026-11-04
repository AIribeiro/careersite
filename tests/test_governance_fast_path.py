"""Governance-page fast path: published writing, no synchronous CMS dependency."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from governance_writing_snapshot import GOVERNANCE_WRITING
from page_home_featured import (
    current_governance_writing,
    inject_writing_footer,
)


class GovernanceFastPathTests(unittest.TestCase):
    def test_snapshot_has_both_published_editorial_formats(self):
        self.assertGreaterEqual(len(GOVERNANCE_WRITING), 8)
        self.assertIn("Executive Briefing", {x[3] for x in GOVERNANCE_WRITING})
        self.assertTrue(any(x[3] != "Executive Briefing" for x in GOVERNANCE_WRITING))
        self.assertEqual(len({x[1] for x in GOVERNANCE_WRITING}), len(GOVERNANCE_WRITING))
        for title, slug, deck, kind, category, minutes, published in GOVERNANCE_WRITING:
            self.assertTrue(title and slug and deck and category and published)
            self.assertTrue(minutes > 0)
            self.assertFalse(slug.startswith("weekly-ai-"))

    def test_home_instant_preview_uses_full_published_snapshot(self):
        from site_writing_snapshot import PUBLIC_WRITING_SNAPSHOT
        from page_home_featured import home_featured_article
        self.assertGreaterEqual(len(PUBLIC_WRITING_SNAPSHOT), 20)
        self.assertTrue(any(x["kind"] == "Executive Briefing" for x in PUBLIC_WRITING_SNAPSHOT))
        self.assertTrue(any(x["kind"] != "Executive Briefing" for x in PUBLIC_WRITING_SNAPSHOT))
        with patch("page_home_featured.current_home_article",
                   side_effect=AssertionError("CMS must not block instant Home preview")):
            html = home_featured_article(instant=True)
        self.assertIn('class="home-featured-story"', html)

    def test_governance_footer_does_not_call_live_cms_lookup(self):
        sample = "<main><section>Governance content</section></main>"
        with patch("page_home_featured.current_home_article",
                   side_effect=AssertionError("Unexpected blocking CMS fetch")):
            rendered = inject_writing_footer(sample, "ai-data-governance")
        self.assertIn("Governance content", rendered)
        self.assertEqual(rendered.count('data-analytics-section="site-writing-footer"'), 1)
        self.assertIn("writing-footer-art", rendered)

    def test_randomized_contextual_link_points_to_a_real_published_item(self):
        for source in GOVERNANCE_WRITING:
            with patch("page_home_featured.choice", return_value=source):
                item = current_governance_writing()
            expected_page = "briefing" if source[3] == "Executive Briefing" else "thinking"
            self.assertEqual(item.href, f"?page={expected_page}&article={source[1]}")
            self.assertEqual(item.content_type, expected_page if expected_page == "briefing" else "article")

    def test_page_loader_does_not_eagerly_import_every_other_public_page(self):
        app = (Path(__file__).resolve().parents[1] / "main.py").read_text()
        split = app.index('if PAGE == "analytics":')
        self.assertNotIn("from page_executive_briefings import", app[:split])
        self.assertNotIn("from page_thinking import", app[:split])
        self.assertNotIn("from page_home import", app[:split])
        self.assertNotIn("from site_cms import", app[:app.index("if ARTICLE_QUERY:")])
        self.assertIn('local_fast=(page == "ai-data-governance")',
                      (Path(__file__).resolve().parents[1] /
                       "src/page_home_featured.py").read_text())


if __name__ == "__main__":
    unittest.main()
