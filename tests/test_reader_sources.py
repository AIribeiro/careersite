from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_article_analytics import _reader_source_rows

class ReaderSourcesTests(unittest.TestCase):
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
