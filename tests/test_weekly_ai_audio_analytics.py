from __future__ import annotations

from pathlib import Path
import unittest

from page_weekly_ai_analytics import weekly_ai_report
from site_cms import CmsArticle

ROOT = Path(__file__).resolve().parents[1]


def issue(slug="weekly-ai-2026-10-11"):
    return CmsArticle(
        id=slug, slug=slug, title="WEEKLY AI — Pilot",
        category="Weekly AI", kind="Weekly Brief", status="published",
        published_at="2026-10-11T10:00:00Z", excerpt="A credible weekly summary."
    )


class WeeklyAudioAnalyticsTests(unittest.TestCase):
    def test_audio_counts_are_a_non_additive_subset_of_article_readership(self):
        content_data = {
            "performance": [{"kind": "article", "content": "weekly-ai-2026-10-11",
                             "sessions": 11, "views": 15, "engaged_sessions": 8}],
            "section_reach": [], "article_cards": [], "cta_placements": []
        }
        audio = {
            "started_sessions": 6, "completed_sessions": 4,
            "edition_starts": 6, "edition_completions": 4,
            "estimated_listened_seconds": 345.6,
            "editions": [
                {"slug": "weekly-ai-2026-10-11", "starts": 6,
                 "progress_25": 6, "progress_50": 5, "progress_75": 4,
                 "completions": 4, "estimated_listened_seconds": 345.6}
            ],
        }
        report = weekly_ai_report(content_data, [issue()], audio)
        row = report["rows"][0]
        self.assertEqual(report["reader_sessions"], 11)
        self.assertEqual(report["reader_views"], 15)
        self.assertEqual(report["audio_listening_sessions"], 6)
        self.assertEqual(report["audio_completed_sessions"], 4)
        self.assertEqual(report["audio_edition_starts"], 6)
        self.assertEqual(report["audio_edition_completions"], 4)
        self.assertEqual(report["audio_estimated_minutes"], 5.8)
        self.assertEqual(row["Week"], "Week 41 · 2026")
        self.assertEqual(row["Audio starts"], 6)
        self.assertEqual(row["Audio reached 50%"], 5)
        self.assertEqual(row["Audio completions"], 4)
        self.assertEqual(row["Audio completion rate"], "66.7%")

    def test_missing_rpc_does_not_pretend_there_were_zero_listeners(self):
        report = weekly_ai_report(
            {"performance": [], "section_reach": [], "article_cards": [], "cta_placements": []},
            [issue()], None,
        )
        self.assertFalse(report["audio_available"])
        self.assertEqual(report["rows"][0]["Audio starts"], 0)
        self.assertIn("audio_available", report)

    def test_audio_player_has_an_explicit_instrumentation_slug(self):
        src = (ROOT / "src" / "weekly_ai_audio.py").read_text()
        self.assertIn("data-weekly-ai-audio", src)
        self.assertIn('data-analytics-section="weekly-ai-audio"', src)

    def test_browser_telemetry_is_session_scoped_and_seek_protected(self):
        script = (ROOT / "src" / "site_weekly_audio_telemetry.py").read_text()
        for marker in (
            "doc.addEventListener('playing'",
            "doc.addEventListener('timeupdate'",
            "doc.addEventListener('ended'",
            "doc.addEventListener('seeked'",
        ):
            if marker == "doc.addEventListener('seeked'":
                self.assertIn("'seeked'", script)
            else:
                self.assertIn(marker, script)
        self.assertIn("jair_hq_session_v1", script)
        self.assertIn("data-weekly-ai-audio", script)
        self.assertIn("advance <= elapsed * speed + 0.7", script)
        self.assertIn("state.listenedMs >= durationMs * 0.85", script)
        self.assertIn("!state.milestones[percent]", script)
        self.assertIn("!state.completed", script)

    def test_events_reuse_existing_analytics_context_and_are_not_page_views(self):
        shared = (ROOT / "src" / "site_analytics.py").read_text()
        main = (ROOT / "main.py").read_text()
        for event in ["audio_start", "audio_progress", "audio_complete"]:
            self.assertIn(f'"{event}"', shared)
        self.assertIn("win.__jairAnalyticsSend(name", (ROOT / "src" / "site_weekly_audio_telemetry.py").read_text())
        self.assertIn("inject_weekly_audio_telemetry()", main)
        self.assertIn("careersite_weekly_audio_analytics_v1", (ROOT / "src" / "page_weekly_ai_analytics.py").read_text())

    def test_future_narration_has_portfolio_credit_and_first_person_leadership(self):
        src = (ROOT / "src" / "weekly_ai_audio.py").read_text()
        self.assertIn("from my A I and Data Portfolio", src)
        self.assertIn("From my experience leading enterprise A I and data initiatives", src)
        pilot = (ROOT / "data" / "weekly_ai_audio_scripts" / "weekly-ai-2026-10-11.txt").read_text()
        self.assertNotIn("from my A I and Data Portfolio", pilot)


if __name__ == "__main__":
    unittest.main()
