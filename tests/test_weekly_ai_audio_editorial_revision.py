from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import generate_weekly_ai_audio as generator


class WeeklyAudioEditorialRevisionTests(unittest.TestCase):
    def test_approved_editorial_change_regenerates_once_and_preserves_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "static" / "weekly-ai"
            editorial = root / "data" / "weekly_ai_audio_scripts"
            archive.mkdir(parents=True)
            editorial.mkdir(parents=True)
            slug = "weekly-ai-2026-10-11"
            week40 = "weekly-ai-2026-10-04"
            mp3 = archive / (slug + ".mp3")
            transcript = archive / (slug + ".txt")
            mp3.write_bytes(b"ID3" + b"o" * 6000)
            transcript.write_text("Previously published audio script\n", encoding="utf-8")
            old_sha = mp3.read_bytes()

            # An editorial revision is only permitted for an override that
            # exists explicitly in the repository, never for CMS edits alone.
            (editorial / (slug + ".txt")).write_text("New approved version", encoding="utf-8")
            new_narration = " ".join(["Relevant enterprise AI developments and decisions."] * 24)
            next_mp3 = b"ID3" + b"n" * 8000
            article = {"slug": slug, "content_html": "<p>News</p>"}
            with (patch.object(generator, "ROOT", root),
                  patch.object(generator, "AUDIO_DIR", archive),
                  patch.object(generator, "prepare_spoken_script", return_value=new_narration),
                  patch.object(generator, "_google_audio", return_value=next_mp3) as synth,
                  patch.dict(os.environ, {"GOOGLE_TTS_SERVICE_ACCOUNT_JSON": "testing"})):
                self.assertTrue(generator.publish(article, dry_run=False))
                self.assertNotEqual(mp3.read_bytes(), old_sha)
                self.assertEqual(mp3.read_bytes(), next_mp3)
                self.assertEqual(transcript.read_text().strip(), new_narration)
                self.assertFalse(generator.publish(article, dry_run=False))
                self.assertEqual(synth.call_count, 1)

                # Edited CMS facts alone cannot mutate published audio.
                w40_file = archive / (week40 + ".mp3")
                w40_file.write_bytes(b"ID3" + b"q" * 6000)
                (archive / (week40 + ".txt")).write_text("Former version")
                original = w40_file.read_bytes()
                self.assertFalse(generator.publish({"slug": week40, "content_html": "<p>Changed</p>"}, dry_run=False))
                self.assertEqual(w40_file.read_bytes(), original)
                self.assertEqual(synth.call_count, 1)

    def test_week41_editorial_includes_single_discreet_portfolio_reference(self):
        path = Path(__file__).resolve().parents[1] / "data" / "weekly_ai_audio_scripts" / "weekly-ai-2026-10-11.txt"
        script = path.read_text(encoding="utf-8")
        self.assertGreaterEqual(len(script.split()), 95)
        self.assertLessEqual(len(script.split()), 260)
        self.assertEqual(script.count("my A I and Data Portfolio"), 1)
        self.assertIn("what matters beyond the headlines", script)
        self.assertIn("From my experience leading enterprise A I and data initiatives", script)
        self.assertNotIn("http", script.lower())


if __name__ == "__main__":
    unittest.main()
