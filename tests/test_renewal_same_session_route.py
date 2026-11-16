"""Renewal A4 download must retain the same verified WebSocket session.

The navigation parser is the security boundary for first-party HTML links.
The real Playwright check in reader_navigation_browser_smoke exercises the
actual Streamlit component and confirms the authenticated session marker stays.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from site_reader_navigation import _parse_portfolio_route, _JS
from briefing_renewal_worksheet import SLUG, decision_record_cta_html


class RenewalSameSessionLinkTests(unittest.TestCase):
    def test_exact_authenticated_reader_worksheet_route_is_intercepted(self):
        html = decision_record_cta_html()
        self.assertIn("worksheet=1", html)
        self.assertIn('target="_self"', html)
        self.assertIn("worksheet", _JS)
        params = _parse_portfolio_route(
            "?page=briefing&article=" + SLUG + "&worksheet=1"
        )
        self.assertEqual(params, {
            "page": "briefing", "article": SLUG, "worksheet": "1",
        })

    def test_other_download_routes_cannot_abuse_authenticated_bridge(self):
        for url in (
            "?page=briefing&article=other-issue&worksheet=1",
            "?page=briefing&article=" + SLUG + "&worksheet=0",
            "?page=briefings&article=" + SLUG + "&worksheet=1",
            "?page=briefing&article=" + SLUG + "&worksheet=1&worksheet=1",
            "?page=briefing&article=" + SLUG + "&worksheet=1&token=secret",
        ):
            with self.subTest(url=url):
                self.assertIsNone(_parse_portfolio_route(url))

    def test_native_resource_is_not_publicly_embedded(self):
        html = decision_record_cta_html()
        self.assertNotIn("data:application/pdf", html)
        self.assertNotIn("access_token", html)
        self.assertNotIn(".pdf", html)


if __name__ == "__main__":
    unittest.main()
