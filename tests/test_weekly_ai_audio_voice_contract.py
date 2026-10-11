"""Future WEEKLY AI audio cannot silently revert to HTML readout."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import generate_weekly_ai_audio as generator


def _episode_script() -> str:
    intro = (
        "Welcome to Weekly A I, a one-minute briefing from my A I and Data Portfolio. "
        "Here is what matters beyond the headlines this week. "
    )
    story = (
        "Enterprise teams are using intelligent systems to improve everyday decisions "
        "while strengthening governance and operational accountability. "
    )
    outro = (
        "From my experience leading enterprise A I and data initiatives, "
        "the takeaway is that reliable progress depends on ownership, adoption "
        "and measurable value. Original sources are linked in the written edition."
    )
    return intro + story * 10 + outro


class WeeklyAudioVoiceContractTests(unittest.TestCase):
    def test_future_edition_requires_a_persisted_spoken_first_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug = "weekly-ai-2026-10-19"
            article = {"slug": slug, "content_html": "<p>Three sourced developments</p>"}
            with patch.object(generator, "ROOT", root), patch.object(
                generator, "AUDIO_DIR", root / "static" / "weekly-ai"
            ), patch.object(
                generator, "prepare_spoken_script", return_value=_episode_script()
            ) as prepared:
                with self.assertRaisesRegex(ValueError, "Editorial audio script missing"):
                    generator.publish(article, dry_run=True)
                prepared.assert_not_called()

    def test_future_edition_must_preserve_single_portfolio_reference_and_leadership_voice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            editorial = root / "data" / "weekly_ai_audio_scripts"
            editorial.mkdir(parents=True)
            slug = "weekly-ai-2026-10-19"
            article = {"slug": slug, "content_html": "<p>News</p>"}
            with patch.object(generator, "ROOT", root):
                missing_personality = " ".join(["AI is changing business workflows"] * 37)
                (editorial / (slug + ".txt")).write_text(missing_personality)
                with self.assertRaisesRegex(ValueError, "portfolio once"):
                    generator.publish(article, dry_run=True)

                text = _episode_script()
                (editorial / (slug + ".txt")).write_text(text)
                with patch.object(generator, "prepare_spoken_script", return_value=text):
                    self.assertFalse(generator.publish(article, dry_run=True))

                with patch.object(generator, "prepare_spoken_script", return_value=text + " altered"):
                    with self.assertRaisesRegex(ValueError, "does not match approved"):
                        generator.publish(article, dry_run=True)

    def test_week_41_remains_the_canonical_reference_and_is_not_reissued(self):
        repository = Path(__file__).resolve().parents[1]
        script = (repository / "data" / "weekly_ai_audio_scripts"
                  / "weekly-ai-2026-10-11.txt").read_text(encoding="utf-8")
        self.assertIn("what matters beyond the headlines", script)
        self.assertEqual(script.count("my A I and Data Portfolio"), 1)
        self.assertIn("From my experience leading enterprise A I and data initiatives", script)


if __name__ == "__main__":
    unittest.main()
