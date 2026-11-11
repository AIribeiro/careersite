"""Regression checks for free registered Executive AI Briefings downloads."""
import ast
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

    def test_new_editorial_ctas_are_first_party(self):
        approved = self._source("src/briefing_approved_asset_renderer.py")
        roi = self._source("src/briefing_roi_studio.py")
        authority = self._source("src/briefing_authority_artwork.py")
        for source in (approved, roi, authority):
            self.assertIn("/readers/download/", source)
            self.assertIn('data-hq-event="briefing_reader_pdf"', source)
        self.assertNotIn("'href=\"https://raw.githubusercontent.com/", approved)

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

    def test_no_service_role_key(self):
        source = self._source("src/reader_membership.py")
        self.assertNotIn("service_role", source.lower())
        self.assertNotIn("sb_secret_", source)


if __name__ == "__main__":
    unittest.main()
