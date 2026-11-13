"""Reader password authentication and optional professional profile tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from page_reader_native import _password_signin, _set_reader_password, _profile_url


class ReaderPasswordProfileTests(unittest.TestCase):
    def source(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_password_login_uses_supabase_auth_not_reader_records(self):
        response = {"access_token": "test-token", "refresh_token": "test-refresh"}
        with (
            patch("page_reader_native._request_json", return_value=response) as request,
            patch("page_reader_native._accept_reader_session", return_value={"id": "reader"}) as accept,
        ):
            identity = _password_signin("  READER@EXAMPLE.COM ", "my-private-password")
        self.assertEqual(identity["id"], "reader")
        self.assertIn("/auth/v1/token?grant_type=password", request.call_args.args[1])
        self.assertEqual(request.call_args.kwargs["payload"], {
            "email": "reader@example.com", "password": "my-private-password",
        })
        accept.assert_called_once_with(response)

    def test_password_login_rejects_empty_or_invalid_credentials(self):
        with patch("page_reader_native._request_json") as request:
            for email, secret in [
                ("not-an-email", "something"), ("reader@example.com", ""),
            ]:
                with self.subTest(email=email, empty=not secret):
                    with self.assertRaises(ValueError):
                        _password_signin(email, secret)
            request.assert_not_called()

    def test_password_setup_changes_supabase_auth_only(self):
        with patch(
            "page_reader_native._request_json",
            return_value={"id": "00000000-0000-0000-0000-000000000001"},
        ) as request:
            _set_reader_password(
                {"access_token": "current-session"}, "long-unique-secret-2026",
            )
        self.assertEqual(request.call_args.args[0], "PUT")
        self.assertIn("/auth/v1/user", request.call_args.args[1])
        self.assertEqual(request.call_args.kwargs["token"], "current-session")
        self.assertEqual(
            request.call_args.kwargs["payload"], {"password": "long-unique-secret-2026"}
        )
        self.assertNotIn("portfolio_reader_profiles", request.call_args.args[1])

    def test_short_password_and_unconfirmed_auth_change_rejected(self):
        with patch("page_reader_native._request_json") as request:
            for secret in ("short", "", "x" * 129):
                with self.subTest(n=len(secret)):
                    with self.assertRaises(ValueError):
                        _set_reader_password({"access_token": "token"}, secret)
            request.assert_not_called()
        with patch("page_reader_native._request_json", return_value={}):
            with self.assertRaises(RuntimeError):
                _set_reader_password({"access_token": "token"}, "valid-length-secret")

    def test_professional_urls_require_https_and_valid_linkedin_domain(self):
        self.assertEqual(_profile_url(""), "")
        self.assertEqual(
            _profile_url("https://www.linkedin.com/in/test", linkedin=True),
            "https://www.linkedin.com/in/test",
        )
        for candidate in (
            "javascript:alert(1)", "http://linkedin.com/in/test",
            "https://notlinkedin.com/in/test", "https://linkedin.com.evil.test/in/x",
            "https://reader@linkedin.com/in/test",
        ):
            with self.subTest(url=candidate):
                with self.assertRaises(ValueError):
                    _profile_url(candidate, linkedin=True)

    def test_streamlit_profile_has_optional_fields_password_and_support(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "reader_password_profile_smoke_app.py"),
            default_timeout=45,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        labels = {str(x.label) for x in app.text_input}
        for expected in (
            "First name", "Last name (optional)", "Job title / professional role",
            "Company / organization", "Industry / sector", "Country",
            "LinkedIn profile URL", "Professional website",
        ):
            with self.subTest(label=expected):
                self.assertIn(expected, labels)
        self.assertTrue(any("Executive AI topics" in str(x.label) for x in app.multiselect))
        self.assertTrue(any("Account security" in str(x.label) for x in app.expander))
        self.assertIn("from site_assets import READERS_EMAIL, PRIVACY_EMAIL", self.source("src/page_reader_native.py"))
        self.assertNotIn("info@jairribeiro.com", self.source("src/page_reader_native.py"))

    def test_login_preserves_email_code_fallback_and_generic_auth_errors(self):
        text = self.source("src/page_reader_native.py")
        self.assertIn('st.form("reader_password_signin_form", clear_on_submit=True)', text)
        self.assertIn('st.form("reader_native_code_form")', text)
        self.assertIn('type="password"', text)
        self.assertIn("forgotten it?", text)
        self.assertIn("Check your credentials or use email verification", text)
        self.assertIn('"reader_editorial_opt_in": bool(subscribe)', text)
        self.assertNotIn('"password": password,', self.source("src/reader_membership.py"))

    def test_owner_can_view_optional_fields_but_not_password(self):
        owner = self.source("src/page_owner_reader_management.py")
        for field in (
            "job_title", "organization", "industry", "country",
            "preferred_language", "interests", "ai_adoption_stage",
            "primary_challenge",
        ):
            self.assertIn(field, owner)
        self.assertIn("Passwords are managed only by Supabase Auth", owner)
        self.assertNotIn('"password":', owner)


if __name__ == "__main__":
    unittest.main()
