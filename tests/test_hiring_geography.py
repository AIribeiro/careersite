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
        self.assertEqual(b["geography_context"]["counts"]["needs_verification"],34)
        self.assertEqual(c["geography_context"]["counts"]["impractical"],1)

    def test_location_from_actual_raw_linkedin_payload(self):
        """Regression: the location field existed but the owner query omitted raw_data."""
        jobs=_jobs()
        jobs[0]["raw_data"]={
            "location":"Stockholm (Hybrid)",
            "linkedin_job_id":"test-job-identifier",
        }
        report=assess_geographic_pipeline(jobs,TODAY)
        first=next(p for p in report["opportunities"]
                   if p["employer"]=="enterprise 1")
        self.assertEqual(first["advertised_location"],"stockholm (hybrid)")
        self.assertEqual(first["work_model"],"hybrid")
        self.assertTrue(first["advertised_location_recorded"])
        self.assertTrue(first["arrangement_recorded"])
        self.assertEqual(first["location_evidence_source"],"job_search_source")
        self.assertEqual(report["advertised_locations_recorded"],1)
        self.assertEqual(report["work_arrangements_recorded"],1)

    def test_exact_owner_jobwise_fallback_without_improper_overrides(self):
        jobs=_jobs()
        # No source metadata initially.
        jobs[0].pop("raw_data",None)
        enrichment={
            "method":"linked_user_workspace_exact_company_title",
            "unique_locations":[{
                "employer_key":"enterprise 1",
                "role_key":"head of ai",
                "advertised_location":"Göteborg, Stockholm",
                "country":"Sweden",
                "quality":"exact_company_role_unique_location",
            },{
                "employer_key":"enterprise 2",
                "role_key":"head of ai",
                "advertised_location":"Malmo",
                "country":"Sweden",
                "quality":"exact_company_role_unique_location",
            }]
        }
        report=assess_geographic_pipeline(jobs,TODAY,additional_locations=enrichment)
        self.assertEqual(report["advertised_locations_recorded"],2)
        self.assertEqual(report["source_counts"]["matched_jobwise_application"],2)
        p=next(r for r in report["opportunities"] if r["employer"]=="enterprise 1")
        self.assertEqual(p["location_evidence_source"],"matched_jobwise_application")
        self.assertEqual(p["status"],"compatible")
        # Primary job evidence must win over a Jobwise listing (possibly
        # changed or a secondary posting).
        jobs[0]["raw_data"]={"location":"Stockholm (On-site)"}
        report=assess_geographic_pipeline(jobs,TODAY,additional_locations=enrichment)
        p=next(r for r in report["opportunities"] if r["employer"]=="enterprise 1")
        self.assertEqual(p["advertised_location"],"stockholm (on-site)")
        self.assertEqual(p["location_evidence_source"],"job_search_source")
        self.assertEqual(report["advertised_locations_recorded"],2)

    def test_official_role_source_preserves_explicit_hybrid_model(self):
        jobs=_jobs()
        jobs[0].pop("raw_data",None)
        external={
            "method":"owner_workspace_and_verified_catalog_unique_company_title",
            "unique_locations":[{
                "employer_key":"enterprise 1","role_key":"head of ai",
                "advertised_location":"Stockholm, Sweden",
                "work_model":"Hybrid","country":"Sweden",
                "evidence_source":"official_employer_vacancy",
                "source_url":"https://example.com/official-role",
                "quality":"exact_company_role_unique_location",
            },{
                "employer_key":"enterprise 2","role_key":"head of ai",
                "advertised_location":"Jönköping","country":"Sweden",
                "evidence_source":"externally_verified_job_board",
                "quality":"exact_company_role_unique_location",
            }]
        }
        r=assess_geographic_pipeline(jobs,TODAY,additional_locations=external)
        self.assertEqual(r["advertised_locations_recorded"],2)
        self.assertEqual(r["source_counts"]["official_employer_vacancy"],1)
        self.assertEqual(r["source_counts"]["externally_verified_job_board"],1)
        item=next(x for x in r["opportunities"] if x["employer"]=="enterprise 1")
        self.assertEqual(item["work_model"],"hybrid")
        self.assertTrue(item["arrangement_recorded"])
        self.assertEqual(item["status"],"conditional")
        self.assertEqual(item["probability_effect"],0)

    def test_ambiguous_or_wrong_enrichment_is_rejected(self):
        jobs=_jobs()
        jobs[0].pop("raw_data",None)
        evidence={"method":"linked_user_workspace_exact_company_title",
                  "unique_locations":[
                     {"employer_key":"enterprise 1","role_key":"head of ai",
                      "advertised_location":"Stockholm",
                      "quality":"exact_company_role_unique_location"},
                     {"employer_key":"enterprise 1","role_key":"head of ai",
                      "advertised_location":"Göteborg",
                      "quality":"exact_company_role_unique_location"}]}
        merged=assess_geographic_pipeline(jobs,TODAY,additional_locations=evidence)
        self.assertEqual(merged["advertised_locations_recorded"],0)
        wrong=assess_geographic_pipeline(jobs,TODAY,additional_locations={
            **evidence,"method":"unverified_public_web_lookup",
        })
        self.assertEqual(wrong["advertised_locations_recorded"],0)

    def test_no_new_application_or_forecast_boost_from_geography_enrichment(self):
        jobs=_jobs()
        for job in jobs:
            job.pop("raw_data",None)
        enriched={
            "method":"linked_user_workspace_exact_company_title",
            "unique_locations":[{
                "employer_key":"enterprise 1","role_key":"head of ai",
                "advertised_location":"Gothenburg","country":"Sweden",
                "quality":"exact_company_role_unique_location",
            }]
        }
        a=forecast_hiring(jobs,TODAY)
        b=forecast_hiring(jobs,TODAY,geography_locations=enriched)
        self.assertEqual(a["curve"],b["curve"])
        self.assertEqual(a["crossings"],b["crossings"])
        self.assertEqual(a["reliability"],b["reliability"])
        self.assertEqual(a["sources"],b["sources"])
        self.assertGreater(b["geography_context"]["advertised_locations_recorded"],
                           a["geography_context"]["advertised_locations_recorded"])

    def test_remote_country_is_not_assumed_to_authorize_sweden(self):
        remote_poland=assess_opportunity({"advertised_location":"Poland (Remote)"})
        self.assertEqual(remote_poland["status"],"needs_verification")
        self.assertFalse(remote_poland["advertised_in_sweden"])
        self.assertEqual(remote_poland["work_model"],"remote")
        hybrid_stockholm=assess_opportunity({"advertised_location":"Stockholm (Hybrid)"})
        self.assertEqual(hybrid_stockholm["status"],"conditional")
        self.assertEqual(hybrid_stockholm["work_model"],"hybrid")
        onsite_gbg=assess_opportunity({"advertised_location":"Göteborg (On-site)"})
        self.assertEqual(onsite_gbg["status"],"compatible")

    def test_literal_title_locality_inference_is_labeled_not_verified(self):
        from hiring_geography import infer_from_role_title
        self.assertEqual(
            infer_from_role_title("Digital Engineering Data Lead - Sweden / Gothenburg / Onsite")
                ["advertised_location"],
            "Gothenburg, Sweden",
        )
        self.assertEqual(
            infer_from_role_title("Service Delivery Manager Västerås Sweden")
                ["advertised_location"],
            "Västerås, Sweden",
        )
        self.assertIsNone(infer_from_role_title("Head of AI"))
        self.assertIsNone(infer_from_role_title("Role not surfaced in LinkedIn receipt"))
        self.assertEqual(
            infer_from_role_title("Director Analytics Sweden")["advertised_location"],
            "Sweden (city not specified)",
        )

    def test_geographic_assessment_is_complete_without_fake_city(self):
        jobs=_jobs()
        jobs[0].pop("raw_data",None)
        summary=assess_geographic_pipeline(jobs,TODAY)
        self.assertEqual(summary["assessment_completion_pct"],100)
        self.assertEqual(summary["source_verified_locations"],0)
        self.assertEqual(summary["explicit_title_inferences"],0)
        self.assertEqual(summary["unresolved_locations"],34)
        self.assertEqual(summary["geographically_assessed"],34)
        self.assertEqual(len(summary["resolution_queue"]),34)
        self.assertTrue(all(row["advertised_location"] is None
                            for row in summary["opportunities"]))
        self.assertEqual(summary["numeric_effect"],0)

    def test_title_inference_does_not_move_forecast_probabilities(self):
        jobs=_jobs()
        jobs[0].pop("raw_data",None)
        jobs[0]["role"]="Head of AI Stockholm"
        baseline=forecast_hiring(jobs,TODAY)
        summary=baseline["geography_context"]
        self.assertEqual(summary["explicit_title_inferences"],1)
        self.assertEqual(summary["source_verified_locations"],0)
        self.assertEqual(summary["assessment_completion_pct"],100)
        # Merely placing a role geographically cannot make the probability
        # curve stronger, nor change the reliability score.
        jobs[0]["role"]="Head of AI"
        original=forecast_hiring(jobs,TODAY)
        self.assertEqual(baseline["curve"],original["curve"])
        self.assertEqual(baseline["reliability"],original["reliability"])

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
            "status":"Rejected / closed",
            "raw_data":{"advertised_location":"Stockholm"}
        })
        result=assess_geographic_pipeline(jobs,TODAY)
        self.assertEqual(result["total_live_processes"],33)
        self.assertTrue(all(p["employer"]!="future employer"
                            for p in result["opportunities"]))


if __name__ == "__main__":
    unittest.main()
