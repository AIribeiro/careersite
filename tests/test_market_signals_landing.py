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

    def test_masked_mobile_landing_neutralizes_double_zoom(self):
        # This is specific to the large hero visible through go.jairribeiro.com.
        # The shared fallback stays in place for every other portfolio route.
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn('html[data-jr-masked-mobile="true"] .site.ms-landing {zoom:1!important}',css)
        self.assertIn('html[data-jr-masked-mobile="true"] .site.ms-landing .ms-hero h1 {',css)
        self.assertIn('font-size:36px;line-height:1.12;overflow-wrap:normal',css)
        self.assertIn('width:calc(100% - 32px);max-width:100%',css)
        self.assertIn('html[data-jr-masked-mobile="true"] .site.ms-landing .ms-section h2',css)
        self.assertIn('(min-width:760px) and (max-device-width:700px)',css)
        self.assertNotIn('.site.ms-landing {zoom:1!important}',css.split('@media screen and (min-width:760px)',1)[0])

    def test_market_signals_uses_shared_where_to_next_and_standard_footer(self):
        from page_home_featured import inject_writing_footer
        from about_next_navigation import portfolio_next_navigation
        from site_portfolio_continuation import inject_portfolio_continuation
        from site_styles import CSS
        document=self.page
        navigation=portfolio_next_navigation("advisory-market-signals")
        self.assertIn(navigation,document)
        self.assertEqual(document.count('class="about-next portfolio-next"'),1)
        self.assertEqual(document.count('class="about-next-card"'),3)
        self.assertEqual(document.count('class="about-next-card-number"'),3)
        self.assertEqual(document.count('<footer class="footer">'),1)
        self.assertIn('<p class="eyebrow">Where to next?</p>',document)
        self.assertIn('data-analytics-section="advisory-market-signals-next-destinations"',document)
        self.assertIn('aria-label="Continue exploring the portfolio"',document)
        for href in (
            '?page=advisory',
            '?page=advisory-market-demo',
            '?page=advisory-access&amp;view=market-signals',
        ):
            self.assertIn('href="'+href+'"',navigation)
        self.assertIn('data-hq-event="advisory-market-signals_next_advisory_access_market_signals"',document)
        self.assertLess(document.index('id="advisory-market-signals-continue"'),
                        document.index("</main>"))
        self.assertLess(document.index("</main>"),
                        document.index('<footer class="footer">'))
        self.assertEqual(inject_writing_footer(document,"advisory-market-signals"),document)
        self.assertEqual(inject_portfolio_continuation(document,"advisory-market-signals"),document)
        self.assertNotIn('class="ms-footer-navigation"',document)
        self.assertNotIn('aria-label="Market Signals footer navigation"',document)
        self.assertNotIn('data-analytics-section="site-writing-footer"',document)
        self.assertIn(".site .about-next-grid",CSS)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))",CSS)
        self.assertIn("@media(max-width:900px)",CSS)
        self.assertIn("@media(max-width:600px)",CSS)

    def test_no_generic_old_four_lens_page(self):
        self.assertNotIn("Four evidence lenses",self.page)
        self.assertNotIn("Market signals connected to leadership decisions.",self.page)
        self.assertNotIn("What readers receive",self.page)

    def test_executive_target_and_decision_value_are_explicit(self):
        for phrase in (
            "Swedish AI &amp; Data Market Review",
            "For CEOs, CFOs, CHROs",
            "Recruit, develop internally or seek external expertise?",
            "Which AI investments deserve the next budget?",
            "Bring a stronger case to the leadership table",
            "Market Observatory",
            "Complete AI &amp; Data Market Review",
            "Executive Decision Briefs and source register",
        ):
            self.assertIn(phrase,self.page)

    def test_executive_value_precedes_scope_caveats(self):
        html=MARKET_SIGNALS_LANDING_HTML
        hero=html.split('<section class="ms-hero"',1)[1].split('</section>',1)[0]
        intro=html.split('<section class="ms-section ms-section--white" id="ms-findings"',1)[1].split('<div class="ms-proofs">',1)[0]
        for phrase in (
            "Two free reports on Sweden’s AI &amp; Data market",
            "job titles",
            "Looking for AI or Data work in Sweden",
            "For business leaders · Free report",
            "Looking for work? Read the free report",
            "Both reports are in English and free",
        ):
            self.assertIn(phrase,hero)
        for defensive in ("cannot", "not a market forecast", "comprehensive AI recruitment census", "limited evidence", "where its limits lie"):
            self.assertNotIn(defensive,hero.lower())
            self.assertNotIn(defensive,intro.lower())
        self.assertIn("Research sources and how to use the findings.",html)
        self.assertIn("exact replication is not assured",html)
        self.assertIn("switched to SNI 2025",html)
        self.assertIn("Brainville",html)
        self.assertIn("not a market forecast",html)

    def test_public_jobseeker_experience_is_clear_and_inclusive(self):
        html=MARKET_SIGNALS_LANDING_HTML
        self.assertIn('id="ms-jobseeker-benefits"',html)
        for phrase in (
            "new to the field",
            "changing careers",
            "returning to work",
            "För dig som söker jobb inom AI och data i Sverige",
            "Rapporten är på engelska",
            "Four-week plan",
            "Read the free Jobseeker Edition and download the PDF",
            "Jobseeker report · Free account",
            "not every entry-level opening",
        ):
            self.assertIn(phrase,html)
        self.assertIn("perspective=jobseeker",html)
        self.assertIn("market_signals_final_jobseeker",html)
        self.assertNotIn("guaranteed job",html.lower())

    def test_executive_headlines_use_measured_claims_not_promotional_promises(self):
        expected=[
            "Swedish AI &amp; Data Market Review",
            "What the Swedish market figures show",
            "AI adoption is widespread. Business value is the next question.",
            "Senior AI &amp; Data leadership: examine the roles behind the numbers.",
            "Consulting activity and available capacity rose together.",
            "Recruitment demand extends beyond job advertisements.",
            "Explore the June–August research sample.",
            "Research sources and how to use the findings.",
            "Interpret each measure in its proper context.",
            "Use the November research for your next decision.",
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

    def test_high_value_examples_are_exact_dated_executive_edition_scope(self):
        for phrase in (
            "published on 17 November",
            "published observations",
            "evidence series · 5 publishers",
            "executive decision perspectives",
            "49<span>%</span>",
            "85%",
            "29",
            "+10.7",
            "+18.5",
            "October 2026",
            "evidence series · 5 publishers",
        ):
            self.assertIn(phrase.lower(),self.page.lower())
        self.assertNotIn("AI jobs increased 45%",self.page)
        self.assertNotIn("AI consultant shortages",self.page)

    def test_all_published_edition_labels_match_signed_off_manuscript(self):
        import json
        manuscript=json.loads((ROOT/"docs/market_signals/november_2026_executive_v2.json").read_text(encoding="utf-8"))
        expected="Executive Edition "+manuscript["version"]
        # The two-edition masthead no longer repeats the executive label;
        # the evidence introduction and original executive PDF description do.
        self.assertEqual(MARKET_SIGNALS_LANDING_HTML.count(expected),2)
        self.assertEqual(self.page.count(expected),2)
        self.assertIn("Two ways to use the research",MARKET_SIGNALS_LANDING_HTML)
        self.assertIn("Jobseeker Edition",MARKET_SIGNALS_LANDING_HTML)
        for obsolete in (
            "Executive Edition 2.0</h2>",
            "in Executive Edition 2.0. No single",
            "Executive Edition 2.0 examines",
            "Access Executive Edition 2.0 · Free account",
        ):
            self.assertNotIn(obsolete,self.page)

    def test_three_material_selection_biases_are_publicly_explained(self):
        html=MARKET_SIGNALS_LANDING_HTML
        for phrase in (
            "Historical API results may change and exact replication is not assured",
            "operations, digital, product and commercial titles",
            "Changes in platform participation and coverage can affect",
            "switched to SNI 2025",
            "not a count of all AI leadership roles, vacancies or hires",
            "not a market forecast",
        ):
            self.assertIn(phrase,html)
        self.assertNotIn("author-defined, reproducible set",html)

    def test_superseded_editions_keep_historical_reader_access(self):
        source=(ROOT/"src/page_advisory_market_signals.py").read_text(encoding="utf-8")
        self.assertIn('"sweden-ai-data-market-review-2026-11-v2",',source)
        self.assertIn('"sweden-ai-data-market-review-2026-11-v2-0-1",',source)
        self.assertIn("render_market_observatory(points,historical=False)",source)
        self.assertIn("Select the latest edition",source)

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
            "not a market forecast",
            "not a count of all AI leadership roles, vacancies or hires",
            "marketplace covering many consulting disciplines",
            "The sample was prepared in November using historical JobTech records",
            "not published in the current edition",
            "Create a free Advisory account",
        ):
            self.assertIn(claim.lower(),self.page.lower())


if __name__=="__main__":
    unittest.main()
