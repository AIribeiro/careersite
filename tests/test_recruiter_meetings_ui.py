"""Smoke test for the owner-only recruiter meeting Admin dashboard."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class RecruiterMeetingsUITests(unittest.TestCase):
    def test_dashboard_renders_calendar_and_meeting_evidence(self):
        from streamlit.testing.v1 import AppTest

        fixtures = [
            {
                "id": 1, "source_kind": "outlook", "title": "First interview",
                "employer": "Example A", "role_title": "AI Lead",
                "contact_name": "Recruiter A", "meeting_type": "interview", "stage": 1,
                "scheduled_date": "2026-10-07",
                "starts_at": "2026-10-07T09:00:00Z",
                "ends_at": "2026-10-07T09:45:00Z",
                "attendance": "attended", "outcome": "next_stage",
                "follow_up_status": "sent", "follow_up_due": None,
                "calendar_url": None, "calendar_captured_at": "2026-10-19T12:40:00Z",
            },
            {
                "id": 2, "source_kind": "evidence", "title": "Second interview",
                "employer": "Example A", "role_title": "AI Lead",
                "contact_name": "Hiring manager", "meeting_type": "hiring_manager", "stage": 2,
                "scheduled_date": "2026-10-21",
                "starts_at": None, "ends_at": None,
                "attendance": "unverified", "outcome": "unknown",
                "follow_up_status": "unknown", "follow_up_due": None,
                "calendar_url": None, "calendar_captured_at": None,
            },
        ]
        now = datetime(2026, 10, 19, 14, 40, tzinfo=ZoneInfo("Europe/Stockholm"))
        with (
            patch("page_recruiter_meetings._fetch", return_value=fixtures),
            patch("page_recruiter_meetings._now", return_value=now),
            patch("page_recruiting_journeys.fetch_opportunities", return_value=[]),
        ):
            at = AppTest.from_string(
                "from page_recruiter_meetings import render_recruiter_meetings\n"
                "render_recruiter_meetings({'access_token': 'test-token'})\n"
            ).run(timeout=30)

        self.assertFalse(at.exception)
        self.assertTrue(any("Recruiter interactions" in t.value for t in at.title))
        self.assertTrue(any("Upcoming conversations" in t.value for t in at.subheader))
        self.assertTrue(any("Meeting history" in t.value for t in at.subheader))


if __name__ == "__main__":
    unittest.main()
