"""Public advisory and privacy page regression checks."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_public_services import advisory, privacy
from page_contact import contact
from site_components import footer, nav


class PublicServicePagesTests(unittest.TestCase):
    def test_pages_are_renderable_and_distinct(self):
        advisory_html = advisory()
        privacy_html = privacy()
        self.assertIn('id="advisory-title"', advisory_html)
        self.assertIn('id="advisory-engagements"', advisory_html)
        self.assertIn("AI portfolio and priorities", advisory_html)
        self.assertIn('mailto:advisory@jairribeiro.com', advisory_html)
        self.assertIn("Availability, scope and commercial terms", advisory_html)
        self.assertIn("privacy-page", privacy_html)
        self.assertIn('id="privacy-rights"', privacy_html)
        self.assertIn("privacy@jairribeiro.com", privacy_html)
        self.assertIn("readers@jairribeiro.com", privacy_html)
        self.assertIn("Supabase", privacy_html)
        self.assertIn("Streamlit", privacy_html)
        self.assertIn("13 November 2026", privacy_html)
        self.assertNotIn("jair.ribeiro@outlook", advisory_html + privacy_html)

    def test_all_public_routes_and_discovery_entries(self):
        main = (ROOT / "main.py").read_text()
        app = (ROOT / "app.py").read_text()
        meta = (ROOT / "src/site_meta.py").read_text()
        self.assertIn('"advisory": "Executive AI & Data Advisory', main)
        self.assertIn('"privacy": "Privacy & Data', main)
        self.assertIn('from page_public_services import advisory', main)
        self.assertIn('from page_public_services import privacy', main)
        self.assertIn('/?page=advisory", "2026-11-13"', app)
        self.assertIn('/?page=privacy", "2026-11-13"', app)
        self.assertIn('"advisory": "Executive AI', meta)
        self.assertIn('"privacy": "Privacy notice', meta)

    def test_nav_footer_contact_and_reader_routes(self):
        navigation = nav("advisory")
        common_footer = footer()
        contact_html = contact()
        native = (ROOT / "src/page_reader_native.py").read_text()
        shell = (ROOT / "src/site_reader_shell.py").read_text()
        legacy = (ROOT / "src/reader_membership.py").read_text()
        self.assertIn('href="?page=advisory"', navigation)
        self.assertIn('href="?page=privacy"', common_footer)
        self.assertIn('href="?page=advisory"', common_footer)
        self.assertIn('mailto:jair@jairribeiro.com', common_footer)
        self.assertIn('href="?page=advisory"', contact_html)
        self.assertIn("readers@jairribeiro.com", contact_html)
        self.assertIn("from site_assets import READERS_EMAIL, PRIVACY_EMAIL", native)
        self.assertIn("from site_assets import READERS_EMAIL", shell)
        self.assertIn('RedirectResponse("/?page=privacy"', legacy)

    def test_changed_python_source_compiles(self):
        for name in (
            "main.py",
            "src/site_assets.py",
            "src/page_public_services.py",
            "src/page_contact.py",
            "src/site_components.py",
            "src/site_meta.py",
            "src/site_reader_shell.py",
            "src/page_reader_native.py",
            "src/reader_membership.py",
            "src/agent_discovery.py",
            "app.py",
        ):
            source = (ROOT / name).read_text()
            with self.subTest(path=name):
                compile(source, str(ROOT / name), "exec")


if __name__ == "__main__":
    unittest.main()
