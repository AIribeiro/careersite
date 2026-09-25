from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from page_content_intelligence import performance_rows, export_csv, _rate, _change


class ContentIntelligenceTests(unittest.TestCase):
    def test_missing_depth_does_not_become_zero_percent(self):
        row = dict(kind='page', content='home', views=2, sessions=1, engaged_sessions=0,
                   confirmed_sessions=0, avg_active_seconds=None, depth_measured_sessions=0,
                   halfway_sessions=0, bottom_sessions=0, deep_read_sessions=0, shares=0,
                   sharing_sessions=0, action_sessions=0, later_cv_sessions=0,
                   later_contact_sessions=0, later_portfolio_sessions=0)
        result = performance_rows({'performance': [row]}, 'page')[0]
        self.assertEqual(result['Reached 90%'], '—')
        self.assertIsNone(result['Deep reads ≥30s + 90%'])
        self.assertEqual(performance_rows({'performance': [row]}, 'article'), [])

    def test_rates_always_show_counts(self):
        self.assertEqual(_rate(2, 8), "25.0% (2 of 8)")
        self.assertEqual(_rate(0, 0), "—")
        self.assertEqual(_change(6, 4), "+50.0% (6 vs 4)")

    def test_csv_neutralizes_campaign_formulas(self):
        self.assertIn("'=HYPERLINK", export_csv([{'Campaign': '=HYPERLINK("x")'}]))

    def test_each_route_renders_only_its_dashboard_and_filter(self):
        from streamlit.testing.v1 import AppTest
        code = 'from page_analytics_v2 import render_analytics_dashboard\nrender_analytics_dashboard()'
        for section in ('pages', 'articles'):
            with patch('page_analytics_v2.render_content_intelligence') as content, \
                 patch('page_analytics_v2.render_site_analytics_dashboard') as pages, \
                 patch('page_analytics_v2.render_article_analytics') as articles:
                at = AppTest.from_string(code)
                at.query_params['view'] = section
                at.run()
                self.assertFalse(at.exception)
                self.assertEqual(len(at.selectbox), 1)
                self.assertEqual(pages.call_count, int(section == 'pages'))
                self.assertEqual(articles.call_count, int(section == 'articles'))
                self.assertEqual(content.call_args.args[0], 'page' if section == 'pages' else 'article')


if __name__ == '__main__':
    unittest.main()
