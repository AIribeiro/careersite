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

    def test_short_windows_keep_detailed_content(self) -> None:
        from page_public_portfolio_overview import _selected_portfolio_report
        expected = {"quality": {"site_views": 5}}
        with patch("page_public_portfolio_overview._fast_portfolio_overview", side_effect=AssertionError("short-window fast report unsupported")), \
             patch("page_public_portfolio_overview.fetch_intelligence", return_value=expected) as detailed:
            self.assertEqual(_selected_portfolio_report("today"), expected)
            self.assertEqual(_selected_portfolio_report("this_month"), expected)
            self.assertEqual(detailed.call_count, 2)

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
