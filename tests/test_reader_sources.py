from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_article_analytics import _reader_source_rows, _source_rows

class ReaderSourcesTests(unittest.TestCase):
    def test_acquisition_all_combines_aliases_and_unknowns(self):
        rows = [dict(article_slug='a', attribution_source='LinkedIn', sessions=2),
                dict(article_slug='b', attribution_source='linkedin_launch', sessions=3),
                dict(article_slug='a', attribution_source=None, sessions=1)]
        self.assertEqual(_source_rows(rows), [
            {'source': 'LinkedIn', 'sessions': 5},
            {'source': 'Unattributed / unknown', 'sessions': 1}])
        self.assertEqual(sum(r['sessions'] for r in _source_rows(rows, 'a')), 3)
        self.assertEqual(_source_rows(None), [])

    def test_acquisition_defaults_all_and_preserves_drilldown(self):
        from streamlit.testing.v1 import AppTest
        data = {'articles': [{'article_slug': 'a', 'sessions': 2},
                             {'article_slug': 'b', 'sessions': 3}],
                'sources': [dict(article_slug='a', attribution_source='LinkedIn', sessions=2),
                            dict(article_slug='b', attribution_source='Threads', sessions=3)]}
        with patch('page_article_analytics._article_title', side_effect=lambda x: x), patch(
                'page_article_analytics._fetch_article_dashboard', return_value=data):
            app = AppTest.from_string('from page_article_analytics import render_article_analytics\nrender_article_analytics()').run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].value, '')
            self.assertEqual(app.selectbox[0].options[0], 'All articles')
            self.assertTrue(any('5 article-session visits' in c.value for c in app.caption))
            app.selectbox[0].set_value('a').run()
            self.assertFalse(app.exception)
            self.assertTrue(any('2 article-session visits' in c.value for c in app.caption))

    def test_linkedin_sources_merge_without_losing_visits(self):
        rows = [dict(article_slug='a', attribution_source=source, sessions=1)
                for source in ('linkedin', 'LinkedIn', ' linkedin_launch ', 'linkedin?role=dailyquote')]
        result = _reader_source_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Source'], 'LinkedIn')
        self.assertEqual(result[0]['Reading visits'], 4)
        self.assertEqual(result[0]['Share'], 1)

    def test_threads_aliases_share_one_display_label(self):
        rows = [dict(article_slug='a', attribution_source=source, sessions=1)
                for source in ('thre', 'threads', 'Threads', ' THRE ')]
        result = _reader_source_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Source'], 'Threads')
        self.assertEqual(result[0]['Reading visits'], 4)
        self.assertEqual(result[0]['Share'], 1)

    def test_article_filter_and_case_grouping(self):
        rows = [dict(article_slug='a', attribution_source='KPMG', sessions=2),
                dict(article_slug='a', attribution_source='kpmg', sessions=1),
                dict(article_slug='b', attribution_source='KPMG', sessions=4),
                dict(article_slug='a', attribution_source=None, sessions=1)]
        result = _reader_source_rows(rows, 'a')
        self.assertEqual(result[0]['Source'], 'KPMG')
        self.assertEqual(result[0]['Reading visits'], 3)
        self.assertEqual(result[0]['Share'], .75)
        self.assertFalse(result[1]['Tagged'])
        self.assertEqual(sum(row['Reading visits'] for row in _reader_source_rows(rows)), 8)
        self.assertEqual(_reader_source_rows(rows, 'missing'), [])

    def test_graph_renders_without_opening_details(self):
        from streamlit.testing.v1 import AppTest
        with patch('page_article_analytics._article_title', return_value='Example'), patch('page_article_analytics._fetch_article_dashboard', return_value={
            'sources':[dict(article_slug='example', attribution_source='KPMG', sessions=2)]}):
            at = AppTest.from_string('from page_article_analytics import render_reader_sources\nrender_reader_sources("30d")').run()
            self.assertFalse(at.exception)
            self.assertEqual(at.subheader[0].value, 'Where readers come from')
            self.assertEqual(at.metric[0].value, 'KPMG')
            self.assertEqual(len(at.get('vega_lite_chart')), 1)
