from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from site_cms import CmsArticle
from thinking_weekly_brief import edition_week
from page_weekly_ai_analytics import weekly_ai_report


ROOT = Path(__file__).resolve().parents[1]


def issue(slug="weekly-ai-2026-10-11", **kwargs):
    data = {
        "id": slug,
        "slug": slug,
        "title": "WEEKLY AI — Pilot",
        "category": "Weekly AI",
        "kind": "Weekly Brief",
        "status": "published",
        "published_at": "2026-10-11T10:00:00Z",
        "excerpt": "Five verified stories.",
    }
    data.update(kwargs)
    return CmsArticle(**data)


class WeeklyAiAnalyticsTests(unittest.TestCase):
    def test_edition_report_keeps_website_counts_separate(self):
        signal = {
            "performance": [
                {"kind": "article", "content": "weekly-ai-2026-10-11",
                 "views": 4, "sessions": 2, "engaged_sessions": 1,
                 "avg_active_seconds": 24, "sharing_sessions": 1,
                 "depth_measured_sessions": 2, "three_quarter_sessions": 1,
                 "later_cv_sessions": 1, "later_contact_sessions": 0},
                {"kind": "article", "content": "ordinary-article",
                 "views": 90, "sessions": 50, "engaged_sessions": 40},
                {"kind": "page", "content": "thinking", "views": 70, "sessions": 30},
            ],
            "section_reach": [
                {"page": "thinking", "section_key": "weekly-ai-feature",
                 "page_sessions": 30, "reached_sessions": 12},
                {"page": "thinking", "section_key": "weekly-ai-archive",
                 "page_sessions": 30, "reached_sessions": 3},
            ],
            "article_cards": [{
                "element_key": "weekly-ai-2026-10-11",
                "placement": "thinking:weekly-ai-feature",
                "exposed_sessions": 10, "click_sessions": 3,
            }],
            "cta_placements": [
                {"element_key": "weekly_ai_archive_open",
                 "placement": "thinking:weekly-ai-feature",
                 "exposed_sessions": 8, "click_sessions": 2},
                {"element_key": "weekly-ai-source:brookings.edu",
                 "placement": "thinking:weekly-ai-reader",
                 "exposed_sessions": 3, "click_sessions": 1},
                {"element_key": "weekly-ai-source:example.org",
                 "placement": "thinking:weekly-ai-reader",
                 "exposed_sessions": 2, "click_sessions": 2},
                {"element_key": "cv",
                 "placement": "thinking:weekly-ai-reader",
                 "exposed_sessions": 20, "click_sessions": 15},
            ]
        }
        result = weekly_ai_report(signal, [issue(), issue(slug="weekly-ai-2026-10-18", status="draft")])
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(result["feature_sessions"], 12)
        self.assertEqual(result["feature_page_sessions"], 30)
        self.assertEqual(result["archive_sessions"], 3)
        self.assertEqual(result["reader_sessions"], 2)
        self.assertEqual(result["reader_views"], 4)
        self.assertEqual(result["engaged_sessions"], 1)
        self.assertEqual(result["share_sessions"], 1)
        self.assertEqual(result["archive_link_clicks"], 2)
        self.assertEqual(result["source_click_sessions"], 3)
        self.assertEqual(result["rows"][0]["Week"], "Week 41 · 2026")
        self.assertEqual(result["rows"][0]["Reached 75%"], "50.0%")
        self.assertEqual(result["issue_ctrs"][0]["Click sessions"], 3)

    def test_monday_publication_uses_preceding_swedish_week(self):
        result = weekly_ai_report(
            {"performance": [], "section_reach": [], "article_cards": [], "cta_placements": []},
            [issue(slug="weekly-ai-2026-10-19", published_at="2026-10-19T08:00:00Z")],
        )
        self.assertEqual(result["rows"][0]["Week"], "Week 42 · 2026")
        self.assertEqual(result["rows"][0]["Edition sessions"], 0)
        self.assertEqual(result["feature_sessions"], 0)

    def test_weekly_section_instrumentation_has_stable_keys(self):
        content = (ROOT / "src" / "thinking_weekly_brief.py").read_text()
        for marker in (
            'data-analytics-section=\"weekly-ai-feature\"',
            'data-analytics-section=\"weekly-ai-archive\"',
            'data-analytics-section=\"weekly-ai-reader\"',
            'data-hq-content-slug=',
            'data-hq-event=\"weekly_ai_archive_open\"',
            'data-hq-event=\"weekly_ai_archive_issue_open\"',
        ):
            self.assertIn(marker, content)

    def test_existing_event_names_are_reused_not_new_unregistered_events(self):
        source = (ROOT / "src" / "site_analytics.py").read_text()
        self.assertIn("weekly-ai-source:", source)
        self.assertIn("weekly_ai_archive_open", source)
        self.assertIn("data-hq-content-slug", source)
        self.assertIn("'article_card_click'", source)
        self.assertIn("'cta_click'", source)
        self.assertIn("Boolean(el.closest('.weekly-ai-body'))", source)

    def test_analytics_focus_is_owner_protected_and_explicit(self):
        source = (ROOT / "src" / "page_analytics_v2.py").read_text()
        self.assertIn('options=["page","article","weekly_ai"]', source)
        self.assertIn("render_weekly_ai_analytics(str(window))", source)
        self.assertLess(source.index("session = _owner_session()"), source.index("render_weekly_ai_analytics(str(window))"))


if __name__ == "__main__":
    unittest.main()
