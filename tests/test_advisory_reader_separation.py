"""Advisory vs Reader management and branded Premium URL regression tests."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class AdvisoryReaderSeparationTests(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_new_and_existing_modules_parse(self):
        for name in (
            "src/page_owner_advisory_management.py",
            "src/page_owner_reader_management.py",
            "src/page_analytics_v2.py",
            "src/page_reader_native.py",
            "src/site_meta.py",
            "src/page_advisory_portal.py",
            "src/thinking_articles.py",
        ):
            with self.subTest(name=name):
                ast.parse(self.source(name), filename=name)

    def test_owner_workspaces_have_distinct_reader_and_advisory_tabs(self):
        from page_analytics_v2 import _WORKSPACE_LABELS, _resolve_workspace
        self.assertEqual(_WORKSPACE_LABELS["readers"], "Reader Management")
        self.assertEqual(_WORKSPACE_LABELS["advisory"], "Advisory Management")
        self.assertEqual(_resolve_workspace("advisory", True), "advisory")
        self.assertEqual(_resolve_workspace("advisory", False), "public")
        self.assertEqual(_resolve_workspace("readers", False), "public")

    def test_intent_is_pending_until_advisory_profile_exists(self):
        from page_owner_advisory_management import _people
        uid = "00000000-0000-4000-8000-000000000001"
        intents = [{
            "user_id": uid, "email": "executive@example.org",
            "source": "owner_reconciled", "created_at": "2026-11-13T12:00:00Z",
        }]
        pending = _people([], intents, [])
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["onboarding"], "Pending onboarding")
        self.assertEqual(pending[0]["account_status"], "pending")
        self.assertEqual(pending[0]["relationship_stage"], "inquiry")
        completed = _people([{
            "user_id": uid, "email": "executive@example.org",
            "first_name": "Alex", "last_name": "Smith",
            "organization": "Example Enterprise",
            "role_title": "CIO", "account_status": "active",
            "created_at": "2026-11-13T12:30:00Z",
        }], intents, [{
            "user_id": uid, "relationship_stage": "discovery",
            "next_action": "Discuss operating model",
        }])
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["onboarding"], "Profile completed")
        self.assertEqual(completed[0]["relationship_stage"], "discovery")
        self.assertEqual(completed[0]["source"], "owner_reconciled")

    def test_owner_verification_precedes_any_private_read(self):
        from page_owner_advisory_management import render_owner_advisory_management
        with patch("page_owner_advisory_management._verify_owner",
                   side_effect=PermissionError("Not owner")):
            with patch("page_owner_advisory_management._read_advisory") as fetch:
                render_owner_advisory_management({"access_token": "invalid"})
                fetch.assert_not_called()

    def test_advisory_updates_use_audited_rpc_only(self):
        from page_owner_advisory_management import _owner_action
        uid = "00000000-0000-4000-8000-000000000001"
        with patch("page_owner_advisory_management._request_json",
                   return_value={"user_id": uid, "action": "stage"}) as remote:
            _owner_action("owner-token", uid, "stage", value="discovery")
            self.assertIn("rpc/portfolio_advisory_owner_action_v1",
                          remote.call_args.args[1])
            self.assertEqual(remote.call_args.kwargs["token"], "owner-token")
            self.assertEqual(remote.call_args.kwargs["payload"]["p_value"], "discovery")
        with self.assertRaises(ValueError):
            _owner_action("owner-token", uid, "reader_subscribe", value="true")

    def test_reader_directory_explicitly_labels_advisory_relationship(self):
        reader_admin = self.source("src/page_owner_reader_management.py")
        self.assertIn('"Advisory pending"', reader_admin)
        self.assertIn('"Advisory + Reader"', reader_admin)
        self.assertIn('"Reader only"', reader_admin)
        self.assertIn('"Membership": advisory_membership.get', reader_admin)
        self.assertIn('"portfolio_advisory_intents"', reader_admin)

    def test_branded_origin_for_every_premium_entry_link(self):
        from page_reader_native import _host_origin, BRANDED_PREMIUM_ORIGIN
        from thinking_articles import BASE_URL
        self.assertEqual(_host_origin(), "https://jairribeiro.com")
        self.assertEqual(BRANDED_PREMIUM_ORIGIN, BASE_URL)
        reader = self.source("src/page_reader_native.py")
        self.assertIn('target = _host_origin() + "/?page=" + destination', reader)
        meta = self.source("src/site_meta.py")
        self.assertIn('const base = "https://jairribeiro.com/";', meta)
        self.assertNotIn('"url": "https://jairribeiro-ai.streamlit.app/"', meta)

    def test_advisory_registration_is_distinct_from_editorial_consent(self):
        source = self.source("src/page_owner_advisory_management.py")
        self.assertIn("No marketing consent is inferred", source)
        self.assertIn("registration is not a paid engagement", source.lower())
        self.assertNotIn("portfolio_reader_admin_action_v1", source)


if __name__ == "__main__":
    unittest.main()
