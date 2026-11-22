"""Homepage stays scannable and retains the approved navigation and references."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeGridLayoutTests(unittest.TestCase):
    def test_home_shows_four_equal_compact_linked_cases(self):
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        evidence = (ROOT / "src/portfolio_operating_evidence.py").read_text(encoding="utf-8")
        styles = (ROOT / "src/site_styles.py").read_text(encoding="utf-8")
        self.assertIn("{home_evidence()}", home)
        section = evidence.split("def home_evidence()", 1)[1].split("def impact_evidence()", 1)[0]
        self.assertIn('id="leadership-in-practice"', section)
        self.assertEqual(section.count('<article class="card">'), 4)
        self.assertEqual(section.count('class="home-evidence-card-link"'), 4)
        self.assertEqual(section.count('Read example →'), 4)
        self.assertNotIn('evidence-featured-case', section)
        cases = {
            "customer-interview-analyzer": "Customer Interview Analyzer",
            "ai-portfolio-decisions": "80+ AI opportunities",
            "ai-adoption-learning": "Practical AI learning",
            "operational-governance": "Analytics capacity governance",
        }
        impact_section = evidence.split("def impact_evidence()", 1)[1]
        for anchor, title in cases.items():
            self.assertIn(f'href="?page=impact#{anchor}"', section)
            self.assertIn(title, section)
            self.assertIn(f'id="{anchor}"', impact_section)
        self.assertIn("working multilingual GenAI prototype", section)
        self.assertIn("100+ practical AI learning sessions", section)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", styles)
        self.assertIn("min-height:148px", styles)
        self.assertIn(".site #leadership-in-practice .home-evidence-grid", styles)

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
