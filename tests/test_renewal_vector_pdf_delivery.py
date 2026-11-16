"""Regression: an unchanged article may receive a new approved PRINT revision.

This is the bug that returned an old stretched PDF even though the portfolio's
immutable artwork manifest had been replaced by a newer vector version.
"""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import briefing_approved_asset_renderer as art


class VectorPrintDeliveryTests(TestCase):
    def test_newer_pdf_revision_wins_even_when_article_fingerprint_is_unchanged(self):
        slug = "would-you-fund-the-same-ai-initiatives-today"
        fp = "b9e255ca0e7ac9fdf7504e98fe07dd9e8f642c96c4e492d6aac4adf511c27bd5"
        with TemporaryDirectory() as directory:
            checkout = Path(directory)
            folder = checkout / slug
            folder.mkdir()
            previous = {
                "schema_version": 1, "slug": slug, "article_fingerprint": fp,
                "revision": "v3-premium-editorial-20261116",
                "desktop": {"file": "desktop.webp"},
                "mobile": {"file": "mobile.webp"},
                "pdf": {"file": "infographic.pdf"},
            }
            (folder / "manifest.json").write_text(json.dumps(previous))
            current = dict(previous, revision="v4-vector-print-20261116",
                           pdf={"file": "infographic-a4-vector-v4.pdf"})
            with patch.object(art, "ROOT", checkout), patch.object(
                art, "_remote_manifest", return_value=current
            ) as latest:
                bundle = art.load_bundle(slug, expected_fingerprint=fp)
            latest.assert_called_once_with(slug)
            self.assertEqual(bundle["revision"], "v4-vector-print-20261116")
            self.assertEqual(bundle["pdf"]["file"], "infographic-a4-vector-v4.pdf")
            self.assertEqual(bundle.get("_remote_slug"), slug)
            self.assertNotIn("_root", bundle)

    def test_cdn_cannot_downgrade_newer_local_vector_release(self):
        slug = "would-you-fund-the-same-ai-initiatives-today"
        fp = "b9e255ca0e7ac9fdf7504e98fe07dd9e8f642c96c4e492d6aac4adf511c27bd5"
        with TemporaryDirectory() as directory:
            checkout = Path(directory)
            folder = checkout / slug
            folder.mkdir()
            current = {
                "schema_version": 1, "slug": slug, "article_fingerprint": fp,
                "revision": "v4-vector-print-20261116",
                "desktop": {"file": "desktop.webp"}, "mobile": {"file": "mobile.webp"},
                "pdf": {"file": "infographic-a4-vector-v4.pdf"},
            }
            (folder / "manifest.json").write_text(json.dumps(current))
            old = dict(current, revision="v3-premium-editorial-20261116",
                       pdf={"file": "infographic.pdf"})
            with patch.object(art, "ROOT", checkout), patch.object(
                art, "_remote_manifest", return_value=old
            ):
                bundle = art.load_bundle(slug, expected_fingerprint=fp)
            self.assertEqual(bundle["revision"], "v4-vector-print-20261116")
            self.assertEqual(bundle["pdf"]["file"], "infographic-a4-vector-v4.pdf")
            self.assertEqual(bundle.get("_root"), folder)
            self.assertNotIn("_remote_slug", bundle)

    def test_current_production_manifest_points_at_vector_not_old_raster(self):
        manifest = (
            Path(__file__).resolve().parents[1] / "static" / "briefing-artwork" /
            "would-you-fund-the-same-ai-initiatives-today" / "manifest.json"
        )
        data = json.loads(manifest.read_text())
        self.assertEqual(data["revision"], "v4-vector-print-20261116")
        self.assertEqual(data["pdf"]["file"], "infographic-a4-vector-v4.pdf")
        from pypdf import PdfReader
        path = manifest.parent / data["pdf"]["file"]
        b = path.read_bytes()
        self.assertEqual(hashlib.sha256(b).hexdigest(), data["pdf"]["sha256"])
        pdf = PdfReader(path, strict=True)
        self.assertEqual(len(pdf.pages), 1)
        self.assertEqual(len(pdf.pages[0].images), 0)
        words = pdf.pages[0].extract_text()
        for claim in ("Continuing is a decision, not a default.",
                      "MAKE THE INCUMBENT COMPETE", "REPLACE", "TEST", "STOP"):
            self.assertIn(claim, words)
        self.assertAlmostEqual(float(pdf.pages[0].mediabox.width), 595.28,delta=1)
