"""Regression checks for the private, uncalibrated hiring predictor."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hiring_predictor import forecast_hiring
from page_analytics_overview import _evidence_signature, _changes_since_last_check


TODAY = date(2026, 10, 9)


def event(n: int, days_ago: int, *, employer: str | None = None,
          activity: str = "Application submitted", **flags) -> dict:
    r = {
        "id": n, "record_type": "evidence_event",
        "is_primary_analytics_record": True, "logical_event_key": str(n),
        "event_date": (TODAY - timedelta(days=days_ago)).isoformat(),
        "employer": employer or f"Employer {n}",
        "role": "Head of AI", "activity": activity,
        "is_application": True, "is_active": True,
        "is_closed_or_paused": False, "is_negative_decision": False,
        "is_human_interaction": False, "is_interview": False,
        "event_type": None, "stage_outcome": None,
    }
    r.update(flags)
    return r


class HiringPredictorTests(unittest.TestCase):
    def test_no_evidence_never_fabricates_date(self):
        result = forecast_hiring([], TODAY)
        self.assertEqual(result["status"], "insufficient")
        self.assertEqual(result["curve"], [])

    def test_recent_pipeline_yields_ordered_scenarios(self):
        jobs = [event(n, days_ago=(n * 3) % 52 + 1) for n in range(1, 37)]
        jobs.append(event(80, 12, employer="Interview employer",
                          activity="Interview held", is_application=False,
                          is_interview=True))
        result = forecast_hiring(jobs, TODAY)
        self.assertEqual(result["status"], "scenario")
        self.assertEqual(result["confidence"], "Low — uncalibrated")
        for row in result["curve"]:
            self.assertLessEqual(row["Conservative"], row["Current pace"])
            self.assertLessEqual(row["Current pace"], row["Faster conversion"])
            self.assertGreaterEqual(row["Conservative"], 0)
            self.assertLessEqual(row["Faster conversion"], 1)
        self.assertTrue(result["crossings"]["Current pace"])

    def test_contextual_market_and_site_data_cannot_inflate_probabilities(self):
        jobs = [event(n, days_ago=n % 42 + 1) for n in range(1, 26)]
        baseline = forecast_hiring(jobs, TODAY)
        enriched = forecast_hiring(
            jobs, TODAY,
            market_model={"coverage":{"indicators":8,"observations":32},
                          "findings":[{"status":"Repeated association",
                                       "outcome":"interviews"}]},
            portfolio_correlation={"ranked":[{"status":"Repeated association",
                                               "outcome":"responses"}]},
            hiring_quality={"quality_summary":{"analysis_eligible_sessions":123,
                                               "hiring_intent_sessions":4}},
        )
        self.assertEqual(baseline["curve"], enriched["curve"])
        self.assertEqual(enriched["sources"]["market_indicator_series"], 8)
        self.assertEqual(enriched["sources"]["qualified_portfolio_sessions_30d"], 123)

    def test_source_fingerprint_detects_only_recorded_changes(self):
        previous = {
            "jobs": _evidence_signature([{"id": 1, "status": "applied"}]),
            "market": _evidence_signature([{"id": 1, "score": 15}]),
            "site": _evidence_signature({"sessions": 2}),
        }
        self.assertEqual(_changes_since_last_check(None, previous), [])
        self.assertEqual(_changes_since_last_check(previous, dict(previous)), [])
        changed = dict(previous)
        changed["jobs"] = _evidence_signature([{"id": 1, "status": "interview"}])
        changed["site"] = _evidence_signature({"sessions": 3})
        self.assertEqual(
            _changes_since_last_check(previous, changed),
            ["job search", "portfolio activity"],
        )
        self.assertEqual(
            _changes_since_last_check(previous, {"market": previous["market"]}), [],
        )
        self.assertEqual(
            _evidence_signature({"a": 1, "b": 2}),
            _evidence_signature({"b": 2, "a": 1}),
        )

    def test_future_events_are_not_used_to_predict_today(self):
        now = [event(n, n % 24 + 1) for n in range(1, 20)]
        future = event(999, -10, event_type="offer_received",
                       stage_outcome="offer_received", is_application=False)
        self.assertEqual(forecast_hiring(now, TODAY)["curve"],
                         forecast_hiring(now + [future], TODAY)["curve"])

    def test_confirmed_offer_supersedes_a_first_offer_forecast(self):
        jobs = [event(1, 30), event(
            2, 1, employer="Employer 1", is_application=False,
            event_type="offer_received", stage_outcome="offer_received",
            activity="Formal offer received")]
        result = forecast_hiring(jobs, TODAY)
        self.assertEqual(result["status"], "offer_recorded")
        self.assertEqual(result["sources"]["recorded_offer_events"], 1)


if __name__ == "__main__":
    unittest.main()
