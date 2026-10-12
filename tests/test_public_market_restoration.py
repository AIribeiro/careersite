"""Restore legacy Swedish-market features without private owner data."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from job_market_correlations import analyze_market

MARKET=[
    {"series_key":"survey|national","indicator_key":"employment_outlook_net",
     "indicator_name":"Swedish net employment outlook","metric_value":27,
     "metric_unit":"net_balance","observation_date":"2026-07-31",
     "period_end":"2026-07-31","published_at":"2026-08-10",
     "region":"Sweden","source_organization":"Survey",
     "source_url":"https://example.org/a","relevance_score":90},
    {"series_key":"survey|national","indicator_key":"employment_outlook_net",
     "indicator_name":"Swedish net employment outlook","metric_value":39,
     "metric_unit":"net_balance","observation_date":"2026-09-30",
     "period_end":"2026-09-30","published_at":"2026-10-06",
     "region":"Sweden","source_organization":"Survey",
     "source_url":"https://example.org/b","relevance_score":90},
    {"series_key":"ind|vgr","indicator_key":"employment_outlook_net_vgr",
     "indicator_name":"West Sweden outlook","metric_value":17,
     "metric_unit":"net_balance","observation_date":"2026-09-30",
     "period_end":"2026-09-30","published_at":"2026-10-06",
     "region":"Västra Götaland","source_organization":"Survey",
     "source_url":"https://example.org/c","relevance_score":95},
]
REPORT={
    "totals":{"applications":3,"responses":1,"interviews":0,"rejections":0},
    "daily":[
        {"d":"2026-07-10","applications":1,"responses":0,"interviews":0,"rejections":0},
        {"d":"2026-08-12","applications":1,"responses":0,"interviews":0,"rejections":0},
        {"d":"2026-09-19","applications":1,"responses":1,"interviews":0,"rejections":0},
    ],
    "weekly":[],
}
DATA={"history":MARKET,"latest":MARKET[-2:],"historical_observations":3,"series":2}


class PublicMarketRestorationTests(unittest.TestCase):
    def test_aggregate_public_market_restores_independent_releases(self):
        model=analyze_market(MARKET,[],None,date(2026,10,12),
                             public_job_summary=REPORT)
        self.assertEqual(model["coverage"]["indicators"],2)
        self.assertEqual(model["coverage"]["observations"],3)
        self.assertEqual(len(model["trends"]),1)
        self.assertEqual(model["trends"][0]["Change"],12)
        self.assertEqual(model["coverage"]["job_full_months"],2)
        self.assertEqual(model["monthly"][0]["applications"],1)
        self.assertFalse(model["findings"])
        # The privacy-preserving daily count has no positive progression data.
        self.assertFalse(any(x["outcome"]=="progression" for x in model["checks"]))

    def test_public_market_direction_renders_the_original_full_screen(self):
        from streamlit.testing.v1 import AppTest
        with patch("page_public_market_restored._load_public_market",
                   return_value=(DATA,REPORT,None)):
            app=AppTest.from_string(
                "from page_public_market_restored import render_public_market_restored\n"
                "render_public_market_restored()").run(timeout=15)
        self.assertFalse(app.exception)
        self.assertIn("Swedish Job Market",[x.value for x in app.title])
        self.assertTrue(any("Market direction" in x.value for x in app.subheader))
        self.assertTrue(any("Market trends" in x.value for x in app.subheader))
        self.assertGreaterEqual(len(app.segmented_control),1)

    def test_public_market_relationships_and_evidence_tabs_preserved(self):
        from streamlit.testing.v1 import AppTest
        for focus,heading in (
            ("relationships","Automatic market"),
            ("evidence","Source ledger"),
        ):
            with self.subTest(focus=focus):
                with (
                    patch("page_public_market_restored._load_public_market",
                          return_value=(DATA,REPORT,None)),
                    patch("page_public_market_restored._portfolio_job_relationships"),
                ):
                    app=AppTest.from_string(
                        "from page_public_market_restored import render_public_market_restored\n"
                        "render_public_market_restored()")
                    app.run(timeout=15)
                    app.segmented_control[0].set_value(focus).run(timeout=15)
                self.assertFalse(app.exception)
                self.assertTrue(any(heading in x.value for x in app.subheader))

    def test_analytics_routes_market_to_restored_screen(self):
        src=(Path(__file__).resolve().parents[1]/"src/page_public_analytics.py").read_text()
        self.assertIn("from page_public_market_restored import render_public_market_restored",src)
        self.assertNotIn("Current source-backed signals",src)

    def test_aggregate_market_does_not_query_private_job_records(self):
        src=(Path(__file__).resolve().parents[1]/"src/page_public_market_restored.py").read_text()
        self.assertNotIn("fetch_job_records",src)
        self.assertNotIn("fetch_market_records",src)
        self.assertNotIn("ensure_owner_session",src)
        self.assertIn("careersite_public_market_history_v1",src)
        self.assertIn("careersite_public_job_summary_v1",src)


if __name__=="__main__":
    unittest.main()
