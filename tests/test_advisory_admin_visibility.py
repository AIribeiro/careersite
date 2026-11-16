"""Role-aware Advisory service visibility and owner-managed admin permissions."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class AdvisoryAdminVisibilityTests(unittest.TestCase):
    def test_new_modules_compile(self):
        for rel in (
            "src/advisory_service_visibility.py",
            "src/page_owner_advisory_roles.py",
            "src/page_owner_advisory_services.py",
            "src/page_owner_advisory_management.py",
            "src/page_advisory_member_experience.py",
            "src/page_advisory_portal.py",
            "src/page_public_services.py",
            "src/page_advisory_scorecard_workspace.py",
            "src/page_advisory_rollout.py",
            "main.py",
        ):
            with self.subTest(file=rel):
                ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)

    def test_status_means_hidden_for_regular_and_available_for_admin(self):
        from advisory_service_visibility import service_enabled
        with patch(
            "advisory_service_visibility.service_visibility",
            return_value={
                "requests": True, "decision": True, "scorecard": False,
                "rollout": False, "workshop": False,
            },
        ):
            self.assertFalse(service_enabled("scorecard"))
            self.assertTrue(service_enabled("scorecard", admin=True))
            self.assertFalse(service_enabled("workshop"))
            self.assertTrue(service_enabled("workshop", admin=True))
            self.assertFalse(service_enabled("missing", admin=True))

    def test_public_cards_are_truly_hidden_not_disabled_ghosts(self):
        from page_public_services import advisory
        visibility = {
            "requests": True,
            "decision": True,
            "rollout": False,
            "scorecard": False,
            "workshop": False,
        }
        with (
            patch("page_public_services.viewer_is_admin", return_value=False),
            patch("advisory_service_visibility.service_visibility", return_value=visibility),
        ):
            html = advisory()
        self.assertIn('data-analytics-section="advisory-decision"', html)
        self.assertNotIn('data-analytics-section="advisory-rollout"', html)
        self.assertNotIn('data-analytics-section="advisory-scorecard"', html)
        self.assertNotIn('data-analytics-section="advisory-leadership-workshop"', html)
        self.assertIn("01 / Available now", html)
        self.assertNotIn("Temporarily unavailable</span>", html)

    def test_admin_still_gets_all_cards_and_clickable_ctas(self):
        from page_public_services import advisory
        visibility = {k: False for k in ("requests", "decision", "rollout", "scorecard", "workshop", "renewal")}
        with (
            patch("page_public_services.viewer_is_admin", return_value=True),
            patch("advisory_service_visibility.service_visibility", return_value=visibility),
        ):
            html = advisory()
        for target in (
            'href="?page=advisory-decision"',
            'href="?page=advisory-rollout"',
            'href="?page=advisory-scorecard"',
            'href="?page=advisory-leadership"',
            'href="?page=advisory-renewal"',
            'href="?page=advisory-market-signals"',
        ):
            self.assertIn(target, html)
        self.assertIn("06 / Available now", html)

    def test_verified_admin_rpc_and_owner_controlled_role_writer(self):
        role_source = (ROOT / "src/advisory_service_visibility.py").read_text(encoding="utf-8")
        owner_source = (ROOT / "src/page_owner_advisory_roles.py").read_text(encoding="utf-8")
        self.assertIn("rpc/portfolio_advisory_my_role_v1", role_source)
        self.assertIn("_password_authenticated(session)", role_source)
        self.assertIn("rpc/portfolio_advisory_set_user_role_v1", owner_source)
        self.assertIn("Role change history", owner_source)
        workspace = (ROOT / "src/page_owner_advisory_management.py").read_text(encoding="utf-8")
        self.assertIn('"User roles"', workspace)

    def test_member_navigation_omits_paused_services(self):
        member = (ROOT / "src/page_advisory_member_experience.py").read_text(encoding="utf-8")
        self.assertIn('service_enabled(v, admin=admin)', member)
        self.assertIn("if requested not in displayed", member)
        self.assertIn('if service_enabled("decision", admin=admin)', member)
        self.assertNotIn('service_enabled("investment", admin=admin)', member)

    def test_admin_can_activate_private_workspaces(self):
        for rel in (
            "src/page_advisory_scorecard_workspace.py",
            "src/page_advisory_rollout.py",
        ):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("portfolio_advisory_admin_ensure_workspace_v1", text)


if __name__ == "__main__":
    unittest.main()
