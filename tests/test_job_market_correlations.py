"""Regression gates for independent market observations and honest cross-dataset tests."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from job_market_correlations import analyze_market, _deduplicate_market, _screen


def market(i, observed, *, key="services_pmi", metric=57.4, published=None, score=.5):
    return {
        "id": i, "series_key": "swedbank|services_pmi|monthly|se",
        "indicator_key": key, "indicator_name": "Services PMI",
        "observation_date": observed, "period_end": observed, "frequency": "monthly",
        "metric_value": metric, "signal_score": score, "published_at": published,
        "updated_at": observed, "source_organization": "Swedbank",
        "is_quantitative": True,
    }


def event(i, when, *, application=False, interaction=False):
    return {
        "id": i, "record_type": "evidence_event", "is_primary_analytics_record": True,
        "logical_event_key": str(i), "employer": "Company " + str(i), "role": "AI Lead",
        "event_date": when, "is_application": application,
        "is_human_interaction": interaction,
        "interaction_direction": "inbound" if interaction else None,
    }


class SwedishMarketCorrelationTests(unittest.TestCase):
    def test_one_observation_does_not_generate_trend_or_market_correlation(self):
        data = [market(1,"2026-09-30",published="2026-10-05")]
        jobs = [event(10,"2026-07-07",application=True),
                event(11,"2026-08-18",application=True),
                event(12,"2026-09-21",interaction=True)]
        report = analyze_market(data, jobs, None, today=date(2026,10,9))
        self.assertEqual(report["coverage"]["indicators"],1)
        self.assertEqual(report["coverage"]["observations"],1)
        self.assertEqual(report["coverage"]["repeat_series"],0)
        self.assertEqual(report["coverage"]["job_full_months"],2)
        self.assertEqual(report["coverage"]["tested"],0)
        self.assertFalse(report["trends"])
        self.assertFalse(report["findings"])

    def test_revision_of_same_period_is_not_independent_market_sample(self):
        original=market(1,"2026-09-30",metric=56.5,published="2026-10-01")
        revision=market(2,"2026-09-30",metric=57.4,published="2026-10-05")
        report=analyze_market([original,revision],[],None,today=date(2026,10,9))
        self.assertEqual(report["coverage"]["observations"],1)
        self.assertEqual(report["latest"][0]["metric_value"],57.4)

    def test_subjective_signal_score_does_not_change_raw_market_series(self):
        a=market(1,"2026-08-31",metric=54.2,published="2026-09-02",score=-1)
        b=market(2,"2026-09-30",metric=57.4,published="2026-10-05",score=1)
        report=analyze_market([a,b],[],None,today=date(2026,10,9))
        self.assertEqual(report["coverage"]["repeat_series"],1)
        self.assertEqual(report["trends"][0]["Change"],3.2)
        self.assertFalse(report["findings"])

    def test_undated_release_cannot_look_ahead(self):
        data=[market(i, f"2026-{m:02d}-01",metric=i,published=None)
              for i,m in enumerate(range(1,10),1)]
        jobs=[event(20,"2025-12-31",application=True),
              event(21,"2026-03-12",application=True)]
        report=analyze_market(data,jobs,None,today=date(2026,10,9))
        self.assertEqual(report["coverage"]["repeat_series"],1)
        self.assertEqual(report["coverage"]["tested"],0)

    def test_sparse_series_must_not_be_promoted_by_high_r(self):
        r=_screen(list(range(9)),[0,1,2,3,4,5,6,7,8])
        self.assertIsNone(r["r"])
        self.assertEqual(r["status"],"Insufficient history")

    def test_current_partial_month_not_a_full_search_month(self):
        jobs=[event(1,"2026-07-09",application=True),
              event(2,"2026-08-11",application=True),
              event(3,"2026-09-10",application=True),
              event(4,"2026-10-08",application=True)]
        report=analyze_market([],jobs,None,today=date(2026,10,9))
        self.assertEqual([p["Month"] for p in report["monthly"]],["2026-08-01","2026-09-01"])
        self.assertEqual([p["applications"] for p in report["monthly"]],[1,1])


if __name__ == "__main__":
    unittest.main()
