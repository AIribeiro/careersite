"""Market Signals management: owner boundaries, source review and release contracts."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from page_owner_market_signals import (  # noqa: E402
    _get, _act, _load, _preflight, _status, _core_status, SECTIONS
)
from page_advisory_market_signals import _record_market_event  # noqa: E402


class MarketManagementTests(unittest.TestCase):
    def test_advisory_operations_has_market_management_handoff(self):
        owner=(ROOT/"src/page_owner_advisory_management.py").read_text()
        self.assertIn("Market Signals management",owner)
        self.assertIn("render_owner_market_signals(token)",owner)
        self.assertIn('from page_owner_market_signals import render_owner_market_signals',owner)

    def test_all_seven_management_domains_are_present(self):
        self.assertEqual(set(SECTIONS),
            {"overview","sources","evidence","analysis","editions","engagement","audit"})

    def test_sources_are_marked_overdue_only_after_their_cadence(self):
        today=date.today()
        self.assertEqual(_status((today-timedelta(days=16)).isoformat(),15),"Overdue")
        self.assertEqual(_status((today-timedelta(days=15)).isoformat(),15),"Within interval")
        self.assertEqual(_status(None,30),"Unverified")
        self.assertEqual(_status((today+timedelta(days=1)).isoformat(),30),"Future-dated — investigate")

    def test_owner_request_does_not_accept_public_data_fallback(self):
        with patch("page_owner_market_signals._request_json",return_value={"message":"not authenticated"}):
            with self.assertRaises(RuntimeError):
                _get("invalid","portfolio_market_signal_points?select=*",limit=50)

    def test_owner_read_requires_explicit_valid_release_validation_result(self):
        with patch("page_owner_market_signals._request_json",return_value={}):
            with self.assertRaises(RuntimeError):
                _preflight("invalid")

    def test_editorial_actions_require_justification(self):
        with patch("page_owner_market_signals._request_json") as request:
            with self.assertRaises(ValueError):
                _act("token","source_review",{"source_family":"scb_enterprise_ai_adoption"},"ok")
            request.assert_not_called()

    def test_owner_change_is_read_back_from_database(self):
        payload={"code":"test_ai_leadership_v3"}
        mutation={"action":"point_publish","entity_type":"point",
                  "key":payload["code"],"changed":True}
        with patch("page_owner_market_signals._request_json",return_value=mutation) as request:
            with patch("page_owner_market_signals._get",
                       return_value=[{"code":payload["code"],"is_published":True}]) as reader:
                result=_act("owner-token","point_publish",payload,
                    "Verified publisher method and sample.")
                self.assertTrue(result["changed"])
                request.assert_called_once()
                reader.assert_called_once()

    def test_unconfirmed_database_state_is_rejected(self):
        payload={"code":"test_ai_leadership_v3"}
        mutation={"action":"point_publish","entity_type":"point",
                  "key":payload["code"],"changed":True}
        with patch("page_owner_market_signals._request_json",return_value=mutation):
            with patch("page_owner_market_signals._get",
                       return_value=[{"code":payload["code"],"is_published":False}]):
                with self.assertRaisesRegex(RuntimeError,"Published state"):
                    _act("owner-token","point_publish",payload,
                        "Rechecked source and population.")

    def test_source_and_citation_quality_counts_are_not_overstated(self):
        points=[
            {"code":"p1","is_published":True,"source_family":"scb_enterprise_ai_adoption",
             "verified_on":date.today().isoformat()},
            {"code":"p2","is_published":False,"source_family":"af_jobtech_target_demand",
             "verified_on":date.today().isoformat()},
        ]
        data={"points":points,"briefs":[
            {"slug":"b1","is_published":True,"evidence_codes":["p1","missing"],
             "support_level":"independent_sources"}
        ],"editions":[],"sources":[
            {"source_family":"scb_enterprise_ai_adoption","review_status":"needs_review","recheck_days":410},
            {"source_family":"af_jobtech_target_demand","review_status":"approved","recheck_days":15}
        ]}
        output=_core_status(data,[])
        self.assertEqual(output["published_points"],1)
        self.assertEqual(output["approved_sources"],1)
        self.assertEqual(output["unsupported_briefs"],1)

    def test_market_events_are_whitelisted_and_fail_non_intrusively(self):
        with patch("page_advisory_market_signals._request_json",return_value={"recorded":True}) as request:
            _record_market_event("token","pdf_review","all","market-review")
            self.assertEqual(request.call_count,1)
            _record_market_event("token","private_answers","","confidential notes")
            self.assertEqual(request.call_count,1)
        with patch("page_advisory_market_signals._request_json",
                   side_effect=RuntimeError("source temporarily unavailable")):
            _record_market_event("token","open")

    def test_no_direct_owner_table_writes_in_interface(self):
        code=(ROOT/"src/page_owner_market_signals.py").read_text()
        self.assertIn("portfolio_market_signals_owner_action_v1",code)
        self.assertIn("portfolio_market_signals_release_check_v1",code)
        self.assertNotIn('"_PATCH"',code)
        self.assertNotIn('"_DELETE"',code)
        self.assertNotIn('_request_json("PATCH"',code)


if __name__ == "__main__":
    unittest.main()
