"""Regression checks for the premium Home portfolio index."""

from html.parser import HTMLParser
from base64 import b64decode
import re
from xml.etree import ElementTree
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from home_pathways import ICON_PATHS, PATHWAYS, home_pathways
from home_pathways_styles import HOME_PATHWAYS_CSS


class _PathwayParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.badges = 0
        self.navs = 0
        self.sections = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "section" and "home-pathways" in attributes.get("class", ""):
            self.sections += 1
        if tag == "nav" and "home-pathways-grid" in attributes.get("class", ""):
            self.navs += 1
        if tag == "a" and "home-pathway-card" in attributes.get("class", ""):
            self.links.append(attributes)
        if tag == "span" and "home-pathway-icon" in attributes.get("class", ""):
            self.badges += 1


def test_home_pathways_are_four_distinct_complete_navigation_links():
    markup = home_pathways()
    parser = _PathwayParser()
    parser.feed(markup)
    assert parser.sections == 1
    assert parser.navs == 1
    assert parser.badges == 4
    assert len(parser.links) == 4
    assert len(PATHWAYS) == 4
    assert {card["href"] for card in parser.links} == {
        "?page=impact", "?page=ai-data-governance", "?page=thinking", "?page=about"
    }
    assert len({card["data-hq-event"] for card in parser.links}) == 4
    assert all(card["target"] == "_self" for card in parser.links)
    assert all(card["aria-label"] for card in parser.links)


def test_home_pathway_icons_are_local_and_accessible():
    markup = home_pathways()
    assert set(ICON_PATHS) == {"impact", "governance", "thinking", "about"}
    # Streamlit strips inline SVG in st.html; icons must be CSS images instead.
    assert "<svg" not in markup
    assert markup.count('class="home-pathway-icon" aria-hidden="true"') == 4
    assert markup.count('aria-hidden="true">') >= 4
    assert "<script" not in markup
    assert "https://" not in markup
    assert "<img" not in markup
    payloads = re.findall(r'data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)', HOME_PATHWAYS_CSS)
    assert len(payloads) == 4
    for payload in payloads:
        svg = b64decode(payload).decode("utf-8")
        root = ElementTree.fromstring(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["viewBox"] == "0 0 32 32"
        assert root.attrib["stroke"] == "#a16947"
        assert len(root) >= 2
    for card in PATHWAYS:
        assert card.title in markup.replace("&amp;", "&")


def test_home_pathways_responsive_styles_are_isolated():
    css = HOME_PATHWAYS_CSS
    assert css.startswith("\n<style>")
    assert css.rstrip().endswith("</style>")
    assert ".site .journey-section.home-pathways" in css
    assert all(f".home-pathway-card--{kind} .home-pathway-icon" in css for kind in ICON_PATHS)
    assert "background:linear-gradient(138deg,#20384d" not in css
    assert "background:linear-gradient(147deg,#fffefa,#faf7f2)" in css
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in css
    assert "@media(max-width:720px)" in css
    assert "@media(prefers-reduced-motion:reduce)" in css
    assert "@import" not in css
    assert css.count("url(\"data:image/svg+xml;base64,") == 4
    assert "http://" not in css


def test_home_only_loads_styles_and_preserves_analytics_events():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    home_source = (ROOT / "src" / "page_home.py").read_text(encoding="utf-8")
    assert 'if PAGE == "home":\n        from home_pathways_styles import HOME_PATHWAYS_CSS' in main_source
    assert "CSS + IMAGE_CSS + pathway_css" in main_source
    assert home_source.count("{home_pathways()}") == 1
    for card in PATHWAYS:
        assert card.event in home_pathways()
    assert "home-choose-your-path" in home_pathways()
