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
APP = ROOT / "app.py"


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
                self.assertTrue(binary.startswith(b"\\xff\\xd8"))
                self.assertTrue(binary.endswith(b"\\xff\\xd9"))
                self.assertNotIn("<script", data.lower())
                self.assertNotIn("<foreignObject", data)
                self.assertNotIn("http://", data)
                self.assertNotIn("https://", data)
                self.assertNotIn("Volvo", data)
                self.assertNotIn("MSX", data)

    def test_assets_have_exactly_four_responses_and_four_week_steps(self):
        desktop = DESKTOP.read_text(encoding="utf-8")
        mobile = MOBILE.read_text(encoding="utf-8")
        for source in (desktop, mobile):
            self.assertEqual(source.count(">DEVELOP</text>"), 1)
            self.assertEqual(source.count(">EMPOWER</text>"), 1)
            self.assertEqual(source.count(">ENGAGE</text>"), 1)
            self.assertEqual(source.count(">SUPPORT</text>"), 1)
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
        self.assertIn("ai-adoption-mobile.svg", source)

    def test_cached_local_asset_route_is_constrained(self):
        source = APP.read_text(encoding="utf-8")
        self.assertIn("def _adoption_studio_infographic", source)
        self.assertIn("/briefing-artwork/ai-adoption-{variant}.svg", source)
        self.assertIn('media_type="image/svg+xml"', source)
        self.assertIn('"mobile": "briefing-ai-adoption-studio-mobile.svg"', source)
        self.assertIn('"desktop": "briefing-ai-adoption-studio.svg"', source)
        self.assertIn('"X-Content-Type-Options": "nosniff"', source)
        self.assertIn("stale-while-revalidate", source)


if __name__ == "__main__":
    unittest.main()
