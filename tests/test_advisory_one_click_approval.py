"""Regression: one click from any open request grants service and logs mail delivery."""
from __future__ import annotations
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
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
        self.assertIn("Approve access & email client", operation)
        self.assertNotIn("can_approve = stage == \"active\"", operation)
        self.assertIn('eligible = stage not in ("closed", "declined")', operation)
        inbox = (ROOT / "src/page_owner_advisory_requests.py").read_text("utf-8")
        self.assertIn("render_service_access_for_request(token, req)", inbox)

    def test_email_contents_use_verified_service_link_and_not_marketing(self):
        from advisory_approval_email import _message, PORTAL_URL
        for service in ("scorecard", "rollout"):
            subject, plain, html = _message(service)
            self.assertIn(PORTAL_URL, plain)
            self.assertIn("access is approved", subject)
            self.assertIn("not a marketing subscription", html)
            self.assertIn("advisory@jairribeiro.com", plain)
        with self.assertRaises(ValueError):
            _message("not-real")

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
            self.assertIn("email accepted", message.lower())
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

    def test_claimed_notification_calls_mail_provider_then_confirms_result(self):
        from advisory_approval_email import deliver_approval_notice
        def rpc(method, url, **kwargs):
            if "email_claim" in url:
                return {"id": "notice-1", "state": "sending", "claimed": True,
                        "to": "member@example.org", "service_key": "scorecard"}
            if "email_finish" in url:
                self.assertEqual(kwargs["payload"]["p_sent"], True)
                self.assertEqual(kwargs["payload"]["p_provider_message_id"], "provider-123")
                return {"id": "notice-1", "state": "sent"}
            raise AssertionError("Wrong RPC")
        with (
            patch("advisory_approval_email._request_json", side_effect=rpc),
            patch("advisory_approval_email._send_provider", return_value="provider-123") as send,
        ):
            response = deliver_approval_notice("owner-token", "notice-1")
            self.assertEqual(response["state"], "sent")
            send.assert_called_once_with("notice-1", "member@example.org", "scorecard")

    def test_missing_credentials_do_not_claim_sent(self):
        from advisory_approval_email import deliver_approval_notice
        def rpc(method, url, **kwargs):
            if "email_claim" in url:
                return {"id": "notice-1", "state": "sending", "claimed": True,
                        "to": "member@example.org", "service_key": "rollout"}
            if "email_finish" in url:
                self.assertFalse(kwargs["payload"]["p_sent"])
                self.assertEqual(kwargs["payload"]["p_error_category"], "configuration_missing")
                return {"id": "notice-1", "state": "failed"}
            raise AssertionError("Wrong RPC")
        with (
            patch("advisory_approval_email._request_json", side_effect=rpc),
            patch("advisory_approval_email._secret", return_value=""),
        ):
            result = deliver_approval_notice("token", "notice-1")
            self.assertEqual(result["state"], "failed")
            self.assertEqual(result["error_category"], "configuration_missing")

    def test_provider_resend_idempotency_header(self):
        from advisory_approval_email import _send_using_resend
        fake = MagicMock()
        fake.read.return_value = b'{"id":"provider123"}'
        connection = MagicMock()
        connection.__enter__.return_value = fake
        with patch("advisory_approval_email.request.urlopen", return_value=connection) as post:
            mid = _send_using_resend("notice-123", "verified@example.org", "scorecard", "key")
            self.assertEqual(mid, "provider123")
            req = post.call_args.args[0]
            self.assertEqual(req.headers["Idempotency-key"], "advisory-approval/notice-123")
            self.assertNotIn("key", req.data.decode("utf-8"))

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
