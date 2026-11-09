"""One consistent closing navigator for every core portfolio page."""

from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from about_next_navigation import _destinations_for, portfolio_next_navigation
from page_home_featured import inject_writing_footer
from site_styles import CSS


EXPECTED = {
    "about": {"impact", "ai-data-governance", "thinking"},
    "impact": {"ai-data-governance", "thinking", "about"},
    "ai-data-governance": {"impact", "briefings", "about"},
    "thinking": {"impact", "ai-data-governance", "about"},
    "contact": {"impact", "ai-data-governance", "thinking"},
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.secondary = []
        self.navs = 0

    def handle_starttag(self, tag, attrs):
        details = dict(attrs)
        if tag == "nav" and details.get("aria-label") == "Continue exploring the portfolio":
            self.navs += 1
        if tag == "a" and "about-next-card" in details.get("class", ""):
            self.cards.append(details)
        if tag == "a" and details.get("data-hq-event", "").endswith("_next_contact"):
            self.secondary.append(details)


def test_each_page_gets_three_relevant_distinct_routes_and_no_self_link():
    for page, destinations in EXPECTED.items():
        section = portfolio_next_navigation(page)
        parser = Links()
        parser.feed(section)
        assert parser.navs == 1
        assert len(parser.cards) == 3
        actual = {card["href"].removeprefix("?page=") for card in parser.cards}
        assert actual == destinations
        assert page not in actual
        assert len({card["data-hq-event"] for card in parser.cards}) == 3
        assert all(card.get("target") == "_self" for card in parser.cards)
        assert section.count('class="about-next-card-action"') == 3
        assert section.count("portfolio-next") == 1
        assert section.count("data-analytics-section=") == 1
        assert len(_destinations_for(page)) == 3


def test_contact_has_no_contact_self_link_and_preserves_direct_contact():
    section = portfolio_next_navigation("contact")
    assert 'data-hq-event="contact_next_about"' in section
    assert 'href="?page=about"' in section
    assert 'contact_next_contact' not in section
    contact = (ROOT / "src" / "page_contact.py").read_text(encoding="utf-8")
    assert '{portfolio_next_navigation("contact")}' in contact
    assert 'contact-footer-links' in contact
    assert 'mailto:{EMAIL}' in contact
    assert 'data-hq-event="linkedin_contact"' in contact


def test_single_closing_navigator_replaces_competing_sections():
    impact = (ROOT / "src" / "page_impact.py").read_text(encoding="utf-8")
    governance = (ROOT / "src" / "page_ai_data_governance.py").read_text(encoding="utf-8")
    thinking = (ROOT / "src" / "thinking_landing.py").read_text(encoding="utf-8")
    thinking_page = (ROOT / "src" / "page_thinking.py").read_text(encoding="utf-8")

    assert '{portfolio_next_navigation("impact")}' in impact
    assert '{opportunity()}' not in impact
    assert '{portfolio_next_navigation("ai-data-governance")}' in governance
    assert 'governance_impact_final' not in governance
    assert 'governance_impact_cta' not in governance
    assert '<section class="cta">' not in governance
    assert 'journey_next("thinking")' not in thinking
    assert 'portfolio_next_navigation("thinking")' in thinking_page
    assert '_with_thinking_navigation(document)' in thinking_page
    assert 'return VISUAL_CSS + _with_thinking_navigation(render_weekly_brief_archive(editions))' in thinking_page


def test_generic_writing_footer_is_not_duplicate_closing_navigation():
    document = '<main><p>Example</p></main>'
    for page in EXPECTED:
        assert inject_writing_footer(document, page) == document
    footer_source = (ROOT / "src" / "page_home_featured.py").read_text(encoding="utf-8")
    assert 'page == "thinking" and not article_slug' in footer_source
    assert 'feature = compact_writing_footer(' in footer_source


def test_navigation_reuses_about_design_on_desktop_and_mobile():
    for page in EXPECTED:
        section = portfolio_next_navigation(page)
        assert 'class="about-next portfolio-next"' in section
        assert "<img" not in section
        assert "<svg" not in section
    assert ".site .about-next-grid" in CSS
    assert ".site a.about-next-card" in CSS
    assert "@media(max-width:900px)" in CSS
    assert "@media(max-width:600px)" in CSS
    assert "@media(prefers-reduced-motion:reduce)" in CSS
