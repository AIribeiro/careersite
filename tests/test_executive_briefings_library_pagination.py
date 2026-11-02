"""Regression checks for the Executive AI Briefings catalog, not article readers."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st
import page_executive_briefings as briefings


def published_items(count: int):
    return tuple(
        SimpleNamespace(
            slug=f"briefing-{number}",
            title=f"Briefing {number}",
            subtitle=f"Description for briefing {number}",
            excerpt="",
            published_label=f"November {number}, 2026",
            read_minutes=5,
            published_at=f"2026-11-{number:02d}T09:00:00",
            updated_at="",
        )
        for number in range(1, count + 1)
    )


def render(count: int, page: str = "1") -> str:
    with (
        patch.object(briefings, "published_briefings", return_value=published_items(count)),
        patch.object(briefings, "article_relative_url",
                     side_effect=lambda article: f"?page=briefing&article={article.slug}"),
        patch.object(st, "query_params", {"briefings_page": page}),
    ):
        return briefings.executive_briefings()


class BriefingLibraryPaginationTests(unittest.TestCase):
    def test_four_briefings_all_receive_equal_cards(self):
        html = render(4)
        self.assertEqual(html.count('data-hq-event="briefings_article_open"'), 4)
        self.assertNotIn('<div class="be-feature">', html)
        self.assertNotIn('data-hq-event="briefings_featured_open"', html)
        self.assertIn('aria-label="Read Briefing 4"', html)
        self.assertIn("04 PUBLISHED BRIEFINGS", html)
        self.assertNotIn('class="be-pagination"', html)

    def test_fewer_than_four_are_capped_at_two(self):
        first = render(3, "1")
        second = render(3, "2")
        self.assertEqual(first.count('data-hq-event="briefings_article_open"'), 2)
        self.assertEqual(second.count('data-hq-event="briefings_article_open"'), 1)
        self.assertIn("Page 1 of 2", first)
        self.assertIn("Page 2 of 2", second)
        self.assertIn("briefings_page=2", first)
        self.assertIn('aria-label="Read Briefing 1"', second)

    def test_more_than_four_show_four_per_page(self):
        first = render(9, "1")
        second = render(9, "2")
        third = render(9, "3")
        self.assertEqual(first.count('data-hq-event="briefings_article_open"'), 4)
        self.assertEqual(second.count('data-hq-event="briefings_article_open"'), 4)
        self.assertEqual(third.count('data-hq-event="briefings_article_open"'), 1)
        self.assertIn("Page 3 of 3", third)
        self.assertIn('aria-current="page"', third)

    def test_invalid_and_out_of_range_pages_are_clamped(self):
        self.assertIn('aria-label="Read Briefing 5"', render(5, "invalid"))
        self.assertIn('aria-label="Read Briefing 5"', render(5, "-2"))
        self.assertIn('aria-label="Read Briefing 1"', render(5, "999"))
        self.assertNotIn('aria-label="Read Briefing 5"', render(5, "999"))

    def test_empty_library_is_safe(self):
        html = render(0)
        self.assertIn("The library is being prepared.", html)
        self.assertNotIn('class="be-pagination"', html)


if __name__ == "__main__":
    unittest.main()
