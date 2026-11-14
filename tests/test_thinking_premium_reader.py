"""Thinking-page Premium Reader section and unified library copy contracts."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thinking_landing import landing
from thinking_reader_invitation import reader_invitation
from site_reader_shell import reader_header


class ThinkingPremiumReaderTests(unittest.TestCase):
    def test_invitation_sits_between_thinking_hero_and_editorial_collections(self):
        rendered = landing()
        self.assertIn('id="premium-reader-library"', rendered)
        self.assertLess(rendered.index('class="pagehero"'), rendered.index('id="premium-reader-library"'))
        self.assertLess(rendered.index('id="premium-reader-library"'), rendered.index('id="thinking-briefings"'))
        self.assertLess(rendered.index('id="premium-reader-library"'), rendered.index('id="thinking-articles"'))

    def test_access_copy_leads_with_executive_value_not_access_timers(self):
        rendered = reader_invitation()
        self.assertIn("Premium Reader Library · Free registration", rendered)
        self.assertIn("Read the reasoning behind the decision.", rendered)
        self.assertIn("Examine the decision criteria.", rendered)
        self.assertIn("Assess what matters this week.", rendered)
        self.assertIn("Review the assumptions and implications.", rendered)
        for format_name in ("Executive AI Briefings", "Weekly AI", "Leadership articles"):
            self.assertIn(format_name, rendered)
        self.assertIn("decision frameworks and original infographics", rendered)
        self.assertIn("the original reporting behind them", rendered)
        self.assertIn("prioritization, accountability, governance", rendered)
        self.assertIn("Save relevant briefings", rendered)
        self.assertIn("Registration is free.", rendered)
        self.assertIn("No payment details", rendered)
        self.assertIn("editorial emails", rendered)
        self.assertIn("Access at a glance", rendered)
        self.assertIn("Premium Articles", rendered)
        self.assertIn("Executive AI Briefings", rendered)
        self.assertNotIn("until another Article is published", rendered)
        self.assertNotIn("when a newer Article is published", rendered)
        self.assertNotIn("seven days", rendered.lower())
        self.assertNotIn("day 7", rendered.lower())
        self.assertNotIn("guaranteed", rendered.lower())
        # Make the content-value argument before access conditions appear.
        self.assertLess(rendered.index("Examine the decision criteria."), rendered.index("Access at a glance"))

    def test_registration_and_discovery_are_first_party_links(self):
        rendered = reader_invitation()
        self.assertIn('href="?page=readers"', rendered)
        self.assertIn('href="?page=briefings"', rendered)
        self.assertIn('target="_self"', rendered)
        self.assertIn('data-hq-event="thinking_premium_reader_access"', rendered)

    def test_unified_reader_hero_recognizes_both_formats(self):
        rendered = reader_header()
        self.assertIn("The analysis behind consequential AI decisions.", rendered)
        self.assertIn("complete current articles", rendered)
        self.assertIn("Executive AI Briefings", rendered)
        self.assertIn("A4 briefing infographics", rendered)
        self.assertNotIn("until another Article is published", rendered)
        self.assertNotIn("at least seven days", rendered)

    def test_article_library_status_labels_are_reader_focused(self):
        native = (SRC / "page_reader_native.py").read_text("utf-8")
        self.assertIn("PREMIUM ARTICLE · FULL ACCESS", native)
        self.assertIn('"OPEN ACCESS"', native)
        self.assertIn("article_is_locked(item, published=editorial)", native)
        self.assertNotIn("Premium until another Article is published", native)
        self.assertNotIn("The latest Article stays Premium until", native)

    def test_cms_injection_preserves_invitation_on_thinking_page(self):
        from page_thinking import _thinking_landing_with_catalog
        with patch("page_thinking.inject_cms_landing", side_effect=lambda page: page):
            rendered = _thinking_landing_with_catalog()
        self.assertEqual(rendered.count('id="premium-reader-library"'), 1)
        self.assertIn('id="thinking-briefings"', rendered)


if __name__ == "__main__":
    unittest.main()
