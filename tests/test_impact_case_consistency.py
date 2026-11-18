"""Operating evidence is concise, anonymous and tied to bounded career facts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImpactCaseConsistencyTests(unittest.TestCase):
    def test_featured_case_has_business_mechanism_and_honest_outcome(self):
        src = (ROOT / "src/portfolio_operating_evidence.py").read_text(encoding="utf-8")
        case = src.split('def impact_evidence()', 1)[1]
        self.assertIn('id="customer-interview-analyzer"', case)
        self.assertIn("two hours", case)
        self.assertIn("transcribed and translated", case)
        self.assertIn("not rolled out at scale", case)
        for employer in ("Volvo Group", "MSX International", "Kimberly-Clark"):
            self.assertNotIn(employer, case)
        self.assertLess(case.index('id="customer-interview-analyzer"'), case.index("80+ AI opportunities"))

    def test_career_history_remains_a_separate_bounded_section(self):
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        for phrase in ("MSX International", "Volvo Group / Volvo Trucks",
                       "Kimberly-Clark", "Senior AI Business Expert",
                       "IBM Watson solution design", "2026–2027"):
            if phrase == "2026–2027":
                # Produced dynamically from the canonical approved roadmap date.
                self.assertIn("MSX_ROADMAP", impact)
            else:
                self.assertIn(phrase, impact)
        self.assertIn('{impact_evidence()}', impact)
        self.assertIn('{portfolio_next_navigation("impact")}', impact)
        self.assertIn("100+ AI learning sessions", impact)
        self.assertNotIn("100+ production deployments", impact)


if __name__ == "__main__":
    unittest.main()
