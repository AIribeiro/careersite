"""Recruiter calendar evidence, privacy routing and meeting state regressions."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import inspect
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from page_recruiter_meetings import _phase, _upcoming, _when, _csv, _cohort


class RecruiterMeetingsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 14, 40, tzinfo=ZoneInfo("Europe/Stockholm"))

    def _record(self, day, **overrides):
        row = {
            "id": 1, "title": "Interview", "employer": "Company",
            "scheduled_date": day, "starts_at": None,
            "attendance": "unverified", "source_kind": "outlook",
        }
        row.update(overrides)
        return row

    def test_future_without_time_is_explicitly_tbc(self):
        item = self._record("2026-10-21")
        self.assertEqual(_phase(item, self.now), "Upcoming · time TBC")
        self.assertTrue(_upcoming(item, self.now))
        self.assertIn("time TBC", _when(item))

    def test_calendar_time_is_converted_to_stockholm(self):
        item = self._record("2026-10-20", starts_at="2026-10-20T09:00:00+00:00")
        self.assertIn("11:00", _when(item))
        self.assertEqual(_phase(item, self.now), "Upcoming")

    def test_past_invitation_is_not_completed_meeting(self):
        item = self._record("2026-10-02", starts_at="2026-10-02T07:30:00Z")
        self.assertEqual(_phase(item, self.now), "Past · unverified")
        self.assertFalse(_upcoming(item, self.now))
        self.assertEqual(
            _phase({**item, "attendance": "attended"}, self.now),
            "Attended · verified",
        )

    def test_cancelled_is_never_future(self):
        item = self._record("2026-10-22", attendance="cancelled")
        self.assertEqual(_phase(item, self.now), "Cancelled")
        self.assertFalse(_upcoming(item, self.now))

    def test_csv_excludes_calendar_ids_private_notes(self):
        item = self._record(
            "2026-10-22", source_event_id="sensitive-id",
            evidence_note="private notes", calendar_url="https://calendar.invalid/test",
        )
        content = _csv([item])
        self.assertNotIn("sensitive-id", content)
        self.assertNotIn("private notes", content)
        self.assertNotIn("calendar.invalid", content)

    def test_admin_links_private_section_and_public_route_does_not(self):
        from page_admin import _PRIVATE_VIEW_ROUTES, _dashboard
        from page_analytics_v2 import _resolve_workspace, _workspace_from_url

        self.assertEqual(_PRIVATE_VIEW_ROUTES["meetings"], "Recruiter meetings")
        self.assertIn("render_recruiter_meetings", inspect.getsource(_dashboard))
        self.assertEqual(_resolve_workspace("private", False), "public")
        self.assertIn('"meetings"', inspect.getsource(_workspace_from_url))


if __name__ == "__main__":
    unittest.main()
