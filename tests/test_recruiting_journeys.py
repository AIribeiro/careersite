"""Evidence, timing and identity regressions for per-role interview journeys."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recruiting_journeys import journey, cohort_metrics, comparison_rows, elapsed, recent_interaction_rows


NOW = datetime(2026, 10, 19, 18, 30, tzinfo=ZoneInfo("Europe/Stockholm"))


def opportunity(id=1, **values):
    row = {
        "id": id, "employer": "KPMG", "role_title": "AI Lead – Tax & Legal",
        "application_date": "2026-09-11", "application_date_basis": "confirmed_submission",
        "application_evidence": "ATS receipt", "outcome": "in_progress",
        "decision_date": None, "offer_date": None,
    }
    row.update(values)
    return row


def interview(id, day, *, process=1, stage=1, attendance="attended"):
    return {
        "id": id, "opportunity_id": process,
        "scheduled_date": day, "meeting_type": "interview",
        "stage": stage, "attendance": attendance,
        "source_kind": "outlook",
    }


class RecruitingJourneyTests(unittest.TestCase):
    def test_application_to_first_second_and_gap(self):
        model = journey(
            opportunity(),
            [interview(101, "2026-10-07"),
             interview(102, "2026-10-22", stage=2, attendance="unverified")],
            NOW,
        )
        self.assertEqual(model["by_round"][1]["from_application"], 26)
        self.assertEqual(model["by_round"][2]["from_application"], 41)
        self.assertEqual(model["by_round"][2]["from_previous"], 15)
        self.assertEqual(model["days_to_first_confirmed"], 26)
        self.assertEqual(len(model["confirmed"]), 1)
        self.assertEqual(model["by_round"][2]["state"], "Scheduled · upcoming")
        self.assertIsNone(model["days_application_to_offer"])

    def test_offer_intervals_each_round(self):
        op = opportunity(
            outcome="offer", offer_date="2026-10-31",
            offer_evidence="employer offer email",
        )
        model = journey(
            op,
            [interview(1, "2026-10-07"),
             interview(2, "2026-10-22", stage=2)],
            NOW,
        )
        self.assertEqual(model["days_application_to_offer"], 50)
        self.assertEqual(model["by_round"][1]["to_offer"], 24)
        self.assertEqual(model["by_round"][2]["to_offer"], 9)
        self.assertIn("Offer received", [e["label"] for e in model["events"]])

    def test_unknown_application_prevents_fabricated_latency(self):
        op = opportunity(application_date=None, application_date_basis="unknown")
        model = journey(op, [interview(1, "2026-10-07")], NOW)
        self.assertIsNone(model["by_round"][1]["from_application"])
        self.assertIsNone(model["days_to_first_confirmed"])

    def test_estimated_application_does_not_produce_exact_days(self):
        op = opportunity(application_date="2026-09-12",
                         application_date_basis="estimated")
        model = journey(op, [interview(1, "2026-10-07")], NOW)
        self.assertIsNone(model["by_round"][1]["from_application"])
        self.assertIsNone(model["days_to_first_confirmed"])

    def test_opportunities_never_merge_by_employer_alone(self):
        first = opportunity(id=1, role_title="AI Lead")
        second = opportunity(id=2, role_title="Data Director")
        records = [interview(1, "2026-10-07", process=1),
                   interview(2, "2026-10-12", process=2)]
        a, b = journey(first, records, NOW), journey(second, records, NOW)
        self.assertEqual([m["id"] for m in a["meetings"]], [1])
        self.assertEqual([m["id"] for m in b["meetings"]], [2])

    def test_uncorroborated_calendar_entries_not_completed(self):
        model = journey(
            opportunity(), [interview(1, "2026-10-03",
                                      attendance="unverified")], NOW,
        )
        self.assertEqual(len(model["confirmed"]), 0)
        self.assertIsNone(model["days_to_first_confirmed"])
        self.assertIn("Past invitation", model["events"][1]["state"])

    def test_no_negative_duration_when_dates_are_inconsistent(self):
        self.assertIsNone(elapsed("2026-10-21", "2026-10-20"))

    def test_statistics_use_only_confirmed_applications_and_held_rounds(self):
        confirmed = journey(opportunity(), [
            interview(1, "2026-10-07"), interview(2, "2026-10-12", stage=2)
        ], NOW)
        scheduled = journey(
            opportunity(id=2, application_date_basis="estimated"),
            [interview(3, "2026-10-07", process=2),
             interview(4, "2026-10-22", process=2, stage=2, attendance="unverified")],
            NOW,
        )
        stats = cohort_metrics([confirmed, scheduled])
        self.assertEqual(stats["first_sample"], 1)
        self.assertEqual(stats["median_days_to_first"], 26)
        self.assertEqual(stats["round_sample"], 1)
        self.assertEqual(stats["median_days_between_completed_rounds"], 5)
        self.assertEqual(stats["offer_sample"], 0)

    def test_oct23_betsson_screening_visible_by_actual_date(self):
        today = datetime(2026, 10, 23, 14, 3,
                         tzinfo=ZoneInfo("Europe/Stockholm"))
        op = opportunity(id=2, employer="Betsson Group",
                         role_title="Head of SB Product – Data & AI",
                         application_date="2026-10-09")
        first = interview(15, "2026-10-23", process=2)
        first.update({
            "meeting_type": "recruiter_screening",
            "starts_at": "2026-10-23T08:00:00+00:00",
        })
        cancelled = interview(19, "2026-10-20", process=2,
                              attendance="cancelled")
        m = journey(op, [cancelled, first], today)
        self.assertEqual(m["days_to_first_confirmed"], 14)
        self.assertEqual(len(m["confirmed"]), 1)
        self.assertEqual(m["by_round"][1]["date"].isoformat(), "2026-10-23")
        row = comparison_rows([m])[0]
        self.assertEqual(row["Round 1"], "23 Oct · 14 d · held")
        self.assertEqual(row["Latest held"], "23 Oct 2026")
        activity = recent_interaction_rows([m], today)
        self.assertEqual(activity[0]["Date"], "2026-10-23")
        self.assertEqual(activity[0]["Time (Stockholm)"], "10:00")
        self.assertEqual(activity[0]["Status"], "Completed · confirmed")
        self.assertEqual(len(activity), 2)

    def test_actual_interview_date_visible_even_without_application(self):
        today = datetime(2026, 10, 23, 14,
                         tzinfo=ZoneInfo("Europe/Stockholm"))
        op = opportunity(id=4, application_date=None,
                         application_date_basis="unknown")
        model = journey(op, [interview(22, "2026-10-22", process=4,
                                      stage=2)], today)
        row = comparison_rows([model])[0]
        self.assertEqual(row["Round 2"], "22 Oct · days unknown · held")
        self.assertEqual(row["Latest held"], "22 Oct 2026")

    def test_round_comparison_distinguishes_planned(self):
        model = journey(
            opportunity(),
            [interview(1, "2026-10-07"), interview(2, "2026-10-22",
                                                   stage=2, attendance="unverified")],
            NOW,
        )
        rows = comparison_rows([model])
        self.assertIn("41 d · planned", rows[0]["Round 2"])


if __name__ == "__main__":
    unittest.main()
