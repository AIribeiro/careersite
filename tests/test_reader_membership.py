"""Regression contracts for free verified Executive AI Briefings readers."""
from __future__ import annotations
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReaderMembershipContractTests(unittest.TestCase):
    def source(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_all_edited_python_modules_parse(self):
        for path in (
            "main.py", "app.py", "src/reader_membership.py",
            "src/page_reader_native.py", "src/page_executive_briefings.py",
            "src/reader_catalog_admin.py", "src/page_owner_workspaces.py",
            "src/briefing_approved_asset_renderer.py",
            "src/briefing_roi_studio.py", "src/briefing_authority_artwork.py",
        ):
            with self.subTest(path=path):
                ast.parse(self.source(path), filename=path)

    def test_staging_launcher_bypasses_home_dispatcher(self):
        # Staging override is deliberately isolated to this draft PR.
        launcher = self.source("reader_test.py")
        app = self.source("app.py")
        self.assertIn("render_reader_native()", launcher)
        self.assertIn('App(\n    "reader_test.py"', app)
        self.assertIn("DO NOT MERGE INTO PRODUCTION", app)
        self.assertNotIn("from page_home import", launcher)

    def test_native_staging_app_renders_registration_in_streamlit(self):
        # Exercise the actual widget tree, not only the source text. No email
        # or Supabase Auth request is issued until a user submits the form.
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "reader_test.py"), default_timeout=30).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertTrue(
            any("Take the briefings with you" in x.value for x in app.title),
            "Standalone staging app must render the reader rather than Home",
        )
        self.assertTrue(
            any("Email address" in str(x.label) for x in app.text_input),
        )

    def test_native_reader_is_public_page_with_no_post_proxy(self):
        main = self.source("main.py")
        self.assertIn('"readers"', main)
        self.assertIn("from page_reader_native import render_reader_native", main)
        self.assertIn("render_reader_native()", main)
        native = self.source("src/page_reader_native.py")
        self.assertIn('st.form("reader_native_login_form")', native)
        self.assertIn('st.form("reader_native_code_form")', native)
        self.assertIn("st.download_button(", native)
        self.assertIn('"/auth/v1/otp?"', native)
        self.assertIn('"/auth/v1/verify"', native)
        self.assertNotIn('action="/readers/request"', native)
        self.assertNotIn('action="/~/+/readers/request"', native)

    def test_native_email_identity_and_optional_consent(self):
        native = self.source("src/page_reader_native.py")
        legacy = self.source("src/reader_membership.py")
        self.assertIn('"reader_editorial_opt_in": bool(subscribe)', native)
        self.assertIn('subscribe = st.checkbox(', native)
        self.assertIn("value=False, disabled=returning", native)
        self.assertIn('"email": email, "create_user": not returning', native)
        self.assertIn("portfolio_reader_consent_events", legacy)
        self.assertIn('identity.get("email_confirmed_at")', legacy)
        self.assertIn('auth/v1/user', legacy)

    def test_confirmation_hash_is_consumed_and_secret_not_logged(self):
        native = self.source("src/page_reader_native.py")
        self.assertIn('st.query_params.get("token_hash"', native)
        self.assertIn('st.query_params.pop("token_hash", None)', native)
        self.assertIn('"token_hash": token, "type": "email"', native)
        self.assertIn('"/?page=readers"', native)
        self.assertIn('"https://" + parts.hostname', native)
        self.assertNotIn("st.write(token)", native)
        self.assertNotIn("st.session_state['service_role']", native)

    def test_download_navigation_is_native_and_escapes_masked_frame(self):
        for path in (
            "src/briefing_approved_asset_renderer.py",
            "src/briefing_roi_studio.py",
            "src/briefing_authority_artwork.py",
        ):
            with self.subTest(path=path):
                source = self.source(path)
                self.assertIn("page=readers", source)
                self.assertIn('target="_blank"', source)
                self.assertIn('rel="noopener"', source)
        self.assertIn('href="/?page=readers"',
                      self.source("src/page_executive_briefings.py"))
        self.assertIn('"/?page=readers&download=" + slug',
                      self.source("app.py"))
        self.assertIn('portfolio_reader_downloads',
                      self.source("src/page_reader_native.py"))

    def test_reader_catalog_is_owner_only(self):
        source = self.source("src/reader_catalog_admin.py")
        self.assertIn("OWNER_EMAIL", source)
        self.assertIn("/auth/v1/user", source)
        self.assertIn("portfolio_reader_profiles", source)
        self.assertIn("portfolio_reader_downloads", source)
        self.assertIn("formula injection", source.lower())

    def test_invalid_streamlit_flags_have_been_removed(self):
        config = self.source(".streamlit/config.toml")
        requirements = self.source("requirements.txt")
        self.assertNotIn("useStarlette", config)
        self.assertNotIn("streamlit[starlette]", requirements)
        self.assertIn("streamlit==1.64.0", requirements)

    def test_native_page_uses_only_publishable_credentials(self):
        native = self.source("src/page_reader_native.py").lower()
        self.assertNotIn("service_role", native)
        self.assertNotIn("sb_secret_", native)
        self.assertNotIn("api_secret", native)
        self.assertIn("portfolio_reader_profiles", self.source("src/reader_membership.py"))


if __name__ == "__main__":
    unittest.main()
