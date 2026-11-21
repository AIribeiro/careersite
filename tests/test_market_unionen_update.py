"""Dated Unionen release: source denominator integrity and two generated premium editions."""
from __future__ import annotations
import json
from pathlib import Path
from io import BytesIO
import sys
import unittest

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
from test_market_intelligence_v2 import verified_v2_fixture,SLUG as PRIOR_SLUG
from market_intelligence_v2 import build_executive_market_pdf,validate_editorial
from market_jobseeker_edition import jobseeker_market_pdf,validate_jobseeker_edition
from market_unionen_workforce_update import (
    NEW_SLUG,OLD_SLUG,REQUIRED,CLUBS,AI_ADOPTERS,verify_release,BOUNDARY
)


def verified_unionen_fixture():
    doc=json.loads((ROOT/"docs/market_signals/november_2026_unionen_2_1.json").read_text(encoding="utf-8"))
    assert len(doc["approved_points"])==53
    assert len(doc["unionen_points"])==10
    assert doc["edition_slug"]==NEW_SLUG
    # Full, exactly edition-bound 53-observation snapshot taken from the
    # publication database, avoiding incomplete old synthetic fixtures.
    return doc["approved_points"],doc["editorial"]


class UnionenMarketReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points,cls.editorial=verified_unionen_fixture()

    def test_source_manifest_matches_signed_off_facts(self):
        idx={p["code"]:p for p in self.points}
        self.assertEqual(len(idx),53)
        self.assertEqual(set(REQUIRED).intersection(idx),set(REQUIRED))
        self.assertTrue(verify_release(self.points,NEW_SLUG))
        self.assertFalse(verify_release(self.points,PRIOR_SLUG))
        self.assertEqual(idx["unionen_ai_staffing_need_changed_share"]["value"],42)
        self.assertEqual(idx["unionen_ai_data_it_new_roles_share"]["value"],24)
        self.assertIn("270",idx["unionen_ai_data_it_new_roles_share"]["population_note"])
        self.assertIn("468",idx["unionen_ai_adoption_clubs_share"]["population_note"])
        self.assertIn("adjusted",idx["unionen_ai_adopter_planned_professional_cuts_adjusted"]["metric_label"].lower())
        self.assertEqual(idx["unionen_business_outlook_index"]["metric_unit"],"index points")

    def test_editorial_is_separate_and_preserves_old_snapshot(self):
        self.assertEqual(self.editorial["edition_slug"],NEW_SLUG)
        self.assertEqual(self.editorial["version"],"2.1.0")
        self.assertEqual(self.editorial["issue_date"],"2026-11-21")
        self.assertEqual(self.editorial["unionen_research"]["ai_effects_clubs"],270)
        self.assertEqual(self.editorial["unionen_research"]["clubs"],468)
        self.assertEqual(self.editorial["unionen_research"]["selected_numeric_observations"],10)
        self.assertIs(validate_editorial(self.editorial,self.points,NEW_SLUG),self.editorial)
        self.assertIs(validate_jobseeker_edition(self.points,self.editorial,NEW_SLUG),self.editorial)
        self.assertEqual(PRIOR_SLUG,OLD_SLUG)
        self.assertNotEqual(PRIOR_SLUG,NEW_SLUG)

    def test_different_denominators_are_disclosed(self):
        self.assertEqual(len(CLUBS),2)
        self.assertEqual(len(AI_ADOPTERS),4)
        for phrase in ("270 clubs","SCB","association","employee weighting"):
            self.assertIn(phrase.lower(),BOUNDARY.lower()+
                          " "+self.editorial["reading_note"].lower())
        self.assertNotIn("AI caused",self.editorial["cover_assessment"].lower())
        self.assertNotIn("all Swedish AI vacancies",self.editorial["assessment"].lower())

    def test_executive_pdf_has_unionen_source_and_new_workforce_chapter(self):
        raw=build_executive_market_pdf(self.points,self.editorial,NEW_SLUG)
        self.assertTrue(raw.startswith(b"%PDF"))
        doc=PdfReader(BytesIO(raw))
        self.assertGreaterEqual(len(doc.pages),10)
        self.assertIn("2.1.0",str(doc.metadata.title))
        text=" ".join(" ".join(page.extract_text() or "" for page in doc.pages).split())
        for phrase in (
            "More business activity, slower professional hiring",
            "Unionen","83%","42%","24%","270 clubs","21 November 2026",
            "unionen_ai_adoption_clubs_share",
            "Unionen business outlook index",
        ):
            self.assertIn(phrase.lower(),text.lower())
        self.assertIn("not",text.lower())

    def test_jobseeker_pdf_has_unionen_and_career_guidance(self):
        raw=jobseeker_market_pdf(self.points,self.editorial,NEW_SLUG)
        self.assertTrue(raw.startswith(b"%PDF"))
        doc=PdfReader(BytesIO(raw))
        self.assertGreaterEqual(len(doc.pages),10)
        self.assertIn("Edition 1.2",str(doc.metadata.title))
        text=" ".join(" ".join(page.extract_text() or "" for page in doc.pages).split())
        for phrase in (
            "More business activity, slower professional hiring",
            "Career decision","Unionen","83%","42%","24%",
            "four-week job-search plan","Complete list of checked observations",
        ):
            self.assertIn(phrase.lower(),text.lower())
        self.assertIn("unionen_ai_data_it_new_roles_share",text)


if __name__=="__main__": unittest.main()
