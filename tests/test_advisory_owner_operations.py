"""Advisory owner operations regression: no credentials or production writes."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_owner_advisory_management import _people, _reflect_request_journey
from page_owner_advisory_operations import (
    _invite_reader, _service_action, _service_status, _priority_label,
    SERVICES,
)


class AdvisoryOperationsTests(unittest.TestCase):
    def test_both_owner_modules_are_valid_python(self):
        for path in (
            "src/page_owner_advisory_management.py",
            "src/page_owner_advisory_operations.py",
            "src/page_owner_advisory_requests.py",
            "src/page_owner_reader_management.py",
        ):
            ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)

    def test_reader_can_be_seen_without_becoming_advisory_member(self):
        reader = {
            "user_id": "reader-1", "email": "reader@example.org",
            "first_name": "Alex", "last_name": "Leader",
            "organization": "Example",
        }
        people = _people([], [], [], [reader])
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["onboarding"], "Reader only")
        self.assertEqual(people[0]["account_status"], "reader_only")
        self.assertFalse(_reflect_request_journey(people, [])[0]["has_request"])

    def test_owner_invitation_preserves_reader_identity_without_automatic_access(self):
        uid = "reader-1"
        reader = {"user_id": uid, "email": "reader@example.org", "first_name": "Alex"}
        intent = {"user_id": uid, "email": "reader@example.org",
                  "source": "owner_reconciled"}
        pending = _people([], [intent], [], [reader])
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["first_name"], "Alex")
        self.assertEqual(pending[0]["onboarding"], "Pending onboarding")
        self.assertEqual(pending[0]["account_status"], "pending")

    def test_invitation_uses_private_server_rpc_and_checks_readback(self):
        with patch("page_owner_advisory_operations._request_json",
                   return_value={"user_id": "reader-1", "status": "invited"}) as call:
            self.assertEqual(_invite_reader("owner-token", "reader-1"), "invited")
            self.assertIn("portfolio_advisory_owner_invite_reader_v1",
                          call.call_args.args[1])
            self.assertEqual(call.call_args.kwargs["token"], "owner-token")
        with patch("page_owner_advisory_operations._request_json",
                   return_value={"user_id": "other", "status": "invited"}):
            with self.assertRaises(RuntimeError):
                _invite_reader("owner-token", "reader-1")

    def test_service_approval_is_individually_audited_rpc_not_direct_table_write(self):
        for key, _, rpc, _ in SERVICES:
            with self.subTest(key=key):
                with patch("page_owner_advisory_operations._request_json",
                           return_value={"status": "active", "id": "entitlement"}) as call:
                    result = _service_action("owner-token", "request-1", key, "approve")
                    self.assertEqual(result["status"], "active")
                    self.assertIn("rpc/" + rpc, call.call_args.args[1])
                    self.assertEqual(call.call_args.kwargs["token"], "owner-token")
                    self.assertEqual(
                        call.call_args.kwargs["payload"],
                        {"p_request_id": "request-1", "p_action": "approve"},
                    )
                with patch("page_owner_advisory_operations._request_json",
                           return_value={"status": "revoked"}) as call:
                    _service_action("owner-token", "request-1", key, "revoke")
                    self.assertEqual(call.call_args.kwargs["payload"]["p_action"], "revoke")
        for action in ("delete", "auto_approve"):
            with self.assertRaises(ValueError):
                _service_action("token", "request", "scorecard", action)

    def test_service_entitlements_are_per_request_not_per_person(self):
        access = {"scorecard": [
            {"request_id": "older", "user_id": "person", "status": "revoked"},
            {"request_id": "newer", "user_id": "person", "status": "active"},
        ], "rollout": [{"request_id": "newer", "status": "active"}]}
        self.assertEqual(_service_status(access, "older", "scorecard"), "revoked")
        self.assertEqual(_service_status(access, "newer", "scorecard"), "active")
        self.assertEqual(_service_status(access, "older", "rollout"), "Not granted")

    def test_request_status_does_not_overwrite_relationship_management_stage(self):
        p = {"user_id": "p1", "relationship_stage": "proposal"}
        requests = [
            {"user_id": "p1", "created_at": "2026-11-14T10:00:00Z", "status": "reviewing"},
            {"user_id": "p1", "created_at": "2026-11-13T10:00:00Z", "status": "closed"},
        ]
        result = _reflect_request_journey([p], requests)[0]
        self.assertEqual(result["relationship_stage"], "proposal")
        self.assertEqual(result["latest_request_status"], "reviewing")
        self.assertEqual(result["request_count"], 2)

    def test_migration_limits_member_access_and_invites_only_verified_readers(self):
        sql = (ROOT / "supabase/migrations/"
               "20261114202502_advisory_operations_owner_invites_and_permission_guard.sql"
               ).read_text(encoding="utf-8").lower()
        self.assertIn("portfolio_advisory_owner_invite_reader_v1", sql)
        self.assertIn("email_confirmed_at is not null", sql)
        self.assertIn("owner_reconciled", sql)
        self.assertIn("revoke update on table public.portfolio_advisory_profiles", sql)
        self.assertIn("grant update (", sql)
        self.assertNotIn("account_status, engagement_status", sql)
        self.assertIn("r.user_id = portfolio_advisory_scorecards.user_id", sql)


if __name__ == "__main__":
    unittest.main()
