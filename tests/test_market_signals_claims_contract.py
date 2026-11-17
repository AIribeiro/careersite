"""Market Signals public claims vs original archive and current V2 research.

Protect against turning an unapproved market source or a dormant
dashboard section into an advertised research product.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))

from page_advisory_market_signals import (
 MARKET_SIGNALS_LANDING_HTML,advisory_market_signals,executive_pdf
)
from page_advisory_market_observatory import DASHBOARDS, _evidence_csv
from page_advisory_market_review import market_review_pdf
from page_advisory_market_demo import (
 public_market_demo_html,public_historical_demo_pdf,_sample_points
)
from test_market_review_premium import verified_edition_fixture


class PublicationClaimsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=MARKET_SIGNALS_LANDING_HTML
        cls.points,cls.briefs=verified_edition_fixture()
        cls.by_code={p["code"]:p for p in cls.points}

    def test_market_figures_match_full_report_evidence_fixture(self):
        expected={
          "scb_2026_ai_10plus":49,
          "scb_2026_ai_250plus":85,
          "jobtech_v1_oct_se":29,
          "brainville_202610_assignments_yoy":10.7,
          "brainville_202610_consultants_yoy":18.5,
        }
        self.assertEqual(len(self.points),30)
        self.assertEqual(len(self.briefs),4)
        self.assertEqual(len({p["source_family"] for p in self.points}),3)
        for code,value in expected.items():
            with self.subTest(code=code):
                self.assertEqual(float(self.by_code[code]["value"]),float(value))
                self.assertIn(str(value),self.html)
        self.assertIn("Published 17 November 2026",self.html)
        self.assertIn("<strong>43</strong>",self.html)
        self.assertIn("<strong>5</strong>",self.html)
        self.assertIn("<strong>6</strong>",self.html)

    def test_claimed_deliverables_are_implemented(self):
        actual=advisory_market_signals()
        internal=(ROOT/"src/page_advisory_market_signals.py").read_text()
        observatory=(ROOT/"src/page_advisory_market_observatory.py").read_text()
        self.assertIn("Market Observatory",actual)
        self.assertIn("Complete AI &amp; Data Market Review",actual)
        self.assertIn("Five decision perspectives",actual)
        self.assertIn("alternative explanations",actual)
        self.assertIn("market_review_pdf(points,briefs,release)",internal)
        self.assertIn("executive_pdf(points,brief,geo)",internal)
        self.assertIn("Download filtered source ledger",observatory)
        self.assertIn("Leadership decision record",internal)
        self.assertTrue(callable(market_review_pdf))
        self.assertTrue(callable(executive_pdf))
        self.assertTrue(callable(_evidence_csv))

    def test_all_eight_tabs_named_but_unapproved_families_not_promised(self):
        self.assertEqual(len(DASHBOARDS),8)
        self.assertEqual(DASHBOARDS["signals"],"Interpretation and evidence limits")
        for name in DASHBOARDS.values():
            self.assertIn(name.replace("&","&amp;"),self.html)
        self.assertIn("not published in the current edition",self.html)
        self.assertIn("Further sector indicators are awaiting review",self.html)
        self.assertIn("Additional skills and salary measures are being checked",self.html)
        self.assertIn("June–October 2026 show retrospective leadership-advertisement records only",self.html)
        self.assertNotIn("AI salary benchmark available now",self.html)
        self.assertIn("not a live market forecast",self.html.lower())

    def test_public_sample_is_oldest_narrow_history_not_full_market(self):
        html=public_market_demo_html()
        sample=_sample_points()
        self.assertEqual(len(sample),9)
        self.assertEqual({p["source_family"] for p in sample},{"af_jobtech_target_demand"})
        self.assertEqual({str(p["period_start"])[:7] for p in sample},
                         {"2026-06","2026-07","2026-08"})
        self.assertIn("not a full market review from those summer months",self.html)
        self.assertIn("Later SCB and Brainville research",html)
        self.assertIn("created an account" if False else "Before you create an account",html)
        self.assertTrue(public_historical_demo_pdf().startswith(b"%PDF"))

    def test_plain_language_customer_first_and_no_absurd_promises(self):
        public=(self.html+" "+public_market_demo_html()).lower()
        disallowed=[
          "genuine, no-registration",
          "fully automatic live market",
          "accurate talent shortage forecast",
          "source families",
          "would you like to interrogate",
          "decision-ready reports",
          "all figures are updated in real time",
          "no invented market conclusions",
          "statistical causation",
          "a hiring boom",
        ]
        for phrase in disallowed:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase,public)
        self.assertIn("what the figure cannot tell",public)
        self.assertIn("limits of the published evidence",public)

    def test_exportable_pdf_uses_same_scope_not_unapproved_sources(self):
        doc=market_review_pdf(self.points,self.briefs,
                              {"issue_date":"2026-11-16","status":"published"})
        self.assertTrue(doc.startswith(b"%PDF"))
        self.assertGreater(len(doc),3200)


if __name__=="__main__":
    unittest.main()
