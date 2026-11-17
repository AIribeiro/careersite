"""Market Observatory archived months, public historical PDF, and admin refresh."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch,MagicMock

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from market_archive import (
 _validate_archive,archive_option_label,archive_coverage,load_market_archives
)
from page_advisory_market_demo import (
 _sample_points,public_historical_demo_pdf,historical_market_pdf,
 public_market_demo_html,EARLIEST_COMPLETE_MONTHS
)
from market_admin_refresh import (
 _recalculate,_classify,_source_check,run_admin_market_refresh,JOBTECH_SEEDS
)


class MonthlyObservatoryTests(unittest.TestCase):
    def test_archive_publication_types_are_explicit(self):
        point=_sample_points()[0]
        historic={
          "snapshot_key":"history:jobtech-v1:2026-06","month_start":"2026-06-01",
          "archive_kind":"retrospective_title_basket",
          "observations":[point],"interpretations":[],"edition_slug":None,
        }
        self.assertEqual(_validate_archive(historic),historic)
        self.assertIn("Retrospective leadership",archive_option_label(historic))
        self.assertIn("not a full ai/data market",archive_coverage(historic).lower())
        fake=dict(historic)
        fake["observations"]=[dict(point,source_family="scb_enterprise_ai_adoption")]
        with self.assertRaises(ValueError):
            _validate_archive(fake)
        future=dict(historic)
        future["observations"]=[dict(point,period_start="2026-11-01")]
        with self.assertRaises(ValueError):
            _validate_archive(future)

    def test_archive_member_token_and_dated_result_required(self):
        with self.assertRaises(PermissionError):
            load_market_archives("")
        with patch("market_archive._request_json",return_value=[
            {"archive_kind":"unexpected","observations":[],"interpretations":[]}
        ]):
            with self.assertRaises(ValueError):
                load_market_archives("owner")
        with patch("market_archive._request_json",return_value=[]):
            self.assertEqual(load_market_archives("reader"),[])

    def test_public_demo_matches_nine_oldest_source_codes(self):
        self.assertEqual(len(EARLIEST_COMPLETE_MONTHS),9)
        sample=_sample_points()
        self.assertEqual(len(sample),9)
        self.assertEqual(len({p["code"] for p in sample}),9)
        self.assertEqual({str(p["period_start"])[:7] for p in sample},
                         {"2026-06","2026-07","2026-08"})
        for code in ["jobtech_v1_jun_se","jobtech_v1_jul_sto","jobtech_v1_aug_vgr"]:
            self.assertIn(code,{x["code"] for x in sample})
        self.assertTrue(all(p["source_family"]=="af_jobtech_target_demand" for p in sample))

    def test_public_pdf_is_complete_traceable_and_not_backdated(self):
        blob=public_historical_demo_pdf()
        self.assertGreater(len(blob),3000)
        pdf=PdfReader(BytesIO(blob))
        self.assertGreaterEqual(len(pdf.pages),4)
        content="\n".join(p.extract_text() or "" for p in pdf.pages)
        for phrase in [
            "June-August 2026","16 November 2026","17 November 2026",
            "stockholm","Västra Götaland","No contemporaneous measures",
            "not a report published","jobtech_v1_jun_se","jobtech_v1_aug_vgr",
            "12","15","10",
        ]:
            self.assertIn(phrase.casefold(),content.casefold())
        self.assertNotIn("85% of large enterprises",content)
        self.assertNotIn("Brainville reports assignments",content)
        self.assertIn("Source and audit trail",content)

    def test_historical_pdf_refuses_later_or_incomplete_evidence(self):
        bad=[dict(_sample_points()[0],source_family="brainville_consulting_market")]
        with self.assertRaises(ValueError):
            historical_market_pdf(bad,month_label="June 2026")
        bad=[dict(_sample_points()[0],period_complete=False)]
        with self.assertRaises(ValueError):
            historical_market_pdf(bad,month_label="June 2026")

    def test_public_route_and_fourth_quadrant_exist(self):
        main=(ROOT/"main.py").read_text()
        landing=(ROOT/"src/page_advisory_market_signals.py").read_text()
        visibility=(ROOT/"src/advisory_service_visibility.py").read_text()
        self.assertIn('"advisory-market-demo"',main)
        self.assertIn("render_public_market_demo_download()",main)
        self.assertIn('"advisory-market-demo": "market-signals"',visibility)
        self.assertIn("04 / PUBLIC RESEARCH SAMPLE",landing)
        self.assertIn('?page=advisory-market-demo',landing)
        self.assertIn("No registration",public_market_demo_html())


class AdminMarketRefreshTests(unittest.TestCase):
    def test_frozen_title_classifier_does_not_count_engineers(self):
        self.assertEqual(len(JOBTECH_SEEDS),30)
        self.assertTrue(_classify("Head of AI Strategy"))
        self.assertTrue(_classify("Director Data & Analytics"))
        self.assertFalse(_classify("Senior Data Engineer"))
        self.assertFalse(_classify("Machine Learning Scientist"))

    def test_source_check_keeps_reachability_separate_from_new_metrics(self):
        response=MagicMock(status_code=200,content=b"official source content")
        result={
            "source_family":"scb_enterprise_ai_adoption",
            "review_status":"approved",
            "source_url":"https://www.scb.se/",
        }
        with patch("market_admin_refresh._safe_get",return_value=response):
            evidence=_source_check(result)
        self.assertEqual(evidence["status"],"reachable")
        self.assertFalse(evidence["extracted_new_metrics"])
        self.assertEqual(len(evidence["response_sha256"]),64)

    def test_calculations_use_only_manifest_and_preserve_independent_scope(self):
        points=[
            {"code":"scb","is_published":True,"source_family":"scb_enterprise_ai_adoption",
             "value":49,"metric_unit":"percent","period_label":"2026","geography":"Sweden",
             "verified_on":"2026-11-16","series_code":"scb_ai"},
            {"code":"job","is_published":True,"source_family":"af_jobtech_target_demand",
             "value":29,"metric_unit":"advertisements","period_label":"October 2026",
             "geography":"Sweden","verified_on":"2026-11-16",
             "period_start":"2026-10-01","period_complete":True,
             "series_code":"jobtech_ai_data_leadership_v1"},
            {"code":"draft","is_published":False,"source_family":"scb_enterprise_ai_adoption",
             "value":1000,"metric_unit":"percent","period_label":"2027","geography":"Sweden"}
        ]
        briefs=[{"slug":"analysis","is_published":True,"evidence_codes":["scb","job"],
                 "support_level":"independent_sources"}]
        edition={"slug":"e1","evidence_codes":["scb","job"],"brief_slugs":["analysis"]}
        result=_recalculate(points,briefs,edition)
        self.assertTrue(result["ok"])
        self.assertEqual(result["observation_count"],2)
        self.assertEqual(len(result["complete_monthly_leadership"]),1)
        self.assertNotIn("draft",str(result))

    def test_refresh_requires_explicit_admin_role(self):
        with patch("market_admin_refresh._request_json",return_value="regular"):
            with self.assertRaises(PermissionError):
                run_admin_market_refresh("reader-token",{})

    def test_refresh_records_all_nine_and_does_not_publish(self):
        sources=[{"source_family":f"s{i}","source_url":"https://www.scb.se/",
                  "review_status":"needs_review"} for i in range(9)]
        issued={"status":"published","slug":"edition-01","published_at":"2026-11-16",
                "evidence_codes":["scb"],"brief_slugs":["b"]}
        data={"editions":[issued],"points":[],"briefs":[]}
        requests=[
            "admin",sources,
            {"recorded":True,"run_id":1,"status":"partial","sources_checked":9,
             "sources_failed":1},
        ]
        with patch("market_admin_refresh._request_json",side_effect=requests) as rpc:
            with patch("market_admin_refresh._source_check",
                       side_effect=lambda x:{
                           "source_family":x["source_family"],"status":"reachable",
                           "review_status":"needs_review","extracted_new_metrics":False
                       }):
                with patch("market_admin_refresh._jobtech_latest_complete",
                           return_value={"ok":False,"queries_failed":60}):
                    with patch("market_admin_refresh._recalculate",
                               return_value={"ok":True,"observation_count":1,
                                             "evidence_checksum_sha256":"hash"}):
                        receipt=run_admin_market_refresh("admin-token",data)
        self.assertEqual(receipt["receipt"]["sources_checked"],9)
        self.assertEqual(rpc.call_count,3)
        payload=rpc.call_args.kwargs["payload"]["p_result"]
        self.assertEqual(len(payload["source_results"]),9)
        self.assertEqual(payload["release_slug"],"edition-01")
        self.assertEqual(payload["proposal_count"],0)
        self.assertEqual(len(payload["source_results"]),9)


if __name__=="__main__":
    unittest.main()
