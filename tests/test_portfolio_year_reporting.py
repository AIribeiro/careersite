"""Year/All portfolio reporting stays available without expensive full telemetry scans."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PortfolioYearReportingTests(unittest.TestCase):
    def test_year_and_all_choose_fast_overview(self) -> None:
        from page_public_portfolio_overview import _selected_portfolio_report
        sentinel = {"quality": {"site_views": 3}}
        with patch("page_public_portfolio_overview._fast_portfolio_overview", return_value=sentinel) as fast, \
             patch("page_public_portfolio_overview.fetch_intelligence", side_effect=AssertionError("long-window full query should not run")):
            self.assertEqual(_selected_portfolio_report("this_year"), sentinel)
            self.assertEqual(_selected_portfolio_report("all"), sentinel)
            self.assertEqual(fast.call_count, 2)

    def test_short_windows_use_fast_canonical_overview(self) -> None:
        from page_public_portfolio_overview import _selected_portfolio_report
        expected = {"quality": {"site_views": 5}}
        with patch("page_public_portfolio_overview._fast_portfolio_overview", return_value=expected) as fast, \
             patch("page_public_portfolio_overview.fetch_intelligence", side_effect=AssertionError("heavy query must not run")):
            self.assertEqual(_selected_portfolio_report("today"), expected)
            self.assertEqual(_selected_portfolio_report("this_month"), expected)
            self.assertEqual([c.args[0] for c in fast.call_args_list], ["today", "this_month"])

    def test_fast_overview_tracks_all_calendar_windows_and_quality(self) -> None:
        sql = (ROOT / "supabase/migrations/20261116144800_fast_portfolio_all_reporting_windows.sql").read_text()
        from page_analytics import REPORTING_WINDOW_LABELS
        self.assertIn("careersite_portfolio_overview_fast_v2", sql)
        self.assertIn("careersite_reporting_events_v1", sql)
        for period in REPORTING_WINDOW_LABELS:
            self.assertIn(f"'{period}'", sql)
        for period in ("7d", "previous_7d"):
            self.assertIn(f"'{period}'", sql)
        self.assertIn("AT TIME ZONE 'Europe/Stockholm'", sql)
        self.assertIn("REVOKE ALL ON FUNCTION", sql)
        self.assertNotIn("DELETE FROM", sql.upper())

    def test_fast_recent_comparison_keeps_equal_duration_seven_day_windows(self) -> None:
        from page_public_portfolio_overview import _recent_content_report
        current = {"performance": [
            {"kind": "page", "content": "home", "views": 9},
            {"kind": "article", "content": "essay", "views": 3}]}
        previous = {"performance": [
            {"kind": "page", "content": "home", "views": 4},
            {"kind": "article", "content": "old", "views": 2}]}
        _recent_content_report.clear()
        with patch("page_public_portfolio_overview._fast_portfolio_overview", side_effect=[current, previous]) as fast:
            report = _recent_content_report()
        self.assertEqual([c.args[0] for c in fast.call_args_list], ["7d", "previous_7d"])
        self.assertIn({"kind": "article", "content": "essay", "current_views": 3, "previous_views": 0}, report["period_comparison"])
        self.assertIn({"kind": "article", "content": "old", "current_views": 0, "previous_views": 2}, report["period_comparison"])

    def test_fast_year_rpc_retains_canonical_view_and_privacy(self) -> None:
        sql = (ROOT / "supabase/migrations/20261114125805_portfolio_fast_year_overview_v1.sql").read_text()
        self.assertIn("public.careersite_reporting_events_v1", sql)
        self.assertIn("careersite_analytics_admin_config", sql)
        self.assertIn("AT TIME ZONE 'Europe/Stockholm'", sql)
        self.assertIn("COUNT", sql.upper())
        for key in ("site_views", "page_views", "article_views", "legacy_thinking_views", "site_sessions"):
            self.assertIn(key, sql)
        self.assertIn("p_window NOT IN ('this_year','all')", sql)
        self.assertIn("REVOKE ALL ON FUNCTION", sql)
        self.assertNotIn("DELETE FROM", sql.upper())
        self.assertNotIn("UPDATE public.careersite_analytics_events", sql)

    def test_refresh_drops_cached_aggregate(self) -> None:
        src = (ROOT / "src/page_public_portfolio_overview.py").read_text()
        self.assertIn("_fast_portfolio_overview.clear()", src)
        self.assertIn("fetch_intelligence.clear()", src)
        self.assertIn("@st.cache_data(ttl=120", src)


if __name__ == "__main__":
    unittest.main()
