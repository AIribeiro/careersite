"""Validate the Friday WEEKLY AI change without altering historical week ranges."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import date
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from thinking_weekly_brief import edition_week, sorted_editions, edition_label


def article(slug: str, published_at: str = "2026-10-23T19:00:00Z"):
    return SimpleNamespace(
        slug=slug, status="published", category="Weekly AI",
        kind="Weekly Brief", published_at=published_at,
        created_at=published_at, updated_at=published_at,
    )


class FridayWeeklyAiCycleTests(unittest.TestCase):
    def test_first_friday_edition_uses_monday_friday_coverage(self):
        a = article("weekly-ai-2026-10-23")
        self.assertEqual(
            edition_week(a),
            (2026, 43, date(2026, 10, 19), date(2026, 10, 23)),
        )
        self.assertEqual(edition_label(a), "Week 43 · 2026")

    def test_historical_monday_and_sunday_ranges_are_unchanged(self):
        self.assertEqual(
            edition_week(article("weekly-ai-2026-10-19")),
            (2026, 42, date(2026, 10, 12), date(2026, 10, 18)),
        )
        self.assertEqual(
            edition_week(article("weekly-ai-2026-10-11")),
            (2026, 41, date(2026, 10, 5), date(2026, 10, 11)),
        )

    def test_friday_crosses_iso_week_year_correctly(self):
        self.assertEqual(
            edition_week(article("weekly-ai-2027-01-01")),
            (2026, 53, date(2026, 12, 28), date(2027, 1, 1)),
        )

    def test_latest_friday_is_featured_and_archive_keeps_prior_editions(self):
        a = article("weekly-ai-2026-10-23")
        b = article("weekly-ai-2026-10-19")
        c = article("weekly-ai-2026-10-11")
        output = sorted_editions([b, c, a])
        self.assertEqual([x.slug for x in output], [a.slug, b.slug, c.slug])


if __name__ == "__main__":
    unittest.main()
