"""Editorial analytics auto-window: never use portfolio-only views as activity."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_reporting_period import WINDOW_KEY, remember_reporting_period
from page_public_portfolio_overview import (
    EDITORIAL_AUTO_WINDOWS, editorial_read_count,
    initialize_editorial_reporting_period, _editorial_reporting_activity,
)


def _report(*, editorial=0, portfolio=0):
    performance = [
        {"kind": "page", "content": "home", "views": portfolio, "sessions": 1},
    ]
    if editorial:
        performance += [
            {"kind": "article", "content": "test-essay", "views": editorial, "sessions": 1},
        ]
    return {"quality": {"article_views": editorial, "page_views": portfolio},
            "performance": performance}


class EditorialPeriodTests(unittest.TestCase):
    def test_only_editorial_views_qualify_and_three_categories_share_article_events(self):
        self.assertEqual(editorial_read_count(_report(editorial=0, portfolio=120)), 0)
        self.assertEqual(editorial_read_count(_report(editorial=3, portfolio=120)), 3)
        report = {"quality": {"article_views": 12}, "performance": [
            {"kind": "article", "content": "essay", "views": 2},
            {"kind": "article", "content": "weekly-edition", "views": 4},
            {"kind": "article", "content": "executive-briefing", "views": 6},
            {"kind": "page", "content": "briefings", "views": 300},
        ]}
        self.assertEqual(editorial_read_count(report), 12)

    def test_bad_data_does_not_masquerade_as_zero(self):
        self.assertIsNone(editorial_read_count({}))
        self.assertIsNone(editorial_read_count({"quality": {"article_views": 0}}))
        self.assertIsNone(editorial_read_count({"quality": {"article_views": 2},
                                                "performance": []}))
        self.assertIsNone(editorial_read_count({"quality": {"article_views": "unknown"},
                                                "performance": []}))

    def test_automatic_selection_skips_page_only_periods(self):
        self.assertEqual(EDITORIAL_AUTO_WINDOWS[-1], "this_year")
        self.assertNotIn("all", EDITORIAL_AUTO_WINDOWS)
        state = {}
        fetch = Mock(side_effect=lambda period: {"totals": {
            "recorded_views": 2 if period == "this_week" else 0,
        }})
        with patch("page_public_portfolio_overview._editorial_reporting_activity", fetch):
            initialize_editorial_reporting_period(state)
        self.assertEqual(state[WINDOW_KEY], "this_week")
        self.assertEqual([c.args[0] for c in fetch.call_args_list],
                         list(EDITORIAL_AUTO_WINDOWS[:4]))

    def test_automatic_ceiling_and_manual_override(self):
        state = {}
        fetch = Mock(return_value={"totals": {"recorded_views": 0}})
        with patch("page_public_portfolio_overview._editorial_reporting_activity", fetch):
            initialize_editorial_reporting_period(state)
        self.assertEqual(state[WINDOW_KEY], "this_year")
        self.assertEqual(fetch.call_count, len(EDITORIAL_AUTO_WINDOWS))
        state[WINDOW_KEY] = "yesterday"
        remember_reporting_period(state)
        fetch.reset_mock()
        with patch("page_public_portfolio_overview._editorial_reporting_activity", fetch):
            initialize_editorial_reporting_period(state)
        self.assertEqual(state[WINDOW_KEY], "yesterday")
        fetch.assert_not_called()

    def test_auto_count_uses_content_rpc_not_dashboard_traffic(self):
        _editorial_reporting_activity.clear()
        with (patch("page_public_portfolio_overview._article_metadata", return_value=[]),
              patch("page_public_portfolio_overview._fetch_rpc",
                    return_value=_report(editorial=0, portfolio=800)) as rpc):
            result = _editorial_reporting_activity("yesterday")
        self.assertEqual(result, {"totals": {"recorded_views": 0}})
        rpc.assert_called_once()
        self.assertEqual(rpc.call_args.args[0], "careersite_content_intelligence_v2")

    def test_year_auto_check_uses_fast_reporting(self):
        _editorial_reporting_activity.clear()
        with (patch("page_public_portfolio_overview._fast_portfolio_overview",
                    return_value=_report(editorial=3, portfolio=800)) as fast,
              patch("page_public_portfolio_overview._fetch_rpc",
                    side_effect=AssertionError("expensive query should not run"))):
            self.assertEqual(_editorial_reporting_activity("this_year")["totals"]
                             ["recorded_views"], 3)
        fast.assert_called_once_with("this_year")


if __name__ == "__main__":
    unittest.main()
