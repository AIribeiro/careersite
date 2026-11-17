"""Public Market Signals landing page: executive value, claims and responsive access."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from page_advisory_market_signals import (
    advisory_market_signals,MARKET_SIGNALS_LANDING_CSS,MARKET_SIGNALS_LANDING_HTML
)


class LandingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.ids=[]
        self.headings=[]
        self.images=[]
        self.live_regions=[]
        self.text=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get("id"):self.ids.append(d["id"])
        if tag=="a":self.links.append(d)
        if tag=="img":self.images.append(d)
        if d.get("role")=="alert":self.live_regions.append(d)
    def handle_data(self,data):
        self.text.append(data)


class MarketSignalsLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page=advisory_market_signals()
        cls.parser=LandingParser()
        cls.parser.feed(cls.page)
        cls.copy=" ".join(cls.parser.text)

    def test_headlines_and_subheadings_use_full_available_content_width(self):
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn(".ms-hero-grid {display:grid;grid-template-columns:minmax(0,1fr)",css)
        self.assertIn(".ms-section-head {display:block;width:100%",css)
        self.assertIn(".ms-cta-grid {display:grid;grid-template-columns:minmax(0,1fr)",css)
        self.assertIn(".ms-hero h1 {display:block;width:100%;max-width:none",css)
        self.assertIn(".ms-section h2 {display:block;width:100%;max-width:none",css)
        self.assertIn(".ms-lastcta h2 {display:block;width:100%;max-width:none",css)
        self.assertIn(".ms-section-intro {font-size:15px;color:#56687A;line-height:1.77;width:100%;max-width:none",css)
        self.assertIn(".ms-hero-lead {color:#D6DFE9;font-size:clamp(17px,1.5vw,20px);line-height:1.65;width:100%;max-width:none",css)
        self.assertIn(".container {width:calc(100% - clamp(30px,5vw,88px));max-width:none",css)
        self.assertNotIn("grid-template-columns:minmax(0,1.15fr) minmax(0,.8fr)",css)
        self.assertNotIn("max-width:950px",css)

    def test_market_signals_footer_is_standard_and_contextual(self):
        from page_home_featured import inject_writing_footer
        document=self.page
        self.assertEqual(document.count('<footer class="footer">'),1)
        self.assertIn('aria-label="Market Signals footer navigation"',document)
        self.assertIn('data-analytics-section="market-signals-footer-navigation"',document)
        for href in (
            '?page=advisory',
            '?page=advisory-market-demo',
            '?page=home',
            '?page=advisory-access&amp;view=market-signals',
        ):
            self.assertIn('href="'+href+'"',document)
        self.assertLess(document.index('aria-label="Market Signals footer navigation"'),
                        document.index('<footer class="footer">'))
        self.assertEqual(inject_writing_footer(document,"advisory-market-signals"),document)
        self.assertNotIn('data-analytics-section="site-writing-footer"',document)

    def test_no_generic_old_four_lens_page(self):
        self.assertNotIn("Four evidence lenses",self.page)
        self.assertNotIn("Market signals connected to leadership decisions.",self.page)
        self.assertNotIn("What readers receive",self.page)

    def test_executive_target_and_decision_value_are_explicit(self):
        for phrase in (
            "AI &amp; Data Market Intelligence for Executive Decision-Making",
            "For AI, Data and Analytics leaders",
            "Internal capability, recruitment or external expertise",
            "Business outcomes beyond reported adoption",
            "Presenting evidence and uncertainty to management",
            "Market Observatory",
            "Complete AI &amp; Data Market Review",
            "Decision briefs and source register",
        ):
            self.assertIn(phrase,self.page)

    def test_executive_headlines_use_measured_claims_not_promotional_promises(self):
        expected=[
            "AI &amp; Data Market Intelligence for Executive Decision-Making",
            "What the published evidence shows",
            "AI use is reported; business outcomes require separate evidence.",
            "Senior AI &amp; Data recruitment: a limited observed sample.",
            "Consulting assignments and available capacity both increased.",
            "Historical leadership-advertisement evidence, June–August 2026.",
            "Source provenance, definitions and limitations.",
            "Limits of the published evidence.",
            "November 2026: Research and supporting evidence.",
        ]
        for heading in expected:
            self.assertIn(heading,self.page)
        for obsolete in [
            "Make sense of Sweden's AI",
            "Three findings you can explore",
            "One report you can try",
            "Start with your question, not a headline",
            "Bring a better question",
            "TRY THE RESEARCH",
            "You should be able to check every figure",
        ]:
            self.assertNotIn(obsolete,self.page)

    def test_high_value_examples_are_exact_dated_edition_01_scope(self):
        for phrase in (
            "Published 16 November 2026",
            "published data points",
            "data sources",
            "written analyses",
            "49<span>%</span>",
            "85%",
            "29",
            "+10.7",
            "+18.5",
            "October 2026",
            "measure different things",
        ):
            self.assertIn(phrase.lower(),self.page.lower())
        self.assertNotIn("AI jobs increased 45%",self.page)
        self.assertNotIn("AI consultant shortages",self.page)

    def test_all_eight_real_dashboard_topics_present(self):
        expected=[
            "Executive evidence overview",
            "AI &amp; Data leadership advertisements",
            "Enterprise AI adoption &amp; capabilities",
            "Skills and management pay — under review",
            "Consulting and sector context",
            "Interpretation and evidence limits",
            "Comparable historical observations",
            "Sources and measurement methods",
        ]
        for text in expected:
            self.assertIn(text,self.page)

    def test_reader_access_paths_are_intact(self):
        links=self.parser.links
        registrations=[link for link in links
            if link.get("href")=="?page=advisory-access&view=market-signals"]
        signins=[link for link in links
            if link.get("href")=="?page=advisory-access&view=market-signals&signin=1"]
        self.assertGreaterEqual(len(registrations),2)
        self.assertTrue(signins)
        self.assertTrue(all(link.get("target")=="_self" for link in registrations+signins))
        self.assertIn("ms-findings",self.parser.ids)
        self.assertIn("ms-inside",self.parser.ids)
        self.assertEqual(len(self.parser.ids),len(set(self.parser.ids)))

    def test_public_research_page_does_not_open_private_member_data(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text()
        body=source.split("def advisory_market_signals() -> str:")[1].split("def _checked_url")[0]
        self.assertNotIn("_load_curated(",body)
        self.assertNotIn("auth.users",MARKET_SIGNALS_LANDING_HTML)
        self.assertNotIn("jair.ribeiro@outlook.it",MARKET_SIGNALS_LANDING_HTML)
        self.assertNotIn("recruiter meetings",MARKET_SIGNALS_LANDING_HTML.lower())

    def test_external_evidence_links_are_safe_and_source_specific(self):
        for link in self.parser.links:
            href=link.get("href","")
            if href.startswith("https://") and any(
                publisher in href for publisher in (
                    "scb.se/", "jobtechdev.se/", "brainville.com/"
                )
            ):
                self.assertIn("noopener",link.get("rel",""))
                self.assertIn("noreferrer",link.get("rel",""))
        self.assertIn("/sv/Blog/Post/1923",self.page)
        self.assertIn("it-anvandning-i-foretag-2026",self.page)
        self.assertIn("historical.api.jobtechdev.se/search",self.page)

    def test_page_contains_mobile_wrapping_and_no_oversized_fixed_grid(self):
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn("@media(max-width:1100px)",css)
        self.assertIn("@media(max-width:760px)",css)
        self.assertIn("overflow-wrap:break-word",css)
        self.assertIn("white-space:normal!important",css)
        self.assertIn("grid-template-columns:minmax(0,1fr)",css)
        self.assertIn("overflow-x:clip",css)
        self.assertNotIn("white-space:nowrap",css)
        self.assertNotIn("width:1200px",css)

    def test_explicitly_honest_on_vintages_and_cross_source_logic(self):
        for claim in (
            "not a live market forecast",
            "not a count of all vacancies",
            "not AI/Data specialists alone",
            "not a full market review from those summer months",
            "not published in Edition 01",
            "no personal approval is needed",
        ):
            self.assertIn(claim.lower(),self.page.lower())


if __name__=="__main__":
    unittest.main()
