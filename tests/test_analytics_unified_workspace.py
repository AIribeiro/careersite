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

        self.assertEqual(set(_VIEWS), {"overview", "portfolio"})
        self.assertEqual(set(_WORKSPACE_LABELS), {"public", "private", "linkedin", "cms"})
        self.assertEqual(_WORKSPACE_LABELS["public"], "Portfolio Analytics")
        self.assertEqual(_WORKSPACE_LABELS["private"], "Job Hiring Analytics")
        self.assertEqual(_WORKSPACE_LABELS["linkedin"], "Social Media Presence")
        self.assertEqual(_WORKSPACE_LABELS["cms"], "Content Studio")
        for requested in ("public", "private", "cms", "unknown", None):
            self.assertEqual(_resolve_workspace(requested, False), "public")
        self.assertEqual(_resolve_workspace("private", True), "private")
        self.assertEqual(_resolve_workspace("cms", True), "cms")
        self.assertEqual(_resolve_workspace("linkedin", True), "linkedin")
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

    def test_hiring_home_restores_stage_mto_and_dedicated_route(self):
        from page_admin import _PRIVATE_VIEW_ROUTES
        from page_owner_workspaces import (
            _current_stage_groups, render_owner_hiring_home,
        )

        self.assertEqual(_PRIVATE_VIEW_ROUTES["stages"], "Stages & MTO")
        source = inspect.getsource(render_owner_hiring_home)
        self.assertIn("render_owner_stage_dashboard(session)", source)
        # The stage board must appear before fallible job-search warehouse reads.
        self.assertLess(
            source.index("render_owner_stage_dashboard(session)"),
            source.index("fetch_job_records("),
        )
        prediction = {"top_processes": [
            {"employer": "LeoVegas", "process_key": "leovegas|ai lead",
             "stage": "subsequent_interview_completed", "status": "active_reconciled"},
            {"employer": "Betsson", "process_key": "betsson|head of product",
             "stage": "first_interview_completed", "status": "active_unknown_decision"},
            {"employer": "KPMG", "process_key": "kpmg|ai manager",
             "stage": "subsequent_interview_completed", "status": "active_reconciled"},
            {"employer": "Billerud", "process_key": "billerud|ai lead",
             "stage": "application_only", "status": "active_unknown_decision"},
        ]}
        plans = {"betsson|head of product": {"outcome": "rejected"}}
        progressed, applied = _current_stage_groups(prediction, plans)
        self.assertEqual([p["employer"] for p in progressed], ["LeoVegas", "KPMG"])
        self.assertEqual([p["employer"] for p in applied], ["Billerud"])

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
        self.assertIn('LEGACY_ADMIN_LINK = PAGE == "admin"', source)
        self.assertIn('st.query_params["page"] = "analytics"', source)
        self.assertIn('st.query_params["workspace"] = "cms"', source)
        self.assertNotIn('elif PAGE == "admin":', source)


    def test_portfolio_top_metrics_use_tracked_cv_and_contact_actions(self):
        from unittest.mock import MagicMock
        from page_owner_workspaces import _portfolio_action_totals, _quality_cards

        events = [
            {"event_name": "cv_download", "events": 4},
            {"event_name": "cv_download", "events": 2},
            {"event_name": "email_click", "events": 3},
            {"event_name": "linkedin_click", "events": 5},
            {"event_name": "page_view", "events": 50},
        ]
        self.assertEqual(
            _portfolio_action_totals({"events": events}),
            {"cv_download": 6, "email_click": 3, "linkedin_click": 5},
        )
        self.assertIsNone(_portfolio_action_totals({}))
        self.assertEqual(
            _portfolio_action_totals({"events": [
                {"event_name": "cv_download", "events": -10},
                {"event_name": "email_click", "events": "invalid"},
            ]}),
            {"cv_download": 0, "email_click": 0, "linkedin_click": 0},
        )

        with (
            patch("page_owner_workspaces._fetch_hiring_intelligence",
                  return_value={"quality_summary": {
                      "analysis_eligible_sessions": 20, "engaged_sessions": 10,
                  }}) as quality,
            patch("page_owner_workspaces._fetch_dashboard",
                  return_value={"events": events}) as lifetime,
            patch("page_owner_workspaces.st") as mock_st,
        ):
            mock_st.columns.return_value = [MagicMock() for _ in range(4)]
            _quality_cards()
            quality.assert_called_once_with("30d")
            lifetime.assert_called_once_with("all")
            measured = [(c.args[0], c.args[1]) for c in mock_st.metric.call_args_list]
            self.assertEqual(measured, [
                ("Qualified sessions", "20"),
                ("Engaged sessions", "10"),
                ("CV downloads", "6"),
                ("Contact clicks", "8"),
            ])

    def test_portfolio_kpi_unavailable_source_does_not_claim_zero(self):
        from unittest.mock import MagicMock
        from page_owner_workspaces import _quality_cards

        with (
            patch("page_owner_workspaces._fetch_hiring_intelligence", return_value={}),
            patch("page_owner_workspaces._fetch_dashboard",
                  side_effect=RuntimeError("not available")),
            patch("page_owner_workspaces.st") as mock_st,
        ):
            mock_st.columns.return_value = [MagicMock() for _ in range(4)]
            _quality_cards()
            values = [c.args[1] for c in mock_st.metric.call_args_list]
            self.assertEqual(values, ["—", "—", "—", "—"])


if __name__ == "__main__":
    unittest.main()
