"""First-use guidance and privacy-minimal milestone regression tests."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_onboarding_guidance import (
    ADVISORY_NEEDS, advisor_for_need, select_reader_first_read,
    suggested_decision_need, value_path_html,
)
from site_onboarding_measurement import (
    duration_label, owner_first_value_summary, record_first_value,
)


def publication(slug, title, category="AI governance", kind="executive briefing"):
    return SimpleNamespace(
        slug=slug, title=title, category=category,
        subtitle="", excerpt="", kind=kind,
    )


class ContextualOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            publication("governance-at-scale", "Governance at scale"),
            publication("agent-accountability", "Who owns AI agents?", "AI agents"),
            publication("adoption-evidence", "Practical adoption evidence", "AI adoption"),
        ]

    def test_selected_real_publication_has_priority_over_profile_topic(self):
        selected, why = select_reader_first_read(
            self.catalog, {"interests": ["AI adoption"]},
            requested_slug="agent-accountability",
        )
        self.assertEqual(selected.slug, "agent-accountability")
        self.assertIn("selected", why)

    def test_explicit_topic_overrides_original_article_and_profile(self):
        selected, why = select_reader_first_read(
            self.catalog, {"interests": ["AI governance"]},
            requested_slug="governance-at-scale", selected_topic="AI adoption",
        )
        self.assertEqual(selected.slug, "adoption-evidence")
        self.assertIn("topic", why)

    def test_profile_only_suggestion_explains_itself(self):
        selected, why = select_reader_first_read(
            self.catalog, {"interests": ["AI agents"]},
        )
        self.assertEqual(selected.slug, "agent-accountability")
        self.assertIn("chose in your profile", why)

    def test_no_fake_recommendation_for_missing_topic_or_empty_catalog(self):
        item, why = select_reader_first_read(
            self.catalog, {}, selected_topic="Quantum underwater economics",
        )
        self.assertIsNone(item)
        self.assertIn("No published edition", why)
        self.assertEqual(
            select_reader_first_read([], {}, requested_slug="made-up")[0], None
        )

    def test_unknown_slug_does_not_create_unsafe_route(self):
        item, _ = select_reader_first_read(
            self.catalog + [publication("<script>", "Bad item")],
            {}, requested_slug="<script>",
        )
        self.assertEqual(item.slug, "governance-at-scale")

    def test_advisory_detects_stored_context_without_granting_access(self):
        checks = [
            ("We need to prioritize competing portfolio initiatives", "scorecard"),
            ("Our AI pilot is ready for wider rollout", "rollout"),
            ("Governance ownership is disputed", "requests"),
            ("Assess the ROI of a single AI opportunity", "decision"),
        ]
        for context, expected_view in checks:
            with self.subTest(context=context):
                choice, rationale = suggested_decision_need({"decision_context": context})
                service = advisor_for_need(choice)
                self.assertEqual(service["view"], expected_view)
                self.assertIn("saved", rationale)
                self.assertNotIn("approved", service)
        self.assertTrue(advisor_for_need(ADVISORY_NEEDS[1])["approval"])
        self.assertTrue(advisor_for_need(ADVISORY_NEEDS[2])["approval"])
        self.assertFalse(advisor_for_need(ADVISORY_NEEDS[0])["approval"])

    def test_advisory_fallback_is_explicit_and_nonrestrictive(self):
        selected, rationale = suggested_decision_need({})
        self.assertEqual(selected, ADVISORY_NEEDS[0])
        self.assertIn("not yet selected", rationale)
        with self.assertRaises(ValueError):
            advisor_for_need("Premium assessment access granted")

    def test_before_after_copy_is_responsive_and_escaped(self):
        rendered = value_path_html("<img src=x>", "Clear, evidenced next steps")
        self.assertIn("&lt;img src=x&gt;", rendered)
        self.assertNotIn("<img src=x>", rendered)
        self.assertIn("@media(max-width:630px)", rendered)
        self.assertIn("Starting point", rendered)
        self.assertIn("What you can work with", rendered)

    def test_milestones_send_no_titles_context_or_client_timestamps(self):
        with patch("site_onboarding_measurement._request_json", return_value=None) as request:
            self.assertTrue(record_first_value(
                "valid-access", "example-uuid", "reader", "first_full_read"
            ))
        args = request.call_args
        self.assertEqual(args.args[0], "POST")
        self.assertEqual(args.kwargs["payload"], {
            "user_id": "example-uuid", "journey": "reader",
            "milestone": "first_full_read",
        })
        self.assertEqual(
            args.kwargs["prefer"], "resolution=ignore-duplicates,return=minimal",
        )
        self.assertNotIn("article_slug", str(args.kwargs["payload"]))
        with self.assertRaises(ValueError):
            record_first_value("token", "uid", "reader", "watching_every_click")

    def test_metrics_failure_never_blocks_the_first_edition(self):
        with patch("site_onboarding_measurement._request_json",
                   side_effect=RuntimeError("Offline")):
            self.assertFalse(record_first_value(
                "token", "uid", "advisory", "first_assessment"
            ))

    def test_owner_summary_is_aggregate_only(self):
        created = "2026-11-15T12:00:00+00:00"
        readers = [
            {"user_id": "r1", "created_at": created},
            {"user_id": "r2", "created_at": created},
            {"user_id": "legacy-reader", "created_at": "2026-11-01T00:00:00Z"},
        ]
        advisory = [
            {"user_id": "a1", "account_status": "active", "created_at": created},
            {"user_id": "a2", "account_status": "suspended", "created_at": created},
        ]
        rows = [
            {"user_id": "r1", "journey": "reader", "milestone": "first_full_read",
             "elapsed_seconds": 180},
            {"user_id": "a1", "journey": "advisory", "milestone": "first_assessment",
             "elapsed_seconds": 660},
            {"user_id": "a1", "journey": "advisory", "milestone": "first_personal_request",
             "elapsed_seconds": 45},
            {"user_id": "a2", "journey": "advisory", "milestone": "first_assessment",
             "elapsed_seconds": 2},
        ]
        summary = owner_first_value_summary(readers, advisory, rows)
        self.assertEqual(summary["reader_registrations"], 3)
        self.assertEqual(summary["reader_cohort_registrations"], 2)
        self.assertEqual(summary["reader_first_reads"], 1)
        self.assertEqual(summary["advisory_registrations"], 1)
        self.assertEqual(summary["advisory_cohort_registrations"], 1)
        self.assertEqual(summary["advisory_first_assessments"], 1)
        self.assertEqual(summary["advisory_personal_requests"], 1)
        self.assertEqual(summary["reader_median_seconds"], 180)
        self.assertEqual(summary["advisory_median_seconds"], 660)
        self.assertNotIn("r1", str(summary))
        self.assertEqual(duration_label(180), "3 min")

    def test_instrumentation_only_after_successful_service_writes(self):
        files = {
            "src/page_advisory_investment.py": ("record_id = _submit", "record_first_value"),
            "src/page_advisory_rollout.py": ("new_id=_submit_assessment", "record_first_value"),
            "src/page_advisory_scorecard_experience.py": (
                "if not report[\"rows\"]:", "scorecard_onboarding_first_report_logged",
            ),
            "src/page_advisory_client_journey.py": ("_create_request(token,uid,{", "record_first_value"),
            "src/page_reader_native.py": ("def _open_reader_content", "_record_first_complete_read"),
        }
        for path, markers in files.items():
            content = (ROOT / path).read_text(encoding="utf-8")
            ast.parse(content, filename=path)
            for marker in markers:
                self.assertIn(marker, content, path)

    def test_schema_requires_membership_scoped_first_time_only(self):
        sql = (ROOT / "docs/sql/portfolio_onboarding_milestones_20261115.sql").read_text()
        self.assertIn("references auth.users(id) on delete cascade", sql)
        self.assertIn("primary key (user_id, journey, milestone)", sql)
        self.assertIn("security invoker", sql)
        self.assertIn("enable row level security", sql)
        self.assertIn("user_id = (select auth.uid())", sql)
        self.assertNotIn("service_role", sql)


if __name__ == "__main__":
    unittest.main()
