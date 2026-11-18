"""Selected Home evidence appears after navigation and ahead of editorial."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeCaseOrderTests(unittest.TestCase):
    def test_proof_is_prominent_and_not_buried_in_activity_counts(self):
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        evidence = (ROOT / "src/portfolio_operating_evidence.py").read_text(encoding="utf-8")
        self.assertLess(home.index("{home_pathways()}"), home.index("{home_evidence()}"))
        self.assertLess(home.index("{home_evidence()}"), home.index("{home_whats_new()}"))
        self.assertLess(evidence.index("Customer Interview Analyzer"),
                        evidence.index("80+ AI opportunities"))
        self.assertIn("not scaled", evidence)
        self.assertNotIn("verified ROI", evidence.lower())


if __name__ == "__main__":
    unittest.main()
