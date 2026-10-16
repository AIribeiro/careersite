"""Dynamic public-portfolio narrative, denominator and uncertainty contracts."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_insight_engine import derive_portfolio_insights


def make_report(previous_page=0, previous_article=0):
    return {
        "quality": {
            "page_views": 933,
            "article_views": 289,
            "page_sessions": 793,
            "article_sessions": 268,
        },
        "performance": [
            {"kind": "article", "content": "article-one", "views": 61,
             "sessions": 48, "depth_measured_sessions": 7,
             "deep_read_sessions": 0, "later_portfolio_sessions": 1},
            {"kind": "article", "content": "article-two", "views": 54,
             "sessions": 54, "depth_measured_sessions": 14,
             "deep_read_sessions": 0, "later_portfolio_sessions": 0},
            {"kind": "article", "content": "article-three", "views": 43,
             "sessions": 43, "depth_measured_sessions": 22,
             "deep_read_sessions": 3, "later_portfolio_sessions": 2},
        ],
        "period_comparison": [
            {"kind": "page", "current_views": 933,
             "previous_views": previous_page},
            {"kind": "article", "current_views": 289,
             "previous_views": previous_article},
        ],
        "topic_performance": [
            {"topic": "Governance", "views": 80},
            {"topic": "AI adoption", "views": 45},
        ],
    }


PAGES = [
    {"Content": "Home", "Views": 644, "Sessions": 510},
    {"Content": "Certifications", "Views": 150, "Sessions": 142},
    {"Content": "Impact", "Views": 139, "Sessions": 120},
]
ARTICLES = [
    {"Content": "Article 1", "Views": 61, "Sessions": 48},
    {"Content": "Article 2", "Views": 54, "Sessions": 54},
    {"Content": "Article 3", "Views": 43, "Sessions": 43},
    {"Content": "Other articles", "Views": 131, "Sessions": 120},
]


class PublicPortfolioIntelligenceTests(unittest.TestCase):
    def test_top_insights_explain_where_attention_and_reads_concentrate(self):
        top, bottom = derive_portfolio_insights(make_report(), PAGES, ARTICLES)
        self.assertEqual(len(top), 2)
        self.assertIn("69%", top[0].interpretation)
        self.assertIn("644 of 933 classified", top[0].basis)
        self.assertIn("55%", top[1].interpretation)
        self.assertIn("158 of 289 classified", top[1].basis)
        self.assertIn("31%", bottom[0].interpretation)
        self.assertIn("289 non-Home page views", bottom[0].basis)

    def test_depth_claims_use_measured_denominator_and_do_not_call_zeros_failures(self):
        _, bottom = derive_portfolio_insights(make_report(), PAGES, ARTICLES)
        reading = next(x for x in bottom if "Reading depth" in x.heading)
        self.assertIn("43 depth-measured", reading.basis)
        self.assertIn("3", reading.interpretation)
        self.assertIn("not be classified as", reading.interpretation)
        self.assertIn("145 article-item", reading.basis)

    def test_not_possible_to_infer_acceleration_without_prior_observations(self):
        _, bottom = derive_portfolio_insights(make_report(), PAGES, ARTICLES)
        momentum = next(x for x in bottom if "Movement" in x.heading)
        self.assertIn("cannot yet be assessed", momentum.heading)
        self.assertIn("missing baseline", momentum.interpretation)

    def test_comparable_periods_generate_directional_change(self):
        _, bottom = derive_portfolio_insights(
            make_report(previous_page=800, previous_article=400), PAGES, ARTICLES
        )
        change = next(x for x in bottom if "preceding period" in x.heading)
        self.assertIn("rose by 17%", change.interpretation)
        self.assertIn("fell by 28%", change.interpretation)
        self.assertIn("equal-duration", change.basis)
        self.assertIn("not a causal explanation", change.interpretation)

    def test_low_volume_does_not_overstate_content_preferences(self):
        top, bottom = derive_portfolio_insights(
            {"performance": [], "period_comparison": []},
            [{"Content": "Home", "Views": 2}],
            [{"Content": "A", "Views": 1}],
        )
        self.assertIn("too small", top[0].interpretation)
        self.assertIn("not yet broad enough", top[1].interpretation)
        self.assertFalse(any("rose by" in x.interpretation for x in bottom))

    def test_follow_up_cannot_be_mistaken_for_a_recruiter(self):
        _, bottom = derive_portfolio_insights(make_report(), PAGES, ARTICLES)
        navigation = next(x for x in bottom if "after reading" in x.heading)
        self.assertIn("3 article-level follow-on", navigation.interpretation)
        self.assertIn("not a recruiter identification", navigation.interpretation)

    def test_selected_period_controls_dashboard_and_narratives(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_portfolio_overview.fetch_intelligence",
                  return_value=make_report()),
            patch("page_public_portfolio_overview.initialize_reporting_period",
                  side_effect=lambda state, f: state.setdefault(
                      "careersite_analytics_reporting_window", "30d")),
            patch("page_public_portfolio_overview._ranking_chart") as chart,
        ):
            app = AppTest.from_string(
                "from page_public_portfolio_overview import render_public_portfolio_overview\n"
                "render_public_portfolio_overview()\n"
            ).run(timeout=20)
            self.assertEqual(chart.call_count, 2)
        self.assertFalse(app.exception)
        self.assertIn("What stands out", [x.value for x in app.subheader])
        self.assertIn("Portfolio intelligence", [x.value for x in app.subheader])
        self.assertEqual(len(app.metric), 2)
        self.assertEqual(len(app.get("vega_lite_chart")), 0)


if __name__ == "__main__":
    unittest.main()
