"""Source-fidelity and rendering gates for the 25-decision briefing artwork."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from briefing_authority_artwork import GROUPS, artwork_svg, artwork_mobile_svg, artwork_pdf


def test_twenty_five_unique_decisions():
    assert len(GROUPS) == 5
    assert [len(group[3]) for group in GROUPS] == [5] * 5
    titles = [item[0] for group in GROUPS for item in group[3]]
    assert len(titles) == len(set(titles)) == 25


def test_desktop_and_mobile_are_complete_accessible_svgs():
    for source in (artwork_svg(), artwork_mobile_svg()):
        root = ET.fromstring(source)
        assert root.tag.endswith("svg")
        text = " ".join(t.text or "" for t in root.iter() if t.tag.endswith("text"))
        assert "WHO CAN STOP IT?" in text
        assert "CONTINUING PERMISSION" in text
        for group in GROUPS:
            for title, _ in group[3]:
                assert title in text
        assert "Jair Ribeiro" in text


def test_download_is_vector_two_page_a4_pdf():
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(artwork_pdf()))
    assert len(reader.pages) == 2
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for group in GROUPS:
        for title, _ in group[3]:
            assert title in text
    assert "AI WAS APPROVED" in text
