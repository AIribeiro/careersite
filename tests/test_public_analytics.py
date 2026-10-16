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
            self.assertTrue(any(
                "conversion always uses original dated" in x.value
                for x in at.caption
            ))
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
            # The visual overview intentionally uses date tiles rather than
            # clipped metric values for the hiring forecast.
            self.assertIn("Hiring predictor", [x.value for x in at.subheader])
            private.assert_not_called()

    def test_public_market_renders_cited_aggregates(self):
        from streamlit.testing.v1 import AppTest
        with patch("page_public_market_restored._load_public_market",return_value=(
            {"history":[{"indicator_key":"pmi","indicator_name":"PMI",
              "series_key":"pmi|sweden","observation_date":"2026-10-01",
              "period_end":"2026-10-01","published_at":"2026-10-02",
              "region":"Sweden","metric_value":53.2,"metric_unit":"index",
              "source_organization":"Official source",
              "source_url":"https://example.org"}]},
            JOBS,None
        )):
            at=AppTest.from_string(
                "from page_public_analytics import render_public_swedish_market\n"
                "render_public_swedish_market()").run(timeout=15)
            self.assertFalse(at.exception)
            self.assertEqual(len(at.text_input),0)
            self.assertIn("Swedish Job Market",[x.value for x in at.title])


    def test_portfolio_relationships_show_dashboards_not_main_table(self):
        from datetime import date, timedelta
        from streamlit.testing.v1 import AppTest
        from page_public_analytics import (
            _portfolio_recruitment_trends, _portfolio_signal_explanation,
        )
        start=date(2026,9,26)
        days=[start+timedelta(days=i) for i in range(19)]
        site={d:{"cv_link_visitors":i%4} for i,d in enumerate(days)}
        jobs={d:{"applications":1 if i%3==0 else 0,
                 "responses":1 if i%5==0 else 0}
              for i,d in enumerate(days)}
        trends=_portfolio_recruitment_trends(site,jobs)
        self.assertEqual(len(trends),13)
        self.assertEqual(trends[-1]["CV-linked sessions"],
                         sum(i%4 for i in range(12,19)))
        self.assertIn("sample is too short",_portfolio_signal_explanation({
            "r":.47,"status":"Early observation","n":19,
        }))
        payload={
            "first_day":"2026-09-25",
            "tracking_since":"2026-09-25T19:17:18Z",
            "through":days[-1].isoformat(),
            "daily":[{"d":d.isoformat(),"sessions":8,
                      "cv_link_visitors":site[d]["cv_link_visitors"]}
                     for d in days],
            "pages":[],"sources":[],
        }
        public_jobs={"daily":[{"d":d.isoformat(),**jobs[d]} for d in days]}
        with patch("page_public_analytics._fetch_rpc",return_value=payload):
            app=AppTest.from_string(
                "from page_public_analytics import _portfolio_job_relationships\n"
                f"_portfolio_job_relationships({public_jobs!r})"
            ).run(timeout=15)
        self.assertFalse(app.exception)
        self.assertIn(
            "Does portfolio attention accompany recruitment progress?",
            [h.value for h in app.subheader],
        )
        self.assertGreaterEqual(len(app.get("vega_lite_chart")),2)
        self.assertEqual(len(app.metric),0)
        self.assertGreaterEqual(len(app.expander),1)


if __name__=="__main__":
    unittest.main()
