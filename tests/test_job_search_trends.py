"""Regression checks for canonical, owner-only Job Search Analytics trends."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from job_search_trends import SERIES, analyze_trends


def event(id, event_date, employer="A", role="AI Lead", **flags):
    row = {
        "id": id,
        "record_type": "evidence_event",
        "is_primary_analytics_record": True,
        "logical_event_key": str(id),
        "event_date": event_date,
        "employer": employer,
        "role": role,
        "updated_at": "2026-10-09",
        "is_application": False,
        "is_negative_decision": False,
        "is_human_interaction": False,
    }
    row.update(flags)
    return row


class TrendEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            event(1, "2026-07-15", is_application=True, logical_event_key="same-app"),
            # A later ID is not automatically authoritative; newer updated_at wins.
            event(2, "2026-07-15", is_application=True, logical_event_key="same-app", updated_at="2026-08-01"),
            event(3, "2026-07-22", is_human_interaction=True, interaction_direction="inbound"),
            event(4, "2026-08-03", event_type="interview_completed"),
            event(5, "2026-09-12", employer="B", role="Director Data", is_application=True),
            event(6, "2026-09-10", employer="C", role="Head of AI", is_application=True),
            event(7, "2026-09-15", employer="C", role="Head of AI",
                  is_human_interaction=True, interaction_direction="outbound"),
            event(8, "2026-10-01", employer="C", role="Head of AI",
                  event_type="rejection", is_negative_decision=True),
            # An application row carrying a later status cannot date a rejection.
            event(9, "2026-07-15", employer="A", role="AI Lead",
                  is_application=True, is_negative_decision=True),
            event(10, None, employer="X", role="Unknown", is_application=True),
            event(11, "2026-10-01", employer="D", role="Director",
                  is_application=True, is_primary_analytics_record=False),
        ]
        self.start, self.end = date(2026, 7, 1), date(2026, 10, 9)

    def test_distinct_events_and_decisions(self):
        report = analyze_trends(self.records, self.start, self.end)
        self.assertEqual(report["recent"][SERIES[0]], 1)
        self.assertEqual(report["previous"][SERIES[0]], 1)
        self.assertEqual(report["recent"][SERIES[3]], 1)
        self.assertEqual(report["recent"][SERIES[1]], 0)
        self.assertEqual(report["coverage"]["undated"], 1)
        self.assertEqual(report["coverage"]["all_dated"], 8)

    def test_28_day_cohorts_exclude_immature_and_outbound(self):
        cohort = analyze_trends(self.records, self.start, self.end)["cohorts"]
        self.assertEqual(cohort["matured"], 2)
        self.assertEqual(cohort["pending"], 1)
        self.assertEqual(cohort["contacted"], 1)
        self.assertEqual(cohort["interviewed"], 1)
        september = next(item for item in cohort["rows"] if item["Month"] == "2026-09-01")
        self.assertEqual(september["Matured"], 1)
        self.assertEqual(september["Pending maturation"], 1)
        self.assertEqual(september["Contact %"], 0.0)

    def test_zero_filled_months_and_employer_filter(self):
        report = analyze_trends(self.records, self.start, self.end, employer="B")
        self.assertEqual(len(report["monthly"]), 16)
        self.assertIsNone(report["snapshots"])
        self.assertEqual(report["recent"][SERIES[0]], 1)
        self.assertEqual(report["previous"][SERIES[0]], 0)
        july = [p for p in report["monthly"] if p["Date"] == "2026-07-01"]
        self.assertEqual(len(july), 4)
        self.assertTrue(all(p["Processes"] == 0 for p in july))

    def test_baseline_requires_complete_equal_windows(self):
        report = analyze_trends(self.records, date(2026, 9, 15), self.end)
        self.assertIsNone(report["previous"])
        self.assertFalse(report["baseline_available"])

    def test_snapshots_are_separate_and_not_summed_into_events(self):
        records = list(self.records)
        records += [
            {"id": 20, "record_type": "snapshot_metric", "snapshot_date": "2026-10-07",
             "metric_name": "Confirmed application submissions", "metric_value": 225},
            {"id": 21, "record_type": "snapshot_metric", "snapshot_date": "2026-10-09",
             "metric_name": "Confirmed application submissions", "metric_value": 228},
        ]
        report = analyze_trends(records, self.start, self.end)
        self.assertEqual(report["snapshots"]["metrics"][0]["Delta"], 3)
        self.assertEqual(report["recent"][SERIES[0]], 1)


if __name__ == "__main__":
    unittest.main()
