"""Decision-first analytics navigation and rendering regression gates."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))


class DecisionExperienceTests(unittest.TestCase):
    def test_public_landing_is_summary_not_four_expanded_reports(self):
        from streamlit.testing.v1 import AppTest
        source=("from page_analytics_v2 import render_analytics_dashboard\n"
                "render_analytics_dashboard()")
        with patch("page_analytics_v2.render_public_portfolio_overview") as brief, \
             patch("page_analytics_v2.render_content_intelligence") as portfolio:
            page=AppTest.from_string(source).run(timeout=15)
            self.assertFalse(page.exception)
            brief.assert_called_once()
            portfolio.assert_not_called()
            self.assertEqual(len(page.tabs),0)

    def test_decision_brief_degrades_without_market_or_search(self):
        from streamlit.testing.v1 import AppTest
        source=("from page_analytics_overview import render_analytics_overview\n"
                "render_analytics_overview({'access_token':'owner'})")
        with patch("page_analytics_overview.ensure_owner_session",
                   return_value={"access_token":"owner"}), \
             patch("page_analytics_overview.fetch_job_records",return_value=[]), \
             patch("page_analytics_overview.fetch_market_records",return_value=[]), \
             patch("page_analytics_overview._fetch_rpc",return_value=None), \
             patch("page_analytics_overview._fetch_owner_portfolio_actions",
                   return_value={"quality_checked":True}) as owner_actions, \
             patch("page_analytics_overview._fetch_hiring_intelligence",
                   return_value={"quality_summary":{
                       "analysis_eligible_sessions":10,"evidence_verified_sessions":3,
                       "hiring_intent_sessions":1}}), \
             patch("page_analytics_overview.read_daily_history",
                   return_value=[]):
            page=AppTest.from_string(source).run(timeout=15)
            self.assertFalse(page.exception)
            self.assertIn("Decision overview",[x.value for x in page.title])
            self.assertGreaterEqual(len(page.metric),3)
            self.assertEqual(len(page.tabs),0)
            owner_actions.assert_called_once_with("owner")

    def test_qualified_actions_use_owner_token(self):
        from page_analytics_overview import _fetch_owner_portfolio_actions
        from site_cms import _rest_url

        response={"quality_checked":True,"cv_download_sessions":{
            "recent":2,"previous":1},"contact_click_sessions":{
            "recent":1,"previous":0}}
        with patch("page_analytics_overview._request_json",
                   return_value=response) as rpc:
            self.assertEqual(_fetch_owner_portfolio_actions("owner-access-token"),response)
            rpc.assert_called_once_with(
                "POST",_rest_url("rpc/careersite_hiring_predictor_actions_v1"),
                token="owner-access-token",payload={},timeout=20,
            )
        with patch("page_analytics_overview._request_json") as rpc:
            with self.assertRaises(ValueError):
                _fetch_owner_portfolio_actions("")
            rpc.assert_not_called()
        with patch("page_analytics_overview._request_json",return_value=[]) as rpc:
            with self.assertRaises(RuntimeError):
                _fetch_owner_portfolio_actions("owner-access-token")
            rpc.assert_called_once()

    def test_market_page_does_not_present_single_release_as_time_trend(self):
        from streamlit.testing.v1 import AppTest
        row={"id":1,"series_key":"example|market","indicator_key":"services_pmi",
             "indicator_name":"Services PMI","observation_date":"2026-09-30",
             "published_at":"2026-10-05","period_end":"2026-09-30",
             "metric_value":57.4,"relevance_score":90,"source_organization":"Swedbank",
             "metric_unit":"index_50_expansion","sector":"Private services"}
        source=("from page_job_market_insights import render_swedish_job_market\n"
                "render_swedish_job_market({'access_token':'owner'})")
        with patch("page_job_market_insights._load",return_value=([row],[],None)):
            page=AppTest.from_string(source).run(timeout=15)
            self.assertFalse(page.exception)
            self.assertIn("Swedish Job Market",[x.value for x in page.title])
            self.assertEqual(len(page.tabs),0)
            self.assertGreaterEqual(len(page.info),1)


if __name__ == "__main__":
    unittest.main()
