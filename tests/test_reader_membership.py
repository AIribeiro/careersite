"""Regression checks for free registered Executive AI Briefings downloads."""
import ast
import os
from unittest.mock import patch
from urllib.parse import urlsplit
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReaderMembershipContractTests(unittest.TestCase):
    def _source(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_all_edited_python_modules_parse(self):
        for path in (
            "app.py", "src/reader_membership.py",
            "src/page_executive_briefings.py",
            "src/reader_catalog_admin.py",
            "src/page_owner_workspaces.py",
            "src/briefing_approved_asset_renderer.py",
            "src/briefing_roi_studio.py", "src/briefing_authority_artwork.py",
        ):
            with self.subTest(path=path):
                ast.parse(self._source(path), filename=path)

    def test_reader_routes_are_independent_of_owner_auth(self):
        source = self._source("app.py")
        self.assertIn('Route("/owner-auth/{action}"', source)
        self.assertIn('Route("/readers/download/{slug}.pdf"', source)
        self.assertIn('Route("/readers/{action}"', source)
        self.assertIn('reader_download', source)
        self.assertIn('Route("/readers-admin"', source)
        self.assertIn('Route("/readers-admin/export.csv"', source)

    def test_new_editorial_ctas_are_first_party(self):
        approved = self._source("src/briefing_approved_asset_renderer.py")
        roi = self._source("src/briefing_roi_studio.py")
        authority = self._source("src/briefing_authority_artwork.py")
        for source in (approved, roi, authority):
            self.assertIn("/readers/download/", source)
            self.assertIn('data-hq-event="briefing_reader_pdf"', source)
        self.assertNotIn("'href=\"https://raw.githubusercontent.com/", approved)

    def test_auth_callback_supports_explicit_staging_streamlit_origin(self):
        source = self._source("src/reader_membership.py")
        tree = ast.parse(source)
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "_auth_callback_origin")
        namespace = {
            "os": os,
            "urlsplit": urlsplit,
            "BASE_URL": "https://jairribeiro-ai.streamlit.app",
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     "<auth_callback>", "exec"), namespace)
        get_origin = namespace["_auth_callback_origin"]
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                get_origin(), "https://jairribeiro-ai.streamlit.app")
        with patch.dict(os.environ, {
            "PORTFOLIO_READER_CALLBACK_ORIGIN":
                "https://jairribeiro-reader-test.streamlit.app/"
        }):
            self.assertEqual(
                get_origin(), "https://jairribeiro-reader-test.streamlit.app")
        for malicious in (
            "http://jairribeiro-reader-test.streamlit.app",
            "https://evil.example",
            "https://streamlit.app.evil.example",
            "https://jairribeiro-reader-test.streamlit.app/path",
            "https://jairribeiro-reader-test.streamlit.app?next=other",
        ):
            with self.subTest(origin=malicious), patch.dict(os.environ, {
                "PORTFOLIO_READER_CALLBACK_ORIGIN": malicious
            }):
                with self.assertRaises(ValueError):
                    get_origin()

    def test_download_links_escape_spaceship_masked_frame(self):
        for path in (
            "src/briefing_approved_asset_renderer.py",
            "src/briefing_roi_studio.py",
            "src/briefing_authority_artwork.py",
        ):
            with self.subTest(path=path):
                source = self._source(path)
                self.assertIn('target="_blank"', source)
                self.assertIn('rel="noopener"', source)

        page = self._source("src/page_executive_briefings.py")
        self.assertIn(
            'href="/~/+/readers/library" target="_blank" rel="noopener"',
            page,
        )
        reader = self._source("src/reader_membership.py")
        self.assertIn('target="_blank" rel="noopener">Download PDF', reader)

    def test_cloud_proxy_prefix_survives_reader_signup_and_downloads(self):
        # Cloud's root path does not serve these custom ASGI routes. The
        # /~/+/ proxy path must be retained through every user navigation.
        membership = self._source("src/reader_membership.py")
        for relative in (
            "/readers/signin",
            "/readers/login",
            "/readers/confirm",
            "/readers/session",
            "/readers/library",
            "/readers/preferences",
            "/readers/privacy",
            "/readers/signout",
            "/readers/download/",
        ):
            with self.subTest(path=relative):
                self.assertIn("/~/+" + relative, membership)
        # The browser POSTs to the same proxied URL that served the form,
        # retaining /~/+/ and any ?next=slug without a separate action.
        self.assertEqual(membership.count("'<form method=\"post\">'"), 2)
        self.assertIn(
            'action in {"request", "login", "signin"}',
            membership,
        )
        self.assertNotIn(
            'action="/readers/request"',
            membership,
        )
        self.assertNotIn(
            'action="/~/+/readers/request"',
            membership,
        )
        self.assertIn(
            '_auth_callback_origin() + "/~/+/readers/confirm"',
            membership,
        )
        self.assertIn(
            'fetch("/~/+/readers/session",',
            membership,
        )
        for path in (
            "src/briefing_approved_asset_renderer.py",
            "src/briefing_roi_studio.py",
            "src/briefing_authority_artwork.py",
        ):
            self.assertIn("/~/+/readers/download/", self._source(path))
        self.assertIn(
            'href="/~/+/readers/library"',
            self._source("src/page_executive_briefings.py"),
        )
        self.assertIn(
            'href="/~/+/readers-admin"',
            self._source("src/page_owner_workspaces.py"),
        )
        self.assertIn(
            '/~/+/readers-admin/export.csv',
            self._source("src/reader_catalog_admin.py"),
        )
        self.assertIn(
            '/~/+/owner-auth/login',
            self._source("src/site_owner_http_auth.py"),
        )
        self.assertEqual(
            self._source("app.py").count(
                'RedirectResponse("/~/+/readers/download/'
            ), 3,
        )
        # The ASGI registrations remain unprefixed since the Cloud proxy
        # strips /~/+/ before forwarding the request to Starlette.
        app = self._source("app.py")
        self.assertIn('Route("/readers/{action}"', app)
        self.assertNotIn('Route("/~/+/readers/{action}"', app)

    def test_service_registration_does_not_enroll_newsletter_by_default(self):
        source = self._source("src/reader_membership.py")
        self.assertIn('type="checkbox" value="yes"', source)
        self.assertIn('opted_in = form.get("editorial") == "yes"', source)
        self.assertIn('newsletter_consent_at', source)
        self.assertIn('portfolio_reader_consent_events', source)

    def test_downloads_enforce_verified_identity(self):
        source = self._source("src/reader_membership.py")
        self.assertIn('identity.get("email_confirmed_at")', source)
        self.assertIn('if not session or not user:', source)
        self.assertIn('portfolio_reader_downloads', source)
        self.assertIn('Cache-Control', source)
        self.assertIn('secure=True, samesite="lax"', source)

    def test_owner_catalog_requires_verified_owner_and_exposes_no_public_rows(self):
        source = self._source("src/reader_catalog_admin.py")
        self.assertIn("OWNER_EMAIL", source)
        self.assertIn("/auth/v1/user", source)
        self.assertIn("portfolio_reader_profiles", source)
        self.assertIn("portfolio_reader_downloads", source)
        self.assertIn("read-only", source.lower())
        self.assertIn("formula injection", source.lower())
        owner_workspace = self._source("src/page_owner_workspaces.py")
        self.assertIn("/readers-admin", owner_workspace)

    def test_no_service_role_key(self):
        source = self._source("src/reader_membership.py")
        self.assertNotIn("service_role", source.lower())
        self.assertNotIn("sb_secret_", source)


if __name__ == "__main__":
    unittest.main()
