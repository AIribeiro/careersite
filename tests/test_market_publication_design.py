"""Print, editorial and evidence contracts shared across the market publications."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))

from page_advisory_market_demo import public_historical_demo_pdf
from market_intelligence_v2 import (
    build_executive_market_pdf,build_executive_decision_pdf,
)
from test_market_intelligence_v2 import SLUG,verified_v2_fixture

def reader(blob):
    assert blob.startswith(b"%PDF")
    return PdfReader(BytesIO(blob))

def uris(document):
    result=[]
    for page in document.pages:
        for ref in page.get("/Annots",[]):
            obj=ref.get_object()
            action=obj.get("/A")
            if action and action.get("/URI"):
                result.append(str(action["/URI"]))
    return result

def printable_text(document):
    return [" ".join((p.extract_text() or "").split()) for p in document.pages]

class MarketPublicationSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points,cls.editorial=verified_v2_fixture()

    def test_free_sample_starts_with_original_executive_argument(self):
        pdf=reader(public_historical_demo_pdf())
        self.assertGreaterEqual(len(pdf.pages),4)
        self.assertLessEqual(len(pdf.pages),9)
        pages=printable_text(pdf)
        cover=pages[0].lower()
        self.assertIn("market signals / sweden",cover)
        self.assertIn("jair ribeiro",cover)
        self.assertIn("public research / historical edition",cover)
        self.assertIn("june-august 2026",cover)
        self.assertIn("the evidence at a glance",cover)
        body=" ".join(pages).lower()
        for phrase in (
            "the signal is small", "the management question is not",
            "geography and interpretation", "four decisions worth making",
            "source and audit trail", "16 november 2026",
            "17 november 2026", "jobtech_v1_jun_se",
            "jobtech_v1_aug_vgr",
        ):
            self.assertIn(phrase,body)
        self.assertNotIn("49%"," ".join(pages))
        self.assertNotIn("85%"," ".join(pages))
        self.assertTrue(any("jobtechdev.se" in u for u in uris(pdf)))
        self.assertFalse(any(u.startswith("http://") for u in uris(pdf)))

    def test_full_premium_report_has_coherent_cover_and_all_sources(self):
        pdf=reader(build_executive_market_pdf(self.points,self.editorial,SLUG))
        self.assertGreaterEqual(len(pdf.pages),9)
        self.assertLessEqual(len(pdf.pages),30)
        pages=printable_text(pdf)
        cover=pages[0].lower()
        for phrase in ("market signals / sweden","executive edition "+self.editorial["version"],
                       "jair ribeiro","the evidence at a glance"):
            self.assertIn(phrase,cover)
        content=" ".join(pages).lower()
        for theme in self.editorial["themes"]:
            self.assertIn(theme["title"].lower(),content)
        for phrase in (
            "executive reading","executive decision agenda",
            "conditional outlook","source and observation register",
            "recommended action","business implication",
        ):
            self.assertIn(phrase,content)
        for p in self.points:
            self.assertIn(p["code"].lower(),content)
        self.assertGreaterEqual(len(uris(pdf)),len(self.points))
        self.assertFalse(any(u.startswith("http://") for u in uris(pdf)))

    def test_version_and_publisher_scope_are_consistent(self):
        pdf=reader(build_executive_market_pdf(self.points,self.editorial,SLUG))
        cover=printable_text(pdf)[0].lower()
        self.assertIn("executive edition "+self.editorial["version"],cover)
        self.assertNotIn("executive edition 2.0 / sweden",cover)
        self.assertIn("edition "+self.editorial["version"],str(pdf.metadata.title).lower())
        pages=printable_text(pdf)
        method_pages=[p for p in pages if "source-series methods and limitations" in p.lower()]
        self.assertEqual(len(method_pages),1)
        self.assertIn("METHOD AND INTERPRETATION BOUNDARIES",
                      method_pages[0])
        content=" ".join(pages)
        self.assertIn("SCB Recruitment Needs and Vacancies",content)
        self.assertIn("Source releases represented:",content)
        self.assertIn("Q1 2026",content)
        self.assertIn("Q2 2026",content)
        # The only inherited Q1 wording must be tied to the Q1 source release,
        # never to the entire seven-observation family.
        for page in pages:
            if "7 observations" in page and "Q1 2026" in page:
                self.assertIn("Q2 2026",page)

    def test_evidence_appendix_is_readable_and_cross_referenced(self):
        pdf=reader(build_executive_market_pdf(self.points,self.editorial,SLUG))
        text=" ".join(printable_text(pdf))
        for phrase in ("OBSERVATION / PROVENANCE","PERIOD / VALUE",
                       "method 1, limit","Population:","Published:","Verified:"):
            self.assertIn(phrase.lower(),text.lower())
        self.assertIn("1 advertisement",text)
        self.assertNotIn("1 advertisements",text)
        self.assertGreaterEqual(len(pdf.outline),10)

    def test_agenda_not_stranded_before_sources(self):
        pdf=reader(build_executive_market_pdf(self.points,self.editorial,SLUG))
        pages=printable_text(pdf)
        agenda=[i for i,p in enumerate(pages) if
            "Decisions to take into the next executive" in p]
        self.assertEqual(len(agenda),1)
        self.assertIn("Set the market review triggers",pages[agenda[0]])
        self.assertNotIn("Source and observation register",pages[agenda[0]])

    def test_decision_briefs_share_identity_and_remain_specific(self):
        for theme in self.editorial["themes"]:
            with self.subTest(key=theme["key"]):
                pdf=reader(build_executive_decision_pdf(
                    self.points,self.editorial,SLUG,theme["key"]))
                self.assertGreaterEqual(len(pdf.pages),3)
                self.assertLessEqual(len(pdf.pages),10)
                pages=printable_text(pdf)
                self.assertIn("market signals / sweden",pages[0].lower())
                self.assertIn(theme["title"][:23].lower(),
                              " ".join(pages).lower())
                text=" ".join(pages).lower()
                self.assertIn("recommended action",text)
                self.assertIn("alternative explanation",text)
                self.assertIn("source record",text)
                self.assertGreaterEqual(len(uris(pdf)),len(theme["evidence_codes"]))

    def test_print_sizing_and_density_no_empty_pages(self):
        docs=[
            reader(public_historical_demo_pdf()),
            reader(build_executive_market_pdf(self.points,self.editorial,SLUG)),
        ]
        for doc in docs:
            for n,p in enumerate(doc.pages,1):
                with self.subTest(pages=len(doc.pages),page=n):
                    self.assertAlmostEqual(float(p.mediabox.width),595.28,delta=.25)
                    self.assertAlmostEqual(float(p.mediabox.height),841.89,delta=.25)
                    length=len(" ".join((p.extract_text() or "").split()))
                    # Editorial covers deliberately use fewer words than analysis pages.
                    min_chars = 650 if n == 1 else (250 if n == len(doc.pages) else 900)
                    self.assertGreater(length,min_chars,
                        "Sparse page in executive publication: "+
                        str(n)+" / "+str(len(doc.pages)))

    def test_one_shared_publication_technology_not_invented_claims(self):
        for path in (
            "src/page_advisory_market_demo.py",
            "src/market_intelligence_v2.py",
        ):
            source=(ROOT/path).read_text(encoding="utf-8")
            self.assertIn("market_publication_design",source)
        helper=(ROOT/"src/market_publication_design.py").read_text(encoding="utf-8")
        self.assertIn("def cover_callback(",helper)
        self.assertIn("def sources_table(",helper)
        self.assertIn("def decision_table(",helper)
        self.assertIn("return assemble(", (ROOT/"src/market_intelligence_v2.py").read_text())

if __name__=="__main__":
    unittest.main()
