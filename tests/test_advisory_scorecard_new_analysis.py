"""Separate approved Scorecard analyses: request, review and workspace lifecycle.

No additional analysis is created until a verified owner approves a request.
Existing client Scorecards retain their IDs, payloads, revisions and access.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ScorecardNewAnalysisTests(unittest.TestCase):
    def source(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_changed_modules_compile(self):
        for path in (
            "src/page_advisory_scorecard_new_analysis.py",
            "src/page_owner_advisory_scorecard_analyses.py",
            "src/page_advisory_scorecard_workspace.py",
            "src/page_owner_advisory_management.py",
        ):
            with self.subTest(path=path):
                ast.parse(self.source(path), filename=path)

    def test_member_request_is_authenticated_and_does_not_create_workspace(self):
        from page_advisory_scorecard_new_analysis import submit_new_analysis
        with patch("page_advisory_scorecard_new_analysis._request_json",
                   return_value={"id":"request-2","status":"pending","already_pending":False}) as api:
            result=submit_new_analysis(
                "client-token","original-approved-id",
                "Operations AI portfolio review",
                "Which five competing operational AI initiatives should receive resources?",
                "An evidence-based prioritized shortlist with executive next steps.",
                "This month",
            )
        self.assertEqual(result["status"],"pending")
        self.assertEqual(api.call_args.args[0],"POST")
        self.assertIn("rpc/portfolio_advisory_scorecard_analysis_request_v1",api.call_args.args[1])
        self.assertEqual(api.call_args.kwargs["token"],"client-token")
        self.assertEqual(api.call_args.kwargs["payload"]["p_anchor_scorecard_id"],
                         "original-approved-id")
        self.assertNotIn("portfolio_advisory_scorecards",api.call_args.args[1])

    def test_client_validates_fields_without_unapproved_writes(self):
        from page_advisory_scorecard_new_analysis import submit_new_analysis
        with patch("page_advisory_scorecard_new_analysis._request_json") as api:
            with self.assertRaises(ValueError):
                submit_new_analysis("jwt","id","Short","Short","Short","Exploratory")
            with self.assertRaises(ValueError):
                submit_new_analysis(
                    "jwt","id","Customer AI portfolio",
                    "A valid full business decision challenge.",
                    "A valid proposed outcome.",
                    "Tomorrow",
                )
            api.assert_not_called()

    def test_owner_approval_requires_database_read_back_of_empty_workspace(self):
        from page_owner_advisory_scorecard_analyses import owner_analysis_action
        responses=[
            {"id":"analysis-2","status":"approved","workspace_id":"new-workspace"},
            [{"id":"new-workspace","user_id":"user-a","status":"active",
              "analysis_request_id":"analysis-2","revision":0,
              "payload":{"settings":{"weights":[15,20,15,15,15,10,10]},
                         "initiatives":[]}}],
        ]
        with patch("page_owner_advisory_scorecard_analyses._request_json",
                   side_effect=responses) as api:
            result=owner_analysis_action("owner-jwt","analysis-2","approve","Accepted")
            self.assertEqual(result["workspace_id"],"new-workspace")
            self.assertEqual(api.call_count,2)
            self.assertIn("rpc/portfolio_advisory_scorecard_analysis_owner_v1",
                          api.call_args_list[0].args[1])
            self.assertEqual(
                api.call_args_list[0].kwargs["payload"]["p_action"],"approve"
            )
            self.assertIn("analysis_request_id=eq.analysis-2",
                          api.call_args_list[1].args[1])

    def test_owner_approval_uses_separate_supabase_access_email_event(self):
        from page_owner_advisory_scorecard_analyses import owner_analysis_action
        responses=[
            {"id":"analysis-2","status":"approved","workspace_id":"new-workspace",
             "notification_id":"new-email-event"},
            [{"id":"new-workspace","user_id":"user-a","status":"active",
              "analysis_request_id":"analysis-2","revision":0,
              "payload":{"initiatives":[]}}],
        ]
        with (
            patch("page_owner_advisory_scorecard_analyses._request_json",
                  side_effect=responses),
            patch("page_owner_advisory_scorecard_analyses.deliver_approval_notice",
                  return_value={"id":"new-email-event","state":"sent"}) as deliver,
        ):
            result=owner_analysis_action("jwt","analysis-2","approve")
        deliver.assert_called_once_with("jwt","new-email-event")
        self.assertIn("Supabase Auth accepted",result["notification_message"])

    def test_original_entitlement_controls_ignore_additional_analyses(self):
        owner=self.source("src/page_owner_advisory_scorecard.py")
        operations=self.source("src/page_owner_advisory_operations.py")
        self.assertIn('analysis_request_id=is.null&limit=1',owner)
        self.assertIn('legacy = "&analysis_request_id=is.null"',operations)

    def test_revoking_service_cascades_to_all_analyses(self):
        migration=self.source(
            "supabase/migrations/20261115_scorecard_original_revoke_all_analyses.sql"
        )
        self.assertIn("where request_id=p_request_id and status='active'",migration)
        self.assertIn("portfolio_advisory_scorecard_analysis_requests",migration)
        self.assertIn("set status='revoked',decided_by=v_owner",migration)
        self.assertIn("values(v_req.request_id",self.source(
            "supabase/migrations/20261115_scorecard_separate_approved_analysis_workspaces.sql"
        ))

    def test_owner_does_not_claim_success_if_workspace_not_empty(self):
        from page_owner_advisory_scorecard_analyses import owner_analysis_action
        with patch("page_owner_advisory_scorecard_analyses._request_json",
                   side_effect=[
                       {"id":"analysis-2","status":"approved",
                        "workspace_id":"new-workspace"},
                       [{"id":"new-workspace","status":"active",
                         "analysis_request_id":"analysis-2",
                         "revision":0,
                         "payload":{"initiatives":[{"name":"unexpected data"}]}}],
                   ]):
            with self.assertRaises(RuntimeError):
                owner_analysis_action("jwt","analysis-2","approve")

    def test_admin_actions_are_scoped_to_an_analysis(self):
        from page_owner_advisory_scorecard_analyses import owner_analysis_action
        for action,status in (("decline","declined"),("revoke","revoked")):
            with self.subTest(action=action):
                with patch("page_owner_advisory_scorecard_analyses._request_json",
                           return_value={"id":"analysis-3","status":status}) as api:
                    self.assertEqual(
                        owner_analysis_action("owner-jwt","analysis-3",action)["status"],
                        status,
                    )
                    self.assertEqual(api.call_count,1)
                    self.assertEqual(
                        api.call_args.kwargs["payload"]["p_analysis_id"],"analysis-3"
                    )

    def test_workspace_selector_keeps_old_analyses_and_promotes_new_one(self):
        source=self.source("src/page_advisory_scorecard_workspace.py")
        self.assertIn('"analysis_request_id"',source)
        self.assertIn("scorecard_seen_workspace_ids_",source)
        self.assertIn("new_ids[0] if new_ids else workspace_ids[0]",source)
        self.assertIn("Original Scorecard",source)
        self.assertIn("Request a new Scorecard analysis",self.source(
            "src/page_advisory_scorecard_new_analysis.py"
        ))
        self.assertIn("Your earlier Scorecards remain available",source)
        self.assertIn('if not data["initiatives"] or (',source)
        self.assertIn('render_new_analysis_request(token,uid,str(workspace["id"]))',source)

    def test_admin_has_explicit_approval_tab_not_existing_request_reuse(self):
        page=self.source("src/page_owner_advisory_management.py")
        self.assertIn('"Scorecard approvals"',page)
        self.assertIn("render_scorecard_analysis_approvals(token, people)",page)
        owner=self.source("src/page_owner_advisory_scorecard_analyses.py")
        self.assertIn("Approve and create new Scorecard",owner)
        self.assertIn("Revoke only this analysis",owner)
        self.assertNotIn("portfolio_advisory_request_owner_action_v1",owner)

    def test_migration_preserves_legacy_entitlement_and_requires_owner(self):
        migration=self.source(
            "supabase/migrations/20261115_scorecard_separate_approved_analysis_workspaces.sql"
        )
        for token in (
            "add column analysis_request_id uuid",
            "where analysis_request_id is null",
            "scorecard_one_pending_analysis_per_client",
            "create unique index scorecard_approved_one_workspace_per_request",
            "portfolio_advisory_scorecard_analysis_request_v1",
            "portfolio_advisory_scorecard_analysis_owner_v1",
            "enable row level security",
            "on conflict(user_id) where status='pending' do nothing",
            "where id=p_analysis_id for update",
            "u.email_confirmed_at is not null",
            "r.status not in ('closed','declined')",
            '"initiatives":[]',
            "values(v_workspace,v_owner,'approve')",
            "values(v_workspace,v_owner,'revoke')",
        ):
            with self.subTest(token=token):
                self.assertIn(token,migration)
        self.assertNotIn("grant insert on public.portfolio_advisory_scorecard_analysis_requests",
                         migration)
        self.assertIn("portfolio_advisory_service_owner_action_v2",migration)


if __name__=="__main__":
    unittest.main()
