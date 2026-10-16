"""Regression checks for one public/owner Analytics and CMS entry point."""
from __future__ import annotations

from pathlib import Path
import inspect
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class UnifiedAnalyticsWorkspaceTests(unittest.TestCase):
    def test_public_views_are_unchanged_and_owner_scope_is_explicit(self):
        from page_analytics_v2 import _VIEWS, _WORKSPACE_LABELS, _resolve_workspace

        self.assertEqual(set(_VIEWS), {
            "overview", "portfolio", "jobs", "predictions", "market",
        })
        self.assertEqual(set(_WORKSPACE_LABELS), {"public", "private", "cms"})
        for requested in ("public", "private", "cms", "unknown", None):
            self.assertEqual(_resolve_workspace(requested, False), "public")
        self.assertEqual(_resolve_workspace("private", True), "private")
        self.assertEqual(_resolve_workspace("cms", True), "cms")
        self.assertEqual(_resolve_workspace("unknown", True), "public")

    def test_existing_private_reports_and_cms_stay_in_place(self):
        from page_admin import _dashboard

        self.assertIn("workspace_mode", inspect.signature(_dashboard).parameters)
        source = inspect.getsource(_dashboard)
        for label in (
            "Decision overview", "Detailed job analytics",
            "Stale applications", "Rejection Analytics", "Hiring market",
            "CMS",
        ):
            self.assertIn(label, source)
        for renderer in (
            "render_job_search_analytics", "render_private_staleness",
            "render_rejection_analytics", "render_swedish_job_market",
            "render_analytics_overview",
        ):
            self.assertIn(renderer, source)
        for action in (
            "admin_list_articles", "_editor(article, token)",
            "duplicate_article", "change_article_status", "delete_article",
        ):
            self.assertIn(action, source)

    def test_anonymous_navigation_never_invokes_private_renderers(self):
        from streamlit.testing.v1 import AppTest

        with (
            patch("page_admin._session", return_value=None),
            patch("page_admin._dashboard") as private,
            patch("page_analytics_v2._render_public_analytics") as public,
            patch("site_owner_persistence.show_owner_login_or_refresh"),
        ):
            at = AppTest.from_string(
                "from page_analytics_v2 import render_analytics_dashboard\n"
                "render_analytics_dashboard()\n"
            ).run(timeout=20)
            self.assertFalse(at.exception)
            public.assert_called_once()
            private.assert_not_called()

    def test_verified_owner_can_reach_existing_private_workspace(self):
        from streamlit.testing.v1 import AppTest

        owner = {
            "access_token": "test-owner-jwt",
            "user": {"email": "test-owner@example.test"},
        }
        with (
            patch("page_admin._session", return_value=owner),
            patch("page_admin._dashboard") as private,
            patch("page_admin._css"),
            patch("page_analytics_v2._workspace_from_url", return_value="private"),
            patch("page_analytics_v2._render_public_analytics") as public,
        ):
            at = AppTest.from_string(
                "from page_analytics_v2 import render_analytics_dashboard\n"
                "render_analytics_dashboard()\n"
            ).run(timeout=20)
            self.assertFalse(at.exception)
            private.assert_called_once_with(owner, workspace_mode="private")
            public.assert_not_called()

    def test_legacy_admin_link_resolves_to_cms_in_analytics(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('if PAGE == "admin":', source)
        self.assertIn('st.query_params["page"] = "analytics"', source)
        self.assertIn('st.query_params["workspace"] = "cms"', source)
        self.assertNotIn('elif PAGE == "admin":', source)


if __name__ == "__main__":
    unittest.main()
