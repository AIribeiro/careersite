from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class RuntimeSmokeTests(unittest.TestCase):
    def test_canonical_cv_delivery(self) -> None:
        import site_cv  # noqa: F401
        from site_assets import CV_BYTES, CV_URI

        filename = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
        data = (ROOT / "static" / filename).read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 4000)
        self.assertEqual(data, CV_BYTES)
        self.assertEqual(CV_URI, f"/app/static/{filename}")

    def test_curated_media_bundle_loads(self) -> None:
        import site_media  # noqa: F401
        from site_assets import (
            ABOUT_BW_URI,
            HERO_URI,
            PANEL_DIALOGUE_URI,
            THINKING_PANEL_URI,
            WORKSHOP_URI,
        )

        assets = [HERO_URI, WORKSHOP_URI, PANEL_DIALOGUE_URI, THINKING_PANEL_URI, ABOUT_BW_URI]
        for uri in assets:
            self.assertTrue(uri.startswith("data:image/"))
            self.assertGreater(len(uri), 10000)

    def test_all_public_pages_are_in_navigation(self) -> None:
        from site_components import ROLE_LENSES, nav

        html = nav("home")
        for label in ("Home", "Leadership Impact", "Thinking", "About", "Contact", "Role lenses"):
            self.assertIn(label, html)
        self.assertEqual(
            set(ROLE_LENSES),
            {"enterprise", "transformation", "governance", "consulting"},
        )

    def test_experience_metrics_are_precise(self) -> None:
        for relative in ("src/page_home.py", "src/page_about.py", "src/site_cv.py"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("20+", text, relative)
            self.assertIn("8+", text, relative)
            self.assertNotIn("15+ years", text, relative)
            self.assertNotIn("More than 15 years", text, relative)


if __name__ == "__main__":
    unittest.main()
