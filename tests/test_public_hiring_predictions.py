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
        self.assertNotIn("predictions",_VIEWS)
        from page_admin import _PRIVATE_VIEW_ROUTES
        self.assertEqual(_PRIVATE_VIEW_ROUTES["predictions"], "Job predictions")

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

    def test_public_page_shows_visual_hiring_date_and_collapsed_details(self):
        from streamlit.testing.v1 import AppTest
        timing = {
            "available": True,
            "model_version": "hiring-v2-stage-evidence-provisional",
            "as_of": "2026-10-16",
            "offer_earliest": "2026-11-05",
            "offer_central": "2026-11-19",
            "offer_latest": "2026-12-10",
            "start_earliest": "2026-11-19",
            "start_central": "2026-12-17",
            "start_latest": "2027-01-21",
            "needs_refresh": False,
        }
        with (
            patch("page_public_predictions.fetch_public_hiring_timing_v2",
                  return_value=timing) as public_timing,
            patch("page_public_predictions.fetch_public_analytics_rpc",
                  return_value={"signals":[]}),
            patch("page_public_predictions.render_public_conversion_quality") as quality,
            patch("public_hiring_forecast.forecast_public_hiring") as old_forecast,
        ):
            at=AppTest.from_string(
                "from page_public_predictions import render_public_hiring_predictions\n"
                "render_public_hiring_predictions()").run(timeout=20)
            self.assertFalse(at.exception)
            self.assertIn("When could I get my next job?", [v.value for v in at.title])
            self.assertEqual(len(at.text_input), 0)
            values = [m.value for m in at.markdown]
            self.assertTrue(any("17 December 2026" in value for value in values))
            self.assertTrue(any("19 Nov 2026" in value for value in values))
            self.assertTrue(any("17 Dec 2026" in value for value in values))
            self.assertTrue(any("19 Nov ’26 – 21 Jan ’27" in value for value in values))
            self.assertFalse(any("→" in value for value in values))
            # Streamlit metric widgets ellipsize long dates in narrow columns.
            self.assertEqual(len(at.metric), 0)
            self.assertEqual(len(at.get("vega_lite_chart")), 1)
            self.assertEqual(len(at.expander), 2)
            self.assertEqual([x.label for x in at.expander],
                             ["Recruitment evidence and conversion",
                              "Methodology, market context and limitations"])
            self.assertFalse(any("From applications to actual hiring progress" in x.value
                                 for x in at.subheader))
            quality.assert_called_once_with(compact=False)
            public_timing.assert_called_once()
            old_forecast.assert_not_called()

    def test_timing_unavailable_does_not_invent_dates(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_predictions.fetch_public_hiring_timing_v2",
                  return_value={"available":False}),
            patch("page_public_predictions.render_public_conversion_quality"),
            patch("page_public_predictions.fetch_public_analytics_rpc",
                  return_value={"signals":[]}),
        ):
            at = AppTest.from_string(
                "from page_public_predictions import render_public_hiring_predictions\n"
                "render_public_hiring_predictions()").run(timeout=20)
        self.assertFalse(at.exception)
        self.assertTrue(any("No current start-date scenario" in m.value
                            for m in at.markdown))
        self.assertEqual(len(at.metric), 0)
        self.assertEqual(len(at.get("vega_lite_chart")), 0)

    def test_timing_range_chart_contains_only_date_fields(self):
        from page_public_predictions import _timing_chart
        timing={
            "offer_earliest":"2026-11-05","offer_central":"2026-11-19",
            "offer_latest":"2026-12-10","start_earliest":"2026-11-19",
            "start_central":"2026-12-17","start_latest":"2027-01-21",
        }
        spec=_timing_chart(timing).to_dict()
        self.assertEqual(len(spec["layer"]),2)
        self.assertEqual(len(spec["data"]["values"]),2)
        self.assertNotIn("Employer",str(spec))
        self.assertNotIn("recruiter",str(spec))


if __name__=="__main__":
    unittest.main()
