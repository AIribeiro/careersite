"""Public rejection intelligence: threshold, evidence discipline and dynamic advice."""
from __future__ import annotations

import sys
import json
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from public_rejection_insights import rejection_overview_readout
from site_analytics_public import fetch_public_analytics_rpc


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

    def _fetch_public_rpc(self, payload):
        with patch("site_analytics_public.request.urlopen") as opener:
            response = opener.return_value.__enter__.return_value
            response.read.return_value = json.dumps(payload).encode()
            return fetch_public_analytics_rpc("careersite_public_rejection_summary_v1")

    def test_accepts_new_aggregate_fields_without_public_data_leaks(self):
        # Regression for the 2026-10-13 public RPC v2/allowlist mismatch.
        payload = {
            **BASE,
            "method": "privacy-thresholded-process-aggregate-v2",
            "previous_decisions_30d": 14,
            "comparative_selection_count": 24,
            "employer_specific_reasons_count": 4,
            "matched_cohort_application_pairs": 79,
            "matched_cohort_negative_pairs": 20,
            "minimum_documented_rejection_share_pct": 25.3,
            "most_frequent_explained_category":
                "Comparative selection (underlying differentiator unverified)",
            "cohort_since": "2026-06-01",
            "rejection_share_method":
                "lower-bound-exact-employer-role-match-not-final-outcome-rate",
        }
        value = self._fetch_public_rpc(payload)
        self.assertEqual(value["matched_cohort_application_pairs"], 79)
        self.assertEqual(value["comparative_selection_count"], 24)

    def test_rejects_suspect_private_or_malformed_cohort_data(self):
        payload = {**BASE, "method": "privacy-thresholded-process-aggregate-v2",
                   "employer": "Any Employer"}
        with self.assertRaisesRegex(RuntimeError, "Unexpected public rejection-summary fields"):
            self._fetch_public_rpc(payload)
        payload.pop("employer")
        payload["matched_cohort_application_pairs"] = 30
        payload["matched_cohort_negative_pairs"] = 8
        with self.assertRaisesRegex(RuntimeError, "Invalid cohort outcome count"):
            self._fetch_public_rpc(payload)

    def test_no_implicit_offer_probability(self):
        result = rejection_overview_readout(BASE)
        self.assertNotIn("offer probability", result["interpretation"].lower())


if __name__ == "__main__":
    unittest.main()
