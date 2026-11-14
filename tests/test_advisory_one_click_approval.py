"""Regression: one click from any open request grants service and logs mail delivery."""
from __future__ import annotations
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ApprovalTests(TestCase):
    def test_python_compiles_and_owner_action_is_not_engagement_gated(self):
        for path in (
            "src/advisory_approval_email.py",
            "src/page_owner_advisory_operations.py",
            "src/page_owner_advisory_requests.py",
            "src/page_owner_advisory_management.py",
        ):
            ast.parse((ROOT / path).read_text("utf-8"), filename=path)
        operation = (ROOT / "src/page_owner_advisory_operations.py").read_text("utf-8")
        self.assertIn("Approve access & send Supabase email", operation)
        self.assertNotIn("can_approve = stage == \"active\"", operation)
        self.assertIn('eligible = stage not in ("closed", "declined")', operation)
        inbox = (ROOT / "src/page_owner_advisory_requests.py").read_text("utf-8")
        self.assertIn("render_service_access_for_request(token, req)", inbox)

    def test_approval_email_uses_existing_supabase_auth_and_verified_callback(self):
        from advisory_approval_email import _send_using_supabase_auth
        from page_reader_native import _callback_origin
        with patch("advisory_approval_email._request_json", return_value={}) as request:
            result = _send_using_supabase_auth("Verified@Example.org", "rollout")
            self.assertEqual(result, "supabase-auth-accepted")
            url = request.call_args.args[1]
            self.assertIn("/auth/v1/otp?", url)
            callback = parse_qs(urlparse(url).query)["redirect_to"][0]
            self.assertEqual(
                callback, _callback_origin("advisory-access") + "/?page=advisory-access"
            )
            self.assertEqual(
                request.call_args.kwargs["payload"],
                {"email": "verified@example.org", "create_user": False},
            )
        with self.assertRaises(ValueError):
            _send_using_supabase_auth("invalid-address", "scorecard")
        with self.assertRaises(ValueError):
            _send_using_supabase_auth("verified@example.org", "not-a-service")

    def test_owner_grant_uses_audited_rpc(self):
        from page_owner_advisory_operations import _service_action
        with patch("page_owner_advisory_operations._request_json", return_value={
            "id": "workspace", "status": "active",
            "notification_id": "notice-1", "unchanged": False
        }) as remote:
            outcome = _service_action("owner-token", "request-1", "rollout", "approve")
            self.assertEqual(outcome["notification_id"], "notice-1")
            self.assertIn("portfolio_advisory_rollout_owner_action_v1",
                          remote.call_args.args[1])
            self.assertEqual(remote.call_args.kwargs["payload"]["p_request_id"], "request-1")

    def test_approval_records_and_attempts_automatic_email(self):
        from page_owner_advisory_operations import _approval_decision
        with (
            patch("page_owner_advisory_operations._service_action", return_value={
                "id": "workspace", "status": "active",
                "notification_id": "notice-1", "unchanged": False,
            }),
            patch("page_owner_advisory_operations.deliver_approval_notice",
                  return_value={"id": "notice-1", "state": "sent"}) as email,
        ):
            message = _approval_decision("owner-token", "request-1", "rollout")
            self.assertIn("Supabase Auth accepted", message)
            email.assert_called_once_with("owner-token", "notice-1")

    def test_repeated_active_approval_does_not_create_duplicate_email(self):
        from page_owner_advisory_operations import _approval_decision
        with (
            patch("page_owner_advisory_operations._service_action", return_value={
                "id": "workspace", "status": "active",
                "notification_id": "notice-1", "unchanged": True,
            }),
            patch("page_owner_advisory_operations.deliver_approval_notice") as email,
        ):
            message = _approval_decision("owner-token", "request-1", "scorecard")
            self.assertIn("already approved", message)
            email.assert_not_called()

    def test_claimed_notification_uses_supabase_auth_and_records_acceptance(self):
        from advisory_approval_email import deliver_approval_notice
        def rpc(method, url, **kwargs):
            if "email_claim" in url:
                return {"id": "notice-1", "state": "sending", "claimed": True,
                        "to": "member@example.org", "service_key": "scorecard"}
            if "email_finish" in url:
                self.assertEqual(kwargs["payload"]["p_sent"], True)
                self.assertEqual(kwargs["payload"]["p_provider_message_id"], "supabase-auth-accepted")
                return {"id": "notice-1", "state": "sent"}
            raise AssertionError("Wrong RPC")
        with (
            patch("advisory_approval_email._request_json", side_effect=rpc),
            patch("advisory_approval_email._send_using_supabase_auth",
                  return_value="supabase-auth-accepted") as send,
        ):
            response = deliver_approval_notice("owner-token", "notice-1")
            self.assertEqual(response["state"], "sent")
            send.assert_called_once_with("member@example.org", "scorecard")

    def test_supabase_auth_rate_limits_are_not_marked_as_sent(self):
        from advisory_approval_email import deliver_approval_notice
        def rpc(method, url, **kwargs):
            if "email_claim" in url:
                return {"id": "notice-1", "state": "sending", "claimed": True,
                        "to": "member@example.org", "service_key": "rollout"}
            if "email_finish" in url:
                self.assertFalse(kwargs["payload"]["p_sent"])
                self.assertEqual(kwargs["payload"]["p_error_category"], "supabase_auth_rate_limited")
                return {"id": "notice-1", "state": "failed"}
            raise AssertionError("Wrong RPC")
        with (
            patch("advisory_approval_email._request_json", side_effect=rpc),
            patch("advisory_approval_email._send_using_supabase_auth",
                  side_effect=RuntimeError("Supabase request failed (429): email rate limit exceeded")),
        ):
            result = deliver_approval_notice("token", "notice-1")
            self.assertEqual(result["state"], "failed")
            self.assertEqual(result["error_category"], "supabase_auth_rate_limited")

    def test_user_access_email_cannot_be_misrepresented_as_custom_transactional_mail(self):
        source = (ROOT / "src/advisory_approval_email.py").read_text("utf-8")
        self.assertIn("/auth/v1/otp?", source)
        self.assertNotIn("api.resend.com", source)
        self.assertNotIn("smtp.resend.com", source)
        self.assertIn("create_user", source)


    def test_migration_preserves_request_stage_and_grants_directly(self):
        sql = (ROOT / "supabase/migrations/20261114213000_advisory_one_click_approval_and_email_outbox.sql").read_text("utf-8")
        self.assertIn("portfolio_advisory_service_owner_action_v2", sql)
        self.assertIn("portfolio_advisory_approval_notifications", sql)
        self.assertIn("portfolio_advisory_email_claim_v1", sql)
        self.assertIn("portfolio_advisory_email_finish_v1", sql)
        self.assertIn("r.status not in ('closed','declined')", sql)
        self.assertIn("v_stage in ('closed','declined')", sql)
        self.assertNotIn("v_stage <> 'active'", sql)
        self.assertNotIn("set status='active' where id=p_request_id", sql)
