"""Default analytics must remain useful without optional browser statistics."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class DefaultAggregateAnalyticsTests(unittest.TestCase):
    def test_source_categories_use_exact_domain_boundaries(self):
        from site_aggregate_traffic import _channel
        self.assertEqual(_channel(source="linkedin"), "linkedin")
        self.assertEqual(_channel(source="linkedin-post"), "linkedin")
        self.assertEqual(_channel(referrer="https://www.linkedin.com/feed/"), "linkedin")
        self.assertEqual(_channel(referrer="https://notlinkedin.com/"), "untagged")
        self.assertEqual(_channel(referrer="https://notgoogle.com/"), "untagged")
        self.assertEqual(_channel(referrer="https://www.google.com/search?q=x"), "search")
        self.assertEqual(_channel(source="my-unregistered-campaign"), "other_tagged")
        self.assertEqual(_channel(referrer=""), "untagged")

    def test_empty_optin_does_not_hide_aggregate_portfolio_pages(self):
        import site_content_demand
        report = {
            "available": True, "portfolio_loads": 17, "editorial_page_loads": 2,
            "editorial_loads": 0, "channel_coverage_loads": 0,
            "unattributed_portfolio_loads": 17,
            "top_pages": [{"page": "home", "loads": 9},
                          {"page": "thinking", "loads": 8}],
            "top_content": [], "channels": [],
        }
        with patch.object(site_content_demand, "content_load_report", return_value=report):
            with patch.object(site_content_demand.st, "html") as html:
                site_content_demand.render_content_demand("today")
        rendered = str(html.call_args.args[0])
        self.assertIn("Most-visited portfolio pages", rendered)
        self.assertIn("Home", rendered)
        self.assertIn("Thinking &amp; Articles", rendered)
        self.assertIn("Source not classified", rendered)
        self.assertIn("17 portfolio opens", rendered)
        self.assertNotIn("Most-opened publications</h3>", rendered)

    def test_overview_uses_dynamic_editorial_period_and_preserves_manual_choice(self):
        main = (ROOT / "src/page_public_portfolio_overview.py").read_text()
        overview = main.split("def render_public_portfolio_overview()", 1)[1]
        self.assertIn("initialize_editorial_reporting_period(st.session_state)", overview)
        self.assertNotIn('st.session_state[WINDOW_KEY] = "this_week"', overview)
        self.assertLess(overview.index("initialize_editorial_reporting_period(st.session_state)"),
                        overview.index('window = st.selectbox('))
        self.assertIn("on_change=remember_reporting_period", overview)
        self.assertLess(overview.index("render_basic_page_loads(str(window))"),
                        overview.index("reader_registration_kpi(str(window), reader_counts)"))
        self.assertLess(overview.index("reader_registration_kpi(str(window), reader_counts)"),
                        overview.index("_selected_portfolio_report(str(window))"))

    def test_dynamic_period_selects_first_verified_read_and_retains_manual_choice(self):
        from analytics_reporting_period import (
            WINDOW_KEY, MANUAL_KEY, PREFERENCE_KEY, initialize_reporting_period,
            remember_reporting_period,
        )
        windows = ("last_hour", "today", "yesterday", "this_week", "this_month")
        fetches = []
        def fetch(window):
            fetches.append(window)
            return {"totals": {"recorded_views": 4 if window == "yesterday" else 0}}

        state = {}
        initialize_reporting_period(state, fetch, windows=windows)
        self.assertEqual(state[WINDOW_KEY], "yesterday")
        self.assertEqual(fetches, ["last_hour", "today", "yesterday"])
        state[WINDOW_KEY] = "this_month"
        remember_reporting_period(state)
        self.assertTrue(state[MANUAL_KEY])
        self.assertEqual(state[PREFERENCE_KEY], "this_month")
        initialize_reporting_period(state, fetch, windows=windows)
        self.assertEqual(state[WINDOW_KEY], "this_month")
        self.assertEqual(fetches, ["last_hour", "today", "yesterday"])

    def test_unknown_editorial_measurements_are_not_treated_as_zero(self):
        from analytics_reporting_period import WINDOW_KEY, initialize_reporting_period
        state = {}
        initialize_reporting_period(
            state, lambda _: {"totals": {"recorded_views": None}},
            windows=("last_hour", "today", "this_week"),
        )
        self.assertEqual(state[WINDOW_KEY], "last_hour")

    def test_storage_dependent_tracking_stays_opt_in(self):
        source = (ROOT / "src/site_analytics.py").read_text()
        self.assertIn("if (choice() !== 'yes') {", source)
        self.assertIn("if (choice() !== 'yes' || !allowed.has(eventName))", source)
        main = (ROOT / "main.py").read_text()
        self.assertIn("public_content_slug", main)
        self.assertIn("if CMS_ARTICLE_META is not None else", main)
        self.assertIn("if ARTICLE_META is not None else", main)


if __name__ == "__main__":
    unittest.main()
