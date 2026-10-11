from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from weekly_ai_audio import audio_player_html, audio_url
from scripts.normalize_weekly_ai_audio import _probe, normalize_audio


class WeeklyAiAudioDeliveryTests(unittest.TestCase):
    def test_html_has_absolute_audio_sources_and_direct_open_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            slug = "weekly-ai-2026-10-11"
            (Path(folder) / (slug + ".mp3")).write_bytes(b"ID3" + b"0" * 5000)
            with patch("weekly_ai_audio.AUDIO_DIR", Path(folder)):
                self.assertEqual(
                    audio_url(slug),
                    f"https://jairribeiro-ai.streamlit.app/weekly-ai-audio/{slug}.mp3",
                )
                html = audio_player_html(slug)
                self.assertIn('preload="metadata"', html)
                self.assertIn("https://jairribeiro-ai.streamlit.app/weekly-ai-audio/", html)
                self.assertIn("https://raw.githubusercontent.com/AIribeiro/careersite/main/static/weekly-ai/", html)
                self.assertIn("Audio not playing? Open the MP3 directly", html)
                self.assertEqual(html.count("<audio "), 1)
                self.assertEqual(html.count("<source "), 2)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not available")
    def test_mp3_is_normalized_to_mpeg_one_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "weekly-ai-2026-10-11.mp3"
            subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                 "-t", "0.8", "-c:a", "libmp3lame", "-b:a", "48k",
                 str(dest)],
                check=True,
            )
            self.assertEqual(int(_probe(dest)["sample_rate"]), 24000)
            self.assertTrue(normalize_audio(dest))
            meta = _probe(dest)
            self.assertEqual(meta["codec_name"], "mp3")
            self.assertEqual(int(meta["sample_rate"]), 44100)
            self.assertEqual(int(meta["channels"]), 1)
            content = dest.read_bytes()
            self.assertGreater(len(content), 4000)
            self.assertFalse(normalize_audio(dest))
            self.assertEqual(content, dest.read_bytes())


if __name__ == "__main__":
    unittest.main()
