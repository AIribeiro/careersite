"""All-channel first-touch attribution reconciliation and page/article grain."""
from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from page_attribution_integrity import fetch_attribution_integrity

EXAMPLE={
    "overview":{
        "recorded_sessions":11,"test_sessions":1,"content_sessions":9,
        "quality_eligible":4,"legacy_ungraded":3,"telemetry_only":1,
        "suspected_preview_bursts":1,"suspected_automation_other":1,
        "navigation_page_views":11,"article_views":5,
        "article_page_wrappers":2,"source_conflicts":1,
        "campaign_conflicts":0,"untagged_with_referrer":1,
    },
    "channels":[
        {"channel":"LinkedIn","recorded_sessions":4,"content_sessions":4,
         "quality_eligible":2,"legacy_ungraded":2,"preview_burst_sessions":0,
         "other_suspected_automation":0,"navigation_page_views":5,
         "article_views":3,"article_page_wrappers":1},
        {"channel":"Unattributed / unknown","recorded_sessions":4,"content_sessions":3,
         "quality_eligible":1,"legacy_ungraded":0,"preview_burst_sessions":1,
         "other_suspected_automation":1,"telemetry_only":1,
         "navigation_page_views":4,"article_views":0,"article_page_wrappers":0},
        {"channel":"WhatsApp","recorded_sessions":1,"content_sessions":1,
         "quality_eligible":1,"legacy_ungraded":0,"navigation_page_views":1,
         "article_views":1,"article_page_wrappers":1},
        {"channel":"Facebook","recorded_sessions":1,"content_sessions":1,
         "quality_eligible":0,"legacy_ungraded":1,"navigation_page_views":1,
         "article_views":1,"article_page_wrappers":0},
        {"channel":"Application","recorded_sessions":0,"content_sessions":0},
    ],
    "campaigns":[
        {"channel":"LinkedIn","campaign":"dailyquote","content_sessions":2,"quality_eligible":1},
        {"channel":"LinkedIn","campaign":"thinking","content_sessions":2,"quality_eligible":1},
        {"channel":"Unattributed / unknown","campaign":"untagged","content_sessions":3,"quality_eligible":1},
        {"channel":"WhatsApp","campaign":"dailyquote","content_sessions":1,"quality_eligible":1},
        {"channel":"Facebook","campaign":"facebook_groups","content_sessions":1,"quality_eligible":0},
    ],
    "unexpected_tags":[{"raw_first_source":"unsupported_weird_tag","sessions":1}],
}


class IntegrityTests(unittest.TestCase):
    def test_sums_of_parent_channels_and_campaigns_are_disjoint(self):
        self.assertEqual(
            sum(x["content_sessions"] for x in EXAMPLE["channels"]),9)
        self.assertEqual(
            sum(x["content_sessions"] for x in EXAMPLE["campaigns"]),9)
        self.assertEqual(sum(x.get("quality_eligible",0) for x in EXAMPLE["channels"]),4)
        self.assertEqual(EXAMPLE["overview"]["quality_eligible"],4)

    def test_article_wrappers_are_not_navigation_views(self):
        self.assertEqual(EXAMPLE["overview"]["navigation_page_views"],11)
        self.assertEqual(EXAMPLE["overview"]["article_page_wrappers"],2)
        self.assertNotEqual(11+5+2,11+5)

    def test_private_request_window_and_bearer_header(self):
        response=MagicMock()
        response.__enter__.return_value=response
        response.read.return_value=json.dumps(EXAMPLE).encode()
        with patch("page_attribution_integrity.owner_rpc_headers",return_value={
            "Authorization":"Bearer owner-test","apikey":"mock",
        }), patch("page_attribution_integrity.request.urlopen",return_value=response) as opened:
            data=fetch_attribution_integrity("7d")
            self.assertEqual(data["overview"]["content_sessions"],9)
            req=opened.call_args.args[0]
            self.assertEqual(json.loads(req.data),{"p_days":7,"p_window":"days"})
            self.assertIn("Bearer owner-test",req.headers.values())

    def test_unknown_reporting_window_rejected(self):
        with self.assertRaises(ValueError):
            fetch_attribution_integrity("unbounded")

    def test_render_exposes_disjoint_counts_without_doublecounting(self):
        from streamlit.testing.v1 import AppTest
        program="from page_attribution_integrity import render_attribution_integrity\nrender_attribution_integrity('30d')"
        with patch("page_attribution_integrity.fetch_attribution_integrity",return_value=EXAMPLE):
            app=AppTest.from_string(program).run(timeout=15)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric),4)
            self.assertEqual(app.metric[0].value,"9")
            self.assertEqual(app.metric[1].value,"4")


if __name__=="__main__":
    unittest.main()
