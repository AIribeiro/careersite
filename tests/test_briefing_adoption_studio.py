"""Regression checks for the first-party Executive AI Adoption Studio image."""
from __future__ import annotations

import base64
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "static" / "briefing-ai-adoption-studio.svg"
MOBILE = ROOT / "static" / "briefing-ai-adoption-studio-mobile.svg"
STORE = ROOT / "src" / "briefing_infographic_store.py"
CONFIG = ROOT / ".streamlit" / "config.toml"
READER = ROOT / "src" / "page_executive_briefings.py"


class AdoptionArtworkTests(unittest.TestCase):
    def test_both_assets_are_self_contained_svg_and_include_original_speaker_photo(self):
        for path, dimensions in ((DESKTOP, "0 0 1800 2400"), (MOBILE, "0 0 420 1790")):
            with self.subTest(path=path.name):
                data = path.read_text(encoding="utf-8")
                root = ET.fromstring(data)
                self.assertEqual(root.attrib.get("viewBox"), dimensions)
                self.assertIn("JAIR RIBEIRO", data)
                self.assertIn("AI LEADER", data)
                self.assertIn("DEVELOP", data)
                self.assertIn("EMPOWER", data)
                self.assertIn("ENGAGE", data)
                self.assertIn("SUPPORT", data)
                self.assertIn("FIRST, CHECK THE WORK", data)
                self.assertIn("EXECUTIVE TEST", data)
                self.assertIn("data:image/jpeg;base64,", data)
                photo = re.search(r'data:image/jpeg;base64,([^"]+)', data)
                self.assertIsNotNone(photo)
                binary = base64.b64decode(photo.group(1), validate=True)
                self.assertTrue(binary.startswith(bytes.fromhex("ffd8")))
                self.assertTrue(binary.endswith(bytes.fromhex("ffd9")))
                self.assertNotIn("<script", data.lower())
                self.assertNotIn("<foreignObject", data)
                self.assertNotRegex(data, r'(?:href|src)="https?://')
                self.assertNotIn("Volvo", data)
                self.assertNotIn("MSX", data)

    def test_assets_have_exactly_four_responses_and_four_week_steps(self):
        desktop = DESKTOP.read_text(encoding="utf-8")
        mobile = MOBILE.read_text(encoding="utf-8")
        for source in (desktop, mobile):
            self.assertEqual(source.count(">DEVELOP</text>"), 1)
            self.assertEqual(source.count(">EMPOWER</text>"), 1)
            self.assertEqual(source.count(">ENGAGE</text>"), 1)
            self.assertGreaterEqual(source.count(">SUPPORT</text>"), 1)
            self.assertIn("TASK FIT", source)
            self.assertIn("PERMISSION", source)
            self.assertIn("VALUE EVIDENCE", source)
            for stage in ("CHOOSE", "LISTEN", "RESPOND", "DECIDE"):
                self.assertIn(">" + stage + "</text>", source)
        for week in ("WEEK 01", "WEEK 02", "WEEK 03", "WEEK 04"):
            self.assertIn(week, desktop)
        for week in ("W1", "W2", "W3", "W4"):
            self.assertIn(">" + week + "</text>", mobile)

    def test_approved_visual_is_not_bypassed(self):
        source = STORE.read_text(encoding="utf-8")
        self.assertIn("row.get(\"source_fingerprint\")!=source_fingerprint(article)", source)
        self.assertIn("if article.slug == _STUDIO_ADOPTION_SLUG:", source)
        self.assertIn('data-analytics-section="briefing-infographic"', source)
        self.assertIn('download="ai-adoption-executive-infographic.svg"', source)
        self.assertIn("max-width:700px", source)
        self.assertIn("briefing-ai-adoption-studio-mobile.svg", source)

    def test_portfolio_uses_native_static_url_for_all_artwork(self):
        config = CONFIG.read_text(encoding="utf-8")
        store = STORE.read_text(encoding="utf-8")
        reader = READER.read_text(encoding="utf-8")
        self.assertIn("enableStaticServing = true", config)
        desktop = "/app/static/briefing-ai-adoption-studio.svg"
        mobile = "/app/static/briefing-ai-adoption-studio-mobile.svg"
        self.assertIn(desktop, store)
        self.assertIn(mobile, store)
        self.assertIn(desktop, reader)
        self.assertNotIn("/briefing-artwork/", store)
        self.assertNotIn("/briefing-artwork/", reader)
        self.assertIn('loading="lazy"', reader)
        self.assertIn('loading="eager"', store)


if __name__ == "__main__":
    unittest.main()
