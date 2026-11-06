"""Contract tests for future Briefing infographics: no per-article renderer."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import hashlib
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from PIL import Image
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from briefing_infographic_engine import source_fingerprint
from briefing_approved_asset_renderer import (
    ArtworkError, load_bundle, validate_bundle, render_approved_bundle,
    verified_pdf_for_article,
)
from build_briefing_artwork_bundle import bundle as package_bundle


class ApprovedAssetContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.article = SimpleNamespace(
            id="future-briefing-id",
            slug="future-ai-leadership-briefing",
            title="A New Executive AI Decision",
            subtitle="An accountable business approval requires evidence.",
            content_html="<p>Business accountability, operating evidence and a review gate.</p>",
            status="published",
        )
        self.fingerprint = source_fingerprint(self.article)
        self.approved = {
            "status": "approved",
            "source_fingerprint": self.fingerprint,
            "alt_text": "Original source-locked executive graphic illustrating a management decision in four steps.",
            "caption": "Illustrated executive decision framework by Jair Ribeiro.",
        }
        desktop = self.root / "approved-desktop.png"
        mobile = self.root / "approved-mobile.png"
        pdf = self.root / "approved-a4.pdf"
        Image.new("RGB", (1200, 1680), (9, 46, 74)).save(desktop)
        Image.new("RGB", (850, 1600), (240, 244, 241)).save(mobile)
        doc = FPDF(unit="mm", format="A4")
        doc.add_page()
        doc.set_font("Helvetica", "B", 18)
        doc.text(12, 24, "A source-locked executive judgment")
        doc.output(str(pdf))
        self.sources = (desktop, mobile, pdf)

    def create(self):
        d, m, p = self.sources
        return package_bundle(
            slug=self.article.slug, article_fingerprint=self.fingerprint,
            revision="2026-11-06-r1", desktop=d, mobile=m, pdf=p,
            heading="The executive decision", deck="Who owns the next action?",
            out_root=self.root / "published",
        )

    def test_new_briefing_works_without_a_python_renderer_branch(self):
        self.assertIsNone(render_approved_bundle(self.article, self.approved, asset_root=self.root))
        self.create()
        asset_root = self.root / "published"
        html = render_approved_bundle(self.article, self.approved, asset_root=asset_root)
        self.assertIsInstance(html, str)
        self.assertEqual(html.count("data:image/webp;base64,"), 2)
        self.assertEqual(html.count('data-analytics-section="briefing-infographic"'), 1)
        self.assertEqual(html.count('class="canonical-infographic-download"'), 1)
        self.assertIn("future-ai-leadership-briefing/download.pdf", html)
        self.assertIn("2026-11-06-r1", html)
        self.assertLess(html.find("Download infographic"), html.find("data:image/webp;base64"))
        self.assertNotIn('src="/briefing', html)
        self.assertIn("Who owns the next action?", html)
        self.assertGreater(len(html), 2000)
        reader_pdf = verified_pdf_for_article(self.article, asset_root=asset_root)
        self.assertTrue(reader_pdf.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", reader_pdf[-2048:])

    def test_stale_or_unapproved_row_never_displays_old_image(self):
        self.create()
        root = self.root / "published"
        for row in (
            dict(self.approved, status="draft"),
            dict(self.approved, source_fingerprint="0" * 64),
            dict(self.approved, alt_text="too short"),
        ):
            self.assertEqual(render_approved_bundle(self.article, row, asset_root=root), "")
        mutated = SimpleNamespace(**vars(self.article))
        mutated.content_html += "<p>New assumption.</p>"
        self.assertEqual(render_approved_bundle(mutated, self.approved, asset_root=root), "")
        self.assertIsNone(verified_pdf_for_article(mutated, asset_root=root))

    def test_corrupt_image_and_checksum_fail_closed(self):
        self.create()
        root = self.root / "published"
        image = root / self.article.slug / "desktop.webp"
        image.write_bytes(image.read_bytes() + b"modified")
        self.assertEqual(render_approved_bundle(self.article, self.approved, asset_root=root), "")
        self.assertIsNone(verified_pdf_for_article(self.article, asset_root=root))

    def test_manifest_paths_cannot_escape_bundle(self):
        self.create()
        root = self.root / "published"
        manifest_path = root / self.article.slug / "manifest.json"
        import json
        data = json.loads(manifest_path.read_text())
        data["desktop"]["file"] = "../unsafe.webp"
        manifest_path.write_text(json.dumps(data))
        self.assertEqual(render_approved_bundle(self.article, self.approved, asset_root=root), "")

    def test_bundle_builder_wont_silently_overwrite_an_approved_release(self):
        self.create()
        with self.assertRaises(FileExistsError):
            self.create()


if __name__ == "__main__":
    unittest.main()
