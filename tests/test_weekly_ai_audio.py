from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from site_cms import CmsArticle
from weekly_ai_audio import (
    AUDIO_DIR, audio_player_html, audio_url, mp3_path, prepare_spoken_script, valid_slug,
)
from thinking_weekly_brief import inject_weekly_brief_landing, render_weekly_brief_article

PUBLISHED_HTML = """
<p>Five important developments for enterprises.</p>
<p><strong>1. Research and work.</strong> Research found changing jobs. <a href="https://brookings.edu/example">Brookings</a></p>
<p><strong>2. Industrial agents.</strong> AI moves into machines. <a href="https://microsoft.com/example">Microsoft</a></p>
<p><strong>3. Agent identity.</strong> A shared proposal emerged. <a href="https://qz.com/example">Quartz</a></p>
<p><strong>Leadership signal:</strong> Governance determines accountability in workflows.</p>
"""


def weekly_article(slug: str = "weekly-ai-2026-10-11") -> CmsArticle:
    return CmsArticle(
        id=slug, slug=slug, title="WEEKLY AI — Verified Briefing",
        content_html=PUBLISHED_HTML, kind="Weekly Brief", category="Weekly AI",
        status="published", published_at="2026-10-11T10:00:00Z",
    )


class WeeklyAiAudioTests(unittest.TestCase):
    def test_rejects_traversal_and_other_slug_types(self):
        self.assertFalse(valid_slug("../secrets"))
        self.assertFalse(valid_slug("random-article"))
        self.assertIsNone(mp3_path("../secrets"))
        self.assertEqual(audio_player_html("../secrets"), "")

    def test_spoken_script_drops_publisher_links_not_facts(self):
        script = prepare_spoken_script("weekly-ai-2026-10-19", PUBLISHED_HTML, week=42, iso_year=2026)
        self.assertIn("Welcome to Weekly A I", script)
        self.assertIn("Swedish week 42", script)
        self.assertIn("Research found changing jobs", script)
        self.assertIn("governance determines accountability", script.lower())
        self.assertIn("my A I and Data Portfolio", script)
        self.assertIn("From my experience leading enterprise A I and data initiatives", script)
        self.assertEqual(script.count("my A I and Data Portfolio"), 1)
        self.assertNotIn("https://", script)
        self.assertNotIn("brookings.edu", script)
        self.assertNotIn("Quartz", script)

    def test_editorial_pilot_is_spoken_first_and_short(self):
        script = prepare_spoken_script(
            "weekly-ai-2026-10-11", PUBLISHED_HTML, week=41, iso_year=2026
        )
        self.assertIn("Swedish week forty-one", script)
        self.assertIn("Harvard Business Review", script)
        self.assertGreaterEqual(len(script.split()), 95)
        self.assertLessEqual(len(script.split()), 260)

    def test_missing_audio_yields_no_false_play_button(self):
        with patch("weekly_ai_audio.AUDIO_DIR", Path("/nonexistent-weekly-ai-static-audio")):
            self.assertIsNone(audio_url("weekly-ai-2026-10-11"))
            self.assertEqual(audio_player_html("weekly-ai-2026-10-11"), "")
            article_html = render_weekly_brief_article(weekly_article(), "<footer>Share</footer>")
            self.assertNotIn("<audio controls", article_html)

    def test_audio_exists_renders_native_player_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            slug = "weekly-ai-2026-10-11"
            (folder / f"{slug}.mp3").write_bytes(b"ID3" + b"\x00" * 5000)
            with patch("weekly_ai_audio.AUDIO_DIR", folder):
                player = audio_player_html(slug)
                self.assertIn('id="weekly-ai-audio"', player)
                self.assertIn('type="audio/mpeg"', player)
                self.assertIn("/weekly-ai-audio/weekly-ai-2026-10-11.mp3", player)
                self.assertEqual(player.count("<audio "), 1)
                page = render_weekly_brief_article(weekly_article(), "")
                self.assertIn("Listen to the Weekly AI news briefing", page)
                self.assertEqual(page.count("<audio controls"), 1)
                landing = inject_weekly_brief_landing("<main>Thinking</main>", [weekly_article()])
                self.assertIn("Listen · audio", landing)
                self.assertIn("#weekly-ai-audio", landing)

    def test_app_routes_validate_audio_file(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "app.py").read_text()
        self.assertIn('Route("/weekly-ai-audio/{slug}.mp3"', source)
        self.assertIn("mp3_path(slug)", source)
        self.assertIn('media_type="audio/mpeg"', source)

    def test_pipeline_is_idempotent_and_provider_secret_is_optional(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "scripts/generate_weekly_ai_audio.py").read_text()
        wf = (root / ".github/workflows/weekly-ai-audio.yml").read_text()
        self.assertIn("if dest.exists() and dest.stat().st_size > 1024", script)
        self.assertIn('GOOGLE_TTS_SERVICE_ACCOUNT_JSON', script)
        self.assertIn('en-US-AndrewNeural', wf)
        self.assertIn('schedule:', wf)
        self.assertIn('workflow_dispatch:', wf)


if __name__ == "__main__":
    unittest.main()
