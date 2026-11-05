"""Complete, readable 25-decision executive infographic and printable PDF."""
from __future__ import annotations

import sys
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from briefing_authority_artwork import GROUPS, artwork_svg, artwork_mobile_svg, artwork_pdf


class OperatingAuthorityArtworkTests(unittest.TestCase):
    def test_twenty_five_unique_decisions(self):
        self.assertEqual(len(GROUPS), 5)
        self.assertEqual([len(group[3]) for group in GROUPS], [5] * 5)
        titles = [item[0] for group in GROUPS for item in group[3]]
        self.assertEqual(len(titles), 25)
        self.assertEqual(len(set(titles)), 25)

    def test_desktop_mobile_complete_accessible_svg(self):
        for source in (artwork_svg(), artwork_mobile_svg()):
            root = ET.fromstring(source)
            self.assertTrue(root.tag.endswith("svg"))
            svg_text = " ".join(t.text or "" for t in root.iter() if t.tag.endswith("text"))
            self.assertIn("WHO CAN STOP IT?", svg_text)
            self.assertIn("CONTINUING PERMISSION", svg_text)
            for group in GROUPS:
                for title, _ in group[3]:
                    self.assertIn(title, svg_text)
            self.assertIn("Jair Ribeiro", svg_text)

    def test_two_page_a4_pdf_contains_all_decisions(self):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(artwork_pdf()))
        self.assertEqual(len(reader.pages), 2)
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for group in GROUPS:
            for title, _ in group[3]:
                self.assertIn(title, pdf_text)
        self.assertIn("AI WAS APPROVED", pdf_text)
        self.assertIn("THE EXECUTIVE APPROVAL RECORD", pdf_text)


if __name__ == "__main__":
    unittest.main()
