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

    def test_inline_images_and_pdf_cta_are_self_contained(self):
        import base64
        import re
        from types import SimpleNamespace
        from briefing_authority_artwork import approved_authority_studio
        html = approved_authority_studio(SimpleNamespace(slug="ai-was-approved-who-can-stop-it"), {
            "alt_text": "Original graphic with twenty operating decisions across four duties.",
            "caption": "Twenty executive governance decisions.",
        })
        self.assertEqual(html.count('class="auth-download"'), 1)
        self.assertIn('/readers/download/ai-was-approved-who-can-stop-it.pdf', html)
        self.assertIn('data-hq-event="briefing_reader_pdf"', html)
        self.assertNotIn('25-decision', html)
        self.assertEqual(html.count('data:image/webp;base64,'), 2)
        self.assertNotIn('/briefing-ai-authority/infographic.webp', html)
        self.assertNotIn('infographic.svg', html)
        self.assertIn('auth-artwork-desktop', html)
        self.assertIn('auth-artwork-mobile', html)
        self.assertLess(html.index('class="auth-download"'), html.index('auth-artwork-container'))
        assets = re.findall(r'src="data:image/webp;base64,([A-Za-z0-9+/=]+)"', html)
        self.assertEqual(len(assets), 2)
        from PIL import Image
        for b64, dimensions in zip(assets, ((1600,2220),(900,3850))):
            data=base64.b64decode(b64,validate=True)
            self.assertGreater(len(data),15000)
            with Image.open(BytesIO(data)) as im:
                self.assertEqual(im.format,'WEBP')
                self.assertEqual(im.size,dimensions)
                im.verify()

    def test_published_reader_bridge_contains_inline_images(self):
        """Prove the briefing reader actually includes images, not just the studio helper."""
        import hashlib
        from types import SimpleNamespace
        from unittest.mock import patch
        from page_executive_briefings import _article_infographic

        article = SimpleNamespace(
            id="known-article",
            slug="ai-was-approved-who-can-stop-it",
            title="The AI Is Live. Who Holds the Authority?",
            subtitle="Original twenty-decision operating mandate.",
            content_html="<p>Twenty operating decisions.</p>",
            status="published",
        )
        fingerprint = hashlib.sha256(
            "|".join((article.title,article.subtitle,article.content_html)).encode()
        ).hexdigest()
        approved = {
            "status":"approved",
            "source_fingerprint":fingerprint,
            "alt_text":"Original artwork, twenty AI decisions across four operating commitments.",
            "caption":"A twenty-decision operating mandate by Jair Ribeiro.",
        }
        with patch("briefing_infographic_store.fetch_public_infographic",return_value=approved):
            html = _article_infographic(article)
        self.assertEqual(html.count('data:image/webp;base64,'), 2)
        self.assertIn('class="auth-download"', html)
        self.assertNotIn('src="/briefing-ai-authority/',html)

    def test_raster_images_decode_without_missing_artwork(self):
        from PIL import Image
        from briefing_authority_raster import artwork_webp
        for mode, expected in (("desktop", (1600, 2220)), ("mobile", (900, 3850))):
            data = artwork_webp(mode)
            self.assertGreater(len(data), 15000)
            self.assertLess(len(data), 2_000_000)
            with Image.open(BytesIO(data)) as im:
                self.assertEqual(im.format, "WEBP")
                self.assertEqual(im.size, expected)
                im.verify()

    def test_premium_icon_and_gradient_system_survives_rendering(self):
        """Icons and four distinct branded headers are in the actual image bytes."""
        from PIL import Image
        from briefing_authority_raster import artwork_webp, HEADER_GRADIENTS
        self.assertEqual(len(HEADER_GRADIENTS), 4)
        with Image.open(BytesIO(artwork_webp("desktop"))) as im:
            pix = im.convert("RGB")
            samples = (
                pix.getpixel((100, 476)),
                pix.getpixel((855, 476)),
                pix.getpixel((100, 1186)),
                pix.getpixel((855, 1186)),
            )
            self.assertEqual(len(set(samples)), 4)
            for sample in samples:
                self.assertGreater(sum(sample), 60)
            # The icon strokes are light on the darker gradient headers.
            self.assertGreater(sum(pix.getpixel((131, 490))), 30)
        from briefing_authority_raster import _symbol, _premium_card_header
        self.assertTrue(callable(_symbol))
        self.assertTrue(callable(_premium_card_header))

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
