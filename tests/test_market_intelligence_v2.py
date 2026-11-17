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


SLUG="sweden-ai-data-market-review-2026-11-v2-0-1"


def verified_v2_fixture():
    p,b=verified_edition_fixture()
    editorial=json.loads(
        (ROOT/"docs/market_signals/november_2026_executive_v2.json").read_text(
            encoding="utf-8"
        )
    )
    # Exact source-vintage test values make rendered preview pages honest
    # examples of the published research, not 1% placeholder indicators.
    # These are fixture-only copies of verified official observations.
    official={
      "scb_lor_2026q1_total":(143600,"vacancies","Total vacancies","2026 Q1"),
      "scb_lor_2026q2_total":(159500,"vacancies","Total vacant jobs, all recruitment channels","2026 Q2"),
      "scb_lor_2026q2_advertised":(127500,"vacancies","Advertised vacant jobs","2026 Q2"),
      "scb_lor_2026q2_other_channels":(32100,"vacancies","Vacancies via other recruitment channels","2026 Q2"),
      "scb_lor_2026q2_vgr_per100":(3.2,"vacancies per 100 jobs","Västra Götaland vacancy rate","2026 Q2"),
      "scb_lor_2026q2_national_per100":(2.9,"vacancies per 100 jobs","National vacancy rate","2026 Q2"),
      "scb_lor_2026q2_yoy_percent":(8,"percent","Reported vacancy change, YoY","2026 Q2"),
      "ki_2026_10_business_confidence":(110.7,"index points","Business confidence indicator","October 2026"),
      "ki_2026_10_staffing_past_net":(2,"net balance","Recent employment change balance","October 2026"),
      "ki_2026_10_staffing_future_net":(7,"net balance","Expected employment balance","October 2026"),
      "ec_dd_sweden_2026_roadmap_measures":(68,"measures","Digital Decade roadmap measures","Sweden 2026"),
      "ec_dd_sweden_2026_roadmap_total_eurb":(3.55,"EUR billion","Combined national roadmap budget","Sweden 2026"),
      "ec_dd_sweden_2026_roadmap_expiring_pct":(46,"percent","Roadmap measures ending in 2026","Sweden 2026"),
    }
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
        val,unit,label,period=official.get(code,(1,"percent",code,"2026"))
        row=point(code,val)
        row.update({
            "source_family":family,
            "source_url":{
                "scb_recruitment_needs_lor":"https://www.scb.se/am0702",
                "ki_konjunkturbarometern":"https://www.konj.se/publikationer/konjunkturbarometern/",
                "ec_digital_decade_sweden":"https://digital-strategy.ec.europa.eu/en/factpages/swedens-2026-digital-decade-country-report",
            }[family],
            "metric_label":label,
            "metric_unit":unit,
            "period_label":period,
            "period_complete":True,
        })
        row["source_title"]={"scb_recruitment_needs_lor":"SCB Recruitment Needs and Vacancies", "ki_konjunkturbarometern":"KI Business Tendency Survey", "ec_digital_decade_sweden":"European Commission Digital Decade Sweden"}[family]
        row["population_note"]="Defined survey or policy population, not AI-specialist hiring."
        row["methodology"]="Official reported measure, with an explicit observational date."
        row["caveat"]="Not a causal measure of AI investment returns, workforce shortages or outcomes."
        row["published_on"]="2026-11-05"
        row["verified_on"]="2026-11-17"
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

    def test_full_report_retains_source_denominators_and_caveats_in_pdf(self):
        raw=build_executive_market_pdf(self.points,self.editorial,SLUG)
        pages=PdfReader(BytesIO(raw)).pages
        all_text="\n".join(page.extract_text() or "" for page in pages)
        for term in (
            "Population:", "Research method / limitation:",
            "Method 1:", "Limit 1:", "Published:", "Verified:",
            "query seeds, classifier", "Source-series methods and limitations",
        ):
            self.assertIn(term,all_text)
        for point_record in self.points:
            self.assertIn(point_record["code"],all_text)
        for sentence in self.editorial["cover_assessment"].split(". "):
            self.assertIn(sentence[:35],all_text.replace("\n"," "))

    def test_decimal_precision_is_retained_in_full_and_focused_pdfs(self):
        from market_review_premium import _num
        self.assertEqual(_num(3.55),"3.55")
        self.assertEqual(_num(10.7),"10.7")
        self.assertEqual(_num(49),"49")
        self.assertEqual(_num(159500),"159,500")
        full=build_executive_market_pdf(self.points,self.editorial,SLUG)
        text=" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(full)).pages)
        self.assertIn("3.55 EUR billion",text)
        focused=build_executive_decision_pdf(self.points,self.editorial,SLUG,"investment")
        focused_text=" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(focused)).pages)
        self.assertIn("3.55 EUR billion",focused_text)

    def test_editorial_rejects_missing_cover_summary(self):
        copy=json.loads(json.dumps(self.editorial))
        copy.pop("cover_assessment")
        with self.assertRaisesRegex(ValueError,"incomplete"):
            validate_editorial(copy,self.points,SLUG)

    def test_sources_require_full_provenance(self):
        broken=json.loads(json.dumps(self.points))
        broken[0].pop("population_note")
        with self.assertRaisesRegex(ValueError,"missing provenance"):
            build_executive_market_pdf(broken,self.editorial,SLUG)

    def test_full_report_download_is_visible_before_decision_drilldown(self):
        source=(ROOT/"src/market_intelligence_v2.py").read_text(encoding="utf-8")
        member=source.split("def render_executive_intelligence(",1)[1]
        self.assertIn("Download complete Executive Market Review",member)
        self.assertIn("Download this Executive Decision Brief",member)
        self.assertLess(
            member.index("Download complete Executive Market Review"),
            member.index("st.selectbox("),
        )
        self.assertLess(
            member.index("st.selectbox("),
            member.index("Download this Executive Decision Brief"),
        )
        self.assertEqual(member.count('key="market_v2_complete_pdf"'),1)
        self.assertEqual(member.count('key="market_v2_decision_pdf"'),1)

    def test_all_five_decision_pdfs_have_substantial_analysis(self):
        for t in self.editorial["themes"]:
            with self.subTest(lens=t["key"]):
                raw=build_executive_decision_pdf(
                    self.points,self.editorial,SLUG,t["key"])
                reader=PdfReader(BytesIO(raw))
                self.assertGreaterEqual(len(reader.pages),2)
                text="\n".join(page.extract_text() or "" for page in reader.pages)
                self.assertIn(t["title"][:15],text)
                self.assertIn("recommended action",text.lower())
                self.assertIn("source record",text.lower())

if __name__=="__main__":
    unittest.main()
