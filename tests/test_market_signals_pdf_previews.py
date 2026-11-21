"""Verify four unchanged PDF-page previews and their public positioning."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from page_advisory_market_signals import (
    MARKET_SIGNALS_LANDING_HTML,
    MARKET_SIGNALS_LANDING_CSS,
)

FILES={
  "executive-unionen-workforce.png":("executive",6),
  "executive-ai-investment.png":("executive",3),
  "jobseeker-unionen-workforce.png":("jobseeker",5),
  "jobseeker-four-week-plan.png":("jobseeker",12),
}
PATH=ROOT/"static/market-signals/previews/unionen-2026-11"


class MarketSignalsPreviewTests(unittest.TestCase):
    def test_four_full_a4_page_captures_are_published(self):
        manifest=json.loads((PATH/"manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["images"]),4)
        self.assertEqual(manifest["render"],"PyMuPDF 1.85x full A4 original page, uncropped")
        self.assertEqual(manifest["editorial_version"],"2.1.0")
        self.assertEqual({Path(x["file"]).name for x in manifest["images"]},set(FILES))
        for entry in manifest["images"]:
            name=Path(entry["file"]).name
            with self.subTest(name=name):
                self.assertEqual((entry["edition"],entry["page"]),FILES[name])
                data=(PATH/name).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                width,height=struct.unpack(">II",data[16:24])
                self.assertEqual((width,height),(1102,1558))
                self.assertEqual(hashlib.sha256(data).hexdigest(),entry["sha256"])
                self.assertGreater(len(data),70_000)
                self.assertIn("pdf_sha256",entry)

    def test_gallery_is_between_edition_choice_and_market_analysis(self):
        html=MARKET_SIGNALS_LANDING_HTML
        self.assertLess(html.index('id="ms-perspectives"'),
                        html.index('id="ms-report-previews"'))
        self.assertLess(html.index('id="ms-report-previews"'),
                        html.index('id="ms-careers"'))
        self.assertEqual(html.count('class="ms-preview-page"'),4)
        self.assertEqual(html.count('class="ms-preview-row'),2)
        self.assertEqual(html.count('data-hq-event="market_signals_pdf_preview_'),2)
        self.assertIn("perspective=jobseeker",html)
        self.assertIn("perspective=executive",html)

    def test_original_resolution_link_and_accessible_caption_for_every_image(self):
        html=MARKET_SIGNALS_LANDING_HTML
        for name in FILES:
            src='static/market-signals/previews/unionen-2026-11/'+name
            self.assertEqual(html.count(src),2,(name,"expected href + img src"))
            self.assertIn('alt="Unaltered',html)
        self.assertIn("complete pages",html)
        for n in ("Page 06","Page 03","Page 05","Page 12"):
            self.assertIn(n,html)
        self.assertIn("complete report",html.lower())

    def test_responsive_cards_preserve_uncropped_image_geometry(self):
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn(".ms-preview-page img{display:block;width:100%;height:auto",css)
        self.assertIn("object-fit:contain",css)
        self.assertIn("@media(max-width:1080px)",css)
        self.assertIn("@media(max-width:560px)",css)
        self.assertNotIn(".ms-preview-page img{object-fit:cover",css)


if __name__=="__main__":
    unittest.main()
