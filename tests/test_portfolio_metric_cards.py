"""Visual/semantic contracts for the four equal-height public portfolio cards."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_metric_cards import portfolio_metric_grid


def spec(title: str, *, rows: list[dict] | None = None, available: bool = True) -> dict:
    return {
        "title": title,
        "category": "Content",
        "measure": "Views",
        "views": 1200,
        "lifetime": 1234,
        "sessions": 900,
        "sessions_label": "article-item sessions",
        "items": 5,
        "item_unit": "items read",
        "rank_title": "Most-read items",
        "rows": rows if rows is not None else [
            {"Content": "An article title", "Views": 12, "Sessions": 6},
        ],
        "available": available,
    }


class PortfolioMetricCardTests(unittest.TestCase):
    def test_four_cards_have_identical_sections_and_order(self):
        content = portfolio_metric_grid([
            spec("Portfolio visits"), spec("Articles"),
            spec("Weekly AI"), spec("Executive Briefings"),
        ])
        for section in ("pv-card__header", "pv-card__metric",
                        "pv-card__activity", "pv-card__ranking"):
            self.assertEqual(content.count(f'class="{section}"'), 4)
        self.assertEqual(content.count('<section class="pv-card"'), 4)
        self.assertLess(content.index('Portfolio visits analytics'),
                        content.index('Articles analytics'))
        self.assertLess(content.index('Articles analytics'),
                        content.index('Weekly AI analytics'))
        self.assertLess(content.index('Weekly AI analytics'),
                        content.index('Executive Briefings analytics'))
        self.assertEqual(content.count("1,200"), 4)
        self.assertEqual(content.count("Lifetime · 1,234 views"), 4)

    def test_tablet_and_mobile_use_container_width_not_viewport(self):
        content = portfolio_metric_grid([spec(x) for x in ("A", "B", "C", "D")])
        self.assertIn("container-type:inline-size", content)
        self.assertIn("@container(max-width:1150px)", content)
        self.assertIn("@container(max-width:580px)", content)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", content)
        self.assertIn("grid-template-columns:minmax(0,1fr)", content)

    def test_html_labels_are_escaped_before_rendering(self):
        bad = '<img src=x onerror="alert(1)">'
        content = portfolio_metric_grid([
            spec("Portfolio visits", rows=[{"Content": bad, "Views": 5}]),
            spec("Articles"), spec("Weekly AI"), spec("Executive Briefings"),
        ])
        self.assertNotIn(bad, content)
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", content)
        self.assertIn('title="&lt;img src=x', content)

    def test_missing_and_sparse_categories_do_not_shift_the_grid(self):
        content = portfolio_metric_grid([
            spec("Portfolio visits", rows=[]),
            spec("Articles", rows=[{"Content": "One", "Views": 7}]),
            spec("Weekly AI", available=False),
            spec("Executive Briefings", rows=[]),
        ])
        self.assertIn("No recorded views in this reporting period", content)
        self.assertIn("Content classification is temporarily unavailable", content)
        self.assertIn("pv-card__item--placeholder", content)
        self.assertIn("article-item sessions", content)
        self.assertIn("Lifetime unavailable", content)

    def test_briefing_coverage_distinguishes_viewed_from_published(self):
        briefings = spec("Executive Briefings")
        briefings.update({
            "views": 1,
            "lifetime": 7,
            "sessions": 1,
            "items": 1,
            "total_items": 6,
            "item_unit": "published briefings viewed",
            "period_label": "Today",
            "rank_title": "Most-viewed briefings",
        })
        content = portfolio_metric_grid([
            spec("Portfolio visits"), spec("Articles"), spec("Weekly AI"), briefings,
        ])
        self.assertIn("Views · Today", content)
        self.assertIn("1 of 6", content)
        self.assertIn("published briefings viewed", content)
        self.assertIn("Lifetime · 7 views", content)
        self.assertIn("Most-viewed briefings", content)

    def test_site_session_headline_has_correct_lifetime_and_view_breakdown(self):
        visits = spec("Portfolio visits")
        visits.update({
            "measure": "Site-wide sessions",
            "views": 38,
            "lifetime": 482,
            "lifetime_unit": "views",
            "sessions": 39,
            "sessions_label": "content views (all sections)",
            "items": 3,
            "item_unit": "active destinations",
            "rank_title": "Top portfolio pages",
        })
        content = portfolio_metric_grid([
            visits, spec("Articles"), spec("Weekly AI"), spec("Executive Briefings"),
        ])
        self.assertIn("Site-wide sessions", content)
        self.assertIn(">38</strong>", content)
        self.assertIn("Lifetime · 482 views", content)
        self.assertIn(">39</strong>", content)
        self.assertIn("content views (all sections)", content)
        self.assertIn("Top portfolio pages", content)

    def test_period_label_is_escaped(self):
        card = spec("Executive Briefings")
        card["period_label"] = '<custom>'
        content = portfolio_metric_grid([
            spec("Portfolio visits"), spec("Articles"), spec("Weekly AI"), card,
        ])
        self.assertNotIn('<custom>', content)
        self.assertIn("&lt;custom&gt;", content)

    def test_rejects_incomplete_category_groups(self):
        with self.assertRaises(ValueError):
            portfolio_metric_grid([spec("One")])


if __name__ == "__main__":
    unittest.main()
