"""Regression contracts for the four owner-only administration domains."""
from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from page_analytics_v2 import _WORKSPACE_LABELS, _resolve_workspace
from page_owner_workspaces import (
    _PORTFOLIO_VIEWS, _SOCIAL_VIEWS, _social_rows,
    render_owner_portfolio, render_owner_social, render_owner_hiring_home,
)


class OwnerWorkspaceSeparationTests(unittest.TestCase):
    def test_four_domains_are_clear_and_private_gates_survive(self):
        self.assertEqual(
            list(_WORKSPACE_LABELS.values()),
            ["Portfolio Analytics", "Job Hiring Analytics",
             "Social Media Presence", "Content Studio"],
        )
        self.assertEqual(_resolve_workspace("linkedin", False), "public")
        self.assertEqual(_resolve_workspace("private", False), "public")
        self.assertEqual(_resolve_workspace("cms", False), "public")
        self.assertEqual(_resolve_workspace("linkedin", True), "linkedin")

    def test_portfolio_owns_all_site_and_attribution_evidence(self):
        source = inspect.getsource(render_owner_portfolio)
        self.assertEqual(
            set(_PORTFOLIO_VIEWS),
            {"overview", "content", "audience", "quality", "contribution"},
        )
        for renderer in (
            "render_public_portfolio_overview",
            "render_content_intelligence",
            "render_visitor_diagnostics",
            "render_cv_attribution_audit",
            "render_portfolio_job_correlations",
        ):
            self.assertIn(renderer, source)

    def test_job_home_separates_recruiting_from_portfolio_views(self):
        from page_public_analytics import render_public_job_search

        source = inspect.getsource(render_owner_hiring_home)
        self.assertIn("render_public_job_search(include_portfolio=False)", source)
        self.assertIn("_action_queue", source)
        self.assertIn("fetch_job_records", source)
        self.assertIn("include_portfolio: bool = True", inspect.getsource(render_public_job_search))

    def test_social_source_aggregates_exclude_unknown_and_non_social(self):
        report = {"campaigns": [
            {"channel": "linkedin", "campaign": "article",
             "sessions": 8, "reader_sessions": 6,
             "engaged_sessions": 4, "cv_sessions": 2, "contact_sessions": 1},
            {"channel": "threads", "campaign": "weekly_ai",
             "sessions": 3, "reader_sessions": 2,
             "engaged_sessions": 1, "cv_sessions": 0, "contact_sessions": 0},
            {"channel": "direct/unknown", "campaign": "untagged",
             "sessions": 30, "reader_sessions": 20,
             "engaged_sessions": 14, "cv_sessions": 4, "contact_sessions": 2},
            {"channel": "email", "campaign": "recruiter",
             "sessions": 12, "reader_sessions": 7,
             "engaged_sessions": 5, "cv_sessions": 2, "contact_sessions": 1},
        ]}
        with patch("page_owner_workspaces.fetch_intelligence", return_value=report) as fetch:
            rows = _social_rows("30d")
        fetch.assert_called_once_with("30d")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Source"], "linkedin")
        self.assertEqual(rows[0]["Sessions"], 8)
        self.assertEqual(rows[1]["Source"], "threads")

    def test_linkedin_actions_and_campaign_generator_live_in_social(self):
        source = inspect.getsource(render_owner_social)
        self.assertIn("render_linkedin_career_scorecard(embedded=True)", source)
        self.assertIn("_distribution_links(articles)", source)
        self.assertIn("fetch_intelligence", inspect.getsource(_social_rows))
        self.assertEqual(
            set(_SOCIAL_VIEWS),
            {"overview", "relationships", "channels", "distribution"},
        )


if __name__ == "__main__":
    unittest.main()
