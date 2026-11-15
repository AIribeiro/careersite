"""Advisory Overview premium UX and entitlement regression contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MEMBER = ROOT / "src" / "page_advisory_member_experience.py"
PORTAL = ROOT / "src" / "page_advisory_portal.py"


class AdvisoryOverviewExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MEMBER.read_text(encoding="utf-8")
        cls.portal = PORTAL.read_text(encoding="utf-8")

    def test_one_rollout_derived_visual_system(self):
        ast.parse(self.source, filename=str(MEMBER))
        self.assertEqual(self.source.count('OVERVIEW_CSS = """'), 1)
        self.assertIn("from page_rollout_workspace_ui import WORKSPACE_CSS", self.source)
        for element in (
            "Private executive decision advisory",
            "A clear view of your next AI decision.",
            "summarybar",
            "section-head",
            "advisory-overview",
            "status-panel",
            "membership-note",
        ):
            self.assertIn(element, self.source)

    def test_overview_is_focus_first_and_services_use_two_by_two_grid(self):
        start = self.source.index("def render_overview(")
        end = self.source.index("\ndef render_requests(", start)
        overview = self.source[start:end]
        self.assertLess(overview.index("Your current position"),
                        overview.index("Your advisory services"))
        self.assertIn("left, right = st.columns(2", overview)
        self.assertIn("left2, right2 = st.columns(2", overview)
        for key in (
            "overview_card_discussion", "overview_card_scorecard",
            "overview_card_rollout", "overview_card_investment",
        ):
            self.assertIn(key, overview)
        self.assertIn("OVERVIEW_SECTIONS = (\"workspaces\", \"process\", \"membership\")",
                      self.source)

    def test_service_permissions_remain_independent(self):
        start = self.source.index("def render_overview(")
        end = self.source.index("\ndef render_requests(", start)
        overview = self.source[start:end]
        for required in (
            "_load_requests(token, uid)", "_read_workspaces(token, uid)",
            "_entitlements(token, uid)", "Individual approval required",
            "Access status unavailable",
        ):
            self.assertIn(required, overview)
        self.assertNotIn("rpc/portfolio_advisory", overview)
        self.assertIn('profile.get("account_status") != "active"', self.portal)

    def test_all_native_service_actions_are_preserved(self):
        for label in (
            "Manage requests", "Open conversations", "Open Scorecard workspace",
            "Open Rollout Advisor", "Open Investment Decision Advisor",
            "Open Premium Reader Library",
        ):
            self.assertIn(label, self.source)
        for destination in ('navigate("requests")', 'navigate("messages")',
                            'navigate("scorecard")', 'navigate("rollout")',
                            'navigate("decision")'):
            self.assertIn(destination, self.source)
        self.assertIn('st.query_params["page"] = "readers"', self.source)


if __name__ == "__main__":
    unittest.main()
