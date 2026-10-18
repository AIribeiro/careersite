from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from site_cms import CmsArticle, inject_cms_landing, select_auto_featured_article


class AutomaticHighlightTests(unittest.TestCase):
    NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)

    def article(self, name: str, age_hours: float, **kwargs) -> CmsArticle:
        published = self.NOW - timedelta(hours=age_hours)
        return CmsArticle(
            id=name,
            slug=name,
            title=name,
            status="published",
            published_at=published.isoformat(),
            **kwargs,
        )

    def test_latest_new_publication_wins_even_against_more_reads(self) -> None:
        popular = self.article("popular-essay", 180, legacy_key="investable_portfolio")
        newest = self.article("new-essay", 18)
        result = select_auto_featured_article(
            [popular, newest], {"popular-essay": 300, "new-essay": 0},
            as_of=self.NOW,
        )
        self.assertEqual(result.slug, "new-essay")

    def test_feature_window_is_exactly_48_hours(self) -> None:
        popular = self.article("most-read", 250, legacy_key="investable_portfolio")
        new = self.article("new", 48)
        self.assertEqual(
            select_auto_featured_article(
                [new, popular], {"most-read": 80, "new": 5},
                as_of=self.NOW,
            ).slug,
            "most-read",
        )

    def test_multiple_recent_publications_choose_most_recent(self) -> None:
        earlier = self.article("yesterday", 28)
        newest = self.article("today", 2)
        self.assertEqual(
            select_auto_featured_article(
                [earlier, newest], {"yesterday": 100, "today": 1},
                as_of=self.NOW,
            ).slug,
            "today",
        )

    def test_later_edits_do_not_restart_publication_window(self) -> None:
        older = self.article("edited-older", 100, updated_at=self.NOW.isoformat())
        popular = self.article("popular", 400)
        self.assertEqual(
            select_auto_featured_article(
                [older, popular], {"edited-older": 12, "popular": 54},
                as_of=self.NOW,
            ).slug,
            "popular",
        )

    def test_weekly_briefs_are_not_eligible(self) -> None:
        weekly = self.article("weekly", 1, kind="Weekly Brief", category="Weekly AI")
        ordinary = self.article("ordinary", 200)
        self.assertEqual(
            select_auto_featured_article(
                [weekly, ordinary], {"weekly": 1000, "ordinary": 2},
                as_of=self.NOW,
            ).slug,
            "ordinary",
        )

    def test_unavailable_analytics_uses_last_database_selection(self) -> None:
        stored = self.article("stored", 300, featured=True)
        newest = self.article("newer", 120)
        self.assertEqual(
            select_auto_featured_article([stored, newest], None, as_of=self.NOW).slug,
            "stored",
        )

    def test_zero_reads_defaults_to_latest_published(self) -> None:
        previous = self.article("previous", 320)
        latest = self.article("latest", 100)
        self.assertEqual(
            select_auto_featured_article([previous, latest], {}, as_of=self.NOW).slug,
            "latest",
        )

    def test_empty_or_unpublished_catalog_has_no_feature(self) -> None:
        self.assertIsNone(select_auto_featured_article([], {}, as_of=self.NOW))
        self.assertIsNone(
            select_auto_featured_article(
                [CmsArticle(slug="draft", status="draft")], {}, as_of=self.NOW,
            )
        )

    def test_legacy_essays_participate_in_public_readership_list(self) -> None:
        legacy = self.article("legacy", 300, legacy_key="investable_portfolio", featured=True)
        newer = self.article("newer", 150)
        landing = (
            '<article class="featured-thinking"><h2>Fallback</h2></article>'
            '<section class="section white"><div class="container"><div class="head">'
            '<div><p class="eyebrow">More leadership questions</p>'
            '<section class="section paper">'
        )
        with patch("site_cms.fetch_published_articles", return_value=(newer, legacy)), \
             patch("site_cms._public_reads_or_none", return_value={"legacy": 54, "newer": 12}):
            html = inject_cms_landing(landing)
        self.assertIn("Legacy", html.title())
        self.assertIn("cms_article_open", html)


if __name__ == "__main__":
    unittest.main()
