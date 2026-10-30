"""Pure presentation regression checks for the compact recruiting comparison."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hiring_opportunity_comparison import (
    opportunity_comparison_html, opportunity_evidence_score,
)


class OpportunityComparisonTests(unittest.TestCase):
    STAGES = {
        "subsequent_interview_completed": "Subsequent interview completed",
        "first_interview_completed": "First interview completed",
        "human_response": "Recruiter / human response",
    }

    def test_live_ranked_rows_scores_and_stage(self):
        rows = [
            {"employer": "LeoVegas", "role": "AI Strategy Lead",
             "stage": "subsequent_interview_completed", "credibility_index": 71.1},
            {"employer": "KPMG", "role": "AI Lead",
             "stage": "subsequent_interview_completed", "credibility_index": 67.0},
            {"employer": "Betsson", "role": "Head of SB Product",
             "stage": "first_interview_completed", "credibility_index": 42.6},
            {"employer": "SkillHuset", "role": "Digital Product Owner",
             "stage": "human_response", "credibility_index": 18.5},
        ]
        html = opportunity_comparison_html(rows, self.STAGES)
        self.assertEqual(html.count('class="op-compare__row"'), 4)
        self.assertLess(html.index("LeoVegas"), html.index("KPMG"))
        self.assertLess(html.index("KPMG"), html.index("Betsson"))
        for score in ("71.1", "67.0", "42.6", "18.5"):
            self.assertIn(f'aria-valuenow="{score}"', html)
            self.assertIn(f'width:{score}%', html)
        self.assertIn("Subsequent interview completed", html)
        self.assertIn("First interview completed", html)
        self.assertIn("Recruiter / human response", html)
        self.assertIn("@media(max-width:760px)", html)
        self.assertNotIn("probability", html.lower())

    def test_untrusted_labels_escaped_and_missing_score_not_zero(self):
        html = opportunity_comparison_html([
            {"employer": '<script>alert("x")</script>', "role": "<b>Role</b>",
             "stage": "human_response", "credibility_index": None},
        ], self.STAGES)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;Role&lt;/b&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("Not scored", html)
        self.assertNotIn('aria-valuenow="0.0"', html)
        self.assertIsNone(opportunity_evidence_score({"credibility_index": "nan"}))
        self.assertIsNone(opportunity_evidence_score({"credibility_index": True}))
        self.assertEqual(opportunity_evidence_score({"credibility_index": 150}), 100.0)
        self.assertEqual(opportunity_evidence_score({"credibility_index": -20}), 0.0)

    def test_real_next_interview_only(self):
        html = opportunity_comparison_html([
            {"employer": "KPMG", "role": "AI Lead",
             "stage": "first_interview_completed", "credibility_index": 67,
             "next_interview": "2026-11-04"},
        ], self.STAGES)
        self.assertIn("Confirmed next interview · 04 Nov 2026", html)
        missing = opportunity_comparison_html([
            {"employer": "KPMG", "role": "AI Lead",
             "stage": "first_interview_completed", "credibility_index": 67},
        ], self.STAGES)
        self.assertNotIn("Confirmed next interview ·", missing)


if __name__ == "__main__":
    unittest.main()
