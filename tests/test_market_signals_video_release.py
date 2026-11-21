"""Verify 21 November Market Signals film publication without touching other briefings."""
import json
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from page_advisory_market_signals import MARKET_SIGNALS_LANDING_HTML as PAGE, MARKET_SIGNALS_LANDING_CSS as CSS

MANIFEST=ROOT/"static/market-signals/video-unionen-2026-11/manifest.json"

class MarketVideoReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_approved_exact_media_and_source_provenance(self):
        m=self.m
        self.assertTrue(m["website_release_authorized"])
        self.assertEqual(m["edition_slug"],"sweden-ai-data-market-review-2026-11-unionen-2-1")
        self.assertEqual(m["web"]["sha256"],"eafa2f511a328d4dc2ed45f10d2349598b822e7f1db166dce66651a62ffa326f")
        self.assertEqual(m["web"]["bytes"],9984008)
        self.assertEqual(m["poster"]["sha256"],"7fdbd6cedc8aa013abadbb89a18c629e93d17df98e448cc166590b44599f2ce3")
        self.assertEqual(m["poster"]["bytes"],105462)
        self.assertTrue(m["web"]["anonymous_head_200"])
        self.assertTrue(m["web"]["start_mid_end_http_206"])
        self.assertFalse(m["linkedIn"]["published"])

    def test_public_page_plays_exact_approved_video_and_preserves_archive(self):
        m=self.m
        video=m["web"]["public_url"]
        poster=m["poster"]["public_url"]
        self.assertEqual(PAGE.count('class="ms-video-player"'),1)
        self.assertEqual(PAGE.count('src="'+video+'"'),1)
        self.assertEqual(PAGE.count('poster="'+poster+'"'),1)
        self.assertIn("controls playsinline webkit-playsinline preload=\"metadata\"",PAGE)
        self.assertIn("<source src=\""+video+"\" type=\"video/mp4\">",PAGE)
        self.assertIn('href="'+video+'"',PAGE)
        self.assertIn("November research video directly",PAGE)
        self.assertIn("Previous 58-second Market Signals introduction",PAGE)
        self.assertIn("app.heygen.com/share/55e1d1dff94641d2a3f6e915cef8fd3d",PAGE)
        self.assertIn("Executive Edition 2.1.0",PAGE)
        self.assertIn("Jobseeker Edition 1.2",PAGE)
        chunk=PAGE.split('class="ms-video-player"',1)[1].split("</video>",1)[0]
        self.assertNotIn("autoplay",chunk)
        self.assertNotIn("/app/static/market-signals/",chunk)
        self.assertIn(".site.ms-landing .ms-video-layout",CSS)
        self.assertIn(".site.ms-landing .ms-film-archive",CSS)

    def test_original_master_and_poster_remain_retrievable_as_old_assets(self):
        old_video=ROOT/"static/market-signals/market-review-november-2026.mp4"
        old_poster=ROOT/"static/market-signals/market-review-poster.jpg"
        self.assertTrue(old_video.is_file())
        self.assertTrue(old_poster.is_file())
        with old_video.open("rb") as f:
            self.assertEqual(f.read(8)[4:8],b"ftyp")
        with old_poster.open("rb") as f:
            self.assertEqual(f.read(3),bytes((255,216,255)))

if __name__=="__main__":
    unittest.main()
