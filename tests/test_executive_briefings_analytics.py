"""Executive Briefings analytics regression: CMS classification and event reuse."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from site_cms import CmsArticle
from page_executive_briefings_analytics import (
    briefing_analytics_report, published_briefings,
)
from page_public_portfolio_overview import split_editorial_rows, portfolio_visit_rows


def item(slug: str, kind: str = "Executive Briefing",
         status: str = "published") -> CmsArticle:
    return CmsArticle(
        title="Executive guide " + slug,
        slug=slug, kind=kind, status=status,
        published_at="2026-11-01T18:00:00Z",
    )


def evidence() -> dict:
    return {
        "quality": {"page_views": 14, "article_views": 16},
        "performance": [
            {"kind": "page", "content": "briefings", "views": 6, "sessions": 5},
            {"kind": "page", "content": "home", "views": 8, "sessions": 6},
            {"kind": "article", "content": "b1", "views": 5, "sessions": 3,
             "engaged_sessions": 2, "depth_measured_sessions": 2,
             "three_quarter_sessions": 1, "sharing_sessions": 1,
             "later_cv_sessions": 1, "later_contact_sessions": 1,
             "avg_active_seconds": 21.2},
            {"kind": "article", "content": "b2", "views": 2, "sessions": 2,
             "engaged_sessions": 1, "depth_measured_sessions": 0,
             "three_quarter_sessions": 0, "sharing_sessions": 0,
             "later_contact_sessions": 1},
            {"kind": "article", "content": "draft-b", "views": 4, "sessions": 4},
            {"kind": "article", "content": "essay", "views": 5, "sessions": 4},
        ],
        "section_reach": [
            {"page": "briefings", "section_key": "briefings-library",
             "page_sessions": 5, "reached_sessions": 4},
            {"page": "home", "section_key": "home-executive-briefings",
             "reached_sessions": 3},
        ],
        "article_cards": [
            {"element_key": "b1", "placement": "briefings:briefings-library",
             "exposed_sessions": 4, "click_sessions": 2},
            {"element_key": "b2", "placement": "briefings:briefings-library",
             "exposed_sessions": 3, "click_sessions": 1},
            {"element_key": "b1", "placement": "other:featured",
             "exposed_sessions": 100, "click_sessions": 80},
            {"element_key": "draft-b", "placement": "briefings:briefings-library",
             "exposed_sessions": 4, "click_sessions": 4},
        ],
    }


class ExecutiveBriefingsAnalyticsTests(unittest.TestCase):
    def test_report_classifies_only_published_briefings(self):
        catalogue = [item("b1"), item("b2"), item("draft-b", status="draft"),
                     item("essay", kind="Article")]
        data = briefing_analytics_report(evidence(), catalogue)
        self.assertEqual(data["published_count"], 2)
        self.assertEqual(data["read_count"], 5)
        self.assertEqual(data["view_count"], 7)
        self.assertEqual(data["engaged_count"], 3)
        self.assertEqual(data["library_views"], 6)
        self.assertEqual(data["library_reached"], 4)
        self.assertEqual(data["home_reached"], 3)
        self.assertEqual(data["card_exposures"], 7)
        self.assertEqual(data["card_clicks"], 3)
        self.assertEqual(data["later_cv_count"], 1)
        self.assertEqual(data["later_contact_count"], 2)
        self.assertEqual({r["Slug"] for r in data["rows"]}, {"b1", "b2"})

    def test_content_reading_partitions_reconcile_without_library_double_count(self):
        catalogue = [item("b1"), item("b2"), item("draft-b", status="draft")]
        article_rows = portfolio_visit_rows(evidence(), "article")
        essays, weekly, briefings = split_editorial_rows(article_rows, catalogue)
        self.assertEqual(sum(r["Views"] for r in essays), 9)  # includes unclassified draft-b
        self.assertEqual(sum(r["Views"] for r in briefings), 7)
        self.assertEqual(weekly, [])
        self.assertEqual(sum(r["Views"] for r in essays + weekly + briefings), 16)
        self.assertEqual(portfolio_visit_rows(evidence(), "page")[0]["Slug"], "home")

    def test_missing_depth_measurement_is_unknown_not_zero_percent(self):
        data = briefing_analytics_report(evidence(), [item("b1"), item("b2")])
        rows = {row["Slug"]: row for row in data["rows"]}
        self.assertEqual(rows["b1"]["Depth rate"], "50.0%")
        self.assertEqual(rows["b2"]["Depth rate"], "—")
        self.assertEqual(rows["b1"]["Engagement"], "66.7%")
        self.assertEqual(rows["b2"]["Engagement"], "50.0%")
        self.assertEqual(rows["b2"]["Avg confirmed seconds"], None)
        self.assertIn("?page=briefing&article=b1", rows["b1"]["URL"])

    def test_catalogue_is_authoritative_not_slug_or_title_guesswork(self):
        self.assertEqual(published_briefings([item("draft-b", status="draft")]), [])
        self.assertEqual(published_briefings([item("b1", kind="Article")]), [])
        self.assertEqual(briefing_analytics_report(evidence(), [])["read_count"], 0)

    def test_both_public_and_owner_focus_expose_briefings(self):
        src = Path(__file__).resolve().parents[1] / "src"
        public = (src / "page_analytics_v2.py").read_text(encoding="utf-8")
        owner = (src / "page_owner_workspaces.py").read_text(encoding="utf-8")
        for source in (public, owner):
            self.assertIn('"briefings": "Executive Briefings"', source)
            self.assertIn("render_executive_briefings_analytics", source)


if __name__ == "__main__":
    unittest.main()
