from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class SocialPreviewTests(unittest.TestCase):
    def test_branded_social_preview_is_generated_from_site_photography(self) -> None:
        from site_social_preview import PUBLIC_URL, SOURCE, TARGET, ensure_social_preview

        self.assertEqual(SOURCE.name, "profile_red_bg.jpg.jpg")
        self.assertTrue(SOURCE.exists())

        TARGET.unlink(missing_ok=True)
        generated = ensure_social_preview()
        self.assertEqual(generated, TARGET)
        self.assertTrue(TARGET.exists())
        self.assertGreater(TARGET.stat().st_size, 50_000)

        with Image.open(TARGET) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (1200, 630))

        self.assertEqual(
            PUBLIC_URL,
            "https://jairribeiro-ai.streamlit.app/app/static/jair-ribeiro-social-preview.png",
        )

    def test_social_metadata_uses_portfolio_preview_not_github_avatar(self) -> None:
        meta = (ROOT / "src/site_meta.py").read_text(encoding="utf-8")

        self.assertNotIn("avatars.githubusercontent.com", meta)
        self.assertIn("SOCIAL_IMAGE", meta)
        self.assertIn("og:image:width", meta)
        self.assertIn("og:image:height", meta)
        self.assertIn("og:image:alt", meta)
        self.assertIn("twitter:image:alt", meta)
        self.assertIn("summary_large_image", meta)


if __name__ == "__main__":
    unittest.main()
