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

    def test_no_generic_old_four_lens_page(self):
        self.assertNotIn("Four evidence lenses",self.page)
        self.assertNotIn("Market signals connected to leadership decisions.",self.page)
        self.assertNotIn("What readers receive",self.page)

    def test_executive_target_and_decision_value_are_explicit(self):
        for phrase in (
            "Make sense of Sweden's AI &amp; Data market.",
            "For AI, Data and Analytics leaders",
            "Build, recruit or contract?",
            "Is AI changing the work?",
            "What can we confidently tell the leadership team?",
            "Market Observatory",
            "Executive Market Review",
            "Decision briefs &amp; source list",
        ):
            self.assertIn(phrase,self.page)

    def test_high_value_examples_are_exact_dated_edition_01_scope(self):
        for phrase in (
            "Published 16 November 2026",
            "published data points",
            "data sources",
            "four" if False else "executive analyses",
            "49<span>%</span>",
            "85%",
            "29",
            "+10.7",
            "+18.5",
            "October 2026",
            "different populations",
        ):
            self.assertIn(phrase.lower(),self.page.lower())
        self.assertNotIn("AI jobs increased 45%",self.page)
        self.assertNotIn("AI consultant shortages",self.page)

    def test_all_eight_real_dashboard_topics_present(self):
        expected=[
            "Executive market pulse",
            "AI &amp; Data leadership demand",
            "Enterprise adoption &amp; capabilities",
            "AI skills &amp; management economics",
            "Consulting &amp; sector conditions",
            "Interpretations &amp; trade-offs",
            "Explore market trends",
            "Sources &amp; measurement",
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
            "not a live forecast",
            "not a count of all vacancies",
            "not AI/Data specialists alone",
            "not a full market review from those summer months",
            "not published in Edition 01",
            "no personal approval is needed",
        ):
            self.assertIn(claim.lower(),self.page.lower())


if __name__=="__main__":
    unittest.main()
