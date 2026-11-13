"""Unit and widget regression tests for first-contact Advisory registration."""
from __future__ import annotations
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class AdvisoryRegistrationTests(unittest.TestCase):
    def source(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_modules_parse(self):
        for name in ("src/page_advisory_portal.py", "src/page_reader_native.py"):
            ast.parse(self.source(name), filename=name)

    def test_verified_intake_and_privacy_guards(self):
        from page_advisory_portal import _validate_intake
        valid = {
            "first_name": "Alex",
            "last_name": "Morgan",
            "organization": "Example Company",
            "role_title": "Chief Strategy Officer",
            "decision_context": "Evaluate whether to scale two AI pilots.",
            "advisory_focus": "AI strategy and investment priorities",
            "decision_horizon": "1–3 months",
        }
        result = _validate_intake(valid)
        self.assertEqual(result["last_name"], "Morgan")
        self.assertEqual(result["decision_horizon"], "1–3 months")
        for invalid in (
            {**valid, "last_name": ""},
            {**valid, "organization": ""},
            {**valid, "role_title": ""},
            {**valid, "decision_context": "short"},
            {**valid, "advisory_focus": "unregistered-option"},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    _validate_intake(invalid)

    def test_registration_widget_tree(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "advisory_registration_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertTrue(any("Advisory account" == x.label for x in app.radio))
        labels = [x.label for x in app.text_input]
        for expected in (
            "First name *", "Last name *", "Job title / role *",
            "Organization *", "Professional email *",
        ):
            self.assertIn(expected, labels)
        self.assertTrue(any("business outcome" in x.label for x in app.text_area))
        self.assertEqual(len(app.selectbox), 2)
        self.assertTrue(any("Privacy & Data" in x.label for x in app.checkbox))

    def test_returning_advisory_sign_in_does_not_demand_registration(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "advisory_registration_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception)
        app.radio[0].set_value("Sign in to advisory").run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        labels = [x.label for x in app.text_input]
        self.assertIn("Email address", labels)
        self.assertNotIn("Organization *", labels)
        self.assertNotIn("Professional email *", labels)


    def test_password_setup_widget_is_first_step_after_email_confirmation(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "advisory_password_setup_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        labels = [x.label for x in app.text_input]
        self.assertIn("New password", labels)
        self.assertIn("Confirm password", labels)
        self.assertTrue(any("activate my account" in x.label for x in app.button))
        self.assertFalse(app.radio)

    def test_advisory_password_amr_is_checked_by_authenticated_rpc(self):
        from unittest.mock import patch
        from page_advisory_portal import _password_authenticated
        session = {"access_token": "test-not-real"}
        with patch("page_advisory_portal._request_json", return_value=True) as call:
            self.assertTrue(_password_authenticated(session))
            self.assertIn("portfolio_advisory_password_session_v1", call.call_args.args[1])
            self.assertEqual(call.call_args.kwargs["token"], "test-not-real")
        with patch("page_advisory_portal._request_json", return_value=False):
            self.assertFalse(_password_authenticated(session))

    def test_confirmation_link_uses_password_setup_not_otp_code(self):
        source = self.source("src/page_advisory_portal.py")
        self.assertIn("_consume_query_verification()", source)
        self.assertIn("_first_password_form(session, user)", source)
        self.assertIn('with st.form("advisory_first_password"', source)
        self.assertIn('_set_reader_password(session, str(password))', source)
        self.assertIn('_password_signin(str(user["email"]).strip().lower(), str(password))', source)
        self.assertNotIn('with st.form("advisory_email_code")', source)
        self.assertNotIn('Email my sign-in link', source)
        self.assertIn('Email my verification link', source)
        self.assertIn('with st.form("advisory_password_signin"', source)

    def test_reader_magic_link_cannot_open_advisory_account(self):
        source = self.source("src/page_advisory_portal.py")
        self.assertLess(source.index("if not _password_authenticated(session):",
                                     source.index("def render_advisory_portal")),
                        source.index("_get_advisory_profile(session, user)",
                                     source.index("def render_advisory_portal")))
        self.assertIn("Email confirmation establishes identity only", source)


if __name__ == "__main__":
    unittest.main()
