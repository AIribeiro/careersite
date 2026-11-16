"""Contract tests for the curated AI & Data Market Signals service."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
import csv
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from page_advisory_market_signals import (  # noqa: E402
    _checked_url,_freshness,_load_curated,_safe_csv,executive_pdf
)


def point(code="scb_2026_ai_10plus",family="scb_enterprise_ai_adoption",val=49):
    return {
        "code":code,"series_code":code,"source_family":family,
        "metric_label":"Enterprises using AI","value":val,"metric_unit":"percent",
        "geography":"Sweden","period_label":"2026","population_note":
        "Enterprises with at least 10 employees in Sweden",
        "source_title":"SCB enterprise AI use 2026",
        "source_url":"https://www.scb.se/en/NV0116",
        "published_on":"2026-11-05","verified_on":"2026-11-16",
        "period_start":"2026-01-01","period_end":"2026-12-31",
        "evidence_grade":"primary","methodology":"Annual primary enterprise survey",
        "caveat":"Changing sector coverage affects direct comparisons",
    }


def brief():
    return {
        "slug":"adoption-is-not-capability",
        "title":"AI adoption is not capability",
        "thesis":"AI adoption is not a measure of leadership or ownership.",
        "interpretation":"SCB and JobTech measure different populations and cannot establish causation.",
        "decision_question":"Which capability must your business own?",
        "recommended_action":"Name an operating owner and evidence gate.",
        "counterevidence":"AI users may already have strong capability.",
        "limitations":"Small JobTech sample and 2026 survey classification changes.",
        "support_level":"independent_sources",
        "evidence_codes":["scb_2026_ai_10plus","jt_oct_2026"],
        "published_on":"2026-11-16",
    }


class MarketSignalsTests(unittest.TestCase):
    def test_trusted_https_only(self):
        self.assertTrue(_checked_url("https://www.scb.se/en/NV0116"))
        for bad in ("http://example.com","javascript:alert(1)","file:///tmp/x",
                    "https://attacker:secret@example.com"):
            with self.assertRaises(ValueError):
                _checked_url(bad)

    def test_source_specific_review_clock(self):
        p=point()
        self.assertEqual(_freshness(p,date(2027,1,15)),"Verified")
        p["source_family"]="af_jobtech_target_demand"
        self.assertEqual(_freshness(p,date(2026,12,5)),"Review overdue")

    def test_reader_only_or_anonymous_token_not_implicitly_granted(self):
        with self.assertRaises(PermissionError):
            _load_curated("")
        # The database performs the real authorization. This unit test checks
        # that a rejected member REST response never falls back to public data.
        with patch("page_advisory_market_signals._request_json",
                   side_effect=RuntimeError("REST denied")):
            with self.assertRaises(RuntimeError):
                _load_curated("invalid-token")

    def test_independent_source_claim_requires_two_families(self):
        p1=point()
        p2=point("jt_oct_2026","scb_enterprise_ai_adoption",29)
        with patch("page_advisory_market_signals._request_json",side_effect=[[p1,p2],[brief()]]):
            with self.assertRaisesRegex(ValueError,"Independent verification"):
                _load_curated("member-token")

    def test_complete_source_trace(self):
        p1=point()
        p2=point("jt_oct_2026","af_jobtech_target_demand",29)
        with patch("page_advisory_market_signals._request_json",side_effect=[[p1,p2],[brief()]]):
            out=_load_curated("member-token")
            self.assertEqual(len(out[0]),2)
            self.assertEqual(len(out[1]),1)

    def test_market_routes_preserve_member_session(self):
        from site_reader_navigation import _ALLOWED_PAGES, _parse_portfolio_route
        self.assertIn("advisory-market-signals", _ALLOWED_PAGES)
        self.assertEqual(
            _parse_portfolio_route("?page=advisory-access&view=market-signals"),
            {"page": "advisory-access", "view": "market-signals"},
        )
        self.assertEqual(
            _parse_portfolio_route("?page=advisory-market-signals"),
            {"page": "advisory-market-signals"},
        )
        self.assertIsNone(
            _parse_portfolio_route("?page=advisory-market-signals&access_token=secret")
        )

    def test_full_market_review_has_a_chart_decision_agenda_and_traceable_sources(self):
        from page_advisory_market_review import market_review_pdf
        base = point("scb_2026_ai_10plus")
        base["metric_label"] = "AI use among enterprises (10+ employees)"
        large = point("scb_2026_ai_250plus", val=85)
        large["metric_label"] = "AI use among large enterprises (250+ employees)"
        ads = []
        for id, value, start, end in [
            ("jun", 12, "2026-06-01", "2026-06-30"),
            ("jul", 15, "2026-07-01", "2026-07-31"),
            ("aug", 10, "2026-08-01", "2026-08-31"),
            ("sep", 20, "2026-09-01", "2026-09-30"),
            ("oct", 29, "2026-10-01", "2026-10-31"),
        ]:
            item = point("jobtech_v1_" + id + "_se",
                         "af_jobtech_target_demand", value)
            item.update({
                "series_code": "jobtech_ai_data_leadership_v1",
                "geography": "Sweden", "period_complete": True,
                "period_start": start, "period_end": end,
                "lens": "leadership",
                "metric_label": "AI & Data leadership title-basket advertisements",
                "period_label": id.title() + " 2026",
            })
            ads.append(item)
        regional = dict(ads[-1], code="jobtech_v1_oct_vgr",
                        geography="Västra Götaland", value=5)
        review = market_review_pdf(
            [base, large, *ads, regional], [
                {
                    **brief(),
                    "evidence_codes": ["scb_2026_ai_10plus", "jobtech_v1_oct_se"],
                }
            ],
        )
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(review))
        self.assertGreaterEqual(len(reader.pages), 6)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        self.assertIn("Decision agenda", text)
        self.assertIn("Source and observation register", text)
        self.assertIn("Leadership demand", text)
        self.assertIn("29", text)

    def test_csv_escapes_spreadsheet_formula(self):
        p=point()
        p["source_title"]="=IMPORTXML('secret')"
        csv_data=_safe_csv([p]).decode("utf-8-sig")
        rows=list(csv.reader(csv_data.splitlines()))
        self.assertTrue(rows[1][8].startswith("'="))
        self.assertNotIn("email",rows[0])

    def test_pdf_is_downloadable_and_has_sources_and_decision_record(self):
        p1=point()
        p2=point("jt_oct_2026","af_jobtech_target_demand",29)
        result=executive_pdf([p1,p2],brief(),"Sweden")
        self.assertTrue(result.startswith(b"%PDF"))
        from pypdf import PdfReader
        pdf=PdfReader(BytesIO(result))
        self.assertGreaterEqual(len(pdf.pages),3)
        full="\n".join((p.extract_text() or "") for p in pdf.pages)
        self.assertIn("Leadership decision record",full)
        self.assertIn("Enterprises using AI",full)
        self.assertIn("Evidence record",full)
        self.assertNotIn("jair.ribeiro@outlook.it",full)


if __name__=="__main__":
    unittest.main()
