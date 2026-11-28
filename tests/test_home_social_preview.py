from __future__ import annotations

from pathlib import Path
from html import escape
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from scripts.build_home_social_preview import (
    DESCRIPTION, PREVIEW_FILE, TITLE, write_home_share,
)


class HomeSocialPreviewTests(unittest.TestCase):
    def test_public_preview_is_server_rendered_with_real_image(self) -> None:
        self.assertTrue(PREVIEW_FILE.is_file())
        with TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_home_share(output, "https://airibeiro.github.io/careersite")
            document = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn(escape(TITLE), document)
            self.assertIn(DESCRIPTION, document)
            self.assertIn('property="og:image" content="https://airibeiro.github.io/careersite/social/jair-ribeiro-home.png"', document)
            self.assertIn('property="og:image:width" content="1200"', document)
            self.assertIn('property="og:image:height" content="630"', document)
            self.assertIn('name="twitter:card" content="summary_large_image"', document)
            self.assertIn('rel="icon" type="image/png"', document)
            self.assertIn('rel="canonical" href="https://jairribeiro.com/"', document)
            self.assertIn("window.location.replace(destination.toString())", document)
            self.assertIn("'source'", document)
            self.assertIn("'utm_campaign'", document)
            self.assertNotIn("<iframe", document.lower())
            with Image.open(output / "social" / "jair-ribeiro-home.png") as preview:
                self.assertEqual(preview.size, (1200, 630))
                self.assertEqual(preview.format, "PNG")
            with Image.open(output / "favicon.png") as favicon:
                self.assertEqual(favicon.size, (96, 96))
                self.assertEqual(favicon.format, "PNG")

    def test_outreach_bridge_has_server_metadata_and_attribution_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_home_share(output, "https://airibeiro.github.io/careersite")
            document = (output / "outreach" / "index.html").read_text(encoding="utf-8")
            home = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('property="og:url" content="https://airibeiro.github.io/careersite/outreach/"', document)
            self.assertIn('property="og:image" content="https://airibeiro.github.io/careersite/social/jair-ribeiro-home.png"', document)
            self.assertIn('href="https://jairribeiro.com/?source=outreach"', document)
            self.assertIn("destination.searchParams.set('source', 'outreach')", document)
            self.assertIn("!destination.searchParams.has('utm_source')", document)
            self.assertIn("!destination.searchParams.has('src')", document)
            self.assertIn("allowed.has(key)", document)
            self.assertNotIn("destination.searchParams.set('source', 'outreach')", home)
            self.assertNotIn("<iframe", document.lower())

    def test_rejects_unapproved_static_host(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_home_share(Path(tmp), "https://example.com/other")


if __name__ == "__main__":
    unittest.main()
