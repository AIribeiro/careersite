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

    def test_access_copy_is_specific_truthful_and_complimentary(self):
        rendered = reader_invitation()
        self.assertIn("Premium Reader library · Complimentary access", rendered)
        self.assertIn("Executive AI Briefings", rendered)
        self.assertIn("Articles · Seven-day early access", rendered)
        self.assertIn("After seven days", rendered)
        self.assertIn("Save briefings", rendered)
        self.assertIn("original A4 infographic where one is available", rendered)
        self.assertIn("Premium Reader access is currently free.", rendered)
        self.assertIn("No payment details", rendered)
        self.assertIn("Editorial emails are optional", rendered)
        self.assertNotIn("all articles are members-only", rendered.lower())
        self.assertNotIn("guaranteed", rendered.lower())

    def test_registration_and_discovery_are_first_party_links(self):
        rendered = reader_invitation()
        self.assertIn('href="?page=readers"', rendered)
        self.assertIn('href="?page=briefings"', rendered)
        self.assertIn('target="_self"', rendered)
        self.assertIn('data-hq-event="thinking_premium_reader_access"', rendered)

    def test_unified_reader_hero_recognizes_both_formats(self):
        rendered = reader_header()
        self.assertIn("Your executive reading library", rendered)
        self.assertIn("seven-day early access", rendered)
        self.assertIn("Executive AI Briefings", rendered)
        self.assertIn("A4 infographic PDFs", rendered)
        self.assertIn("Older Articles remain open to everyone", rendered)

    def test_cms_injection_preserves_invitation_on_thinking_page(self):
        from page_thinking import _thinking_landing_with_catalog
        with patch("page_thinking.inject_cms_landing", side_effect=lambda page: page):
            rendered = _thinking_landing_with_catalog()
        self.assertEqual(rendered.count('id="premium-reader-library"'), 1)
        self.assertIn('id="thinking-briefings"', rendered)


if __name__ == "__main__":
    unittest.main()
