"""Rollout decision advisor and contextual customer-satisfaction regression."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

class RolloutAdvisorTests(unittest.TestCase):
    def source(self,path):
        return (ROOT/path).read_text(encoding="utf-8")

    def test_modules_and_routes_parse(self):
        for path in ("main.py","src/page_advisory_rollout.py",
                     "src/page_advisory_feedback.py",
                     "src/page_owner_advisory_rollout.py",
                     "src/page_advisory_portal.py",
                     "src/page_advisory_client_journey.py",
                     "src/page_owner_advisory_requests.py",
                     "src/page_owner_advisory_management.py"):
            with self.subTest(path=path):
                ast.parse(self.source(path),filename=path)
        self.assertIn('PAGE == "advisory-rollout"',self.source("main.py"))
        self.assertIn("render_private_rollout(session, user)",
                      self.source("src/page_advisory_portal.py"))
        self.assertIn('href="?page=advisory-rollout"',
                      self.source("src/page_public_services.py"))

    def _answers(self,value=3):
        from page_advisory_rollout import QUESTIONS,STAGES,CRITICALITIES,SCOPES
        return {
            "responses":{q[0]:value for q in QUESTIONS},
            "context":{"use_case":"Customer service knowledge assistant",
                       "stage":STAGES[0],"criticality":CRITICALITIES[1],
                       "scope":SCOPES[1]}
        }

    def test_exactly_eighteen_questions_five_areas(self):
        from page_advisory_rollout import QUESTIONS,AREAS,validate_answers
        self.assertEqual(len(QUESTIONS),18)
        self.assertEqual(len(set(q[0] for q in QUESTIONS)),18)
        self.assertEqual(set(q[1] for q in QUESTIONS),set(AREAS))
        self.assertEqual(len(validate_answers(self._answers())["responses"]),18)

    def test_proceed_only_when_everything_demonstrated(self):
        from page_advisory_rollout import assess
        result=assess(self._answers())
        self.assertEqual(result["label"],"PHASED GO")
        self.assertEqual(result["overall"],100)
        self.assertEqual(result["confidence"],"Higher")
        self.assertFalse(result["critical_gates"])

    def test_critical_gate_overrides_perfect_average(self):
        from page_advisory_rollout import assess
        inputs=self._answers()
        inputs["responses"]["security"]=0
        result=assess(inputs)
        self.assertEqual(result["label"],"PAUSE SCALING")
        self.assertTrue(result["critical_gates"])

    def test_incomplete_evidence_never_gets_positive_verdict(self):
        from page_advisory_rollout import assess
        inputs=self._answers()
        for k in ("baseline","outcome","economics","data","capacity"):
            inputs["responses"][k]=0
        result=assess(inputs)
        self.assertEqual(result["label"],"EVIDENCE INCOMPLETE")
        self.assertEqual(result["unassessed"],5)

    def test_people_constraint_informs_insight(self):
        from page_advisory_rollout import assess
        inputs=self._answers()
        for k in ("employees","learning","usage"):
            inputs["responses"][k]=1
        result=assess(inputs)
        self.assertEqual(result["label"],"CONTROLLED EXPANSION")
        self.assertIn("adoption",result["insight"])

    def test_reject_missing_and_manipulated_inputs(self):
        from page_advisory_rollout import validate_answers
        inputs=self._answers()
        del inputs["responses"]["baseline"]
        with self.assertRaises(ValueError):
            validate_answers(inputs)
        inputs=self._answers()
        inputs["responses"]["security"]=99
        with self.assertRaises(ValueError):
            validate_answers(inputs)

    def test_rpc_persists_assessment_and_requires_approved_request(self):
        from page_advisory_rollout import _submit_assessment
        with patch("page_advisory_rollout._request_json",return_value={"id":"abc"}) as api:
            self.assertEqual(_submit_assessment("token","request-1",self._answers()),"abc")
            self.assertIn("portfolio_advisory_rollout_assess_v1",api.call_args.args[1])
            self.assertEqual(api.call_args.kwargs["payload"]["p_request_id"],"request-1")

    def test_unified_feedback_is_optional_and_permission_checked(self):
        from page_advisory_service_feedback import submit_feedback,ROLLOUT_SERVICE,STAGE_QUESTIONS
        self.assertIn("executive_recommendation",STAGE_QUESTIONS)
        with patch("page_advisory_service_feedback._request_json",
                   return_value={"status":"recorded","id":"feedback"}) as api:
            self.assertEqual(submit_feedback("token",ROLLOUT_SERVICE,
                             "executive_recommendation",5,comment="Useful",
                             request_id="request-1"),"recorded")
            self.assertIn("portfolio_advisory_rollout_feedback_submit_v1",
                          api.call_args.args[1])
            self.assertEqual(api.call_args.kwargs["payload"]["p_rating"],5)
        with self.assertRaises(ValueError):
            submit_feedback("token",ROLLOUT_SERVICE,"executive_recommendation",6,
                            request_id="request-1")

    def test_pdf_download_not_gated_by_rating(self):
        from page_advisory_rollout import assess,_pdf_report
        answer=self._answers()
        pdf=_pdf_report(assess(answer),answer)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertIn("Download executive decision brief",self.source("src/page_advisory_rollout.py"))
        self.assertNotIn("if rating:",self.source("src/page_advisory_rollout.py"))

    def test_schema_enforces_rls_and_reuses_feedback_store(self):
        schema=self.source("supabase/migrations/20261114_rollout_readiness_advisor_shared_feedback.sql")
        for table in ("portfolio_advisory_rollout_access",
                      "portfolio_advisory_rollout_assessments",
                      "portfolio_advisory_rollout_audit"):
            self.assertIn("alter table public."+table+" enable row level security",schema)
        self.assertNotIn("create table if not exists public.portfolio_advisory_feedback",schema)
        self.assertIn("portfolio_advisory_interaction_feedback",schema)
        self.assertIn("portfolio_advisory_password_session_v1()",schema)
        self.assertIn("p.account_status='active'",schema)
        self.assertIn("r.status in ('active','completed')",schema)
        self.assertIn("portfolio_advisory_rollout_owner_action_v1",schema)
        self.assertIn("portfolio_advisory_rollout_assess_v1",schema)
        self.assertIn("portfolio_advisory_rollout_feedback_submit_v1",schema)
        self.assertIn("grant execute",schema)


if __name__=="__main__":
    unittest.main()
