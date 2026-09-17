from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicCopyGuardTests(unittest.TestCase):
    def test_public_pages_use_audience_facing_storytelling(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        about = (ROOT / "src/page_about.py").read_text(encoding="utf-8")
        lenses = (ROOT / "src/site_lenses.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        thinking = (ROOT / "src/page_thinking.py").read_text(encoding="utf-8")
        thinking_landing = (ROOT / "src/thinking_landing.py").read_text(encoding="utf-8")

        forbidden = (
            "This page reorganizes selected evidence around one hiring context.",
            "It is not a separate CV or a claim to a different professional identity.",
            "They are intended to show the judgment behind the CV bullet point.",
            "Where I create the most value.",
            "The leadership problems I tend to work around.",
            "The six-month mandate was not about claiming a company-wide transformation.",
            "I am not interested in publishing for volume.",
            "If it does not change the conversation, it is mostly content.",
            "The value I try to add is not technical demonstration.",
            "I treat recognition as external validation of the work, not as a professional title.",
            "treated as external recognition rather than a professional title.",
            "The purpose is not publishing volume",
        )
        public_copy = home + "\n" + about + "\n" + lenses + "\n" + impact + "\n" + thinking + "\n" + thinking_landing
        for phrase in forbidden:
            self.assertNotIn(phrase, public_copy)

        self.assertIn(
            "I bring enterprise AI, Data &amp; Analytics experience across strategy, portfolio choices, governance, adoption and operating-model decisions",
            lenses,
        )
        self.assertIn(
            "What changed, what I was accountable for, and the trade-offs behind it.",
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
        self.assertIn(
            "Across these roles, the context changed but the underlying questions became increasingly connected",
            home,
        )
        self.assertIn("The enterprise AI problems that keep recurring.", home)
        self.assertIn("Director of Digital, Innovation &amp; Platforms", home)
        self.assertIn("Building the structures around AI &amp; Data", about)
        self.assertIn("Global Thought Leaders &amp; Influencers on Emerging Technology, 2023.", about)
        self.assertIn("Where the business-translation thread started.", impact)
        self.assertIn("Writing, speaking and research extend the operating perspective.", thinking)

        # Employability evidence should remain explicit rather than inferred.
        self.assertIn("1,500+ practitioners", home)
        self.assertIn("130,000+ interactions", home)
        self.assertIn("100+ AI sessions", impact)
        self.assertIn("1,000+ employees", impact)
        self.assertIn("measurable improvements in efficiency and cycle time", impact)
        self.assertIn("reporting directly to the Chief Data & Analytics Officer", impact)
        self.assertIn("Enterprise CoE mandate across strategy, operations, technology and business leaders", impact)
        self.assertIn("2026–2027 maturity roadmap", impact)
        self.assertIn("2026–2027 maturity roadmap", about)
        self.assertIn("Enterprise AI perspective", about)
        self.assertNotIn('<div class="flow">', about)
        self.assertIn("Start from a situation, not a theme", thinking_landing)
        self.assertIn("when the operating consequence is visible", thinking_landing)


if __name__ == "__main__":
    unittest.main()
