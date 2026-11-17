"""Market Signals 2.0: evidence binding, report content and PDF publication tests."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import json
import sys
import unittest

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))

from market_intelligence_v2 import (
    validate_editorial, build_executive_market_pdf,
    build_executive_decision_pdf, load_published_editorial,
)
from test_market_review_premium import verified_edition_fixture, point


SLUG="sweden-ai-data-market-review-2026-11-v2"


def verified_v2_fixture():
    p,b=verified_edition_fixture()
    editorial=json.loads(
        (ROOT/"docs/market_signals/november_2026_executive_v2.json").read_text(
            encoding="utf-8"
        )
    )
    available={row["code"] for row in p}
    needed={code for theme in editorial["themes"]
            for code in theme["evidence_codes"]}
    for code in sorted(needed-available):
        # Synthetic only: real member report uses the signed-off Supabase rows.
        family=(
            "scb_recruitment_needs_lor" if code.startswith("scb_lor")
            else "ki_konjunkturbarometern" if code.startswith("ki_")
            else "ec_digital_decade_sweden"
        )
        row=point(code,1)
        row.update({
            "source_family":family,
            "source_url":{
                "scb_recruitment_needs_lor":"https://www.scb.se/am0702",
                "ki_konjunkturbarometern":"https://www.konj.se/publikationer/konjunkturbarometern/",
                "ec_digital_decade_sweden":"https://digital-strategy.ec.europa.eu/en/factpages/swedens-2026-digital-decade-country-report",
            }[family],
            "metric_label":code.replace("_"," "),
            "period_complete":True,
        })
        p.append(row)
    return p,editorial


class MarketIntelligenceV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points,cls.editorial=verified_v2_fixture()

    def test_five_decisions_and_source_manifest(self):
        out=validate_editorial(self.editorial,self.points,SLUG)
        self.assertEqual(len(out["themes"]),5)
        self.assertEqual({t["key"] for t in out["themes"]},
                         {"investment","workforce","operating_model","sourcing","regional"})
        self.assertGreaterEqual(len(out["decision_agenda"]),5)

    def test_reject_evidence_outside_published_edition(self):
        data=json.loads(json.dumps(self.editorial))
        data["themes"][0]["evidence_codes"].append("unverified_market_claim")
        with self.assertRaisesRegex(ValueError,"signed-off"):
            validate_editorial(data,self.points,SLUG)

    def test_reject_cross_edition_reuse(self):
        with self.assertRaisesRegex(ValueError,"not bound"):
            validate_editorial(self.editorial,self.points,SLUG+"-different")

    def test_member_token_required_and_no_unchecked_fallback(self):
        with self.assertRaises(PermissionError):
            load_published_editorial("",SLUG,self.points,lambda *a,**k:None,lambda x:x)
        with self.assertRaisesRegex(RuntimeError,"unavailable"):
            load_published_editorial("jwt",SLUG,self.points,
                                     lambda *a,**k:{"wrong":"shape"},lambda x:x)

    def test_full_pdf_has_decisions_outlook_evidence_and_not_owner_data(self):
        raw=build_executive_market_pdf(self.points,self.editorial,SLUG)
        self.assertTrue(raw.startswith(b"%PDF"))
        reader=PdfReader(BytesIO(raw))
        self.assertGreaterEqual(len(reader.pages),9)
        extracted="\n".join((p.extract_text() or "") for p in reader.pages)
        for word in (
            "Executive reading","Conditional outlook",
            "Executive decision agenda","Source and observation register",
            "AI adoption is not a business case",
            "Recruit, develop or contract","Next 30 days",
            "scb_lor_2026q2_total","jobtech_v1_oct_se",
        ):
            self.assertIn(word.lower(),extracted.lower())
        self.assertNotIn("jair.ribeiro@outlook.it",extracted)

    def test_all_five_decision_pdfs_have_substantial_analysis(self):
        for t in self.editorial["themes"]:
            with self.subTest(lens=t["key"]):
                raw=build_executive_decision_pdf(
                    self.points,self.editorial,SLUG,t["key"])
                reader=PdfReader(BytesIO(raw))
                self.assertGreaterEqual(len(reader.pages),2)
                text="\n".join(page.extract_text() or "" for page in reader.pages)
                self.assertIn(t["title"][:15],text)
                self.assertIn("Recommended action",text)
                self.assertIn("source record",text.lower())

if __name__=="__main__":
    unittest.main()
