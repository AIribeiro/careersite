"""Stage naming must not imply attendance, a confirmed offer or a conditional round."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hiring_stage_inference import classify_stage, resolve_stage


class StageInferenceTests(unittest.TestCase):
    def test_recruiter_explicit_culture_fit_beats_calendar_template(self):
        current = resolve_stage(
            forecast_stage="subsequent_interview_completed",
            outcome="in_progress",
            today="2026-10-30",
            attended=[
                {"attendance": "attended", "scheduled_date": "2026-10-02", "meeting_type": "recruiter_screening"},
                {"attendance": "attended", "scheduled_date": "2026-10-28", "meeting_type": "interview",
                 "interviewer_role": "Chief AI Officer"}],
            scheduled=[{"attendance": "unverified", "scheduled_date": "2026-11-09",
                        "meeting_type": "interview", "title": "Hiring Manager Interview"}],
            signals=[{"kind": "stage_progression", "anchor_date": "2026-10-30",
                      "source_kind": "outlook",
                      "event_label": "Final culture fit interview scheduled with Giulio Calleja"}])
        self.assertEqual(current["label"], "Culture fit interview")
        self.assertEqual(current["state"], "scheduled")
        self.assertEqual(current["date"], "2026-11-09")
        self.assertEqual(current["confidence"], "high")

    def test_completed_panel_and_unconfirmed_partner(self):
        current = resolve_stage(
            outcome="in_progress", today="2026-10-30",
            attended=[{"attendance": "attended", "scheduled_date": "2026-10-22",
                       "meeting_type": "interview", "interviewer_role": "Cross-functional interview panel"}],
            signals=[{"kind": "conditional_stage", "anchor_date": "2026-10-25",
                      "source_kind": "outlook", "event_label": "Potential partner interview"}])
        self.assertEqual(current["label"], "Panel interview completed")
        self.assertEqual(current["state"], "completed")

    def test_old_invitation_cannot_override_newer_held_meeting(self):
        current = resolve_stage(
            outcome="in_progress", today="2026-10-30",
            attended=[{"attendance": "attended", "scheduled_date": "2026-10-28",
                       "meeting_type": "interview", "interviewer_role": "Chief AI Officer"}],
            signals=[{"kind": "stage_progression", "anchor_date": "2026-10-19",
                      "source_kind": "outlook", "event_label": "Invitation to second interview"}])
        self.assertEqual(current["label"], "Chief AI Officer interview completed")

    def test_past_calendar_invite_is_not_completed(self):
        current = resolve_stage(
            outcome="in_progress", today="2026-11-11",
            scheduled=[{"attendance": "unverified", "scheduled_date": "2026-11-09",
                        "meeting_type": "interview", "title": "Final culture fit interview"}])
        self.assertEqual(current["state"], "attendance_unverified")
        self.assertNotIn("completed", current["label"].lower())

    def test_dashboard_shows_specific_stage_and_confirmed_date(self):
        from hiring_opportunity_comparison import opportunity_comparison_html
        process = {"employer": "Example Enterprise", "role": "AI Lead",
                   "process_key": "example|ai lead",
                   "stage": "subsequent_interview_completed", "credibility_index": 75.0,
                   "next_interview": None}
        plan = {"pending_stage_label": "Culture fit interview",
                "pending_stage_source": "outlook",
                "pending_stage_confidence": "high",
                "pending_stage_state": "scheduled",
                "pending_stage_date": "2026-11-09",
                "mto_source_type": "employer_confirmed",
                "mto_total_min": 3, "mto_total_max": 3,
                "outcome": "in_progress"}
        html = opportunity_comparison_html([process],
            {"subsequent_interview_completed": "Subsequent interview completed"},
            meeting_counts={"example|ai lead": 2},
            meeting_details={"example|ai lead": []},
            process_plans={"example|ai lead": plan})
        self.assertIn("Culture fit interview", html)
        self.assertIn("Confirmed next interview", html)
        self.assertIn("09 Nov 2026", html)
        self.assertIn("Stage source: outlook", html)
        self.assertNotIn(">Subsequent interview completed<", html)

    def test_rejection_dominates_old_interview_signals(self):
        current = resolve_stage(
            outcome="rejected", today="2026-10-30",
            signals=[{"kind": "stage_progression", "anchor_date": "2026-10-29",
                      "source_kind": "outlook", "event_label": "Final interview scheduled"}])
        self.assertEqual(current["state"], "closed")

    def test_new_employer_can_get_specific_stage(self):
        self.assertEqual(classify_stage("We invite you to the case study interview"), "Case interview")
        self.assertEqual(classify_stage("Culture-fit with our process lead"), "Culture fit interview")
        self.assertEqual(classify_stage("Partner interview with our regional leader"), "Partner interview")
        self.assertIsNone(classify_stage("We will update you later"))

    def test_assessment_not_mislabeled_as_interview(self):
        stage = resolve_stage(
            outcome="in_progress", today="2026-10-30",
            signals=[{"kind": "stage_progression", "anchor_date": "2026-10-30",
                      "source_kind": "outlook",
                      "event_label": "Personality and logic assessment requested"}])
        self.assertEqual(stage["source"], "forecast")
        self.assertNotIn("interview", stage["label"].lower())


if __name__ == "__main__":
    unittest.main()
