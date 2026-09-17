from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImpactCaseConsistencyTests(unittest.TestCase):
    def test_home_uses_three_modern_cases_while_impact_keeps_ibm_as_foundation(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")

        home_expected = [
            "Volvo Group / Volvo Trucks",
            "MSX International",
            "Kimberly-Clark",
        ]

        home_section = home.split('<p class="eyebrow">Selected leadership cases</p>', 1)[1]
        home_section = home_section.split('<p class="eyebrow">Leadership focus</p>', 1)[0]

        home_positions = [home_section.index(f'<span class="org">{org}</span>') for org in home_expected]
        self.assertEqual(home_positions, sorted(home_positions))
        self.assertNotIn('<span class="org">IBM</span>', home_section)

        impact_positions = [impact.index(f'            "{org}",') for org in home_expected]
        self.assertEqual(impact_positions, sorted(impact_positions))
        self.assertEqual(impact.count("        case(\n"), 3)

        self.assertIn("Foundation · IBM", impact)
        self.assertIn("Where the business-translation thread started.", impact)
        self.assertIn("Cloud and AI Project Manager | IBM Watson Solution Designer", impact)
        self.assertIn("IBM Design Thinking", impact)
        self.assertIn("A foundation for the work that followed", impact)


if __name__ == "__main__":
    unittest.main()
