"""Public portfolio only; hiring predictions/markets require owner session."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PortfolioOnlyAccessTests(unittest.TestCase):
    def test_portfolio_visits_and_reads_are_the_public_landing(self):
        from page_analytics_v2 import _VIEWS, _url_view, _resolve_workspace
        from page_public_portfolio_overview import portfolio_visit_rows

        self.assertEqual(list(_VIEWS), ["overview", "portfolio"])
        self.assertEqual(_VIEWS["overview"], "Visits & reads")
        for value in ("jobs", "predictions", "market", "hiring", "deep"):
            self.assertEqual(_resolve_workspace(value, False), "public")
        report = {"performance": [
            {"kind": "article", "content": "a", "views": 7, "sessions": 3},
            {"kind": "article", "content": "b", "views": 2, "sessions": 1},
            {"kind": "page", "content": "home", "views": 9, "sessions": 4},
        ]}
        self.assertEqual(portfolio_visit_rows(report, "page")[0]["Views"], 9)
        self.assertEqual(len(portfolio_visit_rows(report, "article")), 2)

    def test_public_entry_does_not_route_to_hiring_renderers(self):
        from page_analytics_v2 import _render_public_analytics
        from streamlit.testing.v1 import AppTest

        with patch("page_analytics_v2.render_public_portfolio_overview") as portfolio:
            app = AppTest.from_string(
                "from page_analytics_v2 import _render_public_analytics\n"
                "_render_public_analytics()\n"
            ).run(timeout=20)
            self.assertFalse(app.exception)
            portfolio.assert_called_once()
            labels = [item.label for item in app.button]
            self.assertNotIn("Job predictions", labels)

    def test_job_network_calls_require_owner_token(self):
        from site_analytics_public import owner_hiring_headers, public_analytics_rpc_headers

        self.assertNotIn("Authorization", public_analytics_rpc_headers())
        with patch("site_analytics_public.st.session_state", {}):
            with self.assertRaises(PermissionError):
                owner_hiring_headers()
        with patch("site_analytics_public.st.session_state", {
            "cms_auth": {"access_token": "test-jwt"},
        }):
            self.assertEqual(owner_hiring_headers()["Authorization"], "Bearer test-jwt")

    def test_hiring_sections_are_private_and_original_renderers_remain(self):
        from page_analytics_v2 import _VIEWS
        from page_admin import _dashboard
        import inspect

        self.assertNotIn("jobs", _VIEWS)
        self.assertNotIn("market", _VIEWS)
        self.assertNotIn("predictions", _VIEWS)
        source = inspect.getsource(_dashboard)
        for label in ("Hiring overview", "Job search", "Job market",
                      "Job predictions", "Detailed analysis"):
            self.assertIn(label, source)
        for renderer in (
            "render_public_analytics_overview", "render_public_job_search",
            "render_public_swedish_market", "render_public_hiring_predictions",
            "render_job_search_analytics", "render_rejection_analytics",
            "render_private_staleness", "render_swedish_job_market",
            "render_analytics_overview",
        ):
            self.assertIn(renderer, source)

    def test_database_hiring_endpoints_have_an_owner_guard(self):
        sql = (ROOT / "supabase/migrations/20261016_owner_only_hiring_market_forecasts.sql").read_text()
        for endpoint in (
            "careersite_public_job_summary_v1",
            "careersite_public_market_summary_v1",
            "careersite_public_market_history_v1",
            "careersite_public_hiring_inputs_v1",
            "careersite_public_conversion_quality_v1",
            "careersite_public_pipeline_health_v1",
            "careersite_public_rejection_summary_v1",
            "careersite_hiring_intelligence_v1",
        ):
            self.assertIn(endpoint, sql)
        self.assertIn("auth.uid()", sql)
        self.assertIn("REVOKE EXECUTE", sql)
        self.assertIn("DROP POLICY IF EXISTS public_hiring_timing_read", sql)
        self.assertIn("public_hiring_timing_owner_select", sql)


if __name__ == "__main__":
    unittest.main()
