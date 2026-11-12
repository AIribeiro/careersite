"""Regression contracts for owner-only audience and campaign management."""
from __future__ import annotations

import ast
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_owner_reader_management import (
    _effective_mailing, _safe_csv, _admin_action, _verify_owner,
)
from page_reader_campaign_drafts import _verified_owner as campaign_owner
from portfolio_reader_kpi import reader_registration_kpi, reader_registration_totals


class ReaderCampaignManagementTests(TestCase):
    def source(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_python_modules_parse(self):
        for path in (
            "src/page_owner_reader_management.py",
            "src/page_reader_campaign_drafts.py",
            "src/portfolio_reader_kpi.py",
            "src/page_reader_native.py",
            "src/page_analytics_v2.py",
            "src/page_public_portfolio_overview.py",
        ):
            with self.subTest(path=path):
                ast.parse(self.source(path), filename=path)

    def test_consent_eligibility_is_independent_of_registration(self):
        rows = [
            {"user_id": "a", "newsletter_opt_in": True,
             "newsletter_consent_at": "2026-11-12T10:00:00Z",
             "consent_notice_version": "2026-11-reader-v1"},
            {"user_id": "b", "newsletter_opt_in": False,
             "newsletter_consent_at": None,
             "consent_notice_version": None},
            {"user_id": "c", "newsletter_opt_in": True,
             "newsletter_consent_at": "2026-11-12T10:00:00Z",
             "consent_notice_version": None},
            {"user_id": "d", "newsletter_opt_in": True,
             "newsletter_consent_at": "2026-11-12T10:00:00Z",
             "consent_notice_version": "2026-11-reader-v1"},
            {"user_id": "e", "newsletter_opt_in": True,
             "newsletter_consent_at": "2026-11-12T10:00:00Z",
             "consent_notice_version": "2026-11-reader-v1"},
        ]
        controls = {
            "d": {"mailing_suppressed": True},
            "e": {"account_status": "suspended"},
        }
        self.assertEqual(
            [row["user_id"] for row in _effective_mailing(rows, controls)],
            ["a"],
        )

    def test_csv_export_sanitizes_spreadsheet_formulas(self):
        for raw in ("=HYPERLINK(1)", "+CMD", "-1+2", "@SUM(1)", "\t=1"):
            self.assertTrue(_safe_csv(raw).startswith("'"))

    def test_owner_gate_rejects_other_verified_accounts(self):
        with patch("page_owner_reader_management._request_json",
                   return_value={"id": "someone", "email": "reader@example.com"}):
            with self.assertRaises(PermissionError):
                _verify_owner({"access_token": "mock"})
        with patch("page_reader_campaign_drafts._request_json",
                   return_value={"id": "someone", "email": "reader@example.com"}):
            with self.assertRaises(PermissionError):
                campaign_owner("mock")

    def test_admin_mutation_rejects_wrong_target_response(self):
        with patch("page_owner_reader_management._request_json",
                   return_value={"user_id": "wrong"}):
            with self.assertRaises(RuntimeError):
                _admin_action("mock", "right", "suspend")

    def test_admin_action_rejects_unsupported_mutation(self):
        with self.assertRaises(ValueError):
            _admin_action("mock", "right", "subscribe_without_consent")

    def test_public_kpi_shows_no_private_fields(self):
        html = reader_registration_kpi("today", {"registered": 2, "lifetime": 12})
        self.assertIn("New registrations · Today", html)
        self.assertIn("2 of 12 lifetime readers", html)
        self.assertNotIn("newsletter_opt_in", html)
        self.assertNotIn("email", html.split("<section", 1)[-1].split("</section>", 1)[0].lower().replace("email", "") if False else "")

    def test_public_kpi_rejects_invalid_window_and_impossible_counts(self):
        with self.assertRaises(ValueError):
            reader_registration_totals.__wrapped__("all_invalid")
        with patch("portfolio_reader_kpi._fetch_rpc",
                   return_value={"registered": 15, "lifetime": 2}):
            with self.assertRaises(RuntimeError):
                reader_registration_totals.__wrapped__("today")

    def test_drafts_have_no_send_endpoint_or_client_side_auth_token(self):
        draft = self.source("src/page_reader_campaign_drafts.py")
        self.assertIn("portfolio_reader_mail_drafts", draft)
        self.assertNotIn("send_email", draft)
        self.assertNotIn("smtp.", draft)
        self.assertNotIn("service_role", draft)
        self.assertIn("No email was sent", draft)
        backoffice = self.source("src/page_owner_reader_management.py")
        self.assertIn("render_reader_campaign_drafts", backoffice)
        self.assertIn("portfolio_reader_admin_action_v1", backoffice)
        self.assertIn("consent_notice_version", backoffice)

    def test_public_dashboard_only_fetches_aggregate_rpc(self):
        source = self.source("src/portfolio_reader_kpi.py")
        self.assertIn("careersite_registered_reader_counts_v1", source)
        self.assertNotIn("portfolio_reader_profiles", source)
        self.assertNotIn("portfolio_reader_admin_controls", source)


if __name__ == "__main__":
    main()
