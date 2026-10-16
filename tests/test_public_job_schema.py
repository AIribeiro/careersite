"""Contract test: live anonymous job-report grain stays object-based.

The earlier SQL used jsonb_agg(to_jsonb(d)) where `d` resolved as the date
column rather than the row alias. It emitted date strings and caused both
Swedish Market and Job Search production crashes.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from site_analytics_public import fetch_public_analytics_rpc
from job_market_correlations import analyze_market
from datetime import date


REPORT={
    "horizon_days":30,"through":"2026-10-12",
    "method":"dated-primary-deduplicated-per-process-per-day-v1",
    "totals":{"applications":3,"responses":1,"interviews":0,"rejections":0},
    "daily":[
        {"d":"2026-09-20","applications":1,"responses":0,"interviews":0,"rejections":0},
        {"d":"2026-09-24","applications":1,"responses":1,"interviews":0,"rejections":0},
        {"d":"2026-10-02","applications":1,"responses":0,"interviews":0,"rejections":0},
    ],
    "weekly":[
        {"week":"2026-09-14","applications":1,"responses":0,"interviews":0,"rejections":0},
        {"week":"2026-09-21","applications":1,"responses":1,"interviews":0,"rejections":0},
        {"week":"2026-09-28","applications":1,"responses":0,"interviews":0,"rejections":0},
    ],
}
MARKET=[
    {"series_key":"market-a","indicator_key":"market-a","indicator_name":"Market A",
     "metric_value":25,"metric_unit":"index","observation_date":"2026-08-31",
     "period_end":"2026-08-31","published_at":"2026-09-01",
     "region":"Sweden","source_organization":"Official",
     "source_url":"https://example.org"},
]


class PublicJobSchemaTests(unittest.TestCase):
    def _fetch(self,payload):
        with patch("site_analytics_public.request.urlopen") as opener:
            response=opener.return_value.__enter__.return_value
            response.read.return_value=json.dumps(payload).encode()
            return fetch_public_analytics_rpc(
                "careersite_public_job_summary_v1",{"p_days":30}
            )

    def test_rejects_malformed_daily_date_strings(self):
        bad={**REPORT,"daily":["2026-09-20","2026-09-24"]}
        with self.assertRaisesRegex(RuntimeError,"Invalid public job-search daily"):
            self._fetch(bad)

    def test_rejects_malformed_weekly_rows_and_missing_metrics(self):
        bad={**REPORT,"weekly":["2026-09-21"]}
        with self.assertRaisesRegex(RuntimeError,"Invalid public job-search weekly"):
            self._fetch(bad)
        bad2={**REPORT,"daily":[{"d":"2026-09-20","applications":1}]}
        with self.assertRaisesRegex(RuntimeError,"Invalid public job-search daily"):
            self._fetch(bad2)

    def test_accepts_valid_daily_objects(self):
        value=self._fetch(REPORT)
        self.assertIsInstance(value["daily"][0],dict)
        self.assertEqual(sum(r["applications"] for r in value["daily"]),3)

    def test_market_model_with_real_public_daily_contract(self):
        data=analyze_market(MARKET,[],None,date(2026,10,12),
                            public_job_summary=REPORT)
        self.assertEqual(data["coverage"]["indicators"],1)
        self.assertEqual(data["coverage"]["observations"],1)
        self.assertEqual(data["coverage"]["job_full_months"],0)

    def test_job_activity_renders_real_daily_objects(self):
        from streamlit.testing.v1 import AppTest
        with patch("page_public_analytics._job_summary",return_value=REPORT):
            app=AppTest.from_string(
                "from page_public_analytics import render_public_job_search\n"
                "render_public_job_search()")
            app.session_state["public_job_focus"] = "activity"
            app.run(timeout=15)
        self.assertFalse(app.exception)
        self.assertTrue(any("Dated recruitment activity" in x.value
                            for x in app.subheader))
        self.assertGreaterEqual(len(app.get("vega_lite_chart")), 1)

    def test_migration_explicitly_serializes_composite_row(self):
        sql=(Path(__file__).resolve().parents[1]/
             "supabase/migrations/20261012_fix_public_daily_row_json.sql").read_text()
        self.assertIn("jsonb_agg(to_jsonb(day_row) ORDER BY day_row.d)",sql)
        self.assertNotIn("jsonb_agg(to_jsonb(d) ORDER BY d.d)",sql)


if __name__ == "__main__":
    unittest.main()
