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

from recruiting_journeys import journey, cohort_metrics, comparison_rows, elapsed


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
