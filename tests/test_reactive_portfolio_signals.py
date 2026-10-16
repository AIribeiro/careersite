"""Prioritization, temporal responsiveness and uncertainty in public signals."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_signal_brief import ranked_portfolio_signals


def report(pages_now=271, pages_prior=103, articles_now=35, articles_prior=45,
           *, weekly=18, unknown=194, depth=18, recent=True):
    return {
        "quality": {"page_views": pages_now, "article_views": articles_now},
        "period_comparison": [
            {"kind": "page", "content": "home", "current_views": max(0, pages_now-50),
             "previous_views": max(0, pages_prior-30)},
            {"kind": "page", "content": "thinking", "current_views": 20,
             "previous_views": 1},
            {"kind": "page", "content": "impact", "current_views": 30,
             "previous_views": max(0, pages_prior - max(0, pages_prior-30)-1)},
            {"kind": "article", "content": "weekly-ai-2026-10-11",
             "current_views": weekly, "previous_views": 0},
            {"kind": "article", "content": "other", "current_views": articles_now-weekly,
             "previous_views": articles_prior},
        ],
        "performance": [
            {"kind": "article", "content": "weekly-ai-2026-10-11", "views": weekly,
             "sessions": weekly, "engaged_sessions": 6,
             "depth_measured_sessions": min(depth, weekly), "later_portfolio_sessions": 0},
            {"kind": "article", "content": "other", "views": articles_now-weekly,
             "sessions": articles_now-weekly, "engaged_sessions": 4,
             "depth_measured_sessions": 5, "later_portfolio_sessions": 0},
        ],
        "campaigns": [
            {"channel": "direct/unknown", "sessions": unknown},
            {"channel": "whatsapp", "sessions": 22},
            {"channel": "linkedin", "sessions": 15},
        ],
    }


RECENT_ARTICLES = [
    {"Slug": "weekly-ai-2026-10-11", "Content": "WEEKLY AI", "Views": 18, "Sessions": 18},
    {"Slug": "other", "Content": "Other essay", "Views": 17, "Sessions": 17},
]
RECENT_PAGES = [
    {"Slug": "home", "Content": "Home", "Views": 221, "Sessions": 221},
    {"Slug": "thinking", "Content": "Thinking", "Views": 20, "Sessions": 19},
    {"Slug": "impact", "Content": "Impact", "Views": 30, "Sessions": 30},
]


def ranked(selected, window="7d", recent=None):
    return ranked_portfolio_signals(
        selected, RECENT_PAGES, RECENT_ARTICLES,
        window=window, recent_report=recent,
        recent_pages=RECENT_PAGES if recent else None,
        recent_articles=RECENT_ARTICLES if recent else None,
    )


class ReactivePortfolioSignalTests(unittest.TestCase):
    def test_divergence_outweighs_static_homepage_dominance(self):
        top, more, diagnostics = ranked(report())
        self.assertEqual(top[0].key, "split_movement")
        self.assertIn("page views rose 163%", top[0].message)
        self.assertIn("article views fell 22%", top[0].message)
        self.assertIn("271 vs 103", top[0].evidence)
        self.assertIn("35 vs 45", top[0].evidence)
        self.assertNotIn("Home leads", " ".join(x.message for x in top))

    def test_recent_article_leads_current_reading_and_has_zero_prior(self):
        top, _, _ = ranked(report())
        signal = next(x for x in top if x.key == "current_reading_leader")
        self.assertIn("WEEKLY AI", signal.title)
        self.assertIn("51%", signal.message)
        self.assertIn("newly observed interest", signal.message)
        self.assertNotIn("growth rate of infinity", signal.message)

    def test_historical_window_prefers_verified_recent_pulse(self):
        lifetime = report(933, 0, 289, 0, weekly=18, unknown=719, depth=2)
        recent = report()
        top, more, diagnostics = ranked(lifetime, "365d", recent=recent)
        self.assertEqual(top[0].key, "split_movement")
        self.assertIn("past 7 days", top[0].message)
        self.assertTrue(any("seven-day vs preceding" in x for x in diagnostics))
        self.assertFalse(any("Movement cannot yet be assessed" in x.title
                             for x in top + more))

    def test_changes_when_direction_reverses(self):
        shifted = report(pages_now=60, pages_prior=120,
                         articles_now=70, articles_prior=30,
                         weekly=28, unknown=0)
        top, _, _ = ranked(shifted)
        self.assertEqual(top[0].key, "split_movement")
        self.assertIn("page views fell 50%", top[0].message)
        self.assertIn("article views rose 133%", top[0].message)

    def test_no_fake_movement_from_missing_baselines(self):
        selected = report(933, 0, 289, 0)
        top, more, diagnostics = ranked(selected, "365d")
        self.assertFalse(any(x.key.endswith("movement") for x in top + more))
        self.assertTrue(any("insufficient baseline" in x for x in diagnostics))

    def test_source_unknown_reveals_real_attribution_limitation(self):
        top, more, _ = ranked(report(pages_now=0, pages_prior=0,
                                    articles_now=8, articles_prior=0, weekly=8))
        source = next(x for x in top + more if x.key == "attribution_gap")
        self.assertIn("direct or unknown", source.message)
        self.assertIn("194", source.evidence)
        self.assertIn("channel-tagged", source.next_check)

    def test_low_traffic_is_not_exaggerated(self):
        empty = {"period_comparison": [], "performance": [], "campaigns": []}
        top, more, caveats = ranked(empty)
        self.assertEqual(top[0].key, "limited_activity")
        self.assertFalse(more)
        self.assertTrue(caveats)

    def test_depth_coverage_improvement_not_an_engagement_failure(self):
        lifetime = report(933, 0, 289, 0, weekly=18, unknown=0, depth=0)
        recent = report(271,103,35,45,weekly=18,unknown=0,depth=18)
        recent["performance"][1]["depth_measured_sessions"] = 17
        top, more, _ = ranked(lifetime, "365d", recent=recent)
        coverage = next(x for x in top + more if x.key == "coverage_improving")
        self.assertIn("100%", coverage.message)
        self.assertIn("unmeasured", coverage.next_check)


if __name__ == "__main__":
    unittest.main()
