"""Contracts for shared portfolio navigation/header/footer on Streamlit pages."""
from __future__ import annotations
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


class NativePortfolioIntegrationTests(unittest.TestCase):
    def source(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_all_native_shell_sources_parse(self):
        for name in (
            "main.py", "src/site_native_shell.py",
            "src/site_components.py", "src/site_reader_navigation.py",
            "src/page_advisory_portal.py", "src/page_analytics_v2.py",
        ):
            with self.subTest(file=name):
                ast.parse(self.source(name), filename=name)

    def test_advisory_uses_actual_portfolio_menu_and_footer(self):
        from site_native_shell import native_header, native_footer
        head = native_header("advisory-access")
        foot = native_footer("advisory-access")
        self.assertIn('class="site native-shell native-shell-header"', head)
        self.assertIn('class="site native-shell native-shell-footer"', foot)
        self.assertIn('href="?page=home"', head)
        self.assertIn('href="?page=advisory"', head)
        self.assertIn('href="?page=advisory-access"', head)
        self.assertIn('href="?page=thinking"', head)
        self.assertIn('href="?page=contact"', head)
        self.assertIn('class="native-crumb"', head)
        self.assertIn('class="footer"', foot)
        self.assertIn('href="?page=briefings"', foot)
        self.assertIn('href="?page=privacy"', foot)
        self.assertIn('advisory@jairribeiro.com', foot)

    def test_analytics_uses_identical_menu_and_footer_components(self):
        from site_native_shell import native_header, native_footer
        head = native_header("analytics")
        foot = native_footer("analytics")
        self.assertIn('href="?page=analytics"', head)
        self.assertIn('class="link on"', head)
        self.assertIn('class="nav"', head)
        self.assertIn('class="footer"', foot)
        self.assertIn('href="?page=home"', foot)

    def test_advisory_does_not_expose_one_time_token_before_brand_image(self):
        source = self.source("src/page_advisory_portal.py")
        renderer = source.split('def render_advisory_portal() -> None:', 1)[1]
        self.assertLess(renderer.index('_consume_query_verification()'),
                        renderer.index('st.html(native_header("advisory-access"))'))
        self.assertIn('with st.container(key="native_advisory_content"):', renderer)
        self.assertIn('st.html(native_footer("advisory-access"))', renderer)
        self.assertLess(renderer.index('if not _password_authenticated(session):') if
                        'if not _password_authenticated(session):' in renderer else
                        renderer.index('elif not _password_authenticated(session):'),
                        renderer.index('profile = _get_advisory_profile(session, user)'))
        self.assertNotIn('st.html("""<header class="advisory-private-hero"', renderer)

    def test_same_session_navigation_handles_every_portfolio_account_page(self):
        from site_reader_navigation import _parse_portfolio_route
        for page in ("home", "thinking", "readers", "advisory",
                     "advisory-access", "privacy", "analytics", "about"):
            with self.subTest(page=page):
                self.assertEqual(
                    _parse_portfolio_route("?page=" + page), {"page": page},
                )
        self.assertIsNone(_parse_portfolio_route("?page=advisory-access&token_hash=abc"))
        js = self.source("src/site_reader_navigation.py")
        self.assertIn("'advisory-access','privacy','analytics'", js)

    def test_main_dispatches_all_native_pages_through_one_shared_shell(self):
        main = self.source("main.py")
        self.assertIn('elif PAGE == "advisory-access":', main)
        self.assertIn('render_advisory_portal()', main)
        self.assertIn('st.html(native_header("analytics"))', main)
        self.assertIn('st.html(native_footer("analytics"))', main)
        reader = self.source("src/page_reader_native.py")
        self.assertIn('st.html(reader_header(staging=staging))', reader)
        self.assertIn('st.html(reader_footer())', reader)

    def test_advisory_registration_form_renders_with_portfolio_shell(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "advisory_portfolio_shell_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        labels = [x.label for x in app.text_input]
        self.assertIn("First name *", labels)
        self.assertIn("Last name *", labels)
        self.assertIn("Professional email *", labels)
        self.assertTrue(any("Advisory account" == x.label for x in app.radio))


if __name__ == "__main__":
    unittest.main()
