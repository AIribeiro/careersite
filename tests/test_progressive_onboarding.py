"""Progressive Advisory registration and secure Reader email-link contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ProgressiveOnboardingTests(unittest.TestCase):
    def test_sources_parse(self):
        for path in ("src/page_advisory_portal.py", "src/page_advisory_client_journey.py",
                     "src/page_reader_native.py"):
            ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)

    def test_minimal_identity_is_valid_but_name_is_required(self):
        from page_advisory_portal import _validate_registration_intake
        candidate = _validate_registration_intake({"first_name": "Alex"})
        self.assertEqual(candidate["first_name"], "Alex")
        self.assertEqual(candidate["organization"], "")
        self.assertEqual(candidate["role_title"], "")
        self.assertEqual(candidate["decision_context"], "")
        with self.assertRaises(ValueError):
            _validate_registration_intake({"first_name": ""})
        with self.assertRaises(ValueError):
            _validate_registration_intake({"first_name": "A" * 81})

    def test_minimal_registration_still_requires_verified_identity(self):
        from page_advisory_portal import _register_advisory
        user = {"id": "mock-uid", "email": "alex@example.org", "email_confirmed_at": "2026-11-15"}
        with patch("page_advisory_portal._request_json", return_value=[{"user_id": "mock-uid"}]) as post:
            _register_advisory({"access_token": "verified-token"}, user, {"first_name": "Alex"})
            kwargs = post.call_args.kwargs
            self.assertEqual(kwargs["token"], "verified-token")
            self.assertEqual(kwargs["payload"]["organization"], "")
            self.assertEqual(kwargs["payload"]["first_name"], "Alex")
            self.assertEqual(kwargs["payload"]["email"], "alex@example.org")
        with self.assertRaises(ValueError):
            _register_advisory({"access_token": "verified-token"},
                              {**user, "email_confirmed_at": None}, {"first_name": "Alex"})

    def test_personal_request_collects_role_and_company_at_point_of_need(self):
        from page_advisory_client_journey import _complete_request_profile
        uid = "00000000-0000-4000-8000-000000000001"
        with patch("page_advisory_client_journey._request_json",
                   return_value=[{"user_id": uid}]) as patch_request:
            _complete_request_profile("member-token", uid, {}, "AI Director", "Example AB")
            kwargs = patch_request.call_args.kwargs
            self.assertEqual(kwargs["token"], "member-token")
            self.assertEqual(kwargs["payload"],
                             {"role_title": "AI Director", "organization": "Example AB"})
            self.assertIn("user_id=eq.", patch_request.call_args.args[1])
        with self.assertRaises(ValueError):
            _complete_request_profile("member-token", uid, {}, "", "Example AB")
        with patch("page_advisory_client_journey._request_json") as patch_request:
            _complete_request_profile("member-token", uid,
                {"role_title": "AI Director", "organization": "Example AB"},
                "AI Director", "Example AB")
            patch_request.assert_not_called()

    def test_reader_uses_secure_email_link_first_and_keeps_provider_code(self):
        source = (ROOT / "src/page_reader_native.py").read_text(encoding="utf-8")
        self.assertIn("Open the secure link in your email. No code to type.", source)
        self.assertIn('with st.expander("Having trouble with the link?', source)
        self.assertIn('re.fullmatch(r"\\d{6,10}", code)', source)
        self.assertNotIn("4-digit code", source)

    def test_advisory_enrollment_keeps_account_and_reader_separate(self):
        source = (ROOT / "src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn("_signup_context(user)", source)
        self.assertIn("_password_authenticated(session)", source)
        self.assertIn("_validate_registration_intake({\"first_name\": first})", source)
        self.assertNotIn("if not accepted:", source)
        self.assertIn("PRIVACY_NOTICE_URL", source)
        self.assertIn("role, organization", (ROOT / "src/page_advisory_client_journey.py")
                      .read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
