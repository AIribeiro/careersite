"""Structural regression tests for the About page editorial sequence."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_about import LANGUAGE_CAPABILITIES, about


def test_beyond_work_is_last_personal_section_followed_by_navigation_only():
    page = about()
    journey = page.index('id="career-journey"')
    writing = page.index('id="speaking-publications"')
    beyond = page.index('id="beyond-work"')
    continuation = page.index('id="about-continue"')
    assert journey < writing < beyond < continuation
    assert page.count('id="beyond-work"') == 1
    assert page.count('id="about-continue"') == 1
    # The final content after the photographs is deliberate navigation, not
    # another biography or editorial block.
    assert page[beyond:].split("</main>", 1)[0].count("<section") == 1


def test_writing_and_conversations_has_four_distinct_cards():
    page = about()
    writing_section = page.split('id="speaking-publications"', 1)[1].split('id="beyond-work"', 1)[0]
    assert writing_section.count('<article class="card">') == 4
    assert 'Executive AI Briefings' in writing_section
    assert 'Weekly AI' in writing_section
    assert 'href="?page=briefings"' in writing_section
    assert 'href="?page=thinking"' in writing_section


def test_family_photos_remain_in_final_beyond_work_section():
    page = about()
    beyond = page.split('id="beyond-work"', 1)[1]
    assert 'about-family-gallery' in beyond
    assert beyond.count('about-family-photo--') == 3


def test_languages_are_a_visible_leadership_feature_after_career_journey():
    page = about()
    career = page.index('id="career-journey"')
    languages = page.index('id="languages-leadership"')
    recommendations = page.index('about-recommendations')
    writing = page.index('id="speaking-publications"')
    beyond = page.index('id="beyond-work"')
    assert career < languages < recommendations < writing < beyond
    assert page.count('id="languages-leadership"') == 1
    assert 'Communicating across cultures.' in page
    assert 'organizational boundaries' in page
    assert 'about-languages-profile' in page
    assert page.count('class="about-language-tile"') == 6
    assert '<div class="chips"><span>Portuguese' not in page


def test_proficiency_levels_are_precise_not_six_equally_fluent_claims():
    expected = {
        "Portuguese": ("Native / bilingual", "professional"),
        "Italian": ("Native / bilingual", "professional"),
        "English": ("Full professional", "professional"),
        "Spanish": ("Professional", "professional"),
        "Polish": ("Limited working", "developing"),
        "Swedish": ("Elementary", "developing"),
    }
    actual = {name: (level, group) for name, level, _code, group in LANGUAGE_CAPABILITIES}
    assert actual == expected
    assert sum(group == "professional" for _, _, _, group in LANGUAGE_CAPABILITIES) == 4
    assert sum(group == "developing" for _, _, _, group in LANGUAGE_CAPABILITIES) == 2


def test_language_styles_are_scoped_and_responsive():
    site_styles = (ROOT / "src" / "site_styles.py").read_text(encoding="utf-8")
    assert ".site .about-languages-section" in site_styles
    assert ".site .about-languages-layout" in site_styles
    assert "@media(max-width:950px)" in site_styles
    assert "@media(max-width:580px)" in site_styles
    assert ".site .about-language-mark" in site_styles
