"""Visible Reader/Advisory logout and shared Supabase session revocation."""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import page_reader_native as native


class VisibleMemberLogoutTests(unittest.TestCase):
    def fake_streamlit(self, state=None, params=None):
        state = dict(state or {})
        params = dict(params or {})
        return SimpleNamespace(
            session_state=state,
            query_params=params,
            columns=Mock(return_value=(nullcontext(), nullcontext())),
            caption=Mock(),
            button=Mock(return_value=False),
            rerun=Mock(),
        )

    def test_logout_revokes_only_current_supabase_session_and_clears_both_workspaces(self):
        fake = self.fake_streamlit(
            state={
                "reader_native_session": {"access_token": "test-private-token"},
                "reader_native_user": {"email": "test@example.org"},
                "reader_weekly_search": "an earlier account's query",
                "advisory_member": True,
                "advisory_member_navigation": "messages",
                "advisory_signup_intake": {"organization": "Private Org"},
                "rollout_latest_report_id": "private-record",
                "scorecard_selected": "private-record",
                "owner_auth_session": {"owner": True},
                "public_analytics_period": "year",
            },
            params={"page": "advisory-access", "view": "messages",
                    "request": "private-id", "signin": "1"},
        )
        with patch.object(native, "st", fake), patch.object(
            native, "_request_json", return_value=None
        ) as remote:
            self.assertTrue(native._logout_member_session(
                {"access_token": "test-private-token"}
            ))
        self.assertEqual(remote.call_args.args[0], "POST")
        self.assertIn("/auth/v1/logout?scope=local", remote.call_args.args[1])
        self.assertEqual(remote.call_args.kwargs["token"], "test-private-token")
        self.assertEqual(remote.call_args.kwargs["payload"], {})
        self.assertEqual(fake.session_state["owner_auth_session"], {"owner": True})
        self.assertEqual(fake.session_state["public_analytics_period"], "year")
        for key in ("reader_native_session", "reader_native_user",
                    "advisory_member", "advisory_signup_intake",
                    "rollout_latest_report_id", "scorecard_selected"):
            self.assertNotIn(key, fake.session_state)
        self.assertEqual(fake.query_params, {"page": "advisory-access"})
        self.assertEqual(fake.session_state["reader_native_flash"][0], "success")

    def test_local_signout_occurs_even_if_supabase_is_unreachable(self):
        fake = self.fake_streamlit(state={
            "reader_native_session": {"access_token": "expired-token"},
            "advisory_member": True,
        })
        with patch.object(native, "st", fake), patch.object(
            native, "_request_json", side_effect=RuntimeError("unreachable")
        ):
            self.assertFalse(native._logout_member_session(
                {"access_token": "expired-token"}
            ))
        self.assertNotIn("reader_native_session", fake.session_state)
        self.assertNotIn("advisory_member", fake.session_state)
        self.assertEqual(fake.session_state["reader_native_flash"][0], "warning")

    def test_both_toolbars_offer_a_distinct_action_and_only_click_logs_out(self):
        for context in ("reader", "advisory"):
            with self.subTest(context=context):
                fake = self.fake_streamlit()
                session = {"access_token": "test-token"}
                user = {"email": "member@example.org"}
                with patch.object(native, "st", fake), patch.object(
                    native, "_logout_member_session"
                ) as logout:
                    native.member_logout_toolbar(session, user, context=context)
                    logout.assert_not_called()
                    fake.button.assert_called_once()
                    self.assertEqual(
                        fake.button.call_args.kwargs["key"],
                        context + "_member_signout",
                    )
                    self.assertEqual(fake.button.call_args.args[0], "Sign out")
                    fake.button.return_value = True
                    native.member_logout_toolbar(session, user, context=context)
                    logout.assert_called_once_with(session)
                    fake.rerun.assert_called_once()

    def test_toolbar_is_rendered_before_private_library_and_advisory_content(self):
        reader = (ROOT / "src/page_reader_native.py").read_text(encoding="utf-8")
        advisory = (ROOT / "src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn('member_logout_toolbar(session, user, context="reader")', reader)
        self.assertIn('member_logout_toolbar(session, user, context="advisory")', advisory)
        self.assertLess(
            reader.index('member_logout_toolbar(session, user, context="reader")'),
            reader.index("_library(session, user)", reader.index("def render_reader_native")),
        )
        self.assertIn("_logout_member_session(st.session_state.get", advisory)
        self.assertIn('if st.button("Sign out of Advisory and Reader"', advisory)
        self.assertNotIn('key="reader_native_logout"', reader)


if __name__ == "__main__":
    unittest.main()
