"""Regression tests for the generic MTO engine (no company-name overrides)."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from meeting_to_offer import estimate_mto


def held(authority: str | None, role: str = "") -> dict:
    return {
        "attendance": "attended",
        "meeting_type": "interview",
        "decision_authority": authority,
        "interviewer_role": role,
    }


class GenericMeetingToOfferTests(unittest.TestCase):
    def test_new_employer_without_meetings_uses_role_prior(self):
        result = estimate_mto({"employer": "Unseen Enterprise", "role": "Head of AI"}, completed=0)
        self.assertEqual((result.total_low, result.total_high), (3, 5))
        self.assertEqual((result.remaining_low, result.remaining_high), (3, 5))
        self.assertEqual(result.confidence, "low")

    def test_unknown_ledger_does_not_imply_zero(self):
        result = estimate_mto({"employer": "Example AB", "role": "AI Lead"})
        self.assertEqual((result.total_low, result.total_high), (3, 4))
        self.assertIsNone(result.remaining_low)

    def test_recruiter_plus_functional_owner_moves_close_to_decision(self):
        inputs = [held("recruiter"), held("functional_owner", "Chief AI Officer")]
        for employer in ("Employer A", "Entirely New Employer"):
            result = estimate_mto({"employer": employer, "role": "AI Strategy Lead"},
                                  completed=2, meetings=inputs)
            self.assertEqual((result.total_low, result.total_high), (2, 3))
            self.assertEqual((result.remaining_low, result.remaining_high), (0, 1))
            self.assertEqual(result.evidence_level, "decision_authority")
            self.assertEqual(result.confidence, "moderate")

    def test_hiring_manager_plus_panel_not_assumed_final(self):
        result = estimate_mto({"role": "Senior AI Manager"}, completed=2,
                              meetings=[held("hiring_manager"), held("stakeholder")])
        self.assertEqual((result.total_low, result.total_high), (3, 4))
        self.assertEqual((result.remaining_low, result.remaining_high), (1, 2))

    def test_recruiter_only_does_not_misrepresent_progress(self):
        result = estimate_mto({"role": "Director of Data"}, completed=1,
                              meetings=[held("recruiter")])
        self.assertEqual((result.total_low, result.total_high), (3, 5))
        self.assertEqual((result.remaining_low, result.remaining_high), (2, 4))

    def test_executive_title_does_not_prove_final_approval(self):
        result = estimate_mto({"role": "Director of Operations"}, completed=2,
                              meetings=[held("recruiter"), held(None, "Chief Technology Officer")])
        self.assertEqual(result.evidence_level, "decision_authority")
        self.assertEqual((result.remaining_low, result.remaining_high), (0, 2))

    def test_confirmed_employer_sequence_overrides_baseline(self):
        process = {"role": "AI Lead"}
        employer_plan = {
            "mto_source_type": "employer_confirmed",
            "mto_total_min": 4,
            "mto_total_max": 5,
        }
        result = estimate_mto(process, completed=2, employer_plan=employer_plan)
        self.assertEqual((result.total_low, result.total_high), (4, 5))
        self.assertEqual((result.remaining_low, result.remaining_high), (2, 3))
        self.assertEqual(result.confidence, "high")

    def test_general_employer_guidance_does_not_override_role_prior(self):
        process = {"role": "AI Lead"}
        guidance = {"mto_source_type": "general_guidance", "mto_total_min": 7, "mto_total_max": 8}
        result = estimate_mto(process, completed=0, employer_plan=guidance)
        self.assertEqual((result.total_low, result.total_high), (3, 4))

    def test_confirmed_future_meeting_is_not_counted_as_held(self):
        result = estimate_mto({"role": "AI Lead", "next_interview": "2026-11-10"},
                              completed=2, meetings=[held("recruiter"), held("functional_owner")])
        self.assertEqual((result.remaining_low, result.remaining_high), (1, 1))
        self.assertEqual((result.total_low, result.total_high), (3, 3))

    def test_more_meetings_than_baseline_does_not_discard_history(self):
        result = estimate_mto({"role": "AI Lead"}, completed=6,
                              meetings=[held(None)] * 6)
        self.assertGreaterEqual(result.total_low, 6)
        self.assertGreaterEqual(result.total_high, 7)

    def test_ignored_unverified_roles_cannot_accelerate(self):
        result = estimate_mto({"role": "AI Lead"}, completed=1,
                              meetings=[{"attendance": "cancelled",
                                         "decision_authority": "final_decision_maker"}])
        self.assertNotEqual(result.evidence_level, "decision_authority")


if __name__ == "__main__":
    unittest.main()
