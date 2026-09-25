from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from page_content_intelligence import (
    performance_rows,
    export_csv,
    _rate,
    _change,
    _trend_visual_rows,
    _topic_visual_rows,
    _topic_heatmap_rows,
    _first7_visual_rows,
    _content_visual_rows,
    _campaign_visual_rows,
)


class ContentIntelligenceTests(unittest.TestCase):
    def test_missing_depth_does_not_become_zero_percent(self):
        row = dict(kind='page', content='home', views=2, sessions=1, engaged_sessions=0,
                   confirmed_sessions=0, avg_active_seconds=None, depth_measured_sessions=0,
                   halfway_sessions=0, bottom_sessions=0, deep_read_sessions=0, shares=0,
                   sharing_sessions=0, action_sessions=0, later_cv_sessions=0,
                   later_contact_sessions=0, later_portfolio_sessions=0)
        result = performance_rows({'performance': [row]}, 'page')[0]
        self.assertEqual(result['Reached 90%'], '—')
        self.assertEqual(result['Deep reads ≥30s + 90%'], '—')
        self.assertEqual(performance_rows({'performance': [row]}, 'article'), [])

    def test_rates_always_show_counts(self):
        self.assertEqual(_rate(2, 8), "25.0% (2 of 8)")
        self.assertEqual(_rate(0, 0), "—")
        self.assertEqual(_change(6, 4), "+50.0% (6 vs 4)")

    def test_csv_neutralizes_campaign_formulas(self):
        self.assertIn("'=HYPERLINK", export_csv([{'Campaign': '=HYPERLINK("x")'}]))

    def test_trend_visual_rows_preserve_current_previous_counts(self):
        data = {'period_comparison': [{
            'kind': 'article', 'content': 'example', 'current_sessions': 6,
            'previous_sessions': 4, 'current_engaged_sessions': 3,
            'previous_engaged_sessions': 2,
        }]}
        row = _trend_visual_rows(data, 'article')[0]
        self.assertEqual(row['Current sessions'], 6)
        self.assertEqual(row['Previous sessions'], 4)
        self.assertEqual(row['Session change %'], 50.0)

    def test_topic_visuals_keep_unavailable_denominators_blank(self):
        data = {'topic_performance': [{
            'topic': 'AI Governance', 'article_sessions': 4, 'views': 6,
            'engaged_sessions': 2, 'depth_measured_sessions': 0,
            'reached_75_sessions': 0, 'reached_90_sessions': 0,
            'later_portfolio_sessions': 1, 'later_cv_sessions': 1,
            'later_contact_sessions': 0,
        }]}
        row = _topic_visual_rows(data)[0]
        self.assertEqual(row['Engaged %'], 50.0)
        self.assertIsNone(row['Reached 75%'])
        heat = _topic_heatmap_rows([row])
        self.assertNotIn('Reached 75', {cell['Metric'] for cell in heat})

    def test_first7_visual_rows_use_exposure_denominators(self):
        data = {'publication_age': [{
            'slug': 'example', 'title': 'Example', 'topic': 'AI Strategy',
            'published_date': '2026-09-01', 'views': 8, 'sessions': 4,
            'engaged_sessions': 3, 'depth_measured_sessions': 2,
            'reached_75_sessions': 1,
        }]}
        row = _first7_visual_rows(data)[0]
        self.assertEqual(row['Engaged %'], 75.0)
        self.assertEqual(row['Reached 75%'], 50.0)

    def test_content_visual_rows_keep_exact_rate_denominators(self):
        data = {'performance': [{
            'kind': 'article', 'content': 'example', 'views': 8, 'sessions': 4,
            'avg_active_seconds': 21.5, 'engaged_sessions': 3,
            'depth_measured_sessions': 2, 'quarter_sessions': 2, 'halfway_sessions': 2,
            'three_quarter_sessions': 1, 'bottom_sessions': 1, 'deep_read_sessions': 1,
            'sharing_sessions': 1, 'later_portfolio_sessions': 2,
            'later_cv_sessions': 1, 'later_contact_sessions': 0,
        }]}
        row = _content_visual_rows(data, 'article')[0]
        self.assertEqual(row['Engaged'], 75.0)
        self.assertEqual(row['Reached 75'], 50.0)
        self.assertEqual(row['Later CV'], 25.0)

    def test_campaign_visual_rows_retain_raw_action_counts(self):
        data = {'campaigns': [{
            'channel': 'linkedin', 'campaign': 'role-a', 'sessions': 8,
            'reader_sessions': 6, 'engaged_sessions': 4, 'cv_sessions': 2,
            'contact_sessions': 1,
        }]}
        row = _campaign_visual_rows(data)[0]
        self.assertEqual(row['Reader sessions'], 6)
        self.assertEqual(row['Engaged sessions'], 4)
        self.assertEqual(row['CV sessions'], 2)
        self.assertEqual(row['Contact sessions'], 1)
        self.assertEqual(row['Contact'], 12.5)

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
