"""Regression gates for owner-only hiring-stage v2 and forecast version separation."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_hiring_prediction_v2 import (
    VERSION, fetch_hiring_prediction_v2, validate_prediction_v2,
    render_hiring_prediction_v2,
)
from hiring_forecast_history import build_v2_snapshot, stability_summary


def example_v2() -> dict:
    return {
        "model_version": VERSION, "as_of": "2026-10-16",
        "portfolio_credibility_index": 46.5,
        "cohort": {
            "total": 297, "eligible_scored": 43, "offers": 0,
            "subsequent_stage_v2": 1, "scheduled_first_v2": 1,
            "stale_not_rejected": 168, "reconciled_active": 1,
        },
        "top_processes": [{
            "rank": 1, "employer": "KPMG", "role": "AI Lead",
            "stage": "subsequent_interview_scheduled",
            "credibility_index": 61.0, "status": "active_reconciled",
            "next_interview": "2026-10-22", "last_progress": "2026-10-15",
        }, {
            "rank": 2, "employer": "Betsson Group", "role": "Head of Data & AI",
            "stage": "first_interview_scheduled", "credibility_index": 20.7,
            "status": "active_unknown_decision",
            "next_interview": "2026-10-20",
        }],
        "leading_stage_scenario": {
            "employer": "KPMG", "role": "AI Lead",
            "offer_central": "2026-11-19",
            "offer_earliest": "2026-11-05",
            "offer_latest": "2026-12-10",
            "start_earliest": "2026-11-19",
            "start_central": "2026-12-17",
            "start_latest": "2027-01-21",
        },
        "stage_breakdown": {
            "subsequent_interview_scheduled": 1,
            "first_interview_scheduled": 1,
        },
    }


class HiringV2Tests(unittest.TestCase):
    def test_rpc_requires_private_token_and_exact_model_version(self):
        with patch("page_hiring_prediction_v2._request_json",
                   return_value=example_v2()) as rpc:
            self.assertEqual(
                fetch_hiring_prediction_v2("owner-token")["portfolio_credibility_index"],
                46.5,
            )
            rpc.assert_called_once()
            self.assertEqual(rpc.call_args.kwargs["token"], "owner-token")
            self.assertIn("rpc/careersite_hiring_prediction_v2",
                          rpc.call_args.args[1])
        with patch("page_hiring_prediction_v2._request_json") as rpc:
            with self.assertRaises(ValueError):
                fetch_hiring_prediction_v2("")
            rpc.assert_not_called()
        with self.assertRaises(ValueError):
            validate_prediction_v2({
                **example_v2(), "model_version": "hiring-beta-4.3-assumed-date-provisional",
            })

    def test_current_forecast_is_credibility_not_reliability_or_probability(self):
        ui = MagicMock()
        ui.columns.side_effect = lambda size: [MagicMock() for _ in range(size)]
        with patch("page_hiring_prediction_v2.st", ui):
            render_hiring_prediction_v2(example_v2())
        self.assertTrue(any(
            "Around 17 Dec 2026" in str(call.args[0])
            for call in ui.markdown.call_args_list if call.args
        ))
        self.assertTrue(any(
            "Possible job offer: around 19 Nov 2026" in str(call.args[0])
            for call in ui.markdown.call_args_list if call.args
        ))
        self.assertTrue(any(
            "Pipeline credibility: 46.5 / 100" in str(call.args[0])
            for call in ui.markdown.call_args_list if call.args
        ))
        captions = [str(call.args[0]) for call in ui.caption.call_args_list
                    if call.args]
        self.assertTrue(any("not a 46.5% offer chance" in c for c in captions))
        self.assertFalse(any("55%" in c for c in captions))
        self.assertTrue(any("A scheduled interview is not counted as completed" in c
                            for c in captions))

    def test_meeting_totals_count_attendance_not_invites_or_people(self):
        from page_hiring_prediction_v2 import _verified_meetings_by_process
        opportunities = [
            {"id": 7, "forecast_process_key": "kpmg|ai lead - manager - tax & legal technology"},
            {"id": 8, "forecast_process_key": "leovegas mobile gaming group|ai strategy and transformation lead"},
            {"id": 2, "forecast_process_key": "betsson group|head of sb product - data & ai"},
            {"id": 99, "forecast_process_key": "skillhuset|digital product owner"},
        ]
        meetings = [
            {"id": 1, "opportunity_id": 7, "scheduled_date": "2026-10-07",
             "attendance": "attended", "source_event_id": "kpmg-one"},
            {"id": 2, "opportunity_id": 7, "scheduled_date": "2026-10-22",
             "attendance": "attended", "source_event_id": "kpmg-two"},
            # Same calendar event copied from another source must not double-count.
            {"id": 3, "opportunity_id": 7, "scheduled_date": "2026-10-22",
             "attendance": "attended", "source_event_id": "kpmg-two"},
            {"id": 4, "opportunity_id": 8, "scheduled_date": "2026-10-02",
             "attendance": "attended", "source_event_id": "leo-one"},
            {"id": 5, "opportunity_id": 8, "scheduled_date": "2026-10-28",
             "attendance": "attended", "source_event_id": "leo-two"},
            {"id": 6, "opportunity_id": 8, "scheduled_date": "2026-09-30",
             "attendance": "cancelled", "source_event_id": "leo-cancelled"},
            {"id": 7, "opportunity_id": 2, "scheduled_date": "2026-10-23",
             "attendance": "attended", "source_event_id": "betsson-one"},
            {"id": 8, "opportunity_id": 2, "scheduled_date": "2099-01-01",
             "attendance": "attended", "source_event_id": "future-error"},
        ]
        # The production REST query filters cancelled meetings; keep one in
        # this fixture to confirm a second independent attendance safeguard.
        with patch("page_hiring_prediction_v2._request_json",
                   side_effect=[opportunities, meetings]) as api:
            counts = _verified_meetings_by_process("owner-token")
        self.assertEqual(counts["kpmg|ai lead - manager - tax & legal technology"], 2)
        self.assertEqual(counts["leovegas mobile gaming group|ai strategy and transformation lead"], 2)
        self.assertEqual(counts["betsson group|head of sb product - data & ai"], 1)
        self.assertEqual(counts["skillhuset|digital product owner"], 0)
        self.assertEqual(api.call_count, 2)
        self.assertTrue(all(c.kwargs["token"] == "owner-token" for c in api.call_args_list))
        self.assertIn("attendance=eq.attended", api.call_args_list[1].args[1])

    def test_v2_snapshot_has_no_modelled_personal_offer_probability(self):
        x = build_v2_snapshot(example_v2(), {"v2": "signature"})
        self.assertEqual(x["model_version"], VERSION)
        self.assertEqual(x["central_offer_date"], "2026-11-19")
        self.assertIsNone(x["modelled_90d"])
        self.assertEqual(x["evidence_index"], 46)

    def test_history_does_not_compare_different_versions_same_day(self):
        old = {"forecast_day": "2026-10-16",
               "model_version": "hiring-beta-4.3-assumed-date-provisional",
               "central_offer_date": "2026-11-13",
               "observed_at": "2026-10-16T07:20:00Z"}
        new = {"forecast_day": "2026-10-16",
               "model_version": VERSION,
               "central_offer_date": "2026-11-19",
               "observed_at": "2026-10-16T07:27:00Z"}
        summary = stability_summary([old, new], model_version=VERSION)
        self.assertIsNone(summary["shift_days"])
        self.assertEqual(summary["comparable_count"], 1)
        self.assertEqual(summary["model_versions"], 2)
        next_day = {**new, "forecast_day": "2026-10-17",
                    "central_offer_date": "2026-11-21",
                    "observed_at": "2026-10-17T07:00:00Z"}
        summary = stability_summary([old, new, next_day], model_version=VERSION)
        self.assertEqual(summary["shift_days"], 2)




class ReconciledOutcomeTests(unittest.TestCase):
    def test_closed_sportsbook_is_excluded_but_separate_head_ai_survives(self):
        from page_hiring_prediction_v2 import _live_opportunities
        snapshot = {"top_processes": [
            {"process_key": "betsson group|head of sb product - data & ai",
             "stage": "first_interview_completed", "status": "active_unknown_decision"},
            {"process_key": "betsson group|head of artificial intelligence",
             "stage": "human_response", "status": "active_unknown_decision"},
            {"process_key": "leovegas mobile gaming group|ai strategy and transformation lead",
             "stage": "final_interview_scheduled", "status": "active_unknown_decision"},
        ]}
        plans = {
            "betsson group|head of sb product - data & ai": {"outcome": "rejected"},
            "betsson group|head of artificial intelligence": {"outcome": "in_progress"},
            "leovegas mobile gaming group|ai strategy and transformation lead": {"outcome": "in_progress"},
        }
        self.assertEqual(
            [p["process_key"] for p in _live_opportunities(snapshot, plans)],
            ["betsson group|head of artificial intelligence",
             "leovegas mobile gaming group|ai strategy and transformation lead"],
        )

if __name__ == "__main__":
    unittest.main()
