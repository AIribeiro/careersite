"""Contracts for the public insight-led Analytics Overview.

Private employer data must not be requested or projected into public views.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_public_overview_dashboard import (
    conversion_insight, pipeline_insight, portfolio_insight,
    market_demand_insight, recent_recruitment_trend,
)


def evidence():
    return {
        "conversion": {"available": True, "totals": {
            "applications": 267, "human_responses": 11,
            "first_interviews": None, "subsequent_interviews": None}},
        "pipeline": {"metrics": {"matured_unanswered": 158},
                     "status": [
                         {"segment": "closed", "n": 86},
                         {"segment": "recent_awaiting_response", "n": 36},
                         {"segment": "recruiter_engaged", "n": 7},
                         {"segment": "stale_21_44", "n": 44},
                         {"segment": "stale_45_59", "n": 17},
                         {"segment": "stale_60_plus", "n": 107},
                         {"segment": "verified_dormant", "n": 1}]},
        "hiring": {"quality_summary": {
            "analysis_eligible_sessions": 30,
            "evidence_verified_sessions": 9,
            "hiring_intent_sessions": 1}},
        "market": {"signals": [
            {"indicator_key": "jobtech_high_signal_target_ads_v1",
             "metric_value": 19, "change_value": 9, "period_end": "2026-09-30"},
            {"indicator_key": "jobtech_high_signal_target_ads_mtd_v1",
             "metric_value": 14, "period_end": "2026-10-14"}]},
        "jobs": {"weekly": [
            {"week": "2026-09-28", "applications": 5, "responses": 1},
            {"week": "2026-10-05", "applications": 9, "responses": 3},
            {"week": "2026-10-12", "applications": 12, "responses": 5},
        ]},
        "timing": {
            "available": True, "as_of": "2026-10-16",
            "start_earliest": "2026-11-19", "start_central": "2026-12-17",
            "start_latest": "2027-01-21",
            "offer_earliest": "2026-11-05", "offer_central": "2026-11-19",
            "offer_latest": "2026-12-10",
        },
        "rejections": {"available": False},
    }


class PublicVisualOverviewTests(unittest.TestCase):
    def test_response_rate_uses_same_verified_date_cohort(self):
        x = conversion_insight(evidence()["conversion"])
        self.assertEqual(x["applications"], 267)
        self.assertEqual(x["human"], 11)
        self.assertEqual(x["no_documented_human"], 256)
        self.assertEqual(x["observed_pct"], 4.1)
        self.assertFalse(conversion_insight(
            {"available": True, "totals": {
                "applications": 267, "human_responses": None}})["available"])

    def test_stale_and_rejections_not_conflated(self):
        x = pipeline_insight(evidence()["pipeline"])
        self.assertEqual(x["total"], 298)
        self.assertEqual(x["ageing"], 168)
        self.assertEqual(x["matured_unanswered"], 158)
        self.assertEqual(x["engaged"], 7)
        self.assertEqual(x["closed"], 86)
        self.assertNotEqual(x["ageing"], x["closed"])

    def test_partial_jobtech_month_keeps_its_label(self):
        x = market_demand_insight(evidence()["market"])
        self.assertEqual([p["Ads"] for p in x["bars"]], [10, 19, 14])
        self.assertEqual(x["bars"][-1]["Completeness"], "Partial")
        self.assertIn("90%", x["insight"])
        self.assertEqual(x["partial_as_of"], "2026-10-14")

    def test_portfolio_signal_is_not_recruiter_identification(self):
        x = portfolio_insight(evidence()["hiring"])
        self.assertEqual(x["qualified"], 30)
        self.assertEqual(x["verified"], 9)
        self.assertEqual(x["intent"], 1)

    def test_trend_is_dated_and_preserves_independent_event_counts(self):
        x = recent_recruitment_trend(evidence()["jobs"])
        self.assertEqual(x[-1]["Recorded contacts"], 5)
        self.assertEqual(x[-1]["Applications"], 12)

    def test_visual_dashboard_does_not_require_private_evidence(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_analytics._fetch_hiring_intelligence",
                  return_value=evidence()["hiring"]),
            patch("page_public_analytics._job_summary",
                  return_value=evidence()["jobs"]),
            patch("page_public_analytics._market_summary",
                  return_value=evidence()["market"]),
            patch("page_public_analytics.fetch_public_hiring_timing_v2",
                  return_value=evidence()["timing"]),
            patch("page_public_analytics.fetch_public_analytics_rpc",
                  side_effect=lambda name, payload=None: {
                      "careersite_public_conversion_quality_v1": evidence()["conversion"],
                      "careersite_public_rejection_summary_v1": evidence()["rejections"],
                      "careersite_public_pipeline_health_v1": evidence()["pipeline"],
                  }.get(name, {})),
        ):
            at = AppTest.from_string(
                "from page_public_analytics import render_public_analytics_overview\n"
                "render_public_analytics_overview()"
            ).run(timeout=20)
        self.assertFalse(at.exception)
        titles = [x.value for x in at.subheader]
        for title in (
            "Hiring predictor", "Where your search stands", "Recruitment momentum",
            "Portfolio contribution", "What the Swedish market is telling you",
        ):
            self.assertIn(title, titles)
        self.assertGreaterEqual(len(at.get("vega_lite_chart")), 4)
        self.assertGreaterEqual(len(at.expander), 3)
        displayed = [m.value for m in at.markdown]
        for date_text in ("17 Dec 2026", "19 Nov 2026",
                          "19 Nov ’26 – 21 Jan ’27"):
            self.assertTrue(any(date_text in value for value in displayed))
        # Private timing must not be shown via ellipsizing st.metric cards.
        self.assertFalse(any(x.label in ("Potential offer", "Possible start window")
                             for x in at.metric))
        self.assertEqual(len(at.text_input), 0)


if __name__ == "__main__":
    unittest.main()
