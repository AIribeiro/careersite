"""Verified-edition research PDF contract: comprehensive, bounded and readable."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from market_review_premium import _approved, _jobtech, build_market_review_pdf
from page_advisory_market_review import market_review_pdf


SCB_URL=(
 "https://www.scb.se/hitta-statistik/statistik-efter-amne/"
 "forskning-och-det-digitala-samhallet/det-digitala-samhallet/"
 "it-anvandning-i-foretag/pong/statistiknyhet/it-anvandning-i-foretag-2026/"
)


def point(code, value, family="scb_enterprise_ai_adoption", *,
          label=None, geo="Sweden", unit="percent",
          begin="2026-01-01",end="2026-12-31",complete=True,
          series=None):
    urls={
      "scb_enterprise_ai_adoption":SCB_URL,
      "af_jobtech_target_demand":"https://historical.api.jobtechdev.se/search",
      "brainville_consulting_market":"https://www.brainville.com/sv/Blog/Post/1923",
    }
    return {
      "code":code,"value":value,"source_family":family,
      "series_code":series or code,"lens":"adoption" if family.startswith("scb") else "leadership",
      "geography":geo,"period_start":begin,"period_end":end,
      "period_label":begin[:7] if family.startswith("af_jobtech") else "2026",
      "period_complete":complete,"metric_label":label or code.replace("_"," ").title(),
      "metric_unit":unit,"population_note":"Sampled population and methodology explicit",
      "source_title":family+" primary publisher",
      "source_url":urls[family],"published_on":"2026-11-05",
      "verified_on":"2026-11-16","evidence_grade":"primary",
      "methodology":"Defined source measurement scope and classification",
      "caveat":"Scope and population restrictions must be respected.",
    }


def verified_edition_fixture():
    readings={
      "scb_2026_ai_10plus":49,"scb_2026_ai_10to49":45,
      "scb_2026_ai_50to249":65,"scb_2026_ai_250plus":85,
      "scb_2026_data_analytics_use":39,"scb_2026_analytics_internal":33,
      "scb_2026_bi_use":25,"scb_2026_ai_expertise_barrier":62,
      "scb_2026_ai_privacy_barrier":43,"scb_2026_ai_data_quality_barrier":34,
    }
    data=[point(code,value) for code,value in readings.items()]
    monthly={
      "jun":("2026-06-01","2026-06-30",[12,6,2]),
      "jul":("2026-07-01","2026-07-31",[15,8,2]),
      "aug":("2026-08-01","2026-08-31",[10,6,1]),
      "sep":("2026-09-01","2026-09-30",[20,12,4]),
      "oct":("2026-10-01","2026-10-31",[29,13,5]),
      "nov15":("2026-11-01","2026-11-15",[12,3,3]),
    }
    for month,(start,finish,values) in monthly.items():
        for suffix,geo,value in zip(
            ("se","sto","vgr"),("Sweden","Stockholm","Västra Götaland"),values
        ):
            obs=point(
                "jobtech_v1_"+month+"_"+suffix,value,
                "af_jobtech_target_demand",geo=geo,unit="advertisements",
                begin=start,end=finish,complete=month!="nov15",
                series="jobtech_ai_data_leadership_v1",
            )
            obs["period_label"]={
                "sep":"September 2026 (revised)",
                "nov15":"November 1-15, 2026"
            }.get(month,month.title()+" 2026")
            data.append(obs)
    for code,val in [
        ("brainville_202610_assignments_yoy",10.7),
        ("brainville_202610_consultants_yoy",18.5),
    ]:
        data.append(point(code,val,"brainville_consulting_market",
                          label=code,unit="percent YoY",
                          begin="2026-10-01",end="2026-10-31"))
    briefs=[
        {
            "slug":"adoption-is-not-capability",
            "title":"AI adoption is widespread. Where is the operating capability?",
            "thesis":"Usage alone does not prove stable business outcomes.",
            "interpretation":"Different populations, definitions and periods cannot be combined into a single maturity score.",
            "decision_question":"Are we buying licenses or changing an accountable workflow?",
            "recommended_action":"Define process baseline, named accountable owner and measurable outcome.",
            "counterevidence":"Many firms reporting adoption may already operate mature controls.",
            "limitations":"SCB classification break and lack of organisation-level linkage.",
            "support_level":"independent_sources",
            "evidence_codes":["scb_2026_ai_10plus","jobtech_v1_oct_se"],
            "published_on":"2026-11-16",
        },
        {
            "slug":"ai-leadership-demand-is-a-small-signal",
            "title":"AI leadership recruitment is observable but easy to exaggerate",
            "thesis":"A narrow title classifier is not an employment census.",
            "interpretation":"Monthly counts vary and ads do not measure completed hires.",
            "decision_question":"Which skills must we hire, and which can we grow?",
            "recommended_action":"Compare defined roles with internal development and external cover.",
            "counterevidence":"Not every role uses the same title, and indexing may revise counts.",
            "limitations":"Small monthly cohorts, unadvertised roles not measured.",
            "support_level":"independent_sources",
            "evidence_codes":["jobtech_v1_sep_se","jobtech_v1_oct_se","scb_2026_ai_10plus"],
            "published_on":"2026-11-16",
        },
        {
            "slug":"build-or-buy-data-capability",
            "title":"Build, recruit or contract",
            "thesis":"Permanent accountability must be designed even if contractors deliver.",
            "interpretation":"SCB in-house Data practice and Brainville marketplace measure different populations.",
            "decision_question":"What capability must stay accountable inside?",
            "recommended_action":"Set explicit transfer and ownership conditions with every vendor.",
            "counterevidence":"External specialists can offer better learning and lower operating risk.",
            "limitations":"No measure of AI consultant supply or contract prices.",
            "support_level":"independent_sources",
            "evidence_codes":["scb_2026_analytics_internal","brainville_202610_assignments_yoy"],
            "published_on":"2026-11-16",
        },
        {
            "slug":"data-and-risk-barriers-are-business-decisions",
            "title":"Data and risk barriers demand ownership",
            "thesis":"Data access and privacy risks are genuine reported reasons to decline AI.",
            "interpretation":"The subgroup is only non-adopters that considered AI.",
            "decision_question":"Which risk can we resolve in the next quarter?",
            "recommended_action":"Specify a process-level safe operating condition and review.",
            "counterevidence":"Not all companies should adopt every use case.",
            "limitations":"Single-source non-adopter responses, multiple-choice survey.",
            "support_level":"single_source",
            "evidence_codes":["scb_2026_ai_expertise_barrier",
                              "scb_2026_ai_privacy_barrier","scb_2026_ai_data_quality_barrier"],
            "published_on":"2026-11-16",
        },
    ]
    return data,briefs


class FullMarketReviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points,cls.briefs=verified_edition_fixture()
        assert len(cls.points)==30
        cls.edition={"issue_date":"2026-11-16","status":"published",
                     "slug":"ai-data-market-review-2026-11-edition-01"}
        cls.document=market_review_pdf(cls.points,cls.briefs,cls.edition)
        cls.reader=PdfReader(BytesIO(cls.document))
        cls.text="\n".join(page.extract_text() or "" for page in cls.reader.pages)

    def test_all_thirty_approved_evidence_codes_are_in_the_source_register(self):
        for observation in self.points:
            with self.subTest(code=observation["code"]):
                self.assertIn(observation["code"],self.text)
        self.assertNotIn("scb_2026_ict_specialists",self.text)
        self.assertNotIn("market_context_20261116_",self.text)

    def test_research_is_not_repetitive_table_only_summary(self):
        self.assertGreaterEqual(len(self.reader.pages),13)
        for phrase in (
            "What is included - and what is not.",
            "Executive reading",
            "Data & Analytics capabilities",
            "Barriers to adoption",
            "Leadership recruitment",
            "Location & timing",
            "Consulting & external capability",
            "Cross-source synthesis",
            "Leadership decision agenda",
            "Independent executive interpretation",
            "What to monitor next",
            "Source and observation register",
            "reproducibility",
        ):
            with self.subTest(section=phrase):
                self.assertIn(phrase.lower(),self.text.lower())

    def test_correct_populations_and_caveats_are_not_lost(self):
        for phrase in (
            "enterprises that considered AI but decided not to",
            "cannot, on its own",
            "not a measure of",
            "not all Swedish",
            "not a labour-market",
            "not a statistically",
            "does not establish",
            "not a full month",
            "retrospective",
            "SNI",
            "not a price",
            "different denominators",
        ):
            with self.subTest(caveat=phrase):
                self.assertIn(phrase.lower(),self.text.lower())

    def test_report_retains_exact_verified_vintage(self):
        self.assertIn("16 November 2026",self.text)
        self.assertIn("10.7",self.text)
        self.assertIn("18.5",self.text)
        self.assertIn("September 2026 (revised)",self.text)
        self.assertIn("November 1-15",self.text)
        self.assertIn("29",self.text)
        self.assertNotIn("2027 forecast",self.text.lower())
        self.assertIn("jairribeiro.com",self.text.lower())

    def test_a4_and_no_blank_or_near_empty_pages(self):
        for n,page in enumerate(self.reader.pages,1):
            with self.subTest(page=n):
                self.assertAlmostEqual(float(page.mediabox.width),595.28,delta=.2)
                self.assertAlmostEqual(float(page.mediabox.height),841.89,delta=.2)
                self.assertGreater(len(page.extract_text() or ""),110)

    def test_pdf_contains_live_clickable_reference_annotations(self):
        uri=[]
        for page in self.reader.pages:
            for annot in page.get("/Annots",[]):
                obj=annot.get_object()
                action=obj.get("/A")
                if action and action.get("/URI"):
                    uri.append(str(action["/URI"]))
        self.assertTrue(any("scb.se/" in x for x in uri))
        self.assertTrue(any("jobtechdev.se/" in x for x in uri))
        self.assertTrue(any("brainville.com/" in x for x in uri))

    def test_source_revision_and_integrity_fail_closed(self):
        dupe=[self.points[0],*self.points]
        with self.assertRaisesRegex(ValueError,"repeated market evidence"):
            build_market_review_pdf(dupe,self.briefs,self.edition)
        tampered=[dict(p) for p in self.points]
        tampered[0]["value"]=float("nan")
        with self.assertRaisesRegex(ValueError,"not finite"):
            build_market_review_pdf(tampered,self.briefs,self.edition)
        broken=[dict(p) for p in self.points]
        broken[0]["source_url"]="http://untrusted.example"
        with self.assertRaisesRegex(ValueError,"Invalid evidence source"):
            build_market_review_pdf(broken,self.briefs,self.edition)

    def test_missing_optional_indicators_are_not_fabricated(self):
        pts=[p for p in self.points if
            p["source_family"]!="brainville_consulting_market" and
            p["code"] not in {
              "scb_2026_ai_10to49","scb_2026_ai_50to249",
              "scb_2026_analytics_internal","scb_2026_bi_use",
              "scb_2026_data_analytics_use",
              "scb_2026_ai_expertise_barrier","scb_2026_ai_privacy_barrier",
              "scb_2026_ai_data_quality_barrier",
            }]
        compatible=[self.briefs[0]]
        doc=build_market_review_pdf(pts,compatible,self.edition)
        self.assertTrue(doc.startswith(b"%PDF"))
        body="\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(doc)).pages)
        self.assertNotIn("10.7% YoY",body)
        self.assertIn("Leadership demand",body)

    def test_authored_synthesis_not_treated_as_causal_statistic(self):
        assert "causal" in self.text.lower()
        assert "not a measure" in self.text.lower()
        assert "not comparable" in self.text.lower() or "cannot" in self.text.lower()


if __name__=="__main__":
    unittest.main()
