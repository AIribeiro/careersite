"""Public rejection intelligence: threshold, evidence discipline and dynamic advice."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from public_rejection_insights import rejection_overview_readout


BASE = {
    "available": True,
    "as_of": "2026-10-13",
    "analyzed_processes": 62,
    "unknown_causes": 52,
    "confirmed_explanations": 5,
    "employer_stated_explanations": 4,
    "undated_decisions": 20,
    "dated_decisions": 42,
    "unknown_stages": 56,
    "verified_jds": 0,
    "recent_decisions_30d": 39,
}


class PublicRejectionInsightTests(unittest.TestCase):
    def test_baseline_never_claims_a_skills_gap(self):
        insight = rejection_overview_readout(BASE)
        self.assertEqual(insight["status"], "ok")
        self.assertAlmostEqual(insight["unknown_share"], 52/62)
        self.assertIn("cannot establish a recurring capability gap", insight["interpretation"])
        self.assertIn("feedback", insight["action"].lower())
        self.assertEqual(len(insight["cautions"]), 3)

    def test_small_sample_never_renders_an_interpretation(self):
        self.assertEqual(
            rejection_overview_readout({"available": True,
                                        "analyzed_processes": 9})["status"],
            "unavailable",
        )
        self.assertEqual(
            rejection_overview_readout({"available": False})["status"],
            "unavailable",
        )

    def test_readout_changes_when_evidence_quality_changes(self):
        revised = {
            **BASE,
            "unknown_causes": 7,
            "confirmed_explanations": 34,
            "undated_decisions": 3,
            "dated_decisions": 59,
            "unknown_stages": 8,
            "verified_jds": 25,
        }
        result = rejection_overview_readout(revised)
        self.assertEqual(result["evidence_status"], "Better explanation coverage")
        self.assertIn("recurring", result["action"].lower())
        self.assertEqual(result["cautions"], [])

    def test_partial_evidence_is_not_an_employer_reason(self):
        revised = {**BASE, "unknown_causes": 30, "confirmed_explanations": 12}
        result = rejection_overview_readout(revised)
        self.assertEqual(result["evidence_status"], "Mixed explanation coverage")
        self.assertIn("Avoid attributing unknown decisions", result["action"])

    def test_no_implicit_offer_probability(self):
        result = rejection_overview_readout(BASE)
        self.assertNotIn("offer probability", result["interpretation"].lower())


if __name__ == "__main__":
    unittest.main()
