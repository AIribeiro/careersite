from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeGridLayoutTests(unittest.TestCase):
    def test_home_uses_distinct_grids_for_focus_cases_and_references(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")

        focus = home.split('<p class="eyebrow">Leadership focus</p>', 1)[1]
        focus = focus.split('<p class="eyebrow">Selected experience</p>', 1)[0]
        self.assertIn('<div class="grid3 home-focus-grid">', focus)
        self.assertEqual(focus.count('<article class="card">'), 3)
        self.assertIn("Enterprise AI strategy &amp; scaling", focus)
        self.assertIn("Data &amp; Analytics leadership", focus)
        self.assertIn("Governance &amp; operating model", focus)
        self.assertIn("View selected experience →", focus)
        self.assertIn("Governance evidence →", focus)
        self.assertIn("Credentials &amp; verification →", focus)

        cases = home.split('<p class="eyebrow">Selected experience</p>', 1)[1]
        cases = cases.split('{framework_teaser()}', 1)[0]
        self.assertIn(
            '<div class="thoughts home-case-grid">',
            cases,
        )
        self.assertEqual(cases.count('<article class="card">'), 3)

        hero = home.split('<section class="hero">', 1)[1]
        hero = hero.split('<section class="section white">', 1)[0]
        self.assertIn("Explore my leadership experience →", hero)
        self.assertIn("AI &amp; Data Governance →", hero)
        self.assertIn("Download CV ↓", hero)
        self.assertNotIn("Contact me", hero)

        journey = home.split('data-analytics-section="home-choose-your-path"', 1)[1]
        journey = journey.split('<p class="eyebrow">Leadership focus</p>', 1)[0]
        self.assertEqual(journey.count('class="journey-card"'), 3)
        for destination in ("impact", "ai-data-governance", "thinking"):
            self.assertIn(f'href="?page={destination}"', journey)
        for event in ("journey_home_impact", "journey_home_governance",
                      "journey_home_thinking"):
            self.assertIn(f'data-hq-event="{event}"', journey)
        self.assertIn("What I’ve led", journey)
        self.assertIn("How I make AI work", journey)
        self.assertIn("How I think", journey)

        self.assertNotIn('<p class="eyebrow">Recurring questions</p>', home)

        references = home.split('<p class="eyebrow">References</p>', 1)[1]
        references = references.split('<section class="cta">', 1)[0]
        self.assertIn('<div class="principles">', references)
        self.assertEqual(references.count('<article class="principle">'), 2)


if __name__ == "__main__":
    unittest.main()
