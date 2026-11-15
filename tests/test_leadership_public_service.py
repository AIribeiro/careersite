"""Leadership Workshop public discovery and trust-first registration contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LeadershipPublicExperienceTests(unittest.TestCase):
    def source(self, file: str) -> str:
        return (ROOT / file).read_text(encoding="utf-8")

    def test_public_service_uses_investment_advisor_design(self):
        page = self.source("src/page_advisory_leadership_public.py")
        ast.parse(page)
        self.assertIn("SERVICE_CSS as INVESTMENT_SERVICE_CSS", page)
        self.assertIn("SCORECARD_CSS", page)
        self.assertIn("SERVICES_CSS", page)
        self.assertIn('class="scorecard-page investment-product leadership-product"', page)
        self.assertIn('class="sc-hero"', page)
        self.assertIn('class="sc-grid-2"', page)
        self.assertIn('class="sc-boundary"', page)
        self.assertIn('class="sc-actions"', page)

    def test_visitors_learn_value_method_outputs_and_trust_before_signup(self):
        from page_advisory_leadership_public import advisory_leadership
        html = advisory_leadership()
        for phrase in (
            "Executive AI Leadership Workshop.",
            "A leadership decision agenda, not another maturity badge.",
            "21 guided questions",
            "Seven dimensions",
            "Executive dilemmas",
            "downloadable two-page PDF",
            "Why this perspective?",
            "self-reported",
            "Team participants must explicitly choose to share answers",
            "No payment details",
            "fictional",
            "Privacy",
            "?page=impact",
            "?page=thinking",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), html.lower())
        self.assertLess(html.index('id="leadership-value"'),
                        html.index('id="leadership-access"'))
        self.assertIn('href="?page=advisory-access&amp;view=workshop"', html)
        self.assertIn('href="?page=advisory-access&amp;view=workshop&amp;signin=1"', html)
        self.assertNotIn("portfolio_leadership_responses?select=", html)

    def test_public_routes_and_same_session_navigation(self):
        main = self.source("main.py")
        nav = self.source("src/site_reader_navigation.py")
        service_grid = self.source("src/page_public_services.py")
        self.assertIn('PAGE == "advisory-leadership"', main)
        self.assertIn('"advisory-leadership"', main)
        self.assertIn('"advisory-leadership"', nav)
        self.assertIn('href="?page=advisory-leadership"', service_grid)
        self.assertNotIn('data-hq-event="advisory_workshop_service">Open leadership workshop', service_grid)

    def test_account_context_preserves_verification_without_generic_intake_pitch(self):
        shell = self.source("src/site_native_shell.py")
        portal = self.source("src/page_advisory_portal.py")
        ast.parse(shell)
        ast.parse(portal)
        self.assertIn('service: str = ""', shell)
        self.assertIn('if service == "workshop":', shell)
        self.assertIn('requested_service == "workshop"', portal)
        self.assertIn("21 guided questions", portal)
        self.assertIn('?page=advisory-leadership', portal)
        self.assertIn('Email my verification link', portal)
        self.assertIn('_advisory_account(session, user, profile)', portal)
        self.assertIn('render_private_leadership_workshop(session, user)', portal)
        self.assertIn('Privacy & Data notice', portal)


if __name__ == "__main__":
    unittest.main()
