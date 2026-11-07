"""The approved 15-way illustration is not redrawn or split across PDF pages."""
from __future__ import annotations
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_ai_business_changes_approved_artwork import (
    APPROVED_SOURCE, EXPECTED_SOURCE_SHA256, EXPECTED_SIZE, build
)

class ApprovedFifteenWayArtwork(unittest.TestCase):
    def test_approved_image_sha_and_one_page_a4(self):
        with tempfile.TemporaryDirectory() as temp:
            result=build(temp)
            self.assertEqual(result["page_count"],1)
            self.assertEqual(result["approved_png_sha256"],EXPECTED_SOURCE_SHA256)
            source=APPROVED_SOURCE.read_bytes()
            for n in ("desktop.png","mobile.png"):
                self.assertEqual((Path(temp)/n).read_bytes(),source)
                with Image.open(Path(temp)/n) as im:
                    self.assertEqual(im.size,EXPECTED_SIZE)
            pdf=PdfReader(str(Path(temp)/"infographic.pdf"),strict=True)
            self.assertEqual(len(pdf.pages),1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.width),595.2756,delta=0.1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.height),841.8898,delta=0.1)

if __name__=="__main__":
    unittest.main()
