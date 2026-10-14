"""Regression locks for restoring analytical views after removing auth.

Reorganizations may alter styling but must preserve the substantive analytics
and historical-data feeds. Sensitive employer records remain owner-only.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class PublicFeatureParityTests(unittest.TestCase):
    def test_no_login_and_every_primary_view_preserved(self):
        from page_analytics_v2 import _VIEWS
        self.assertEqual(set(_VIEWS),{
            "overview","portfolio","jobs","predictions","market"
        })
        source=(ROOT/"src/page_analytics_v2.py").read_text()
        self.assertNotIn("persistent_owner_session",source)
        self.assertNotIn("_owner_session()",source)
        self.assertNotIn("browser_owner_signout()",source)

    def test_full_market_historical_facets_remain(self):
        market=(ROOT/"src/page_public_market_restored.py").read_text()
        original=(ROOT/"src/page_job_market_insights.py").read_text()
        self.assertIn("careersite_public_market_history_v1",market)
        for component in (
            "_market_pulse(model)",
            "_market_history(model)",
            "_relationship_screen(model,compact=False)",
            "_evidence(model)",
        ):
            self.assertIn(component,market)
        for label in (
            "What is changing?",
            "What connects to my search?",
            "Sources & measurement",
        ):
            self.assertIn(label,market)
        self.assertIn("render_market_trends(model)",original)
        dashboard=(ROOT/"src/market_trend_dashboard.py").read_text()
        self.assertIn("Market trends at a glance",dashboard)
        self.assertIn('st.expander("Exact figures"',dashboard)
        self.assertIn("Automatic market ↔ job-search ↔ portfolio correlations",original)
        self.assertIn("Source ledger",original)
        self.assertNotIn("fetch_job_records",market)
        self.assertNotIn("fetch_market_records",market)

    def test_public_job_analysis_depth_and_horizons(self):
        source=(ROOT/"src/page_public_analytics.py").read_text()
        for label in ("Funnel & conversion","Time trends","Portfolio correlations",
                      "Market relationships","Data quality & definitions"):
            self.assertIn(label,source)
        self.assertIn("[1,7,30,90,180,365,730]",source)
        self.assertIn("default=30",source)
        # Correlations require full history even when Today is selected.
        self.assertIn("history=_job_summary(365)",source)

    def test_decision_overview_composes_three_source_families_and_predictor(self):
        source=(ROOT/"src/page_public_analytics.py").read_text()
        for label in (
            "Where your search stands",
            "Portfolio contribution",
            "What the Swedish market is telling you",
            "Hiring predictor",
        ):
            self.assertIn(label,source)
        self.assertIn("forecast_public_hiring",source)

    def test_anon_rpc_projects_no_personal_or_raw_market_content(self):
        sql=(ROOT/"supabase/migrations/20261012_public_market_history_restore.sql").read_text()
        select=sql.split("SELECT DISTINCT ON (",1)[1].split("FROM public.job_market_insights",1)[0]
        self.assertNotIn("raw_data",select)
        self.assertNotIn("contact_name",select)
        self.assertNotIn("employer",select)
        self.assertIn("period_end",select)
        self.assertIn("source_url",select)
        self.assertIn("GRANT EXECUTE",sql)

    def test_public_overview_shows_decision_sections_without_owner_session(self):
        from streamlit.testing.v1 import AppTest
        market={"signals":[]}
        jobs={"totals":{"applications":3,"responses":1,"interviews":0},
              "daily":[],"weekly":[]}
        hiring={"quality_summary":{"analysis_eligible_sessions":6,
                                   "evidence_verified_sessions":2,
                                   "hiring_intent_sessions":0}}
        with (
            patch("page_public_analytics._job_summary",return_value=jobs),
            patch("page_public_analytics._market_summary",return_value=market),
            patch("page_public_analytics._fetch_hiring_intelligence",return_value=hiring),
            patch("page_public_analytics.fetch_public_analytics_rpc",
                  return_value={"as_of":"2026-10-12","summary":{
                      "recent_applications":1,"prior_applications":0,
                      "currently_offered":0},"stage_buckets":[]}),
        ):
            app=AppTest.from_string(
                "from page_public_analytics import render_public_analytics_overview\n"
                "render_public_analytics_overview()"
            ).run(timeout=15)
        self.assertFalse(app.exception)
        headings=[x.value for x in app.subheader]
        for label in ("Where your search stands","Portfolio contribution",
                      "Hiring predictor","What the Swedish market is telling you"):
            self.assertIn(label,headings)
        self.assertEqual(len(app.text_input),0)


if __name__=="__main__":
    unittest.main()
