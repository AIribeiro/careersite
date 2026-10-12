"""Public Hiring Predictor restoration, safe aggregation and short date windows."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from public_hiring_forecast import forecast_public_hiring
from page_analytics_v2 import _VIEWS
from page_public_predictions import _week

AGGREGATE={
    "as_of":"2026-10-12",
    "summary":{
        "recent_applications":7,"prior_applications":7,
        "matured_applications":14,"mature_contacts":3,
        "currently_offered":0,"linked_processes":30,
        "earliest":"2026-07-07",
    },
    "stage_buckets":[
        {"stage":"interview","age_month_index":0,"stage_weight":1.0,"n":2},
        {"stage":"conversation","age_month_index":1,"stage_weight":.35,"n":3},
        {"stage":"application","age_month_index":0,"stage_weight":1.0,"n":6},
    ],
    "strategy_context":{
        "records_used":12,
        "critical_records":6,
        "high_records":6,
        "features":{
            "conversion_funnel_focus":True,
            "human_access_priority":True,
            "role_positioning_calibrated":True,
            "seniority_calibrated":True,
            "interview_compression_risk_tracked":True,
            "evidence_quality_control":True,
            "targeted_application_strategy":True,
        },
    },
}


class PublicHiringPredictionTests(unittest.TestCase):
    def test_predictor_restored_to_top_level_navigation(self):
        self.assertIn("predictions",_VIEWS)
        self.assertEqual(_VIEWS["predictions"],"Job predictions")

    def test_daily_and_weekly_public_horizons_in_sql(self):
        sql=(Path(__file__).resolve().parents[1]/
             "supabase/migrations/20261012_public_job_horizons_today_7_30.sql").read_text()
        self.assertIn("p_days<1",sql)
        from page_public_analytics import render_public_job_search
        import inspect
        source=inspect.getsource(render_public_job_search)
        self.assertIn("[1,7,30,90,180,365,730]",source)
        self.assertIn("default=30",source)

    def test_forecast_reuses_beta_stage_math_without_private_data(self):
        result=forecast_public_hiring(AGGREGATE)
        self.assertEqual(result["status"],"scenario")
        self.assertEqual(result["as_of"],"2026-10-12")
        self.assertTrue(result["windows"]["offers"])
        self.assertTrue(result["windows"]["starts"])
        self.assertIn("market_effect",result)
        self.assertLessEqual(result["weekly_application_pace"],5.25)
        trend=[row["Current pace"] for row in result["curve"]]
        self.assertTrue(all(b>=a for a,b in zip(trend,trend[1:])))
        self.assertEqual(len(result["curve"]),53)
        self.assertEqual(result["market_effect"],0.0)
        self.assertEqual(result["portfolio_effect"],0.0)
        self.assertEqual(result["strategy_effect"],0.0)
        self.assertEqual(result["strategy_context"]["records_used"],12)
        self.assertTrue(result["strategy_context"]["features"]["conversion_funnel_focus"])
        self.assertTrue(result["strategy_context"]["features"]["human_access_priority"])
        import json
        returned=json.dumps(result)
        self.assertNotIn("employer",returned)
        self.assertNotIn("recruiter",returned)

    def test_forecast_does_not_depend_on_current_short_horizon(self):
        # The prediction input has NO reporting-window arg. The 1-/7-/30-day
        # activity selector is not allowed to distort the 365-day forecast.
        result=forecast_public_hiring(AGGREGATE)
        self.assertEqual(result["status"],"scenario")
        self.assertGreater(len(result["windows"]["offer_weeks"]),3)

    def test_offer_documented_suppresses_new_first_offer_projection(self):
        example={**AGGREGATE,"summary":{**AGGREGATE["summary"],"currently_offered":1}}
        result=forecast_public_hiring(example)
        self.assertEqual(result["status"],"offer_recorded")

    def test_not_enough_evidence_suppresses_windows(self):
        example={**AGGREGATE,"stage_buckets":[],
                 "summary":{**AGGREGATE["summary"],"recent_applications":1,"prior_applications":1}}
        self.assertEqual(forecast_public_hiring(example)["status"],"insufficient")

    def test_date_label_uses_iso_weeks_and_discloses_year(self):
        self.assertEqual(_week({"from":"2026-10-12","to":"2026-10-18"}),"12–18 Oct 2026")

    def test_public_page_renders_no_password_or_owner_only_evidence(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_predictions.fetch_public_analytics_rpc",
                  side_effect=lambda name: AGGREGATE if name.endswith("hiring_inputs_v1")
                      else {"signals":[]}),
            patch("page_public_predictions._fetch_rpc",return_value={}),
        ):
            at=AppTest.from_string(
                "from page_public_predictions import render_public_hiring_predictions\n"
                "render_public_hiring_predictions()").run(timeout=20)
            self.assertFalse(at.exception)
            self.assertIn("Job Predictions",[v.value for v in at.title])
            self.assertEqual(len(at.text_input),0)
            self.assertTrue(at.subheader)


if __name__=="__main__":
    unittest.main()
