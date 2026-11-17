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

    def test_all_nine_management_domains_are_present(self):
        self.assertEqual(set(SECTIONS),
            {"overview","refresh","coverage","sources","evidence","analysis","editions","engagement","audit"})

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

    def test_release_manifest_prevents_unapproved_evidence_from_appearing(self):
        from page_advisory_market_signals import _release_snapshot
        points=[
            {"code":"scb_a","source_family":"scb_enterprise_ai_adoption"},
            {"code":"jobtech_b","source_family":"af_jobtech_target_demand"},
            {"code":"unused","source_family":"brainville_consulting_market"},
        ]
        briefs=[
            {"slug":"approved","evidence_codes":["scb_a","jobtech_b"]},
            {"slug":"not_released","evidence_codes":["unused","jobtech_b"]},
        ]
        response={"published":True,"slug":"initial-release",
            "evidence_codes":["scb_a","jobtech_b"],"brief_slugs":["approved"],
            "title":"Initial release","issue_date":"2026-11-16"}
        with patch("page_advisory_market_signals._request_json",return_value=response):
            chosen,approved,release=_release_snapshot("member-token",points,briefs)
        self.assertEqual([p["code"] for p in chosen],["scb_a","jobtech_b"])
        self.assertEqual([b["slug"] for b in approved],["approved"])
        self.assertTrue(release["published"])

    def test_release_contract_fails_closed_on_missing_or_external_evidence(self):
        from page_advisory_market_signals import _release_snapshot
        points=[{"code":"scb_a","source_family":"scb_enterprise_ai_adoption"},
                {"code":"jobtech_b","source_family":"af_jobtech_target_demand"}]
        briefs=[{"slug":"analysis","evidence_codes":["scb_a","outside_manifest"]}]
        release={"published":True,"evidence_codes":["scb_a","jobtech_b"],
                 "brief_slugs":["analysis"]}
        with patch("page_advisory_market_signals._request_json",return_value=release):
            with self.assertRaisesRegex(ValueError,"outside"):
                _release_snapshot("member-token",points,briefs)
        with patch("page_advisory_market_signals._request_json",return_value={}):
            with self.assertRaises(RuntimeError):
                _release_snapshot("member-token",points,briefs)

    def test_report_edition_must_contain_required_sources_and_complete_months(self):
        from page_owner_market_signals import _review_pdf_compatible
        required=[
            "scb_2026_ai_10plus","scb_2026_ai_250plus",
            "scb_2026_analytics_internal","scb_2026_ai_expertise_barrier",
            "jobtech_v1_sep_se","jobtech_v1_oct_se",
            "jobtech_v1_sep_vgr","jobtech_v1_oct_vgr",
            "brainville_202610_assignments_yoy",
            "brainville_202610_consultants_yoy",
            "jobtech_v1_jun_se",
        ]
        self.assertTrue(_review_pdf_compatible(required))
        self.assertFalse(_review_pdf_compatible(required[:-1]))
        self.assertFalse(_review_pdf_compatible(required[1:]))

    def test_reader_status_is_discreet_and_publication_aware(self):
        code=(ROOT/"src/page_advisory_market_signals.py").read_text()
        self.assertIn("market-editorial-status",code)
        self.assertIn("Market Intelligence · ",code)
        self.assertIn("Evidence-linked indicators with transparent reporting periods",code)
        self.assertIn("Frozen published executive market edition",code)
        self.assertIn("Market Intelligence · '+html_escape(issue_month)",code)
        self.assertNotIn("Initial editorial edition is still under source-by-source review.",code)
        self.assertNotIn("must not be represented as a formally released market report.",code)

    def test_pre_release_is_frozen_to_original_catalogue(self):
        from page_advisory_market_signals import _release_snapshot,INITIAL_PREVIEW_CODES
        initial=[{"code":c,"source_family":"verified_input_family"} for c in INITIAL_PREVIEW_CODES]
        pending={"code":"market_context_20261116_03","source_family":"manpower_employment_outlook"}
        briefs=[{"slug":"initial","evidence_codes":[
            "scb_2026_ai_10plus","jobtech_v1_oct_se"
        ]}]
        with patch("page_advisory_market_signals._request_json",return_value={
            "published":False,"mode":"pre_release"
        }):
            points,selected,meta=_release_snapshot("owner-token",[pending,*initial],briefs)
            self.assertEqual(len(points),31)
            self.assertNotIn(pending,points)
            self.assertEqual([b["slug"] for b in selected],["initial"])
            self.assertEqual(meta["mode"],"pre_release")
            with self.assertRaisesRegex(ValueError,"Frozen"):
                _release_snapshot("owner-token",[],[])

    def test_no_direct_owner_table_writes_in_interface(self):
        code=(ROOT/"src/page_owner_market_signals.py").read_text()
        self.assertIn("portfolio_market_signals_owner_action_v1",code)
        self.assertIn("portfolio_market_signals_release_check_v1",code)
        self.assertNotIn('"_PATCH"',code)
        self.assertNotIn('"_DELETE"',code)
        self.assertNotIn('_request_json("PATCH"',code)


if __name__ == "__main__":
    unittest.main()
