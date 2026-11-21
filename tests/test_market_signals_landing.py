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

    def test_both_audiences_are_explicit(self):
        for value in ("Swedish AI &amp; Data Market Review",
                      "Plan AI investment and hiring decisions.",
                      "Understand how AI and Data connect to your career.",
                      "Complete AI &amp; Data Market Review",
                      "Executive Decision Briefs and source register",
                      "Market Observatory"):
            self.assertIn(value,self.page)

    def test_video_is_secondary_below_both_reports_and_findings(self):
        html=MARKET_SIGNALS_LANDING_HTML
        self.assertIn("What Sweden’s AI and Data figures mean",html)
        self.assertIn("Five market signals worth understanding.",html)
        self.assertLess(html.index('id="ms-perspectives"'),html.index('id="ms-findings"'))
        self.assertLess(html.index('id="ms-findings"'),html.index('id="ms-video"'))
        self.assertLess(html.index('id="ms-video"'),
                        html.index('aria-labelledby="ms-materials-title"'))
        self.assertIn("43",html)
        self.assertIn("Jobseeker Edition",html)
        self.assertIn("Executive Edition",html)
        self.assertIn("switched to SNI 2025",html)

    def test_jobseeker_still_has_a_clear_offer(self):
        html=MARKET_SIGNALS_LANDING_HTML
        for text in ("entry-level analysis","För dig som söker jobb inom AI och data i Sverige",
                     "Rapporten är på engelska","four-week plan",
                     "Read the Jobseeker Edition · Free","not every entry-level opening",
                     "Jobseeker report · Free account"):
            self.assertIn(text,html)
        self.assertIn("perspective=jobseeker",html)
        self.assertNotIn("guaranteed job",html.lower())

    def test_headlines_are_source_led_not_promotional(self):
        for title in ("Swedish AI &amp; Data Market Review",
                      "Two editions. One evidence base.",
                      "Five market signals worth understanding.",
                      "AI adoption is widespread. Business value is the next question.",
                      "Internal analytics capability is a separate measure from AI adoption.",
                      "Consulting activity and available capacity rose together.",
                      "Recruitment demand extends beyond job advertisements.",
                      "Explore the June–August research sample.",
                      "Research sources and how to use the findings.",
                      "Choose your edition and start reading."):
            self.assertIn(title,self.page)

    def test_video_is_intrinsically_responsive_and_served_by_ranged_mp4_origin(self):
        from pathlib import Path
        html=MARKET_SIGNALS_LANDING_HTML
        main=(ROOT/"main.py").read_text(encoding="utf-8")
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn('id="ms-video"',html)
        self.assertEqual(html.count('class="ms-video-player"'),1)
        self.assertIn('controls playsinline webkit-playsinline preload="metadata"',html)
        self.assertIn('poster="https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/careersite-article-images/market-signals/unionen-2026-11/poster-7fdbd6cedc8a.jpg"',html)
        self.assertIn('src="https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/portfolio-public-videos/market-signals/unionen-2026-11/website-eafa2f511a32.mp4"',html)
        self.assertNotIn("MARKET_SIGNALS_VIDEO_PLAYER",html)
        self.assertNotIn("split_market_landing_at_video",main)
        self.assertNotIn('key="market_video_compact"',main)
        self.assertIn("st.html(shared_styles + '<div",main)
        self.assertIn(".site.ms-landing .ms-video-layout",css)
        self.assertIn("html[data-jr-masked-mobile",css)
        self.assertIn("(max-device-width:760px)",css)
        self.assertIn("app.heygen.com/share/55e1d1dff94641d2a3f6e915cef8fd3d",html)
        video=ROOT/"static/market-signals/market-review-november-2026.mp4"
        poster=ROOT/"static/market-signals/market-review-poster.jpg"
        self.assertTrue(video.is_file())
        self.assertTrue(poster.is_file())
        self.assertGreater(video.stat().st_size,500_000)
        self.assertLess(video.stat().st_size,12_000_000)
        self.assertEqual(video.open("rb").read(8)[4:8],b"ftyp")
        self.assertEqual(poster.open("rb").read(3),bytes((255,216,255)))
        self.assertNotIn("/app/static/market-signals/",html)
        self.assertIn("portfolio-public-videos/market-signals/unionen-2026-11/website-eafa2f511a32.mp4",html)
        self.assertIn("1 minute 36 seconds",html)
        self.assertIn("Previous 58-second Market Signals introduction",html)
        self.assertNotIn("autoplay",html.split('class="ms-video-player"',1)[1].split('</video>',1)[0])
        # The new video is immutable public Storage with 200 video/mp4 and
        # independently verified start, middle and end HTTP 206 byte ranges.
        # Original 58-second file and its poster remain in the repository.
        self.assertNotIn("Signature=",self.page)
        self.assertNotIn('id="ms-jobseeker-benefits"',self.page)
        self.assertNotIn('aria-labelledby="ms-decisions-title"',self.page)
        self.assertIn("Explore the nine Observatory sections",self.page)
        self.assertIn("See original sources, definitions and research limitations",self.page)

    def test_both_report_cards_have_equal_priority_and_copy_length(self):
        import re
        html=MARKET_SIGNALS_LANDING_HTML
        cards=re.findall(r'<article class="ms-perspective">([\s\S]*?)</article>',html)
        self.assertEqual(len(cards),2)
        paragraphs=[]
        for card in cards:
            match=re.search(r'<p>([^<]+)</p>',card)
            self.assertIsNotNone(match)
            paragraphs.append(len(match.group(1).split()))
            self.assertEqual(card.count('class="ms-button'),1)
        self.assertLessEqual(abs(paragraphs[0]-paragraphs[1]),7)
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn("display:flex;flex-direction:column;min-width:0",css)
        self.assertIn(".ms-perspective .ms-actions {margin-top:auto",css)

    def test_high_value_examples_are_exact_dated_executive_edition_scope(self):
        for phrase in (
            "17–18 November editions remain archived",
            "published observations",
            "evidence series · 6 publishers",
            "executive decision perspectives",
            "49<span>%</span>",
            "85%",
            "29",
            "+10.7",
            "+18.5",
            "October 2026",
            "evidence series · 6 publishers",
        ):
            self.assertIn(phrase.lower(),self.page.lower())
        self.assertNotIn("AI jobs increased 45%",self.page)
        self.assertNotIn("AI consultant shortages",self.page)

    def test_all_published_edition_labels_match_signed_off_manuscript(self):
        import json
        manuscript=json.loads((ROOT/"docs/market_signals/november_2026_unionen_2_1.json").read_text(encoding="utf-8"))
        expected="Executive Edition "+manuscript["editorial"]["version"]
        self.assertIn(expected,MARKET_SIGNALS_LANDING_HTML)
        self.assertIn(expected,self.page)
        self.assertIn("Jobseeker Edition 1.2",self.page)
        self.assertIn("Two editions. One evidence base.",MARKET_SIGNALS_LANDING_HTML)
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
