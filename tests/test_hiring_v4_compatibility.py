"""Regression: production v4 forecasts must remain readable by both owner views.

The legacy v2 stage model remains a valid historical snapshot, but obsolete beta
models and accidental private fields in the date-only projection stay rejected.
"""
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from page_hiring_prediction_v2 import (
    VERSION, CURRENT_VERSION, validate_prediction_v2,
)
from site_analytics_public import validate_public_hiring_timing_v2


class HiringV4CompatibilityTests(unittest.TestCase):
    def test_owner_snapshot_accepts_v4_and_historical_v2_only(self):
        base = {
            "portfolio_credibility_index": 43.5,
            "cohort": {"total": 15},
            "top_processes": [],
            "leading_stage_scenario": {
                "offer_central": "2026-11-12",
                "start_central": "2026-12-10",
            },
        }
        for version in (VERSION, CURRENT_VERSION):
            row = {**base, "model_version": version}
            self.assertEqual(validate_prediction_v2(row)["model_version"], version)
        for version in ("hiring-beta-4.3-assumed-date-provisional", "unknown"):
            with self.assertRaises(ValueError):
                validate_prediction_v2({**base, "model_version": version})

    def test_published_date_projection_accepts_current_v4_without_exposing_identity(self):
        fields = {
            "as_of": "2026-10-27",
            "offer_earliest": "2026-11-01",
            "offer_central": "2026-11-12",
            "offer_latest": "2026-12-06",
            "start_earliest": "2026-11-15",
            "start_central": "2026-12-10",
            "start_latest": "2027-01-17",
        }
        for version in (VERSION, CURRENT_VERSION):
            row = {"model_version": version, **fields}
            verified = validate_public_hiring_timing_v2([row], today=date(2026, 10, 27))
            self.assertTrue(verified["available"])
            self.assertEqual(verified["model_version"], version)
            self.assertEqual(verified["start_central"], "2026-12-10")
        with self.assertRaises(RuntimeError):
            validate_public_hiring_timing_v2(
                [{"model_version": CURRENT_VERSION, **fields, "employer": "private"}],
                today=date(2026, 10, 27),
            )
        with self.assertRaises(RuntimeError):
            validate_public_hiring_timing_v2(
                [{"model_version": "hiring-beta-4.3-assumed-date-provisional", **fields}],
                today=date(2026, 10, 27),
            )
        stale = validate_public_hiring_timing_v2(
            [{"model_version": CURRENT_VERSION, **fields}], today=date(2027, 1, 1)
        )
        self.assertFalse(stale["available"])


if __name__ == "__main__":
    unittest.main()
