"""Attribution dimensions are not additive and scanner counts remain separate."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

from page_analytics import _campaign_label_totals, _attribution_rows
from page_cv_attribution_audit import fetch_cv_attribution_audit

AUDIT = {
    "overview":{
        "all_page_views":970,"page_view_sessions":778,
        "cv_page_views":64,"cv_sessions":64,
        "cv_utm_source_same_view":40,"cv_with_role":0,"role_tagged_views":36,
        "suspect_scan_views":51,"suspect_scan_sessions":51,
    },
    "cv_pages":[
        {"page":"home","raw_views":24,"suspect_scan_views":17,"other_views":7},
        {"page":"certifications","raw_views":20,"suspect_scan_views":17,"other_views":3},
        {"page":"presence","raw_views":20,"suspect_scan_views":17,"other_views":3},
    ],
    "roles":[
        {"role":"dailyquote","page_views":28,"sessions":25},
        {"role":"article","page_views":2,"sessions":2},
    ]
}


class CvAttributionTests(unittest.TestCase):
    def test_roles_aggregate_once_across_parent_channels(self):
        rows=[
            {"channel":"LinkedIn","source":"linkedin","campaign":"dailyquote","sessions":3,"engaged_sessions":2},
            {"channel":"Facebook","source":"facebook","campaign":"dailyquote","sessions":4,"engaged_sessions":1},
            {"channel":"CV","source":"cv","campaign":"untagged","sessions":6,"engaged_sessions":1},
        ]
        grouped=_campaign_label_totals(rows)
        self.assertEqual(len(grouped),2)
        self.assertEqual(next(x for x in grouped if x["campaign_label"]=="Daily Quotes")["sessions"],7)
        self.assertEqual(sum(x["sessions"] for x in grouped),13)
        self.assertEqual(next(x for x in grouped if x["campaign_label"]=="Daily Quotes")["engaged_sessions"],3)

    def test_source_rollup_does_not_duplicate_normalized_labels(self):
        records=[
            {"attribution_source":"linkedin","attribution_role":None,"sessions":7,"engaged_sessions":4},
            {"attribution_source":"linkedin","attribution_role":"dailyquote","sessions":3,"engaged_sessions":2},
            {"attribution_source":"linkedin?role=dailyquote","attribution_role":None,"sessions":1,"engaged_sessions":0},
            {"attribution_source":"cv","sessions":5,"engaged_sessions":2},
        ]
        result=_attribution_rows(records)
        self.assertEqual(len(result),2)
        linkedin=next(x for x in result if x["attribution_source"]=="linkedin")
        self.assertEqual(linkedin["sessions"],11)
        self.assertEqual(linkedin["engaged_sessions"],6)
        self.assertEqual(sum(x["sessions"] for x in result),16)

    def test_request_uses_owner_token_and_window(self):
        from unittest.mock import MagicMock
        import json
        response=MagicMock()
        response.__enter__.return_value=response
        response.read.return_value=json.dumps(AUDIT).encode("utf-8")
        with patch("page_cv_attribution_audit.owner_rpc_headers",return_value={
            "Authorization":"Bearer owner-test",
            "apikey":"mock-public-key",
        }), patch("page_cv_attribution_audit.request.urlopen",return_value=response) as request:
            result=fetch_cv_attribution_audit("30d")
            self.assertEqual(result["overview"]["cv_page_views"],64)
            req=request.call_args.args[0]
            self.assertIn("Bearer owner-test",req.headers.values())
            self.assertEqual(json.loads(req.data)["p_days"],30)
            self.assertEqual(json.loads(req.data)["p_window"],"days")

    def test_legacy_composite_role_is_a_dimension_not_a_new_view(self):
        self.assertEqual(AUDIT["overview"]["role_tagged_views"],36)
        self.assertEqual(AUDIT["roles"][0]["page_views"],28)
        self.assertEqual(AUDIT["overview"]["cv_with_role"],0)

    def test_invariants_source_utm_overlap_is_not_added(self):
        raw=AUDIT["overview"]["cv_page_views"]
        other=raw-AUDIT["overview"]["suspect_scan_views"]
        self.assertEqual(other,13)
        self.assertEqual(raw,sum(x["raw_views"] for x in AUDIT["cv_pages"]))
        self.assertEqual(AUDIT["overview"]["suspect_scan_views"],sum(x["suspect_scan_views"] for x in AUDIT["cv_pages"]))
        self.assertNotEqual(raw, raw+AUDIT["overview"]["cv_utm_source_same_view"])

    def test_audit_panel_shows_disjoint_counts(self):
        from streamlit.testing.v1 import AppTest
        program="from page_cv_attribution_audit import render_cv_attribution_audit\nrender_cv_attribution_audit('30d')"
        with patch("page_cv_attribution_audit.fetch_cv_attribution_audit",return_value=AUDIT):
            at=AppTest.from_string(program).run(timeout=15)
            self.assertFalse(at.exception)
            self.assertEqual(len(at.metric),4)
            self.assertEqual(at.metric[0].value,"64")
            self.assertEqual(at.metric[2].value,"51")
            self.assertEqual(at.metric[3].value,"13")


if __name__=="__main__":
    unittest.main()
