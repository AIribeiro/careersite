"""Regression tests for live owner-only recruiting status and exploratory contacts."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from current_hiring_pipeline import (
    current_rows, strategic_rows, fetch_current_pipeline, _row_html,
)


def fixtures():
    return {
        "opportunities": [
            {"id": 47, "employer": "Vestas", "role_title": "AI Innovation Lead NCE",
             "outcome": "in_progress", "application_date": None},
            {"id": 46, "employer": "Agile", "role_title": "AI Transformation Lead",
             "outcome": "in_progress", "application_date": "2026-11-17"},
            {"id": 8, "employer": "LeoVegas", "role_title": "AI Strategy and Transformation Lead",
             "outcome": "rejected"},
            {"id": 33, "employer": "Capgemini", "role_title": "AI Transformation Partner",
             "outcome": "closed"},
        ],
        "priorities": [
            {"opportunity_id": 47, "priority_band": "P1", "rank_position": 1,
             "pipeline_state": "video_assessment_completed", "next_action": "Await decision"},
            {"opportunity_id": 46, "priority_band": "P1", "rank_position": 5,
             "pipeline_state": "ats_received", "next_action": "Await recruiter"},
            {"opportunity_id": 8, "priority_band": "P1", "rank_position": 2,
             "pipeline_state": "subsequent_interview_completed"},
            {"opportunity_id": 33, "priority_band": "CLOSED", "rank_position": None,
             "pipeline_state": "user_closed_no_followup"},
        ],
        "statuses": [
            {"source_type": "managed", "source_ref": "46", "status": "recruiter_replied",
             "status_on": "2026-11-19", "status_note": "Profile looks good; no meeting"},
            {"source_type": "managed", "source_ref": "47", "status": "recruiter_replied",
             "status_on": "2026-11-18", "status_note": "Video acknowledged"},
        ],
        "strategic": [
            {"employer": "Nexer Insight",
             "access_status": "direct_executive_conversation",
             "hiring_signal": "exploratory_executive_interest_no_open_role",
             "contact_name": "Jenny Malmqvist"},
        ],
    }


class CurrentHiringPipelineTests(unittest.TestCase):
    def test_ongoing_stages_and_closed_roles_are_distinct(self):
        rows = current_rows(fixtures())
        self.assertEqual([row["employer"] for row in rows], ["Vestas", "Agile"])
        self.assertIn("Video assessment completed", rows[0]["stage"])
        self.assertEqual(rows[1]["stage"], "Recruiter replied · no interview confirmed")

    def test_nexer_is_strategic_conversation_not_an_application(self):
        sources = fixtures()
        self.assertEqual([x["employer"] for x in strategic_rows(sources)], ["Nexer Insight"])
        self.assertNotIn("Nexer Insight", [x["employer"] for x in current_rows(sources)])

    def test_ignored_followups_do_not_reactivate_closed_processes(self):
        sources = fixtures()
        sources["statuses"].append(
            {"source_type": "managed", "source_ref": "47", "status": "ignored"}
        )
        self.assertEqual([x["employer"] for x in current_rows(sources)], ["Agile"])

    def test_owner_token_is_required_and_rpc_is_owner_only(self):
        sources = fixtures()
        with patch("current_hiring_pipeline._request_json", return_value=sources) as call:
            self.assertEqual(fetch_current_pipeline("owner-token"), sources)
            self.assertIn("rpc/careersite_owner_current_hiring_pipeline_v1",
                          call.call_args.args[1])
            self.assertEqual(call.call_args.kwargs["token"], "owner-token")
        with self.assertRaises(ValueError):
            fetch_current_pipeline("")

    def test_user_supplied_html_is_escaped(self):
        row = current_rows(fixtures())[0]
        row["employer"] = '<img src=x onerror=alert(1)>'
        output = _row_html(row)
        self.assertIn("&lt;img", output)
        self.assertNotIn("<img", output)


if __name__ == "__main__":
    unittest.main()
