from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'src'))
from weekly_ai_brand_cover import render_friday_cover, save_friday_cover, SIZE


class FridayCoverTests(unittest.TestCase):
    def test_week43_approved_branding_and_linkedin_ratio(self):
        image=render_friday_cover(iso_year=2026,iso_week=43,
                                  title='Faster Tools, Harder Decisions')
        self.assertEqual(image.size,(1200,627))
        self.assertEqual(image.mode,'RGB')
        self.assertNotEqual(image.getpixel((60,250)), image.getpixel((750,250)))

    def test_different_week_different_issue_image(self):
        a=render_friday_cover(iso_year=2026,iso_week=43,
                              title='Faster Tools, Harder Decisions')
        b=render_friday_cover(iso_year=2026,iso_week=44,
                              title='A New Perspective on AI Governance')
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_oversized_title_and_invalid_week_fail_closed(self):
        with self.assertRaises(ValueError):
            render_friday_cover(iso_year=2026,iso_week=70,title='A headline that is otherwise fine')
        with self.assertRaises(ValueError):
            render_friday_cover(iso_year=2026,iso_week=43,title='X'*96)

    def test_persisted_cover_is_valid_png(self):
        with tempfile.TemporaryDirectory() as td:
            result=save_friday_cover(2026,43,'Faster Tools, Harder Decisions',
                                     'Friday perspective · one minute',Path(td)/'cover.png')
            with Image.open(result) as image:
                self.assertEqual(image.format,'PNG')
                self.assertEqual(image.size,SIZE)


if __name__=='__main__':
    unittest.main()