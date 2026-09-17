from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicCopyGuardTests(unittest.TestCase):
    def test_public_pages_use_audience_facing_storytelling(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        lenses = (ROOT / "src/site_lenses.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        thinking = (ROOT / "src/page_thinking.py").read_text(encoding="utf-8")

        forbidden = (
            "This page reorganizes selected evidence around one hiring context.",
            "It is not a separate CV or a claim to a different professional identity.",
            "They are intended to show the judgment behind the CV bullet point.",
            "Where I create the most value.",
            "The six-month mandate was not about claiming a company-wide transformation.",
            "I am not interested in publishing for volume.",
            "If it does not change the conversation, it is mostly content.",
        )
        public_copy = home + "\n" + lenses + "\n" + impact + "\n" + thinking
        for phrase in forbidden:
            self.assertNotIn(phrase, public_copy)

        self.assertIn(
            "I bring enterprise AI, Data &amp; Analytics experience across strategy, portfolio choices, governance, adoption and operating-model decisions",
            lenses,
        )
        self.assertIn(
            "Across these roles, my work has centered on making AI decisions executable",
            impact,
        )
        self.assertIn(
            "The mandate was to put clearer foundations under an emerging AI & Data capability",
            impact,
        )
        self.assertIn(
            "a more consistent basis for comparing opportunities, exposing assumptions earlier and deciding which ideas were ready for deeper investment",
            impact,
        )
        self.assertIn(
            "I write selectively, usually when a recurring operating question is worth working through.",
            thinking,
        )
        self.assertIn(
            "Selected recommendations from people who worked with me in different roles and organizational contexts.",
            home,
        )


if __name__ == "__main__":
    unittest.main()
