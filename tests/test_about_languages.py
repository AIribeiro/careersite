"""About language profile: prominence, accuracy and responsive presentation."""

from pathlib import Path
import sys
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_about import LANGUAGE_CAPABILITIES, _languages_section, about
from site_styles import CSS


class _LanguageTiles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tiles = 0
        self.sections = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div" and "about-language-tile" in attributes.get("class", ""):
            self.tiles += 1
        if tag == "section" and attributes.get("id") == "languages-leadership":
            self.sections += 1


def test_languages_are_accurate_and_distinguish_working_from_developing():
    assert LANGUAGE_CAPABILITIES == (
        ("Portuguese", "Native / bilingual", "PT", "professional"),
        ("Italian", "Native / bilingual", "IT", "professional"),
        ("English", "Full professional", "EN", "professional"),
        ("Spanish", "Professional", "ES", "professional"),
        ("Polish", "Limited working", "PL", "developing"),
        ("Swedish", "Elementary", "SV", "developing"),
    )


def test_multilingual_section_is_prominent_not_in_family_footer():
    page = about()
    section = _languages_section()
    assert section in page
    assert page.count('id="languages-leadership"') == 1
    assert page.index('id="career-journey"') < page.index('id="languages-leadership"')
    assert page.index('id="languages-leadership"') < page.index('id="speaking-publications"')
    assert page.index('id="languages-leadership"') < page.index('id="beyond-work"')
    family_section = page.split('id="beyond-work"', 1)[1]
    assert "about-language-tile" not in family_section


def test_six_proficiency_tiles_and_leadership_message():
    section = _languages_section()
    parser = _LanguageTiles()
    parser.feed(section)
    assert parser.sections == 1
    assert parser.tiles == 6
    assert "Communicating across cultures." in section
    assert "Trust, clarity and influence" in section
    assert section.count('class="about-language-mark"') == 6


def test_language_tiles_are_responsive_and_need_no_external_icons():
    assert ".site .about-languages-layout" in CSS
    assert ".site .about-language-grid" in CSS
    assert ".site .about-language-tile" in CSS
    assert "@media(max-width:1010px)" in CSS
    assert "@media(max-width:590px)" in CSS
    assert "@media(max-width:360px)" in CSS
    assert "<svg" not in _languages_section()
    assert "<img" not in _languages_section()
