"""Regression checks for privacy-preserving, process-level rejection metrics."""
from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_rejection_analytics import (
    _canonical, _in_window, _quality, _source_ref, _recommendations,
    _momentum, _linked_application_days, _chart,
)


class RejectionAnalyticsTests(unittest.TestCase):
    def test_one_decision_per_process_after_reanalysis(self):
        rows = [
            {"id": 1, "process_key": "company|role|1", "decision_outcome": "rejected",
             "updated_at": "2026-10-01", "reason_code": "UNKNOWN"},
            {"id": 2, "process_key": "company|role|1", "decision_outcome": "rejected",
             "updated_at": "2026-10-13", "reason_code": "POSITION_FILLED"},
            {"id": 3, "process_key": "company|role|2", "decision_outcome": "rejected"},
            {"id": 4, "process_key": "company|pending", "decision_outcome": "pending"},
        ]
        deduplicated, invalid = _canonical(rows)
        self.assertEqual(len(deduplicated), 2)
        self.assertEqual(invalid, 0)
        self.assertEqual(next(r for r in deduplicated
                         if r["process_key"] == "company|role|1")["reason_code"],
                         "POSITION_FILLED")

    def test_undated_not_assigned_to_analysis_day(self):
        today = date(2026, 10, 13)
        old = {"decision_date": "2026-09-01", "analyzed_at": "2026-10-13T14:00:00Z"}
        missing = {"decision_date": None, "analyzed_at": "2026-10-13T14:00:00Z"}
        today_row = {"decision_date": "2026-10-13"}
        self.assertFalse(_in_window(old, today, 7))
        self.assertFalse(_in_window(missing, today, 7))
        self.assertTrue(_in_window(missing, today, None))
        self.assertTrue(_in_window(today_row, today, 1))

    def test_unknown_causes_remain_unknown(self):
        rows = [
            {"reason_code": "UNKNOWN", "reason_basis": "insufficient_evidence",
             "decision_date": None, "hiring_stage": "unknown",
             "jd_match_status": "partial", "mailbox_evidence": []},
            {"reason_code": "POSITION_FILLED", "reason_basis": "employer_stated",
             "decision_date": "2026-10-13", "hiring_stage": "application_review",
             "jd_match_status": "not_found", "mailbox_evidence": [
                 {"message_id": "m-1", "provider": "gmail"}]},
        ]
        q = _quality(rows)
        self.assertEqual(q["Unknown motivation"], 1)
        self.assertEqual(q["JD not verified"], 2)
        self.assertEqual(q["No direct mailbox reference"], 1)
        self.assertTrue(_source_ref(rows[1]))
        self.assertFalse(_source_ref(rows[0]))
        advice = _recommendations(rows, date(2026, 10, 13), None)
        self.assertFalse(any("engineering gap" in a["Action"].lower() for a in advice))

    def test_single_seniority_outcome_not_called_a_pattern(self):
        rows = [
            {"reason_code": "ROLE_BELOW_SENIORITY", "reason_basis": "employer_stated",
             "jd_match_status": "partial"},
            {"reason_code": "UNKNOWN", "jd_match_status": "not_found"},
        ]
        advice = _recommendations(rows, date(2026, 10, 13), None)
        self.assertTrue(any("single case" in a["Area"].lower() for a in advice))

    def test_momentum_deduplicates_events_and_excludes_old_rows(self):
        events = [
            {"id": 1, "logical_event_key": "x1", "record_type": "evidence_event",
             "is_primary_analytics_record": True, "employer": "Company",
             "role": "AI Lead", "event_date": "2026-10-11", "is_human_interaction": True},
            {"id": 2, "logical_event_key": "x2", "record_type": "evidence_event",
             "is_primary_analytics_record": True, "employer": "Company",
             "role": "AI Lead", "event_date": "2026-10-12", "is_interview": True},
            {"id": 3, "logical_event_key": "x3", "record_type": "evidence_event",
             "is_primary_analytics_record": True, "employer": "Another",
             "role": "AI Lead", "event_date": "2026-07-01", "is_human_interaction": True},
        ]
        counts = _momentum(events, date(2026, 10, 13), 30)
        self.assertEqual(counts, {"human": 1, "interview": 1, "qualified": 1})

    def test_chart_with_inline_values_serializes_without_tooltip_inference(self):
        # Reproduces the Streamlit Cloud / Altair failure on Decision overview.
        rows = [
            {"Outcome": "Rejected", "Processes": 58},
            {"Outcome": "Not Selected", "Processes": 2},
        ]
        seen = []
        def validate_chart(chart, **kwargs):
            spec = chart.to_dict(validate=True)
            self.assertEqual(spec["encoding"]["tooltip"][0]["type"], "nominal")
            self.assertEqual(spec["encoding"]["tooltip"][1]["type"], "quantitative")
            seen.append(True)
        with patch("page_rejection_analytics.st.altair_chart", side_effect=validate_chart), \
             patch("page_rejection_analytics.st.dataframe") as fallback:
            _chart(rows, "Outcome", "Processes")
        self.assertTrue(seen)
        fallback.assert_not_called()

    def test_reason_chart_color_is_also_explicitly_typed(self):
        rows = [{"Reason": "Cause unknown", "Basis": "Insufficient evidence", "Processes": 52}]
        seen = []
        def validate_chart(chart, **kwargs):
            spec = chart.to_dict(validate=True)
            self.assertEqual(spec["encoding"]["color"]["type"], "nominal")
            self.assertEqual(spec["encoding"]["tooltip"][2]["type"], "nominal")
            seen.append(True)
        with patch("page_rejection_analytics.st.altair_chart", side_effect=validate_chart), \
             patch("page_rejection_analytics.st.dataframe") as fallback:
            _chart(rows, "Reason", "Processes", color="Basis")
        self.assertTrue(seen)
        fallback.assert_not_called()

    def test_latency_needs_direct_link_and_one_application_date(self):
        event = {"id": 11, "logical_event_key": "applied-11",
                 "record_type": "evidence_event", "is_primary_analytics_record": True,
                 "is_application": True, "date_basis": "Exact Outlook timestamp",
                 "event_date": "2026-09-01", "employer": "Company", "role": "AI Lead"}
        decisions = [{"decision_date": "2026-09-11", "source_event_ids": ["11"]},
                     {"decision_date": "2026-09-20", "source_event_ids": []}]
        self.assertEqual(_linked_application_days(decisions, [event]), [10])


if __name__ == "__main__":
    unittest.main()
