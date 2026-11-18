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
        self.assertIn("Jobseeker Edition",str(pdf.metadata.title))
        self.assertNotIn("Job Market Review",str(pdf.metadata.title))
        overview_pages=[
            " ".join((page.extract_text() or "").split()) for page in pdf.pages
            if "Five ways to plan your job search" in
               " ".join((page.extract_text() or "").split())
        ]
        self.assertEqual(len(overview_pages),1)
        for item in FINDINGS:
            self.assertIn(item["title"][:15].lower(),
                          " ".join(overview_pages[0].lower().split()))
        self.assertGreaterEqual(len(pdf.pages),8)
        text=" ".join(" ".join(p.extract_text() or "" for p in pdf.pages).split())
        for label in (
            TITLE, "four-week job-search plan", "Understanding your job market",
            "Try this next", "What might happen next", "Sources and important limitations", "159,500",
            "49", "29", "32,100", "62%", "September",
            "Detailed source methods and limitations", "Complete list of checked observations",
            "Population:", "Published:", "Verified:",
        ):
            self.assertIn(label.lower(),text.lower())
        for row in self.points:
            self.assertIn(row["code"],text)
        self.assertNotIn("jair.ribeiro@outlook.it",text)
        self.assertNotIn("AI Portfolio Renewal Advisor",text)

    def test_accessible_copy_in_both_member_reader_and_download(self):
        from market_jobseeker_edition import INTRO, VALUE, FINDINGS, READING_HELP
        self.assertIn("more kinds of work",INTRO)
        self.assertIn("changing specialty",VALUE.lower())
        self.assertEqual(len(READING_HELP),5)
        self.assertTrue(any("courses" in item["reading"] for item in FINDINGS))
        self.assertTrue(any("entry-level" in item["reading"] for item in FINDINGS))
        pdf=PdfReader(BytesIO(jobseeker_market_pdf(self.points,self.editorial,SLUG)))
        content=" ".join((p.extract_text() or "") for p in pdf.pages)
        self.assertIn("YOUR QUESTION",content)
        self.assertIn("WHAT TO TRY",content)
        self.assertIn("WEEK / TASK",content)
        self.assertNotIn("DECISION AND ACCOUNTABILITY",content)
        self.assertIn("Five common terms explained",content)
        self.assertIn("Job vacancy",content)
        self.assertIn("four-week",content.lower())
        src=(ROOT/"src/market_jobseeker_edition.py").read_text(encoding="utf-8")
        self.assertIn("New to these market figures?",src)
        for term in ("portfolio_private_search","salary forecast","guaranteed interview"):
            self.assertNotIn(term.lower(),src.lower())

    def test_five_search_questions_remain_useful_to_nonexecutives(self):
        from market_jobseeker_edition import DECISION_MAP, INTRO, VALUE
        self.assertEqual(len(DECISION_MAP),5)
        self.assertIn("more kinds of work",INTRO)
        self.assertIn("changing specialty",VALUE)
        all_questions=" ".join(x[0] for x in DECISION_MAP)
        all_actions=" ".join(x[1] for x in DECISION_MAP).lower()
        for phrase in ("Where should I look?", "Which roles fit my skills?",
                       "How can I show what I can do?"):
            self.assertIn(phrase,all_questions)
        for phrase in ("studies","language","contract","employers"):
            self.assertIn(phrase,all_actions)

    def test_pdf_contains_five_practical_questions_and_research_limits(self):
        from market_jobseeker_edition import DECISION_MAP
        pdf=PdfReader(BytesIO(jobseeker_market_pdf(self.points,self.editorial,SLUG)))
        text=" ".join(" ".join((page.extract_text() or "").split()) for page in pdf.pages).lower()
        self.assertIn("five questions for your job search",text)
        for question,_ in DECISION_MAP:
            self.assertIn(question.lower(),text)
        for phrase in ("salary offers", "selected senior", "survey",
                       "does not measure which application channel works best"):
            self.assertIn(phrase,text)

    def test_public_benefits_and_limitations_are_clear(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text(encoding="utf-8")
        landing=source.split('MARKET_SIGNALS_LANDING_HTML = """',1)[1].split('"""',1)[0]
        self.assertIn('id="ms-perspectives"',landing)
        self.assertIn("Understand how AI and Data connect to your career.",landing)
        self.assertIn("entry-level analysis",landing)
        self.assertIn("selected senior titles",landing)
        self.assertIn("market_signals_jobseeker_cta",landing)
        self.assertIn("Rapporten är på engelska",landing)
        self.assertNotIn("guaranteed job",landing.lower())

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

    def test_static_candidate_claims_fail_closed_if_an_approved_value_drifts(self):
        import copy
        from market_jobseeker_edition import EXPECTED_NUMBERS
        self.assertEqual(EXPECTED_NUMBERS["scb_lor_2026q2_total"], 159500)
        self.assertEqual(EXPECTED_NUMBERS["jobtech_v1_oct_se"], 29)
        self.assertEqual(EXPECTED_NUMBERS["scb_2026_ai_expertise_barrier"], 62)
        changed=copy.deepcopy(self.points)
        for item in changed:
            if item["code"]=="jobtech_v1_oct_se":
                item["value"]=30
                break
        with self.assertRaisesRegex(ValueError, "Published evidence drift"):
            jobseeker_market_pdf(changed,self.editorial,SLUG)

    def test_candidate_pdf_identifies_its_own_date_and_limits(self):
        from market_jobseeker_edition import JOBSEEKER_ISSUE, LIMITS
        self.assertEqual(JOBSEEKER_ISSUE,"18 November 2026")
        self.assertIn("all occupations",LIMITS.lower())
        self.assertIn("salary guide",LIMITS.lower())
        data=jobseeker_market_pdf(self.points,self.editorial,SLUG)
        text=" ".join(" ".join((p.extract_text() or "") for p in PdfReader(BytesIO(data)).pages).split())
        self.assertIn(JOBSEEKER_ISSUE,text)
        self.assertIn("What these numbers do not cover",text)
        self.assertIn("THE JOB SEARCH QUESTION",text)

    def test_member_signup_does_not_require_corporate_email_for_candidates(self):
        portal=(ROOT/"src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn('"Email address *" if requested_service == "market-signals"',portal)
        self.assertIn("Registration accepts a personal or work email address",portal)
        self.assertIn("Executive or Jobseeker Edition",portal)

    def test_public_candidate_copy_does_not_claim_a_complete_ai_job_market(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text(encoding="utf-8")
        self.assertIn("not every entry-level opening",source)
        self.assertIn("JobTech covers selected senior titles only",source)
        self.assertIn("market_review_link_preference",source)

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
        self.assertIn("Executive Edition",landing)
        self.assertIn("Jobseeker Edition",landing)
        self.assertIn("perspective=jobseeker",landing)
        self.assertIn("Two free reports",landing)
        self.assertIn("A4 PDF",landing)
        self.assertNotIn("jair.ribeiro@outlook.it",landing)
        self.assertIn("portfolio_next_navigation",source)

if __name__=="__main__":
    unittest.main()
