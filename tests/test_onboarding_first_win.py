"""First-use onboarding contracts for Reader and Executive Advisory."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    data = (ROOT / path).read_text(encoding="utf-8")
    ast.parse(data, filename=path)
    return data


class FirstWinOnboardingTests(unittest.TestCase):
    def test_reader_opens_a_real_published_briefing(self):
        native = source("src/page_reader_native.py")
        self.assertIn('if articles and not saved_slugs and not unique_downloads:', native)
        self.assertIn('featured = articles[0]', native)
        self.assertIn('featured_slug = _clean_slug(str(featured.slug))', native)
        self.assertIn('key="reader_first_win_open"', native)
        self.assertIn('_open_reader_briefing(featured_slug)', native)
        self.assertIn('No further profile setup is needed.', native)

    def test_reader_pre_registration_keeps_preview_and_consent_optional(self):
        native = source("src/page_reader_native.py")
        self.assertIn('Browse a public briefing preview', native)
        self.assertIn('Editorial updates only with your consent.', native)
        self.assertIn('value=False, disabled=returning', native)

    def test_advisory_first_win_uses_existing_no_approval_service(self):
        member = source("src/page_advisory_member_experience.py")
        self.assertIn('key="overview_first_win_investment"', member)
        self.assertIn('No approval needed', member)
        self.assertIn('navigate("decision")', member)
        self.assertIn('navigate("requests")', member)
        self.assertIn('_read_workspaces(token, uid)', member)
        self.assertIn('_entitlements(token, uid)', member)
        self.assertIn('greeting = ("Welcome, " + escape(first_name)', member)

    def test_registration_and_trust_paths_remain_explicit(self):
        portal = source("src/page_advisory_portal.py")
        public = source("src/page_public_services.py")
        self.assertIn('First verify your email and set a password.', portal)
        self.assertIn('Registration does not guarantee a meeting.', portal)
        self.assertIn('No confidential information is required here.', portal)
        self.assertIn('Read professional recommendations', public)
        self.assertIn('href="?page=about"', public)
        self.assertIn('No separate service approval is required.', portal)


if __name__ == "__main__":
    unittest.main()
