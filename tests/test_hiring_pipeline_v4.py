"""Stage, pipeline health, reconciliation and employer-context v4 regressions."""
from datetime import date,timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from hiring_predictor import forecast_hiring, _stage_evidence
from job_search_metrics import scheduled_interview, progression
from hiring_forecast_history import build_snapshot, stability_summary

NOW=date(2026,10,15)

def sample(n, days, **changes):
    row={
        "id":n,"record_type":"evidence_event","is_primary_analytics_record":True,
        "logical_event_key":str(n),"event_date":(NOW-timedelta(days=days)).isoformat(),
        "employer":f"Employer {n}","role":"Head of AI",
        "is_application":True,"is_active":True,"is_closed_or_paused":False,
        "is_negative_decision":False,"activity":"Application submitted",
        "is_human_interaction":False,"is_interview":False,
    }
    row.update(changes)
    return row

class PredictorV4Tests(unittest.TestCase):
    def test_progression_is_inbound_employer_evidence(self):
        inbound=sample(90,2,employer="KPMG",is_application=False,
                       is_human_interaction=True,interaction_direction="inbound",
                       stage_outcome="Advanced to second interview")
        self.assertTrue(progression(inbound))
        self.assertEqual(_stage_evidence(inbound),"progression")
        outbound=dict(inbound,interaction_direction="outbound",
                      stage_outcome="Second interview accepted")
        self.assertFalse(progression(outbound))

    def test_scheduled_is_distinct_from_completed(self):
        invite=sample(91,1,employer="Betsson Group",is_application=False,
                      is_interview=True,is_human_interaction=True,
                      interaction_type="interview_invitation",
                      interaction_direction="inbound",
                      activity="Recruiting interview invitation after CV review",
                      stage_outcome="Invited to next-stage video call")
        self.assertTrue(scheduled_interview(invite))
        self.assertEqual(_stage_evidence(invite),"interview_scheduled")

    def test_unreconciled_applications_do_not_claim_coverage(self):
        rows=[sample(i,i%20+1) for i in range(1,24)]
        rows.append({"id":700,"record_type":"snapshot_metric",
                     "snapshot_date":NOW.isoformat(),
                     "metric_name":"Confirmed application submissions",
                     "metric_value":18})
        result=forecast_hiring(rows,NOW)
        self.assertTrue(result["sources"]["application_reconciliation_needed"])
        self.assertIsNone(result["sources"]["event_coverage"])

    def test_external_vacancy_title_match_is_not_confirmed_offer(self):
        rows=[sample(i,i%20+1) for i in range(1,24)]
        base=forecast_hiring(rows,NOW)
        external={"source":"jobwise_verified_vacancy_catalog",
                  "vacancies":[{"employer_key":"employer 1",
                                "role_key":"head of ai",
                                "advertised_active":1,
                                "requisition_confirmed":False}]}
        changed=forecast_hiring(rows,NOW,employer_activity=external)
        self.assertEqual(base["curve"],changed["curve"])
        self.assertEqual(changed["employer_context"]["numeric_effect"],0)
        self.assertEqual(changed["employer_context"]["verified_matching_role_listings"],1)

    def test_archive_has_no_employer_details_or_fake_accuracy(self):
        rows=[sample(i,i%20+1) for i in range(1,24)]
        result=forecast_hiring(rows,NOW)
        archived=build_snapshot(result,{"jobs":"digest","market":"digest2"})
        self.assertNotIn("employer",str(archived).lower())
        self.assertEqual(len(archived["source_signature"]),64)
        self.assertIsNone(stability_summary([])["historical_accuracy_pct"])

if __name__=="__main__":
    unittest.main()
