import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

class WeeklyCampaignTests(unittest.TestCase):
    def test_both_trackers_capture_content_and_send_it(self):
        for name in ('site_analytics.py', 'site_article_analytics.py'):
            source = (ROOT / 'src' / name).read_text()
            self.assertIn("params.get('utm_content')", source)
            self.assertIn('utm_content: attribution.utm_content || null', source)
            self.assertIn('|| incomingContent)', source)

    def test_campaign_visual_for_exact_link_tags(self):
        code = '''
from page_weekly_ai_analytics import render_weekly_campaigns
from site_cms import CmsArticle
issue = CmsArticle(id='w41',slug='weekly-ai-2026-10-11',title='WEEKLY AI',category='Weekly AI',kind='Weekly Brief',status='published',published_at='2026-10-11T10:00:00Z',excerpt='News')
render_weekly_campaigns({'campaigns':[dict(article_slug=issue.slug,channel='x',role='weeklyai',campaign='weekly_ai_2026_w41',content='work',reads=2,engaged_reads=1,audio_starts=1,share_sessions=0)]},[issue])
'''
        app = AppTest.from_string(code).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '2')
        self.assertEqual(len(app.get('vega_lite_chart')), 1)
        self.assertIn('weekly_ai_2026_w41', app.selectbox[1].options)

    def test_no_data_is_not_a_false_zero_conversion(self):
        app = AppTest.from_string('from page_weekly_ai_analytics import render_weekly_campaigns\nrender_weekly_campaigns(None, [])').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)

if __name__ == '__main__':
    unittest.main()
