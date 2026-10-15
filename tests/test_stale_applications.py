"""Stale pipeline acceptance checks; no external services required."""
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_stale_applications import (
    private_summary, private_review_queue, fetch_private_pipeline,
)
from hiring_predictor import forecast_hiring

NOW = date(2026, 10, 15)


def process(key, segment, age, *, excluded=False, applied="2026-07-01", contact=None):
    return {
        "process_key": key, "employer": key.split("|")[0],
        "role": key.split("|")[1], "applied_on": applied,
        "days_since_application": age, "health_segment": segment,
        "exclude_from_active_forecast": excluded,
        "last_response_on": contact, "evidence_quality": "unverified",
        "review_expired_or_overridden": False,
    }


def application(index, days_ago, *, is_active=True):
    from datetime import timedelta
    return {
        "id": index, "record_type": "evidence_event",
        "is_primary_analytics_record": True, "logical_event_key": str(index),
        "event_date": (NOW - timedelta(days=days_ago)).isoformat(),
        "employer": f"Employer {index}", "role": "Head of AI",
        "activity": "Application submitted", "is_application": True,
        "is_active": is_active, "is_closed_or_paused": False,
        "is_negative_decision": False, "is_human_interaction": False,
        "is_interview": False,
    }


class StalePipelineTests(unittest.TestCase):
    def test_mutually_exclusive_counting_and_verification_denominator(self):
        rows = [
            process("a|Head of AI", "stale_60_plus", 90),
            process("b|Head of AI", "verified_dormant", 110, excluded=True),
            process("c|Head of AI", "stale_21_44", 28),
            process("d|Head of AI", "recent_awaiting_response", 12),
            process("e|Head of AI", "closed", 72),
            process("f|Head of AI", "date_unverified", None, applied=None),
            process("z|Alias", "identity_alias", 50),
        ]
        summary = private_summary(rows)
        m = summary["metrics"]
        self.assertEqual(m["total_processes"], 6)
        self.assertEqual(m["unanswered"], 4)
        self.assertEqual(m["stale"], 3)
        self.assertEqual(m["verification_backlog"], 2)
        self.assertEqual(m["active_forecast_dormant_exclusions"], 1)
        self.assertEqual(m["matured_unanswered"], 3)
        self.assertEqual(m["matured_denominator"], 4)
        self.assertEqual(m["undated"], 1)

    def test_date_missing_in_closed_still_counts_for_quality(self):
        summary = private_summary([
            process("a|Head of AI", "closed", None, applied=None),
            process("b|Head of AI", "date_unverified", None, applied=None),
        ])
        self.assertEqual(summary["metrics"]["undated"], 2)
        self.assertEqual(summary["metrics"]["undated_unresolved"], 1)

    def test_review_order_does_not_sort_oldest_first(self):
        rows = [
            process("a|Other role", "stale_60_plus", 135),
            process("b|Head of AI Strategy", "stale_21_44", 30),
            process("c|Director of AI", "stale_45_59", 50),
            process("d|Director of AI", "recruiter_engaged", 25),
        ]
        queue = private_review_queue(rows, contacts={"c|Director of AI"})
        self.assertEqual(len(queue), 3)
        self.assertEqual(queue[0]["Employer"], "c")
        self.assertEqual(queue[1]["Employer"], "b")
        self.assertEqual(queue[-1]["Employer"], "a")
        self.assertEqual(queue[-1]["Forecast"], "Provisional")

    def test_no_private_data_without_owner_token(self):
        with self.assertRaises(ValueError):
            fetch_private_pipeline("")

    def test_age_only_does_not_reduce_weight_or_mark_rejection(self):
        row = application(7, 120)
        forecast = forecast_hiring([row], NOW)
        weights = [x["weight"] for x in forecast["active_stages"]
                   if x["stage"] == "application"]
        self.assertTrue(weights)
        # This record has no verified active-process status after canonical
        # reconciliation, so the established 0.35 fallback still applies.
        # Age must not introduce an additional discount.
        self.assertEqual(weights[0], 0.35)
        younger = forecast_hiring([application(7, 25)], NOW)
        younger_weight = [x["weight"] for x in younger["active_stages"]
                          if x["stage"] == "application"]
        self.assertEqual(younger_weight, weights)

    def test_verified_dormancy_removes_only_the_matching_process(self):
        jobs = [application(1, 86), application(2, 70)]
        baseline = forecast_hiring(jobs, NOW)
        suppressed = forecast_hiring(
            jobs, NOW, stale_pipeline=[{
                "process_key": "employer 1|head of ai",
                "health_segment": "verified_dormant",
                "exclude_from_active_forecast": True,
            }],
        )
        self.assertEqual(len(baseline["active_stages"]), 2)
        self.assertEqual(len(suppressed["active_stages"]), 1)
        self.assertEqual(suppressed["sources"]["verified_dormancy_exclusions"], 1)
        # A later substantive response must update the current view; once it
        # returns no active exclusion the process automatically re-enters.
        reopened = forecast_hiring(jobs, NOW, stale_pipeline=[])
        self.assertEqual(reopened["active_stages"], baseline["active_stages"])

    def test_unverified_silence_does_not_trigger_dormancy(self):
        jobs = [application(1, 90)]
        forecast = forecast_hiring(jobs, NOW, stale_pipeline=[{
            "process_key": "employer 1|head of ai",
            "health_segment": "stale_60_plus",
            "exclude_from_active_forecast": False,
        }])
        self.assertEqual(len(forecast["active_stages"]), 1)


if __name__ == "__main__":
    unittest.main()
