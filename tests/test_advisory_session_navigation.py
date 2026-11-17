"""Navigation regression: advisory and Reader keep one verified Streamlit session."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_reader_navigation import _ALLOWED_PAGES, _JS, _parse_portfolio_route


class AdvisorySessionNavigationTests(unittest.TestCase):
    def test_every_public_portfolio_route_is_supported(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        public = next(
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "PUBLIC_VALID"
                    for target in node.targets)
        )
        self.assertFalse(public - _ALLOWED_PAGES, public - _ALLOWED_PAGES)

    def test_member_and_public_routes_are_preserved(self):
        for route in (
            "?page=advisory-access",
            "?page=advisory-access&view=overview",
            "?page=advisory-access&view=scorecard",
            "?page=advisory-access&view=rollout",
            "?page=advisory-access&view=messages&request=00000000-0000-4000-8000-000000000001",
            "?page=advisory-market-demo",
            "?page=advisory",
            "?page=advisory-scorecard",
            "?page=advisory-rollout",
            "?page=readers",
            "?page=thinking&article=ai-governance",
            "?page=briefing&article=ai-governance&pdf=1",
            "?page=analytics&workspace=advisory",
            "?page=home",
        ):
            with self.subTest(route=route):
                self.assertIsNotNone(_parse_portfolio_route(route))

    def test_reject_secrets_unapproved_views_and_duplicate_keys(self):
        for route in (
            "?page=advisory-access&token_hash=anything",
            "?page=advisory-access&access_token=anything",
            "?page=advisory-access&refresh_token=anything",
            "?page=advisory-access&view=admin",
            "?page=advisory-access&view=messages&request=not-a-uuid",
            "?page=advisory&view=overview",
            "?page=advisory-access&workspace=cms",
            "?page=advisory-access&page=readers",
            "?page=advisory-access&signin=1&signin=0",
            "https://jairribeiro.com/?page=advisory-access",
        ):
            with self.subTest(route=route):
                self.assertIsNone(_parse_portfolio_route(route))

    def test_bridge_intercepts_approved_first_party_navigation_without_reload(self):
        self.assertIn("jairribeiro.com", _JS)
        self.assertIn("advisory.jairribeiro.com", _JS)
        self.assertIn("firstPartyRoute", _JS)
        self.assertIn("sameAppPath", _JS)
        self.assertIn("setTriggerValue('route'", _JS)
        self.assertIn("event.preventDefault()", _JS)
        self.assertIn("allowedParams.has(key)", _JS)
        self.assertNotIn("localStorage", _JS)
        self.assertNotIn("sessionStorage", _JS)

    def test_methodology_link_uses_native_routing_not_a_new_browser_tab(self):
        source = (ROOT / "src/page_advisory_rollout.py").read_text(encoding="utf-8")
        self.assertIn('key="rollout_open_methodology"', source)
        self.assertIn('st.query_params.from_dict({"page": "advisory-rollout"})', source)
        self.assertNotIn('st.page_link("https://jairribeiro.com/?page=advisory-rollout"', source)

    def test_private_advisory_still_checks_password_and_member_status(self):
        source = (ROOT / "src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn("_password_authenticated(session)", source)
        self.assertIn("_get_advisory_profile(session, user)", source)
        self.assertIn('profile.get("account_status") != "active"', source)


if __name__ == "__main__":
    unittest.main()
