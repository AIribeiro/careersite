"""Structural regression tests for the About page editorial sequence."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_about import about


def test_beyond_work_is_last_content_section():
    page = about()
    journey = page.index('id="career-journey"')
    writing = page.index('id="speaking-publications"')
    beyond = page.index('id="beyond-work"')
    assert journey < writing < beyond
    assert page.count('id="beyond-work"') == 1
    assert '<section' not in page[beyond:].split("</main>", 1)[0]


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
