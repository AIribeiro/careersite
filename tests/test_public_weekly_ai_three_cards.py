"""Four public content cards; essays, Weekly AI and briefings partition reads."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from site_cms import CmsArticle
from page_public_portfolio_overview import split_reader_rows, split_editorial_rows, portfolio_visit_rows


def edition(slug: str, *, kind: str = "Weekly Brief", category: str = "Weekly AI",
            status: str = "published") -> CmsArticle:
    return CmsArticle(
        title="WEEKLY AI — Adoption, Agents and Human Judgment",
        slug=slug, kind=kind, category=category, status=status,
        published_at="2026-10-19T08:00:00+00:00",
    )


def report() -> dict:
    return {
        "quality": {"site_sessions": 12, "site_views": 16,
                    "page_views": 6, "page_sessions": 6,
                    "article_views": 10, "article_sessions": 9},
        "performance": [
            {"kind": "page", "content": "home", "views": 5, "sessions": 5},
            {"kind": "page", "content": "ai-data-governance", "views": 1, "sessions": 1},
            {"kind": "article", "content": "if-ai-does-routine-work", "views": 6, "sessions": 5},
            {"kind": "article", "content": "weekly-ai-2026-10-19", "views": 4, "sessions": 4},
        ],
        "period_comparison": [],
        "campaigns": [],
    }


class FourColumnPortfolioTests(unittest.TestCase):
    def test_published_weekly_brief_is_split_from_essays_without_double_counting(self):
        articles = portfolio_visit_rows(report(), "article")
        regular, weekly = split_reader_rows(
            articles, [edition("weekly-ai-2026-10-19")],
        )
        self.assertEqual([r["Slug"] for r in regular], ["if-ai-does-routine-work"])
        self.assertEqual([r["Slug"] for r in weekly], ["weekly-ai-2026-10-19"])
        self.assertEqual(weekly[0]["Content"], "Week 42 · 2026")
        self.assertIn("WEEKLY AI", weekly[0]["Title"])
        self.assertEqual(sum(r["Views"] for r in regular), 6)
        self.assertEqual(sum(r["Views"] for r in weekly), 4)
        self.assertEqual(sum(r["Views"] for r in articles), 10)

    def test_draft_and_non_weekly_article_are_never_promoted_to_weekly(self):
        articles = [
            {"Slug": "weekly-ai-2026-10-19", "Content": "Could be a headline",
             "Views": 3, "Sessions": 3}
        ]
        cases = [
            edition("weekly-ai-2026-10-19", status="draft"),
            edition("weekly-ai-2026-10-19", category="Thought leadership"),
            edition("weekly-ai-2026-10-19", kind="Article"),
        ]
        for item in cases:
            regular, weekly = split_reader_rows(articles, [item])
            self.assertEqual(len(regular), 1)
            self.assertEqual(weekly, [])

    def test_analytics_displays_four_metrics_one_row_with_distinct_subsets(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_portfolio_overview.fetch_intelligence", return_value=report()),
            patch("page_public_portfolio_overview.fetch_published_articles",
                  return_value=[edition("weekly-ai-2026-10-19")]),
            patch("page_public_portfolio_overview.initialize_reporting_period",
                  side_effect=lambda state, f: state.setdefault(
                      "careersite_analytics_reporting_window", "7d")),
            patch("page_public_portfolio_overview.render_home_journey"),
            patch("page_public_portfolio_overview.portfolio_metric_grid",
                  return_value="<div>Four analytics cards</div>") as grid,
        ):
            at = AppTest.from_string(
                "from page_public_portfolio_overview import render_public_portfolio_overview\n"
                "render_public_portfolio_overview()\n"
            ).run(timeout=20)
        self.assertFalse(at.exception)
        grid.assert_called_once()
        cards = grid.call_args.args[0]
        self.assertEqual([card["title"] for card in cards], [
            "Portfolio visits", "Articles", "Weekly AI", "Executive Briefings"
        ])
        self.assertEqual([card["views"] for card in cards], [12, 6, 4, 0])
        self.assertEqual(cards[0]["measure"], "Site-wide sessions")
        self.assertEqual(cards[0]["sessions"], 16)
        self.assertEqual(cards[0]["sessions_label"], "content views (all sections)")
        self.assertTrue(all(card.get("available", True) for card in cards))
        self.assertEqual([card["rank_title"] for card in cards], [
            "Top portfolio pages", "Most-read articles",
            "Most-read editions", "Most-read briefings",
        ])
        self.assertTrue(any("Site-wide reach: 12 browser sessions generated "
                            "16 content views" in x.value for x in at.caption))

    def test_no_metadata_means_unknown_not_illusory_zero_editions(self):
        from streamlit.testing.v1 import AppTest
        with (
            patch("page_public_portfolio_overview.fetch_intelligence", return_value=report()),
            patch("page_public_portfolio_overview.fetch_published_articles",
                  side_effect=RuntimeError("catalogue unavailable")),
            patch("page_public_portfolio_overview.initialize_reporting_period",
                  side_effect=lambda state, f: state.setdefault(
                      "careersite_analytics_reporting_window", "7d")),
            patch("page_public_portfolio_overview.render_home_journey"),
            patch("page_public_portfolio_overview.portfolio_metric_grid",
                  return_value="<div>Four analytics cards</div>") as grid,
        ):
            at = AppTest.from_string(
                "from page_public_portfolio_overview import render_public_portfolio_overview\n"
                "render_public_portfolio_overview()\n"
            ).run(timeout=20)
        self.assertFalse(at.exception)
        grid.assert_called_once()
        cards = grid.call_args.args[0]
        self.assertEqual(cards[0]["views"], 12)
        self.assertEqual([card["available"] for card in cards[1:]],
                         [False, False, False])


if __name__ == "__main__":
    unittest.main()
