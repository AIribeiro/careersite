"""The About page should end in clear, measurable portfolio navigation."""

from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from about_next_navigation import DESTINATIONS, about_next_navigation
from page_about import about
from page_home_featured import inject_writing_footer
from site_styles import CSS


class _NavParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.destinations = []
        self.contact = []
        self.nav_count = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "nav" and values.get("aria-label") == "Continue exploring the portfolio":
            self.nav_count += 1
        if tag == "a" and "about-next-card" in values.get("class", ""):
            self.destinations.append(values)
        if tag == "a" and values.get("data-hq-event") == "about_next_contact":
            self.contact.append(values)


def test_about_next_routes_are_real_and_distinct():
    markup = about_next_navigation()
    parser = _NavParser()
    parser.feed(markup)
    assert parser.nav_count == 1
    assert len(parser.destinations) == 3
    assert len(parser.contact) == 1
    assert {a["href"] for a in parser.destinations} == {
        "?page=impact", "?page=ai-data-governance", "?page=thinking"
    }
    assert {a["data-hq-event"] for a in parser.destinations} == {
        "about_next_impact", "about_next_governance", "about_next_thinking"
    }
    assert all(a["target"] == "_self" for a in parser.destinations)
    assert parser.contact[0]["href"] == "?page=contact"
    assert markup.count("about-next-card-arrow") == 3
    assert 'data-analytics-section="about-next-destinations"' in markup


def test_about_narrative_ends_with_next_step_then_footer():
    page = about()
    assert page.index('id="beyond-work"') < page.index('id="about-continue"')
    assert page.index('id="about-continue"') < page.index("</main>")
    assert page.index("</main>") < page.index("<footer")
    assert page.count('id="about-continue"') == 1
    assert page.count('class="about-family-photo ') == 3
    assert len(DESTINATIONS) == 3


def test_generic_writing_strip_is_not_appended_after_about_navigation():
    page = about()
    assert inject_writing_footer(page, "about") == page
    assert 'data-analytics-section="site-writing-footer"' not in page
    # Existing related-reading behavior is unaffected on other public pages.
    other = '<main><section id="sample"></section></main>'
    # The generic footer is selected on non-About pages; check the guard instead
    # of invoking CMS-dependent content retrieval in a unit test.
    source = (ROOT / "src" / "page_home_featured.py").read_text(encoding="utf-8")
    assert '"home", "about", "impact", "ai-data-governance", "contact", "analytics", "admin"' in source


def test_visual_style_is_scoped_and_mobile_responsive():
    assert ".site .about-next" in CSS
    assert ".site .about-next-grid" in CSS
    assert ".site a.about-next-card" in CSS
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in CSS
    assert "@media(max-width:900px)" in CSS
    assert "@media(max-width:600px)" in CSS
    assert "@media(prefers-reduced-motion:reduce)" in CSS
    assert "<svg" not in about_next_navigation()
    assert "<img" not in about_next_navigation()
