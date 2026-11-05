"""Complete, readable 20-decision executive infographic and printable PDF."""
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
    def test_twenty_unique_decisions(self):
        self.assertEqual(len(GROUPS), 4)
        self.assertEqual([len(group[3]) for group in GROUPS], [5] * 4)
        titles = [item[0] for group in GROUPS for item in group[3]]
        self.assertEqual(len(titles), 20)
        self.assertEqual(len(set(titles)), 20)

    def test_desktop_mobile_complete_accessible_svg(self):
        for source in (artwork_svg(), artwork_mobile_svg()):
            root = ET.fromstring(source)
            self.assertTrue(root.tag.endswith("svg"))
            svg_text = " ".join(t.text or "" for t in root.iter() if t.tag.endswith("text"))
            self.assertIn("AUTHORITY?", svg_text)
            self.assertIn("RENEWAL AND EXIT", svg_text)
            for group in GROUPS:
                for title, _ in group[3]:
                    self.assertIn(title, svg_text)
            self.assertIn("Jair Ribeiro", svg_text)

    def test_mobile_and_pdf_cta_match_first_party_route(self):
        from types import SimpleNamespace
        from briefing_authority_artwork import approved_authority_studio
        html = approved_authority_studio(SimpleNamespace(slug="ai-was-approved-who-can-stop-it"), {
            "alt_text": "Original graphic with twenty operating decisions across four duties.",
            "caption": "Twenty executive governance decisions.",
        })
        self.assertIn("/briefing-ai-authority/infographic.mobile.svg", html)
        self.assertIn("/briefing-ai-authority/infographic.pdf", html)
        self.assertNotIn("25-decision", html)
        self.assertEqual(html.count('class="auth-download"'), 1)
        self.assertEqual(html.count('<picture>'), 1)
        self.assertLess(html.index('class="auth-download"'), html.index('<picture>'))
        self.assertIn("20 decisions. Four continuing responsibilities.", html)
        self.assertIn("operating-mandate-20-v2", html)

    def test_two_page_a4_pdf_contains_all_decisions(self):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(artwork_pdf()))
        self.assertEqual(len(reader.pages), 2)
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for group in GROUPS:
            for title, _ in group[3]:
                self.assertIn(title, pdf_text)
        self.assertIn("THE AI IS LIVE", pdf_text)
        self.assertIn("EXECUTIVE GATE", pdf_text)


if __name__ == "__main__":
    unittest.main()
