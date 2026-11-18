"""Homepage stays scannable and retains the approved navigation and references."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeGridLayoutTests(unittest.TestCase):
    def test_home_uses_one_featured_case_and_three_short_supporting_cards(self):
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        evidence = (ROOT / "src/portfolio_operating_evidence.py").read_text(encoding="utf-8")
        self.assertIn("{home_evidence()}", home)
        self.assertIn('id="leadership-in-practice"', evidence)
        section = evidence.split('def home_evidence()', 1)[1].split('def impact_evidence()', 1)[0]
        self.assertEqual(section.count('<article class="card"'), 4)
        self.assertIn("Customer Interview Analyzer", section)
        self.assertIn("was not scaled", section)
        self.assertIn('href="?page=impact#customer-interview-analyzer"', section)
        self.assertNotIn("claim of a fully scaled operating model", section)

    def test_navigation_and_closing_contact_are_preserved(self):
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        self.assertIn("{home_pathways()}", home)
        self.assertIn("{home_whats_new()}", home)
        self.assertIn("{home_featured_article(instant=True)}", home)
        for destination in ("impact", "ai-data-governance"):
            self.assertIn(f'href="?page={destination}"', home)
        self.assertIn("Download CV ↓", home)
        self.assertIn('id="leadership-references"', impact)
        self.assertEqual(impact.count('<article class="principle">'), 2)
        self.assertIn('{portfolio_next_navigation("impact")}', impact)


if __name__ == "__main__":
    unittest.main()
