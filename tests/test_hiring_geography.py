"""Geographic demand != opportunity feasibility: hiring beta regressions."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hiring_geography import (
    assess_opportunity, assess_geographic_pipeline, GEOGRAPHY_POLICY_VERSION,
)
from hiring_predictor import forecast_hiring


TODAY = date(2026, 10, 15)


def _jobs(location="Stockholm", **attrs):
    events = []
    for n in range(1, 35):
        original = {
            "id": n, "record_type": "evidence_event",
            "is_primary_analytics_record": True, "logical_event_key": f"app-{n}",
            "event_date": (TODAY - timedelta(days=n + 2)).isoformat(),
            "employer":f"Enterprise {n}", "role":"Head of AI",
            "activity":"Application sent", "is_application":True,
            "is_active":True,"is_closed_or_paused":False,
            "is_negative_decision":False,"is_human_interaction":False,
            "is_interview":False,
        }
        if n == 1:
            original["raw_data"] = {"advertised_location":location,
                                    "country_code":"SE", **attrs}
        events.append(original)
    return events


class GeographicFeasibilityTests(unittest.TestCase):
    def test_national_market_is_not_reduced_to_gothenburg(self):
        assessed=assess_opportunity({
            "advertised_location":"Stockholm, Sweden",
            "work_model":"hybrid",
            "multi_office_employer":True,
        })
        self.assertEqual(assessed["status"],"needs_verification")
        self.assertTrue(assessed["advertised_in_sweden"])
        self.assertEqual(assessed["probability_effect"],0)
        self.assertIn("office flexibility",assessed["reason"])

    def test_stockholm_multi_office_with_confirmed_gothenburg_option(self):
        a=assess_opportunity({
            "advertised_location":"Stockholm, Sweden",
            "work_model":"hybrid",
            "multi_office_employer":True,
            "gothenburg_office_option":True,
        })
        self.assertEqual(a["status"],"compatible")
        self.assertEqual(a["probability_effect"],0)

    def test_approved_remote_sweden_is_compatible_regardless_of_ad_office(self):
        x=assess_opportunity({"advertised_location":"Stockholm",
                             "country_code":"SE", "work_model":"fully_remote"})
        self.assertEqual(x["status"],"compatible")
        self.assertEqual(x["probability_effect"],0)

    def test_travel_has_no_automatic_penalty(self):
        a=assess_opportunity({"advertised_location":"Stockholm",
                              "country_code":"SE","travel_required":"frequent",
                              "multi_office_employer":True})
        self.assertNotEqual(a["status"],"impractical")
        b=assess_opportunity({"advertised_location":"Stockholm",
                              "country_code":"SE","travel_required":"frequent",
                              "travel_feasible":False})
        self.assertEqual(b["status"],"impractical")

    def test_relocation_quality_and_family_are_explicit_conditions(self):
        facts={"advertised_location":"Stockholm","country_code":"SE",
               "relocation_required":True,"relocation_feasible":True,
               "mandate_quality":"strong","compensation_fit":"competitive",
               "executive_sponsorship":"confirmed",
               "family_feasibility":"feasible"}
        ready=assess_opportunity(facts)
        self.assertEqual(ready["status"],"conditional")
        self.assertTrue(all(ready["relocation_readiness"].values()))
        unresolved=assess_opportunity({**facts,"family_feasibility":None})
        self.assertEqual(unresolved["status"],"conditional")
        self.assertFalse(unresolved["relocation_readiness"]["family"])
        impossible=assess_opportunity({**facts,"family_feasibility":"no"})
        self.assertEqual(impossible["status"],"impractical")

    def test_missing_metadata_is_not_equivalent_to_impossible(self):
        self.assertEqual(assess_opportunity({})["status"],"needs_verification")
        self.assertEqual(assess_opportunity({
            "advertised_location":"Stockholm",
            "country_code":"SE",
        })["status"],"conditional")

    def test_city_and_travel_preferences_do_not_move_offers_or_reliability(self):
        a=forecast_hiring(_jobs("Gothenburg",work_model="onsite"),TODAY)
        b=forecast_hiring(_jobs("Stockholm",multi_office_employer=True,
                                travel_required="frequent"),TODAY)
        c=forecast_hiring(_jobs("Stockholm",relocation_required=True,
                                family_feasibility="no"),TODAY)
        for changed in (b,c):
            self.assertEqual(changed["curve"],a["curve"])
            self.assertEqual(changed["crossings"],a["crossings"])
            self.assertEqual(changed["windows"],a["windows"])
            self.assertEqual(changed["reliability"],a["reliability"])
            self.assertEqual(changed["drivers"]["market"],a["drivers"]["market"])
            self.assertEqual(changed["geography_context"]["numeric_effect"],0)
            self.assertFalse(changed["geography_context"]["automatic_stockholm_penalty"])
            self.assertEqual(changed["geography_context"]["primary_market"],"Sweden")
        self.assertEqual(a["geography_context"]["policy_version"],GEOGRAPHY_POLICY_VERSION)
        self.assertEqual(a["geography_context"]["counts"]["compatible"],1)
        self.assertEqual(b["geography_context"]["counts"]["needs_verification"],33)
        self.assertEqual(c["geography_context"]["counts"]["impractical"],1)

    def test_closed_and_future_opportunities_are_not_geographic_evidence(self):
        jobs = _jobs()
        jobs.append({
            "id":80, "record_type":"evidence_event",
            "is_primary_analytics_record":True,"logical_event_key":"future",
            "event_date":(TODAY+timedelta(days=7)).isoformat(),
            "employer":"Future employer","role":"Director AI",
            "is_application":True,"is_active":True,
            "raw_data":{"advertised_location":"Stockholm"}
        })
        jobs.append({
            "id":81,"record_type":"evidence_event",
            "is_primary_analytics_record":True,"logical_event_key":"closed",
            "event_date":(TODAY-timedelta(days=1)).isoformat(),
            "employer":"Enterprise 2","role":"Head of AI",
            "is_application":False,"is_active":False,
            "is_closed_or_paused":True,"is_negative_decision":True,
            "raw_data":{"advertised_location":"Stockholm"}
        })
        result=assess_geographic_pipeline(jobs,TODAY)
        self.assertEqual(result["total_live_processes"],33)
        self.assertTrue(all(p["employer"]!="future employer"
                            for p in result["opportunities"]))


if __name__ == "__main__":
    unittest.main()
