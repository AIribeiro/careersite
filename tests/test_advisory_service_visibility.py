"""Advisory availability: reversible owner toggles and public CTA safety."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class AdvisoryServiceVisibilityTests(unittest.TestCase):
    def test_catalogue_and_public_page_compile(self):
        for path in (
            "src/advisory_service_visibility.py",
            "src/page_owner_advisory_services.py",
            "src/page_owner_advisory_management.py",
            "src/page_public_services.py",
            "src/page_advisory_member_experience.py",
            "src/page_advisory_client_journey.py",
            "main.py",
        ):
            with self.subTest(path=path):
                ast.parse((ROOT / path).read_text(encoding="utf-8"))

    def test_all_five_services_are_managed(self):
        from advisory_service_visibility import SERVICE_LABELS, PAGE_SERVICES
        self.assertEqual(set(SERVICE_LABELS),
                         {"requests", "decision", "rollout", "scorecard", "workshop"})
        self.assertEqual(set(PAGE_SERVICES),
                         {"advisory-decision", "advisory-rollout",
                          "advisory-scorecard", "advisory-leadership"})

    @patch("advisory_service_visibility.service_enabled", return_value=True)
    def test_enabled_cta_is_an_actual_link(self, _enabled):
        from advisory_service_visibility import public_service_cta
        html = public_service_cta(
            "rollout", "?page=advisory-rollout", "Explore rollout advisor",
            "advisory_rollout_service",
        )
        self.assertIn('href="?page=advisory-rollout"', html)
        self.assertNotIn('aria-disabled="true"', html)

    @patch("advisory_service_visibility.service_enabled", return_value=False)
    def test_paused_cta_is_not_clickable(self, _disabled):
        from advisory_service_visibility import public_service_cta
        html = public_service_cta(
            "rollout", "?page=advisory-rollout", "Explore rollout advisor",
            "advisory_rollout_service",
        )
        self.assertIn("Temporarily unavailable", html)
        self.assertIn('aria-disabled="true"', html)
        self.assertNotIn("href=", html)

    @patch("advisory_service_visibility.service_enabled", return_value=False)
    def test_disabled_detail_page_has_no_registration_link(self, _disabled):
        from advisory_service_visibility import suppress_paused_detail_ctas
        source = (
            '<a class="sc-btn" href="?page=advisory-access&amp;view=workshop" '
            'target="_self">Register free</a>'
            '<a class="sc-btn" href="?page=advisory-access&amp;view=workshop&amp;signin=1" '
            'target="_self">Already registered? Sign in</a>'
            '<a href="?page=advisory">Public Advisory</a>'
        )
        result = suppress_paused_detail_ctas(source, "advisory-leadership")
        self.assertNotIn("advisory-access", result)
        self.assertEqual(result.count("Temporarily unavailable"), 2)
        self.assertIn('href="?page=advisory"', result)

    def test_admin_uses_owner_authorized_rpc_and_audit(self):
        text = (ROOT / "src/page_owner_advisory_services.py").read_text(encoding="utf-8")
        self.assertIn("portfolio_advisory_set_service_visibility_v1", text)
        self.assertIn("portfolio_advisory_service_visibility_audit", text)
        source = (ROOT / "src/page_owner_advisory_management.py").read_text(encoding="utf-8")
        self.assertIn('"Service management"', source)


if __name__ == "__main__":
    unittest.main()
