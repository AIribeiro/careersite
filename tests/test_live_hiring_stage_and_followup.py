"""Owner hiring regression: live stage evidence, recruiter screens, and safe follow-ups."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_live_hiring_stages import stage_display_rows, meeting_summary, stage_board_html
from page_followup_manager import (
    stale_correspondence, guard_send_checkpoint, new_live_engagements,
)


def snapshot() -> dict:
    return {
        "generated_at": "2026-11-19T11:40:00+00:00",
        "opportunities": [
            {"id": 47, "employer": "Vestas", "role_title": "AI Innovation Lead NCE",
             "outcome": "in_progress"},
            {"id": 46, "employer": "Agile", "role_title": "AI Transformation Lead",
             "outcome": "in_progress"},
            {"id": 26, "employer": "Sapiens / Xcede", "role_title": "AI Enablement Lead",
             "outcome": "in_progress"},
            {"id": 8, "employer": "LeoVegas", "role_title": "AI Strategy Lead",
             "outcome": "rejected"},
        ],
        "statuses": [
            {"source_type": "managed", "source_ref": "46", "status": "recruiter_replied",
             "status_on": "2026-11-19",
             "updated_at": "2026-11-19T08:00:00Z"},
        ],
        "priorities": [
            {"opportunity_id": 47, "rank_position": 1, "priority_band": "P1",
             "pipeline_state": "video_assessment_completed", "reviewed_on": "2026-11-18"},
            {"opportunity_id": 46, "rank_position": 2, "priority_band": "P1",
             "pipeline_state": "ats_received", "reviewed_on": "2026-11-18"},
            {"opportunity_id": 26, "rank_position": 3, "priority_band": "P1",
             "pipeline_state": "qualified_recruiter_client_status_unknown",
             "reviewed_on": "2026-11-18"},
            {"opportunity_id": 8, "rank_position": 4, "priority_band": "P1",
             "pipeline_state": "subsequent_interview_completed",
             "reviewed_on": "2026-11-18"},
        ],
        "strategic": [
            {"employer": "Nexer Insight",
             "access_status": "direct_executive_conversation",
             "hiring_signal": "exploratory_executive_interest_no_open_role"},
        ],
        "unreviewed_active": [],
        "sync_runs": [],
        "source_watermarks": {},
    }


class LiveHiringStageTests(unittest.TestCase):
    def test_stage_board_is_responsive_card_grid_not_native_data_table(self):
        rows = stage_display_rows(snapshot(), [])
        html = stage_board_html(rows)
        self.assertIn("Where current opportunities stand", html)
        self.assertIn('class="hiring-board__item"', html)
        self.assertIn("@media(max-width:920px)", html)
        self.assertIn("@media(max-width:670px)", html)
        self.assertNotIn("LeoVegas", html)
        self.assertNotIn("<table", html)
        self.assertNotIn("probability of receiving", html)

    def test_stage_card_escapes_employer_and_role_inputs(self):
        rows = stage_display_rows(snapshot(), [])
        rows[0]["employer"] = '<img src=x onerror=alert(1)>'
        rows[0]["role"] = "<script>bad()</script>"
        html = stage_board_html(rows)
        self.assertIn("&lt;img", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<script>bad", html)

    def test_unknown_attendance_not_rendered_as_no_meetings(self):
        rows = stage_display_rows(snapshot(), None)
        html = stage_board_html(rows)
        self.assertIn("Meeting ledger unavailable", html)
        self.assertIn("Unverified", html)
        self.assertNotIn("None held", html)

    def test_canonical_records_override_old_model_and_exclude_rejected(self):
        rows = stage_display_rows(snapshot(), [])
        self.assertEqual([x["employer"] for x in rows],
                         ["Vestas", "Agile", "Sapiens / Xcede"])
        self.assertIn("Video assessment completed", rows[0]["stage"])
        self.assertIn("Recruiter replied", rows[1]["stage"])
        self.assertTrue(all(x["interviews_held"] == 0 for x in rows))

    def test_recruiter_screening_is_not_hiring_manager_interview(self):
        rows = stage_display_rows(
            snapshot(),
            [{"opportunity_id": 26, "id": 26, "meeting_type": "recruiter_screening",
              "attendance": "attended", "decision_authority": "recruiter"},
             {"opportunity_id": 47, "id": 99, "meeting_type": "interview",
              "attendance": "unverified"},
             {"opportunity_id": 46, "id": 90, "meeting_type": "networking",
              "attendance": "attended"}],
        )
        sapiens = next(x for x in rows if x["employer"].startswith("Sapiens"))
        self.assertEqual((sapiens["screens_held"], sapiens["interviews_held"]), (1, 0))
        self.assertEqual(next(x for x in rows if x["employer"] == "Vestas")["screens_held"], 0)

    def test_unavailable_meeting_ledger_never_claims_zero_held(self):
        rows = stage_display_rows(snapshot(), None)
        self.assertTrue(all(x["interviews_held"] is None for x in rows))
        self.assertTrue(all(x["remaining"] == "Unknown" for x in rows))

    def test_exact_requisition_focus_does_not_merge_employers(self):
        rows = stage_display_rows(
            snapshot(), [], {"47": "vestas-ai-79781", "46": "agile-ai-123"},
            "agile-ai-123",
        )
        self.assertEqual([x["employer"] for x in rows], ["Agile"])


class FollowupFreshnessTests(unittest.TestCase):
    NOW = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)

    def test_due_checkpoint_requires_recent_mailbox_check(self):
        row = {
            "action": "follow_up_now",
            "source_checked_at": "2026-10-26T15:33:32Z",
            "due_date": "2026-11-05",
        }
        self.assertTrue(stale_correspondence(row, self.NOW))
        guarded = guard_send_checkpoint(row, self.NOW)
        self.assertEqual(guarded["action"], "hold")
        self.assertEqual(guarded["due_date"], "2026-11-05")
        self.assertTrue(guarded["needs_source_check"])

    def test_recent_correspondence_preserves_due_action(self):
        row = {"action": "follow_up_now",
               "source_checked_at": "2026-11-19T10:00:00+00:00"}
        self.assertFalse(stale_correspondence(row, self.NOW))
        self.assertEqual(guard_send_checkpoint(row, self.NOW)["action"], "follow_up_now")

    def test_recent_recruiter_evidence_not_lost_from_followup_view(self):
        rows = new_live_engagements(snapshot(), {26})
        self.assertEqual({x["employer"] for x in rows}, {"Agile", "Vestas"})
        self.assertNotIn("Nexer Insight", {x["employer"] for x in rows})


if __name__ == "__main__":
    unittest.main()
