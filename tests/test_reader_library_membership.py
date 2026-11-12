"""One-login portfolio reading and personal library regression tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_reader_navigation import _parse_portfolio_route


class ReaderLibraryMembershipTests(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_allowed_same_origin_reader_navigation_keeps_edition_context(self):
        route = _parse_portfolio_route(
            "?page=briefing&article=too-many-ai-opportunities-too-little-capacity&pdf=1"
        )
        self.assertEqual(route["page"], "briefing")
        self.assertEqual(route["article"], "too-many-ai-opportunities-too-little-capacity")
        self.assertEqual(route["pdf"], "1")
        self.assertEqual(_parse_portfolio_route("?page=briefings"), {"page": "briefings"})
        self.assertEqual(_parse_portfolio_route("?page=readers"), {"page": "readers"})

    def test_navigation_rejects_secrets_unregistered_urls_and_duplicates(self):
        bad = (
            "https://outside.example/?page=briefing",
            "?page=briefing&token_hash=should-never-move",
            "?page=briefing&access_token=should-never-move",
            "?page=analytics",
            "?page=briefing&article=../../login",
            "?page=briefing&page=readers",
            "?page=readers&article=a%0Ab",
            "?page=briefings&redirect=https://evil.example",
            "?page=briefings&foo=bar",
            "",
            None,
        )
        for candidate in bad:
            with self.subTest(candidate=candidate):
                self.assertIsNone(_parse_portfolio_route(candidate))

    def test_reader_auth_is_not_in_js_browser_storage_or_url(self):
        nav = self.source("src/site_reader_navigation.py")
        self.assertIn("setTriggerValue('route'", nav)
        self.assertIn("event.preventDefault()", nav)
        self.assertIn("document.addEventListener('click'", nav)
        self.assertIn('st.query_params.from_dict(route)', nav)
        self.assertNotIn("localStorage", nav)
        self.assertNotIn("sessionStorage", nav)
        self.assertNotIn("refresh_token", nav)
        self.assertNotIn("access_token", nav)
        main = self.source("main.py")
        self.assertIn("mount_reader_navigation()", main)
        self.assertIn('st.session_state.get("reader_native_session")', main)

    def test_membership_nav_only_when_signed_in(self):
        from site_components import nav
        with patch("streamlit.session_state", {}):
            public_nav = nav("thinking")
        with patch("streamlit.session_state", {
            "reader_native_session": {"access_token": "server-only-test"}
        }):
            member_nav = nav("thinking")
        self.assertNotIn("reader_member_nav", public_nav)
        self.assertIn('href="?page=readers"', member_nav)
        self.assertIn("My Library", member_nav)
        self.assertNotIn("server-only-test", member_nav)

    def test_reader_hub_contains_complete_catalog_and_account_sections(self):
        native = self.source("src/page_reader_native.py")
        hub = native.split("def _library(session: dict, user: dict) -> None:", 1)[1]
        hub = hub.split("def _dismiss_briefing_dialog()", 1)[0]
        for text in (
            "All briefings", "Saved", "My PDFs", "My profile",
            "fetch_published_articles()", "portfolio_reader_saved_briefings",
            "portfolio_reader_downloads", "Read complete briefing",
            "Save to my library", "Remove from saved",
            "Download again", "Your professional profile", "Account security", "Sign out",
        ):
            with self.subTest(item=text):
                self.assertIn(text, hub + native)
        self.assertNotIn(
            "available = [a for a in articles if _clean_slug(a.slug) and has_briefing_pdf(a.slug)]",
            hub,
        )
        self.assertIn("st.query_params.from_dict", native)

    def test_premium_member_navigation_and_every_tab_has_a_distinct_purpose(self):
        native = self.source("src/page_reader_native.py")
        shell = self.source("src/site_reader_shell.py")
        self.assertIn("reader-member-welcome", native)
        self.assertIn("reader-member-stats", native)
        self.assertIn("reader-member-number", shell)
        self.assertIn('reader-tab-hint', native)
        self.assertIn('Swipe to see all six sections', native)
        self.assertIn('aria-selected="true"', shell)
        self.assertIn('min-height:49px', shell)
        self.assertIn('overflow-x:auto', shell)
        self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))', shell)
        self.assertIn('st.tabs([', native)
        for tab in (
            '"All briefings"', '"Articles"', '"Weekly AI"',
            '"Saved"', '"My PDFs"', '"My profile"',
        ):
            self.assertIn(tab, native)
        for section in (
            "THE COMPLETE BRIEFING LIBRARY",
            "ARTICLES · LEADERSHIP JUDGMENT",
            "WEEKLY AI · EXECUTIVE PERSPECTIVES",
            "YOUR PERSONAL READING LIST",
            "YOUR DECISION VISUALS",
            "YOUR ACCOUNT & READING PREFERENCES",
        ):
            with self.subTest(section=section):
                self.assertIn(section, native)

    def test_member_search_cards_and_pdf_history_are_customer_oriented(self):
        native = self.source("src/page_reader_native.py")
        for label in (
            "Find a briefing", "Find an article", "Find a Weekly AI edition",
            "Find a downloaded infographic", "Read complete briefing",
            "Read complete article", "Read this Weekly AI edition",
            "Save to my library", "Remove from saved",
            "Last downloaded: ", "reader_resource_",
            "reader_edition_", "reader_account",
        ):
            with self.subTest(label=label):
                if label == "reader_account":
                    self.assertIn("reader-account-summary", native)
                else:
                    self.assertIn(label, native)
        self.assertIn('with st.expander("Edit my professional profile', native)
        self.assertIn("_render_password_settings(session)", native)
        self.assertNotIn("st.dataframe(summary", native)
        self.assertIn("html_escape(str(user.get", native)
        self.assertIn('token=str(session["access_token"])', native)

    def test_signed_in_member_library_renders_all_collections_without_network(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(
            str(ROOT / "tests" / "reader_member_workspace_smoke_app.py"),
            default_timeout=45,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertEqual(
            [str(tab.label) for tab in app.tabs],
            ["All briefings", "Articles", "Weekly AI", "Saved", "My PDFs", "My profile"],
        )
        search_labels = {str(item.label) for item in app.text_input}
        for expected in (
            "Find a briefing", "Find an article", "Find a Weekly AI edition",
            "Find a downloaded infographic",
        ):
            self.assertIn(expected, search_labels)
        button_labels = {str(item.label) for item in app.button}
        for expected in (
            "Read complete briefing", "Read complete article",
            "Read this Weekly AI edition", "Open related briefing",
        ):
            self.assertIn(expected, button_labels)

    def test_native_reader_and_analytics_can_log_slow_renders_without_html_timers(self):
        """Exercise the real telemetry block without HTML-only local variables."""
        from unittest.mock import patch

        source = self.source("main.py")
        telemetry = source.split(
            "# Slow-only, privacy-preserving diagnostics. No article content or visitors.",
            1,
        )[1]
        for page in ("readers", "analytics"):
            with self.subTest(page=page):
                context = {
                    "PAGE": page,
                    "RUN_STARTED": 1.0,
                    "perf_counter": lambda: 2.0,
                    "logging": __import__("logging"),
                    # build_done/build_started/footer_done/html_done/page_html_size
                    # intentionally undefined, as in native Streamlit routes.
                }
                with patch("logging.getLogger") as logger:
                    exec(compile(telemetry, "main.py:slow_render", "exec"), context)
                    warning = logger.return_value.warning
                    warning.assert_called_once()
                    arguments = warning.call_args.args
                    self.assertEqual(arguments[1], page)
                    self.assertEqual(arguments[3:], (0, 0, 0, 0))

    def test_signed_in_read_buttons_use_readable_warm_fill_and_label_color(self):
        shell = self.source("src/site_reader_shell.py")
        self.assertIn('background:#E9B98E!important', shell)
        self.assertIn('color:#142B3D!important', shell)
        self.assertIn('button[kind="primary"] :is(p,span,strong)', shell)
        self.assertIn('button[data-testid="stBaseButton-primary"]', shell)
        self.assertIn('button[kind="primary"]:focus-visible', shell)
        self.assertIn('button[kind="primary"]:disabled', shell)
        self.assertIn('background:#F4CDAA!important', shell)

    def test_personal_collections_never_have_anonymous_access(self):
        native = self.source("src/page_reader_native.py")
        self.assertIn('token=str(session["access_token"])', native)
        self.assertIn('user_id=eq.', native)
        self.assertIn('_clean_slug(slug)', native)


if __name__ == "__main__":
    unittest.main()
