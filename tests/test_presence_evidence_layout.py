"""Presence page keeps three documented items visible without orphan grid cells."""
from __future__ import annotations

from pathlib import Path
import sys
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_presence import presence
from site_styles import CSS


class _PresenceCards(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.card_count = 0
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "article" and "presence-card" in attributes.get("class", "").split():
            self.card_count += 1
        if tag == "section" and attributes.get("id", "").startswith("presence-"):
            self.ids.append(attributes["id"])


def test_publications_and_recognition_have_three_real_cards():
    html = presence()
    parser = _PresenceCards()
    parser.feed(html)
    assert "presence-publications" in parser.ids
    assert "presence-recognition" in parser.ids
    assert html.count('class="grid3 presence-evidence-grid"') == 2
    publications = html.split('id="presence-publications"', 1)[1].split(
        '<section', 1
    )[0]
    recognition = html.split('id="presence-recognition"', 1)[1].split(
        '<section', 1
    )[0]
    assert publications.count('class="card presence-card"') == 3
    assert recognition.count('class="card presence-card"') == 3
    assert publications.count('data-hq-event="article_presence_') == 3
    assert recognition.count('class="presence-media') == 3
    assert "Navigating the Ethical AI Landscape" in publications
    assert "Transforming the Trucking Industry" in publications
    assert "100+ AI learning sessions" in recognition
    assert "Global AI Ambassador" in recognition


def test_evidence_grid_uses_all_columns_and_controls_tall_cover():
    assert ".site .presence-evidence-grid{" in CSS
    assert "grid-template-columns:repeat(3,minmax(0,1fr));" in CSS
    assert "@media(min-width:701px) and (max-width:839px)" in CSS
    assert ".site .presence-evidence-grid>.presence-card:last-child{" in CSS
    assert "grid-column:1/-1;" in CSS
    assert "grid-template-columns:minmax(0,.78fr) minmax(0,1.22fr)" in CSS
    assert ".site .presence-evidence-grid .presence-media.portrait-cover" in CSS
    assert "height:clamp(185px,21vw,230px)" in CSS
    assert "object-fit:contain;" in CSS
    assert "@media(max-width:700px)" in CSS
    assert "grid-template-columns:minmax(0,1fr);" in CSS


def test_other_speaking_cards_stay_in_the_original_six_item_grid():
    html = presence()
    before = html.split('id="presence-publications"', 1)[0]
    assert before.count('class="card presence-card"') == 6
    assert 'class="grid3 presence-evidence-grid"' not in before
