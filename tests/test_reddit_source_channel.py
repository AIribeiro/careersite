"""Regression: named Reddit traffic must not be hidden under Other social."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_legacy_signal_model import channel_label, channel_rollup
from portfolio_public_attribution import channel_role_cohorts


class RedditSourceChannelTests(unittest.TestCase):
    def test_public_source_labels_keep_reddit_separate(self):
        for source in ("reddit", "Reddit", "reddit.com",
                       "reddit?utm_campaign=thinking_articles"):
            with self.subTest(source=source):
                self.assertEqual(channel_label(source), "Reddit")
        self.assertEqual(channel_label("social"), "Other social")
        self.assertEqual(channel_label("bluesky"), "Other social")
        self.assertEqual(channel_label("instagram"), "Other social")

    def test_reddit_rollup_reallocates_but_never_duplicates_sessions(self):
        rows = [
            {"attribution_source": "reddit", "sessions": 2,
             "engaged_sessions": 1, "article_sessions": 1},
            {"attribution_source": "Reddit?role=thinking", "sessions": 3,
             "engaged_sessions": 2, "article_sessions": 2},
            {"attribution_source": "social", "sessions": 4},
            {"attribution_source": "bluesky", "sessions": 5},
            {"attribution_source": "linkedin", "sessions": 6},
        ]
        result = channel_rollup(rows)
        self.assertEqual(sum(row["sessions"] for row in result), 20)
        counts = {row["Channel"]: row["sessions"] for row in result}
        self.assertEqual(counts["Reddit"], 5)
        self.assertEqual(counts["Other social"], 9)
        self.assertEqual(counts["LinkedIn"], 6)
        roles = channel_role_cohorts([
            {"attribution_source": "reddit", "attribution_role": "article",
             "sessions": 2},
        ])
        self.assertEqual(roles[0]["Channel"], "Reddit")

    def test_legacy_overview_uses_the_same_reddit_split(self):
        from page_public_legacy_insights import _source_channel, _channel_rows

        self.assertEqual(_source_channel("reddit"), "Reddit")
        self.assertEqual(_source_channel("reddit?utm_campaign=thinking_articles"),
                         "Reddit")
        self.assertEqual(_source_channel("social"), "Other social")
        rows = _channel_rows([
            {"attribution_source": "reddit", "sessions": 2},
            {"attribution_source": "Reddit", "sessions": 1},
            {"attribution_source": "bluesky", "sessions": 3},
            {"attribution_source": "linkedin", "sessions": 4},
        ])
        self.assertEqual(sum(row["sessions"] for row in rows), 10)
        counts = {row["channel"]: row["sessions"] for row in rows}
        self.assertEqual(counts["Reddit"], 3)
        self.assertEqual(counts["Other social"], 3)
        self.assertEqual(counts["LinkedIn"], 4)


if __name__ == "__main__":
    unittest.main()
