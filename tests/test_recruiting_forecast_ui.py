"""Dashboard chart smoke test: documented Betsson, KPMG, LeoVegas next steps."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class HiringTimingUITest(unittest.TestCase):
    def test_visual_renders_without_provider_access(self):
        from streamlit.testing.v1 import AppTest
        source = '''
from datetime import date
from page_recruiting_forecast import render_next_steps
opportunities = [
    {"id": 2, "employer": "Betsson", "role_title": "Head of SB Product",
     "outcome": "in_progress", "application_date": "2026-10-09"},
    {"id": 7, "employer": "KPMG", "role_title": "AI Lead",
     "outcome": "in_progress", "application_date": "2026-09-11"},
    {"id": 8, "employer": "LeoVegas", "role_title": "AI Strategy Lead",
     "outcome": "in_progress", "application_date": "2026-09-18"},
    {"id": 16, "employer": "Betsson", "role_title": "Head of Artificial Intelligence",
     "outcome": "in_progress", "application_date": "2026-10-12"},
]
meetings = [
    {"opportunity_id": 2, "id": 15, "stage": 1,
     "scheduled_date": "2026-10-23", "attendance": "attended",
     "meeting_type": "recruiter_screening"},
    {"opportunity_id": 7, "id": 16, "stage": 2,
     "scheduled_date": "2026-10-22", "attendance": "attended",
     "meeting_type": "interview"},
    {"opportunity_id": 8, "id": 18, "stage": 2,
     "scheduled_date": "2026-10-28", "attendance": "unverified",
     "meeting_type": "interview"},
]
signals = [
    {"opportunity_id": 2, "kind": "employer_response_window",
     "anchor_date": "2026-10-23", "event_label": "Recruiter reply",
     "window_start": "2026-10-26", "window_end": "2026-10-27",
     "source_reference": "Confirmed recruiter verbal statement"},
    {"opportunity_id": 16, "kind": "referral_intent",
     "anchor_date": "2026-10-23",
     "source_reference": "Interview review"},
]
render_next_steps(opportunities,meetings,signals,date(2026,10,24))
'''
        at = AppTest.from_string(source).run(timeout=45)
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertTrue(any("Next-step planner" in x.value for x in at.subheader))
        self.assertTrue(any("4" in str(x.value) for x in at.metric))


if __name__ == "__main__":
    unittest.main()
