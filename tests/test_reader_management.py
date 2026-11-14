"""Reader Management and aggregate registration KPI regressions."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio_reader_kpi import reader_registration_kpi
from page_owner_reader_management import (
    _effective_mailing, _csv_bytes, _admin_action, _verify_owner,
)


class ReaderManagementTests(unittest.TestCase):
    def source(self, p):
        return (ROOT / p).read_text(encoding="utf-8")

    def test_public_kpi_respects_period_and_lifetime(self):
        html = reader_registration_kpi("today", {"registered": 2, "lifetime": 12})
        self.assertIn("Registered Readers", html)
        self.assertIn("New registrations · Today", html)
        self.assertIn("2 of 12 lifetime readers", html)
        self.assertNotIn("john@example.com", html)
        self.assertIn("Verified membership", html)
        all_html = reader_registration_kpi("all", {"registered": 12, "lifetime": 12})
        self.assertIn("New registrations · All", all_html)
        unavailable = reader_registration_kpi("today", None)
        self.assertIn("Registration service temporarily unavailable", unavailable)
        self.assertNotIn(">0</strong>", unavailable)

    def test_public_dashboard_uses_same_filter_and_refresh(self):
        src = self.source("src/page_public_portfolio_overview.py")
        self.assertIn('reader_registration_totals(str(window))', src)
        self.assertIn('reader_registration_kpi(str(window), reader_counts)', src)
        self.assertIn('reader_registration_totals.clear()', src)
        self.assertIn('st.html(portfolio_metric_grid(cards))', src)
        kpi = self.source("src/portfolio_reader_kpi.py")
        self.assertIn('"careersite_registered_reader_counts_v1"', kpi)
        self.assertIn('"p_window": window', kpi)
        self.assertNotIn("portfolio_reader_profiles?select", kpi)

    def test_mailing_eligibility_requires_explicit_optin_timestamp(self):
        readers = [
            {"user_id": "a", "email": "eligible@example.com",
             "newsletter_opt_in": True, "newsletter_consent_at": "2026-11-12",
             "consent_notice_version": "2026-11-reader-v1"},
            {"user_id": "b", "email": "no-consent@example.com",
             "newsletter_opt_in": False, "newsletter_consent_at": None},
            {"user_id": "c", "email": "suppressed@example.com",
             "newsletter_opt_in": True, "newsletter_consent_at": "2026-11-12",
             "consent_notice_version": "2026-11-reader-v1"},
            {"user_id": "d", "email": "suspended@example.com",
             "newsletter_opt_in": True, "newsletter_consent_at": "2026-11-12",
             "consent_notice_version": "2026-11-reader-v1"},
            {"user_id": "e", "email": "no-timestamp@example.com",
             "newsletter_opt_in": True, "newsletter_consent_at": None},
        ]
        controls = {
            "c": {"mailing_suppressed": True},
            "d": {"account_status": "suspended"},
        }
        self.assertEqual([p["user_id"] for p in _effective_mailing(readers, controls)], ["a"])

    def test_mailing_csv_sanitizes_formula_inputs(self):
        output = _csv_bytes(
            ["First name", "Email"],
            [["=SUM(1,2)", "john@example.com"],
             ["+calc", "@attack"]],
        ).decode("utf-8-sig")
        self.assertIn("'=SUM(1,2)", output)
        self.assertIn("'+calc", output)
        self.assertIn("'@attack", output)

    def test_live_owner_validation_rejects_nonowner(self):
        with patch("page_owner_reader_management._request_json",
                   return_value={"email": "visitor@example.com"}):
            with self.assertRaises(PermissionError):
                _verify_owner({"access_token": "a-valid-looking-token"})
        with patch("page_owner_reader_management._request_json",
                   return_value={"email": "jair.ribeiro@outlook.it"}):
            self.assertEqual(_verify_owner({"access_token": "safe"}), "safe")

    def test_admin_mutations_call_atomic_audited_rpc_only(self):
        with patch("page_owner_reader_management._request_json",
                   return_value={"account_status": "suspended",
                                 "user_id": "00000000-0000-0000-0000-000000000002"}) as request:
            _admin_action("owner-token", "00000000-0000-0000-0000-000000000002",
                          "suspend")
            self.assertIn("rpc/portfolio_reader_admin_action_v1",
                          request.call_args.args[1])
            self.assertEqual(
                request.call_args.kwargs["payload"]["p_action"], "suspend")
            self.assertEqual(
                request.call_args.kwargs["token"], "owner-token")
        with self.assertRaises(ValueError):
            _admin_action("owner-token", "id", "newsletter_opt_in")

    def test_private_workspace_cannot_be_opened_by_anonymous_visitor(self):
        src = self.source("src/page_analytics_v2.py")
        self.assertIn('"readers": "Reader Management"', src)
        self.assertIn('if workspace == "readers":', src)
        self.assertIn("render_owner_reader_management(owner)", src)
        self.assertIn('value in ("private", "cms", "linkedin", "readers", "advisory")', src)
        self.assertIn('return value if authenticated and value in', src)
        self.assertIn('else "public"', src)
        backoffice = self.source("src/page_owner_reader_management.py")
        self.assertIn('_verify_owner(session)', backoffice)
        self.assertIn('Consent timestamp', backoffice)
        self.assertIn('account_status', backoffice)
        self.assertIn('mailing_suppressed', backoffice)
        self.assertIn('portfolio_reader_admin_action_v1', backoffice)
        self.assertNotIn("service_role", backoffice)
        self.assertNotIn("smtp", backoffice.lower())

    def test_suspended_reader_cannot_reach_complete_briefing(self):
        src = self.source("src/page_reader_native.py")
        self.assertIn("rpc/portfolio_reader_member_status_v1", src)
        self.assertIn('if status != "active":', src)
        self.assertIn('st.session_state.pop("reader_native_session", None)', src)
        self.assertIn("from page_reader_native import _session",
                      self.source("src/site_cms.py"))


if __name__ == "__main__":
    unittest.main()
