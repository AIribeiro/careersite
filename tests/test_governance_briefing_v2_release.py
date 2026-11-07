"""Source, artwork, cover and reader integration for revised policy-governance briefing."""
from __future__ import annotations
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from site_cms import CmsArticle,reader_header_image_src,effective_header_image_url
from briefing_approved_asset_renderer import load_bundle,validate_bundle,render_approved_bundle
from briefing_infographic_engine import source_fingerprint

SLUG='policy-is-not-permission-executive-ai-governance'

class GovernanceV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'docs'/'briefing_revisions'/'policy-is-not-permission-v2.json').read_text(encoding='utf-8'))
        cls.article=CmsArticle(
            title=cls.data['title'],subtitle=cls.data['subtitle'],
            content_html=cls.data['content_html'],slug=SLUG,
            status='published',kind='Executive Briefing',read_minutes=8,
            header_image_url='',header_image_alt=cls.data['header_image_alt'])
        cls.bundle=load_bundle(SLUG)
    def test_source_is_locked_to_approved_artwork(self):
        self.assertIsNotNone(self.bundle)
        self.assertEqual(self.bundle['article_fingerprint'],source_fingerprint(self.article))
        self.assertEqual(self.bundle['revision'],'2026-11-07-r3')
        self.assertIn('The executive decision record',self.article.content_html)
        self.assertIn('15.3 hours',self.article.content_html)
        self.assertIn('Illustrative calculation',self.article.content_html)
        self.assertEqual(self.article.content_html.count('<li>'),12)
        validate_bundle(self.bundle)
    def test_cover_reaches_reader_as_embedded_webp(self):
        source=reader_header_image_src(self.article)
        self.assertTrue(source.startswith('data:image/webp;base64,'))
        raw=base64.b64decode(source.split(',',1)[1],validate=True)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.bundle['cover']['sha256'])
        with Image.open(BytesIO(raw)) as image:
            self.assertEqual(image.size,(1600,900));image.verify()
        listing=effective_header_image_url(self.article)
        self.assertIn('/'+SLUG+'/cover.webp?v=',listing)
    def test_responsive_infographic_and_pdf_are_source_matched(self):
        row={'status':'approved','source_fingerprint':source_fingerprint(self.article),
             'alt_text':'Original six-proof AI governance diagram demonstrating runtime enforcement and evidence.',
             'caption':'Executive governance infographic by Jair Ribeiro.'}
        html=render_approved_bundle(self.article,row)
        self.assertEqual(html.count('data:image/webp;base64,'),2)
        self.assertEqual(html.count('data-analytics-section="briefing-infographic"'),1)
        self.assertLess(html.find('Download infographic'),html.find('data:image/webp;base64,'))
        bundle_dir=ROOT/'static'/'briefing-artwork'/SLUG
        reader=PdfReader(str(bundle_dir/'infographic.pdf'),strict=True)
        self.assertEqual(len(reader.pages),1)
        self.assertEqual(self.bundle['pdf']['pages'],1)
        for page in reader.pages:
            self.assertTrue(589<float(page.mediabox.width)<601)
            self.assertTrue(836<float(page.mediabox.height)<848)
if __name__=='__main__':unittest.main()
