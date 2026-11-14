"""Regression checks: optional, contextual, private Advisory service feedback."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class AdvisoryServiceFeedbackTests(unittest.TestCase):
    def source(self,path:str)->str:
        return (ROOT/path).read_text(encoding="utf-8")

    def test_modules_parse_and_all_five_stages_exist(self):
        paths=(
            "src/page_advisory_service_feedback.py",
            "src/page_owner_advisory_feedback.py",
            "src/page_advisory_client_journey.py",
            "src/page_advisory_scorecard_workspace.py",
            "src/page_owner_advisory_management.py",
        )
        for path in paths:
            with self.subTest(path=path):
                ast.parse(self.source(path),filename=path)
        from page_advisory_service_feedback import STAGE_QUESTIONS
        self.assertEqual(set(STAGE_QUESTIONS),{
            "registration_access","assessment_completion",
            "executive_recommendation","report_download","personal_advisory",
        })
        self.assertIn("Decision Usefulness",STAGE_QUESTIONS["executive_recommendation"][0])

    def test_member_dedup_scope_is_individual(self):
        from page_advisory_service_feedback import already_recorded,SCORECARD_SERVICE
        rows=[
            {"service_key":SCORECARD_SERVICE,"stage":"executive_recommendation",
             "request_id":"request-1","scorecard_id":"workspace-a"},
        ]
        self.assertTrue(already_recorded(
            rows,SCORECARD_SERVICE,"executive_recommendation","request-1","workspace-a"
        ))
        self.assertFalse(already_recorded(
            rows,SCORECARD_SERVICE,"executive_recommendation","request-1","workspace-b"
        ))
        self.assertFalse(already_recorded(
            rows,SCORECARD_SERVICE,"assessment_completion","request-1","workspace-a"
        ))

    def test_feedback_uses_server_guarded_rpc_without_direct_table_writes(self):
        from page_advisory_service_feedback import submit_feedback,SCORECARD_SERVICE
        with patch("page_advisory_service_feedback._request_json",return_value={
            "status":"recorded","id":"feedback-1"
        }) as api:
            self.assertEqual(submit_feedback(
                "jwt",SCORECARD_SERVICE,"executive_recommendation",4,
                "Useful decision criteria",request_id="request-a",
                scorecard_id="workspace-a",
            ),"recorded")
            args=api.call_args
            self.assertIn("rpc/portfolio_advisory_feedback_submit_v1",args.args[1])
            self.assertEqual(args.kwargs["token"],"jwt")
            self.assertEqual(args.kwargs["payload"]["p_rating"],4)
            self.assertEqual(args.kwargs["payload"]["p_request_id"],"request-a")
            self.assertEqual(args.kwargs["payload"]["p_scorecard_id"],"workspace-a")

    def test_rating_validation_and_optional_low_score_followup(self):
        from page_advisory_service_feedback import (
            submit_feedback, ADVISORY_SERVICE,
        )
        with patch("page_advisory_service_feedback._request_json") as api:
            with self.assertRaises(ValueError):
                submit_feedback("token",ADVISORY_SERVICE,"registration_access",0)
            with self.assertRaises(ValueError):
                submit_feedback("token",ADVISORY_SERVICE,"registration_access",3,
                                "x"*801)
            api.assert_not_called()
        code=self.source("src/page_advisory_service_feedback.py")
        self.assertIn("if rating is not None and rating <= 3:",code)
        self.assertIn("Send optional feedback",code)
        self.assertIn("You can skip this",code)

    def test_recommendation_and_download_are_never_gated_by_feedback(self):
        ui=self.source("src/page_advisory_scorecard_decision_ui.py")
        code=self.source("src/page_advisory_scorecard_workspace.py")
        # The new PDF decision memo replaces the CSV as the primary deliverable.
        self.assertLess(ui.index('st.markdown("#### Recommended decision")'),
                        ui.index('"executive_recommendation"'))
        self.assertLess(ui.index('st.download_button('),
                        ui.index('"report_download"'))
        self.assertIn("build_executive_pdf(report)",ui)
        self.assertIn("if st.session_state.get(pdf_key):",ui)
        self.assertIn('"assessment_completion"',code)
        self.assertIn('st.download_button("Export summary (CSV)"',code)

    def test_owner_feedback_dashboard_and_decision_usefulness(self):
        from page_owner_advisory_feedback import summarize_feedback,review_feedback
        rows=[
            {"stage":"executive_recommendation","rating":5,"created_at":"2026-11-14T10:00:00"},
            {"stage":"executive_recommendation","rating":2,"created_at":"2026-11-14T11:00:00"},
            {"stage":"registration_access","rating":3,"created_at":"2026-11-14T12:00:00"},
        ]
        stages,monthly=summarize_feedback(rows)
        decision=next(x for x in stages if x["Interaction"]=="Decision Usefulness")
        self.assertEqual(decision["Responses"],2)
        self.assertEqual(decision["Average /5"],3.5)
        self.assertEqual(decision["Low (1–2)"],1)
        self.assertTrue(monthly)
        with patch("page_owner_advisory_feedback._request_json",
                   return_value={"id":"feedback-a","status":"reviewed"}) as api:
            self.assertEqual(review_feedback("owner-jwt","feedback-a","reviewed","Followed up"),{
                "id":"feedback-a","status":"reviewed"
            })
            self.assertIn("rpc/portfolio_advisory_feedback_owner_review_v1",api.call_args.args[1])

    def test_owner_private_notes_are_not_member_readable(self):
        migration=self.source(
            "supabase/migrations/20261114_advisory_feedback_owner_notes_private.sql"
        )
        self.assertIn("revoke all on public.portfolio_advisory_interaction_feedback from authenticated",migration)
        self.assertIn("grant select (",migration)
        self.assertNotIn("rating,comment,followup_answer,contact_ok,owner_status",migration.split("grant select (")[1].split(") on")[0])
        self.assertIn("portfolio_advisory_feedback_owner_list_v1",migration)
        self.assertIn("lower(u.email)='jair.ribeiro@outlook.it'",migration)
        from page_owner_advisory_feedback import read_owner_feedback
        with patch("page_owner_advisory_feedback._request_json",return_value=[]) as api:
            self.assertEqual(read_owner_feedback("owner-jwt"),[])
            self.assertIn("rpc/portfolio_advisory_feedback_owner_list_v1",api.call_args.args[1])
            self.assertEqual(api.call_args.kwargs["token"],"owner-jwt")

    def test_service_and_privacy_disclose_optionality(self):
        service=self.source("src/page_advisory_scorecard.py")
        notice=self.source("src/page_public_services.py")
        self.assertIn("feedback never delays the decision or download",service)
        self.assertIn("Optional Advisory service feedback",notice)
        self.assertIn("Leaving feedback is optional",notice)
        self.assertIn('"Service feedback"',self.source("src/page_owner_advisory_management.py"))
        self.assertIn('"personal_advisory"',self.source("src/page_advisory_client_journey.py"))
        self.assertIn('"registration_access"',self.source("src/page_advisory_portal.py"))

    def test_schema_guards_anonymous_and_direct_writes(self):
        migration=self.source("supabase/migrations/20261114_advisory_service_interaction_feedback.sql")
        self.assertIn("enable row level security",migration)
        self.assertIn("revoke all on public.portfolio_advisory_interaction_feedback",migration)
        self.assertIn("grant select on public.portfolio_advisory_interaction_feedback to authenticated",migration)
        self.assertNotIn("grant insert on public.portfolio_advisory_interaction_feedback to authenticated",migration)
        self.assertIn("portfolio_advisory_password_session_v1()",migration)
        self.assertIn("on conflict(user_id,service_key,stage,scope_key) do nothing",migration)


if __name__=="__main__":
    unittest.main()
