"""Decision-first analytics navigation and rendering regression gates."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))


class DecisionExperienceTests(unittest.TestCase):
    def test_owner_landing_is_summary_not_four_expanded_reports(self):
        from streamlit.testing.v1 import AppTest
        source=("from page_analytics_v2 import render_analytics_dashboard\n"
                "render_analytics_dashboard()")
        with patch("page_analytics_v2._owner_session",
                   return_value={"access_token":"owner"}) as owner, \
             patch("page_analytics_v2.render_analytics_overview") as brief, \
             patch("page_analytics_v2.render_content_intelligence") as portfolio, \
             patch("page_analytics_v2.render_job_search_analytics") as jobs, \
             patch("page_analytics_v2.render_swedish_job_market") as market:
            page=AppTest.from_string(source).run(timeout=15)
            self.assertFalse(page.exception)
            owner.assert_called()
            brief.assert_called_once()
            portfolio.assert_not_called()
            jobs.assert_not_called()
            market.assert_not_called()
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
             patch("page_analytics_overview._fetch_hiring_intelligence",
                   return_value={"quality_summary":{
                       "analysis_eligible_sessions":10,"evidence_verified_sessions":3,
                       "hiring_intent_sessions":1}}):
            page=AppTest.from_string(source).run(timeout=15)
            self.assertFalse(page.exception)
            self.assertIn("Decision overview",[x.value for x in page.title])
            self.assertGreaterEqual(len(page.metric),3)
            self.assertEqual(len(page.tabs),0)

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
