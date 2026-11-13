"""Advisory Auth callback and recovery redirection contract tests.

No live email or password is sent in these checks. Exact callback and token
handoff matter because Supabase falls back to the Site URL when not allowlisted.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class AdvisoryEmailCallbackTests(unittest.TestCase):
    def test_dedicated_advisory_callback_does_not_use_root_or_streamlit(self):
        from page_reader_native import (
            _callback_origin, _host_origin, ADVISORY_CALLBACK_ORIGIN,
        )
        self.assertEqual(
            _callback_origin("advisory-access"),
            "https://advisory.jairribeiro.com",
        )
        self.assertEqual(ADVISORY_CALLBACK_ORIGIN,
                         "https://advisory.jairribeiro.com")
        self.assertEqual(_callback_origin("readers"), _host_origin())
        with self.assertRaises(ValueError):
            _callback_origin("analytics")

    def test_password_recovery_uses_recovery_endpoint_and_advisory_subdomain(self):
        from page_reader_native import _request_password_recovery
        with patch("page_reader_native._request_json", return_value={}) as request:
            _request_password_recovery("  test@example.org  ")
            method,url=request.call_args.args
            self.assertEqual(method, "POST")
            self.assertEqual(urlsplit(url).path, "/auth/v1/recover")
            callback=parse_qs(urlsplit(url).query)["redirect_to"][0]
            self.assertEqual(callback,
                "https://advisory.jairribeiro.com/?page=advisory-access")
            self.assertEqual(request.call_args.kwargs["payload"],
                             {"email": "test@example.org"})
            self.assertNotIn("create_user", request.call_args.kwargs["payload"])
            self.assertNotIn("password", request.call_args.kwargs["payload"])

    def test_signup_confirmation_uses_same_branded_advisory_subdomain(self):
        from page_reader_native import _request_email
        with patch("page_reader_native.st.query_params", {}):
            with patch("page_reader_native.st.session_state", {}):
                with patch("page_reader_native._request_json", return_value={}) as request:
                    _request_email("Alex","test@example.org",False,False,
                                   destination="advisory-access",
                                   advisory_intake={"first_name":"Alex",
                                                    "privacy_notice_ack":True})
        method,url=request.call_args.args
        self.assertEqual(method, "POST")
        self.assertEqual(urlsplit(url).path, "/auth/v1/otp")
        callback=parse_qs(urlsplit(url).query)["redirect_to"][0]
        self.assertEqual(callback,
                         "https://advisory.jairribeiro.com/?page=advisory-access")
        self.assertEqual(request.call_args.kwargs["payload"]["create_user"], True)

    def test_recovery_query_token_verified_as_recovery_not_magic_email(self):
        from page_reader_native import _consume_query_verification
        token_hash="a"*64
        params={"page":"advisory-access", "token_hash":token_hash, "type":"recovery"}
        state={}
        user={"id":"00000000-0000-0000-0000-000000000001",
              "email":"test@example.org","user_metadata":{}}
        with patch("page_reader_native.st.query_params",params):
            with patch("page_reader_native.st.session_state",state):
                with patch("page_reader_native._verify",return_value=user) as verify:
                    _consume_query_verification()
        verify.assert_called_once_with({"token_hash":token_hash,"type":"recovery"})
        self.assertNotIn("token_hash",params)
        self.assertNotIn("type",params)
        self.assertTrue(state.get("advisory_recovery_verified"))
        self.assertIn("Password-reset email verified",
                      state["reader_native_flash"][1])

    def test_recovery_email_is_not_a_passwordless_signin_email(self):
        source=(ROOT/"src"/"page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn('_request_password_recovery(address, destination="advisory-access")',source)
        self.assertIn("<h2>Reset your Advisory password.</h2>",source)
        self.assertNotIn('_request_email("", address, False, True, destination="advisory-access")',source)

if __name__=="__main__":
    unittest.main()
