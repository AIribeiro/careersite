"""Anonymous analytics must never request private records or owner credentials."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from site_analytics_public import public_analytics_rpc_headers, fetch_public_analytics_rpc

JOBS={"totals":{"applications":6,"responses":2,"interviews":1,"rejections":0},
      "weekly":[{"week":"2026-10-05","applications":6,"responses":2,
                 "interviews":1,"rejections":0}],
      "daily":[{"d":"2026-10-05","applications":6,"responses":2,
                "interviews":1,"rejections":0}]}
MARKET={"signals":[{"indicator_key":"pmi","indicator_name":"PMI",
                    "observation_date":"2026-10-01","region":"Sweden",
                    "metric_value":53.2,"metric_unit":"index",
                    "source_organization":"Official source",
                    "source_url":"https://example.org"}]}


class PublicAnalyticsTests(unittest.TestCase):
    def test_public_rpc_headers_never_include_credentials(self):
        headers=public_analytics_rpc_headers()
        self.assertIn("apikey",headers)
        self.assertNotIn("Authorization",headers)
        self.assertNotIn("cookie",str(headers).lower())
        self.assertNotIn("refresh_token",str(headers))

    def test_public_rpc_rejects_private_functions(self):
        for name in ("careersite_hiring_predictor_actions_v1",
                     "careersite_analytics_reset","job_search_analytics"):
            with self.assertRaises(ValueError):
                fetch_public_analytics_rpc(name,{})

    def test_public_job_dashboard_renders_without_private_evidence(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_analytics._job_summary",return_value=JOBS),
            patch("page_public_analytics._portfolio_job_relationships"),
            patch("page_job_search_analytics.fetch_job_records") as private,
        ):
            at=AppTest.from_string(
                "from page_public_analytics import render_public_job_search\n"
                "render_public_job_search()").run(timeout=15)
            self.assertFalse(at.exception)
            self.assertEqual(at.title[0].value,"Job Search Analytics")
            self.assertEqual(len(at.text_input),0)
            self.assertGreaterEqual(len(at.metric),4)
            private.assert_not_called()

    def test_public_overview_never_fetches_private_job_rows(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_analytics._job_summary",return_value=JOBS),
            patch("page_public_analytics._market_summary",return_value=MARKET),
            patch("page_public_analytics._fetch_hiring_intelligence",
                  return_value={"quality_summary":{"analysis_eligible_sessions":9}}),
            patch("page_job_search_analytics.fetch_job_records") as private,
        ):
            at=AppTest.from_string(
                "from page_public_analytics import render_public_analytics_overview\n"
                "render_public_analytics_overview()").run(timeout=15)
            self.assertFalse(at.exception)
            self.assertIn("Analytics overview",[x.value for x in at.title])
            self.assertGreaterEqual(len(at.metric),4)
            private.assert_not_called()

    def test_public_market_renders_cited_aggregates(self):
        from streamlit.testing.v1 import AppTest
        with patch("page_public_analytics._market_summary",return_value=MARKET):
            at=AppTest.from_string(
                "from page_public_analytics import render_public_swedish_market\n"
                "render_public_swedish_market()").run(timeout=15)
            self.assertFalse(at.exception)
            self.assertEqual(len(at.text_input),0)
            self.assertIn("Swedish market intelligence",[x.value for x in at.title])


if __name__=="__main__":
    unittest.main()
