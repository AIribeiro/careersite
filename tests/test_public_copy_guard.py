from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicCopyGuardTests(unittest.TestCase):
    def test_role_lenses_and_impact_use_audience_facing_copy(self) -> None:
        lenses = (ROOT / "src/site_lenses.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")

        forbidden = (
            "This page reorganizes selected evidence around one hiring context.",
            "It is not a separate CV or a claim to a different professional identity.",
            "They are intended to show the judgment behind the CV bullet point.",
        )
        public_copy = lenses + "\n" + impact
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


if __name__ == "__main__":
    unittest.main()
