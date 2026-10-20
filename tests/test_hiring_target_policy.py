"""Mandate-aligned AI leadership policy and non-scoring forecast test."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))
from hiring_target_policy import (POLICY_VERSION, classify_title,
                                  assess_role, catalog_sensitivity,
                                  pipeline_sensitivity)
from hiring_market_shadow import evaluate_market_shadow
from page_market_shadow import fetch_role_catalog


def vacancy(title, company, first="2026-10-10", **kwargs):
    return {"title":title,"company_name":company,"first_seen_at":first,
            "country_code":"SE","is_active":True,**kwargs}


class RolePolicyTests(unittest.TestCase):
    def test_ambition_separate_from_conversion(self):
        for role in ("AI Director","Director, AI Transformation",
                     "Director of AI Transformation","Head of AI",
                     "VP Domain Head, AI Scaling Hub"):
            with self.subTest(role=role):
                self.assertEqual(classify_title(role),"primary")
        for role in ("Senior Manager, AI Strategy","AI Strategy Lead",
                     "AI Transformation Lead","Head of AI Adoption",
                     "AI Lead - Manager - Tax & Legal Technology",
                     "AI Capability Lead","AI Productivity Lead"):
            with self.subTest(role=role):
                self.assertEqual(classify_title(role),"functional")
        self.assertEqual(classify_title("Head of SB Product - Data & AI"),"adjacent")
        self.assertEqual(classify_title("AI Engineer"),"outside_or_uncertain")
        self.assertEqual(classify_title("Senior Director of IT Operations"),"outside_or_uncertain")

    def test_mandate_evidence_never_auto_verifies_vacancy(self):
        a=assess_role("AI Strategy Lead","Own the AI roadmap, portfolio, "
                      "operating model and governance across business functions.")
        self.assertEqual(a["scope"],"strategic_signals_review")
        self.assertFalse(a["verified_suitable"])
        self.assertEqual(assess_role("AI Strategy Lead")["scope"],"mandate_unverified")
        self.assertEqual(assess_role("AI Transformation Lead",
                    "Primary responsibilities are hands-on coding of ML models.")["scope"],
                         "craft_conflict_review")

    def test_catalog_sensitivity_deduplicates_and_does_not_invent_probabilities(self):
        items=[vacancy("Head of AI","One"),
               vacancy("Head of AI","One","2026-10-12"),
               vacancy("AI Strategy Lead","Two"),
               vacancy("Head of AI Adoption","Three"),
               vacancy("AI Engineer","Four"),
               {"title":"Director of AI","company_name":"Five",
                "country_code":"SE","is_active":False,
                "first_seen_at":"2026-10-13"}]
        r=catalog_sensitivity(items,date(2026,10,20))
        self.assertEqual(r["sample_size"],4)
        self.assertEqual(r["primary"],1)
        self.assertEqual(r["incremental_functional"],2)
        self.assertEqual(r["primary_plus_functional"],3)
        self.assertEqual(r["verified_suitable"],0)
        self.assertEqual(r["policy_version"],POLICY_VERSION)
        self.assertNotIn("offer_probability",r)

    def test_policy_adds_conversion_title_visibility_not_offer_date(self):
        processes=[
            {"process_key":"A","employer":"LeoVegas","role":"AI Strategy and Transformation Lead",
             "stage":"first_interview_completed","status":"active_unknown_decision"},
            {"process_key":"B","employer":"KPMG","role":"AI Lead - Manager - Tax & Legal Technology",
             "stage":"subsequent_interview_scheduled","status":"active_reconciled"},
            {"process_key":"C","employer":"Other","role":"AI Director",
             "stage":"human_response","status":"active_unknown_decision"},
        ]
        sensitivity=pipeline_sensitivity(processes)
        self.assertEqual(sensitivity["counts"]["functional"],2)
        self.assertEqual(sensitivity["counts"]["primary"],1)
        self.assertEqual(sensitivity["advanced"]["functional"],2)
        before={"model_version":"hiring-v2-stage-evidence-provisional",
                "top_processes":processes,
                "leading_stage_scenario":{"offer_central":"2026-11-19",
                                          "start_central":"2026-12-17"}}
        model=evaluate_market_shadow([],[],before,"2026-10-20",
                  catalog_rows=[vacancy("AI Strategy Lead","Two")])
        self.assertEqual(model["shadow_timing"],model["baseline_timing"])
        self.assertEqual(model["offer_date_delta_days"],0)
        self.assertEqual(model["role_policy"]["pipeline"]["counts"]["functional"],2)
        self.assertEqual(model["role_policy"]["catalog"]["primary_plus_functional"],1)
        self.assertFalse(model["promotion_allowed"])

    def test_role_catalog_sql_special_forms_and_access_guards(self):
        """Regression: COALESCE cannot be prefixed with pg_catalog schema."""
        sql = (Path(__file__).resolve().parents[1] / "sql" /
               "20261020_fix_role_catalog_coalesce.sql").read_text()
        self.assertNotIn("pg_catalog.coalesce(", sql)
        self.assertIn("coalesce(pg_catalog.jsonb_agg(", sql)
        self.assertIn("coalesce(description,''),2200", sql)
        self.assertIn("auth.uid() is distinct from", sql)
        self.assertIn("is_anonymous", sql)
        self.assertIn("limit 500", sql.lower())
        self.assertIn("REVOKE ALL ON FUNCTION", sql)
        self.assertIn("GRANT EXECUTE ON FUNCTION", sql)

    def test_private_catalog_request_is_owner_only(self):
        with self.assertRaises(PermissionError):
            fetch_role_catalog("")
        with patch("page_market_shadow._request_json",return_value=[]) as api:
            self.assertEqual(fetch_role_catalog("owner-token"),[])
            self.assertEqual(api.call_args.kwargs["token"],"owner-token")
            self.assertIn("rpc/careersite_hiring_role_catalog_v1",api.call_args.args[1])


if __name__=="__main__":
    unittest.main()
