"""Regression checks for the exact AI ROI visual and direct PNG download."""
from __future__ import annotations

import ast
import base64
import io
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class RoiInfographicTests(unittest.TestCase):
    def test_source_compiles_and_preserves_seven_measurement_lenses(self):
        source = (ROOT / "src" / "briefing_roi_artwork.py").read_text(encoding="utf-8")
        ast.parse(source)
        for word in ("COST", "PRODUCTIVITY", "QUALITY", "REVENUE",
                     "ADOPTION", "RISK REDUCTION", "STRATEGIC VALUE"):
            self.assertIn(word, source)
        for gate in ("BASELINE", "ATTRIBUTION", "REALIZATION", "TOTAL COST"):
            self.assertIn(gate, source)
        self.assertIn("contribution margin", source)
        self.assertIn("expected-loss", source)
        self.assertIn("Do not price them as cash", source)

    def test_generated_assets_are_valid_high_resolution_images(self):
        from briefing_roi_artwork import artwork_bytes, artwork_data_uri
        from PIL import Image
        png = artwork_bytes("download")
        webp = artwork_bytes("display")
        self.assertTrue(png.startswith(bytes.fromhex("89504e470d0a1a0a")))
        self.assertEqual(webp[:4], b"RIFF")
        self.assertEqual(webp[8:12], b"WEBP")
        self.assertLess(len(png), 1_500_000)
        self.assertLess(len(webp), 1_500_000)
        for binary in (png, webp):
            with Image.open(io.BytesIO(binary)) as image:
                self.assertEqual(image.size, (1800, 2400))
                image.verify()
        self.assertTrue(artwork_data_uri("download").startswith("data:image/png;base64,"))
        self.assertEqual(
            base64.b64decode(artwork_data_uri("download").split(",", 1)[1]), png
        )

    def test_reader_has_one_image_and_download_after_approval(self):
        from briefing_roi_studio import approved_roi_studio
        source = (ROOT / "src" / "briefing_infographic_store.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('row.get("source_fingerprint")!=source_fingerprint(article)', source)
        self.assertIn('if article.slug == "ai-roi-what-executives-must-prove-before-scaling":', source)
        row = {
            "alt_text": (
                "AI ROI executive decision infographic with seven lenses, cost baseline, "
                "four financial benefit categories, adoption and strategic value signals."
            ),
            "caption": "Original AI ROI infographic by Jair Ribeiro.",
            "spec": {},
        }
        html = approved_roi_studio(
            SimpleNamespace(slug="ai-roi-what-executives-must-prove-before-scaling"), row
        )
        self.assertEqual(html.count("<img "), 1)
        self.assertIn('data-analytics-section="briefing-infographic"', html)
        self.assertIn('download="ai-roi-proof-before-scale-executive-infographic.png"', html)
        self.assertIn("data:image/webp;base64,", html)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("@media(max-width:700px)", html)
        self.assertNotIn("/app/static/", html)


if __name__ == "__main__":
    unittest.main()
