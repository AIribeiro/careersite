"""Jobseeker Edition contract: same evidence, different audience, independent PDF."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import copy
import sys
import unittest

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))
from test_market_intelligence_v2 import verified_v2_fixture, SLUG
from market_jobseeker_edition import (
    EDITION, FINDINGS, CANDIDATE_AGENDA, SCENARIOS,
    TITLE, validate_jobseeker_edition, jobseeker_market_pdf,
)


class JobseekerMarketReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points,cls.editorial=verified_v2_fixture()

    def test_same_published_manifest_and_five_independent_perspectives(self):
        self.assertEqual(EDITION, SLUG)
        self.assertIs(validate_jobseeker_edition(self.points,self.editorial,SLUG),
                      self.editorial)
        self.assertEqual(len(FINDINGS),5)
        self.assertEqual(len({t["key"] for t in FINDINGS}),5)
        self.assertEqual(len(SCENARIOS),3)
        self.assertEqual(len(CANDIDATE_AGENDA),6)
        codes={p["code"] for p in self.points}
        self.assertTrue(all(set(t["codes"]).issubset(codes) for t in FINDINGS))

    def test_jobseeker_pdf_is_original_edition_with_same_evidence_register(self):
        raw=jobseeker_market_pdf(self.points,self.editorial,SLUG)
        self.assertTrue(raw.startswith(b"%PDF"))
        self.assertGreater(len(raw),10000)
        pdf=PdfReader(BytesIO(raw))
        self.assertGreaterEqual(len(pdf.pages),8)
        text=" ".join(" ".join(p.extract_text() or "" for p in pdf.pages).split())
        for label in (
            TITLE, "30-day plan", "candidate reading", "Your next move",
            "Conditional outlook", "Evidence and limits", "159,500",
            "49", "29", "32,100", "62%", "September",
            "Methods and source-family limits", "Signed-off observation register",
            "Population:", "Published:", "Verified:",
        ):
            self.assertIn(label.lower(),text.lower())
        for row in self.points:
            self.assertIn(row["code"],text)
        self.assertNotIn("jair.ribeiro@outlook.it",text)
        self.assertNotIn("AI Portfolio Renewal Advisor",text)

    def test_edition_binding_and_missing_evidence_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "not bound|approved"):
            validate_jobseeker_edition(self.points,self.editorial,SLUG+"-wrong")
        changed=copy.deepcopy(self.editorial)
        changed["version"]="2.0.3"
        with self.assertRaises(ValueError):
            validate_jobseeker_edition(self.points,changed,SLUG)
        missing=[p for p in self.points if p["code"]!="scb_lor_2026q2_total"]
        with self.assertRaises(ValueError):
            jobseeker_market_pdf(missing,self.editorial,SLUG)

    def test_only_published_member_path_can_render_or_download(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text(encoding="utf-8")
        part=source.split("def render_private_market_signals",1)[1]
        self.assertIn("render_jobseeker_intelligence",part)
        self.assertLess(part.find("_release_snapshot("),part.find("render_jobseeker_intelligence("))
        self.assertLess(part.find("load_published_editorial("),part.find("render_jobseeker_intelligence("))
        module=(ROOT/"src/market_jobseeker_edition.py").read_text(encoding="utf-8")
        self.assertIn("validate_jobseeker_edition(points, editorial, edition_slug)",module)
        self.assertIn('on_click=record_event,args=(token,"pdf_review","jobseeker",edition_slug)',module)
        for disallowed in ("private_career","job_market_forecast","job_search_applications",
                           "portfolio_private_search"):
            self.assertNotIn(disallowed,module)

    def test_public_landing_has_two_clear_edition_routes_and_no_open_pdf(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text(encoding="utf-8")
        landing=source.split('MARKET_SIGNALS_LANDING_HTML = """',1)[1].split('"""',1)[0]
        self.assertIn("Executive edition",landing)
        self.assertIn("Jobseeker edition",landing)
        self.assertIn("perspective=jobseeker",landing)
        self.assertIn("Two editions",landing)
        self.assertIn("A4 PDF",landing)
        self.assertNotIn("jair.ribeiro@outlook.it",landing)
        self.assertIn("portfolio_next_navigation",source)

if __name__=="__main__":
    unittest.main()
