"""Tests for official JobTech target-family momentum, release timing and lags."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from jobtech_demand_forecast import analyze_jobtech_demand, jobtech_lag_diagnostics, JOBTECH_KEYS
from hiring_forecast_signals import market_adjustment
from hiring_predictor import forecast_hiring

COUNTS = {
    "tier_a": [10,12,9,18],
    "national": [12,15,10,19],
    "stockholm": [6,8,6,12],
    "vgr": [2,2,1,3],
}
MONTHS = ((2026,6,30),(2026,7,31),(2026,8,31),(2026,9,30))


def _market(counts=None, seen="2026-10-11", *, version="v1"):
    counts = counts or COUNTS
    history = {}
    for key, values in counts.items():
        rows = []
        for index, value in enumerate(values):
            month = index + 6
            if month > 12:
                continue
            end = date(2026, month+1, 1) - timedelta(days=1) if month < 12 else date(2026,12,31)
            row = {
                "indicator_key": JOBTECH_KEYS[key],
                "frequency":"monthly",
                "period_start": date(2026, month, 1).isoformat(),
                "period_end": end.isoformat(),
                "observation_date":end.isoformat(),
                "metric_value": str(value),
                "is_current":index==len(values)-1,
                "source_registry_key":"af_jobtech_target_demand",
                "first_seen_at": seen if month < 10 else "2026-11-05",
                "source_accessed_at":seen if month < 10 else "2026-11-05",
                "raw_data":{"methodology_version":version,
                            "date_semantics":"publication month"},
                "source_organization":"Arbetsförmedlingen JobTech",
                "confidence_score":90 if key not in ("vgr","stockholm") else 78,
                "relevance_score":100,
            }
            rows.append(row)
        history[JOBTECH_KEYS[key]] = rows
    return {"groups":history,
            "latest":[v[-1] for v in history.values()]}


class JobTechDemandTests(unittest.TestCase):
    def test_verified_september_rebound_is_small_positive_unconfirmed(self):
        model = _market()
        result = analyze_jobtech_demand(model,date(2026,10,11))
        self.assertGreater(result["effect"],0)
        self.assertLessEqual(result["effect"],.012)
        self.assertEqual(result["latest_month"],"2026-09")
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["history_months"],4)
        self.assertEqual(result["families"]["tier_a"]["previous"],9)
        self.assertEqual(result["families"]["tier_a"]["value"],18)
        self.assertEqual(result["families"]["national"]["value"],19)
        self.assertEqual(result["families"]["vgr"]["value"],3)
        self.assertLess(result["families"]["vgr"]["quality"],
                        result["families"]["tier_a"]["quality"])
        self.assertEqual(result["configuration"]["weights"]["tier_a"],.45)

    def test_october_10_cannot_see_october_11_backfill(self):
        model=_market()
        result=analyze_jobtech_demand(model,date(2026,10,10))
        self.assertEqual(result["effect"],0)
        self.assertIsNone(result["latest_month"])
        self.assertFalse(result["confirmed"])

    def test_strict_methodology_lock_and_discontinuous_months(self):
        bad=analyze_jobtech_demand(_market(version="v2"),date(2026,10,11))
        self.assertEqual(bad["effect"],0)
        model=_market()
        model["groups"][JOBTECH_KEYS["tier_a"]].pop(1)
        missing=analyze_jobtech_demand(model,date(2026,10,11))
        self.assertEqual(missing["effect"],0)

    def test_conflicting_duplicate_month_cannot_silently_rewrite_history(self):
        model=_market()
        original=model["groups"][JOBTECH_KEYS["tier_a"]][-1]
        model["groups"][JOBTECH_KEYS["tier_a"]].append({
            **original,"metric_value":"500","first_seen_at":"2026-10-11",
        })
        result=analyze_jobtech_demand(model,date(2026,10,11))
        self.assertEqual(result["effect"],0)
        self.assertTrue(any("Conflicting JobTech" in warning for warning in result["alerts"]))

    def test_october_confirmation_unlocks_larger_but_bounded_coefficient(self):
        data={key: counts + [counts[-1]+1] for key,counts in COUNTS.items()}
        result=analyze_jobtech_demand(_market(data),date(2026,11,10))
        self.assertTrue(result["confirmed"])
        self.assertEqual(result["latest_month"],"2026-10")
        self.assertEqual(result["cap"],.04)
        self.assertGreater(result["effect"],0)
        self.assertLessEqual(result["effect"],.04)

    def test_negative_reversal_yields_negative_momentum(self):
        data={key:[30,22,14,5] for key in COUNTS}
        result=analyze_jobtech_demand(_market(data),date(2026,10,11))
        self.assertLess(result["effect"],0)
        self.assertGreaterEqual(result["effect"],-.012)

    def test_configurable_weights_are_normalized(self):
        model=_market()
        config={"weights":{"tier_a":.60,"national":.25,"stockholm":.10,"vgr":.05}}
        changed=analyze_jobtech_demand(model,date(2026,10,11),config=config)
        self.assertNotEqual(changed["score"],
                            analyze_jobtech_demand(model,date(2026,10,11))["score"])
        with self.assertRaises(ValueError):
            analyze_jobtech_demand(model,date(2026,10,11),config={"weights":{"tier_a":2}})

    def test_lag_screens_do_not_use_backfilled_june_august_hiring_outcomes(self):
        result=jobtech_lag_diagnostics(_market(),[],date(2026,10,11))
        self.assertEqual(result["eligible_months"],1)
        self.assertTrue(all(
            x["status"]=="Insufficient prospective history"
            for x in result["tests"]
        ))
        self.assertEqual(
            {x["outcome"]:x["lag_days"] for x in result["tests"]},
            {"opportunities_discovered":[0,14],
             "applications":[0,21],
             "employer_interactions":[7,30],
             "interviews":[14,45],
             "offers":[30,75]},
        )

    def test_jobtech_joins_existing_market_budget_without_double_counting(self):
        moment=date(2026,10,11)
        jobtech_only=market_adjustment(_market(),moment)
        self.assertGreater(jobtech_only["effect"],0)
        self.assertEqual(jobtech_only["jobtech"]["effect"],
                         jobtech_only["effect"])
        self.assertLessEqual(jobtech_only["effect"],.12)
        self.assertEqual(sum(d["topic"]=="target_role_demand"
                             for d in jobtech_only["drivers"]),1)
        # Adding a generic positive IT hiring signal must not count it at full
        # weight independently of the overlapping official targeted demand.
        overlap=_market()
        overlap["latest"].append({
            "indicator_key":"employment_outlook_it_tech",
            "observation_date":"2026-09-30",
            "published_at":"2026-10-01",
            "signal_score":.9,"relevance_score":95,"confidence_score":95,
        })
        with_jobtech=market_adjustment(overlap,moment)
        without_jobtech=market_adjustment({"latest":[overlap["latest"][-1]]},moment)
        generic_in_combined=next(d for d in with_jobtech["drivers"]
                                 if d["topic"]=="it_tech_demand")
        generic_alone=next(d for d in without_jobtech["drivers"]
                           if d["topic"]=="it_tech_demand")
        self.assertAlmostEqual(generic_in_combined["effect"],
                               generic_alone["effect"]/2,delta=.0002)


if __name__=="__main__":
    unittest.main()
