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

    def test_staging_sender_redirect_never_uses_localhost(self):
        launcher = self.source("reader_test.py")
        native = self.source("src/page_reader_native.py")
        self.assertIn(
            'os.environ["PORTFOLIO_READER_CALLBACK_ORIGIN"]',
            launcher,
        )
        self.assertIn("https://jairribeiro-reader-test.streamlit.app", launcher)
        self.assertIn('target = _host_origin() + "/?page=readers"', native)
        self.assertIn('urlencode({"redirect_to": target})', native)
        self.assertNotIn("localhost:3000", native)

    def test_portfolio_main_launcher_restored_and_standalone_smoke_kept(self):
        # The deployed app must boot the real portfolio, not only signup.
        launcher = self.source("reader_test.py")
        app = self.source("app.py")
        main = self.source("main.py")
        footer = self.source("src/site_components.py")
        self.assertIn("render_reader_native()", launcher)
        self.assertIn('app = App(', app)
        self.assertIn('"main.py",', app)
        self.assertNotIn('"reader_test.py",', app)
        self.assertIn('if PAGE == "readers":', main)
        self.assertIn('render_reader_native()', main)
        self.assertIn('href="?page=readers"', footer)
        self.assertIn('reader_library_footer', footer)
        self.assertNotIn("from page_home import", launcher)

    def test_native_staging_app_renders_registration_in_streamlit(self):
        # Exercise the actual widget tree, not only the source text. No email
        # or Supabase Auth request is issued until a user submits the form.
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "reader_test.py"), default_timeout=30).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertTrue(
            any("Reader status" in str(x.label) for x in app.radio),
            "Standalone staging app must render native reader sign-in controls",
        )
        self.assertTrue(
            any("Email address" in str(x.label) for x in app.text_input),
        )

    def test_reader_reuses_actual_portfolio_shell_and_safe_token_order(self):
        native = self.source("src/page_reader_native.py")
        shell = self.source("src/site_reader_shell.py")
        stage = self.source("reader_test.py")
        self.assertIn("from site_components import footer, nav", shell)
        self.assertIn('nav("thinking")', shell)
        self.assertIn('footer()', shell)
        self.assertIn("CSS + IMAGE_CSS + READER_SHELL_CSS", shell)
        self.assertIn("reader-hero", shell)
        self.assertIn("reader-shell-footer", shell)
        self.assertIn('layout="wide"', stage)
        self.assertIn('st.container(key="reader_flow")', native)
        self.assertIn("st.html(reader_header(staging=staging))", native)
        self.assertIn("st.html(reader_footer())", native)
        self.assertLess(
            native.index("    _consume_query_verification()", native.index("def render_reader_native")),
            native.index("    st.html(reader_header", native.index("def render_reader_native")),
            "One-time email tokens must be removed before logo and other media load",
        )
        self.assertIn('top.replace(\'href="?page=\'', shell)
        self.assertIn("https://jairribeiro-reader-test.", native)

    def test_production_portfolio_dispatcher_renders_native_reader(self):
        # In addition to isolated reader_test.py, run the real main.py page
        # router to catch Home fallback or missing Streamlit context.
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "main.py"), default_timeout=50)
        app.query_params["page"] = "readers"
        app.run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertTrue(
            any("Email address" in str(x.label) for x in app.text_input),
            "Main portfolio route ?page=readers must render native signup",
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
                self.assertIn("page=briefing", source)
                self.assertIn('target="_self"', source)
                self.assertIn('pdf=1', source)
        self.assertIn('href="/?page=readers"',
                      self.source("src/page_executive_briefings.py"))
        self.assertIn('"/?page=briefing&article=" + slug + "&pdf=1"',
                      self.source("app.py"))
        self.assertIn('portfolio_reader_downloads',
                      self.source("src/page_reader_native.py"))
        self.assertIn("render_briefing_access_dialog", self.source("main.py"))
        self.assertIn('"access"', self.source("src/page_reader_native.py"))
        self.assertIn('render_public_briefing_preview', self.source("src/site_cms.py"))
        self.assertIn('get full briefing', self.source("src/briefing_reader_preview.py").lower())


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
