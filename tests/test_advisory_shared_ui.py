"""Cross-service Advisory UX contract: consistent shell, differentiated access."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(file: str) -> str:
    return (ROOT / file).read_text(encoding="utf-8")


class SharedAdvisoryExperienceTests(unittest.TestCase):
    def test_shared_component_and_all_services_are_valid_python(self):
        for path in (
            "src/page_advisory_shared_ui.py",
            "src/page_rollout_workspace_ui.py",
            "src/page_advisory_rollout.py",
            "src/page_advisory_scorecard_experience.py",
            "src/page_advisory_investment.py",
        ):
            with self.subTest(path=path):
                ast.parse(source(path), filename=path)

    def test_rollout_remains_design_reference(self):
        rollout = source("src/page_rollout_workspace_ui.py")
        self.assertIn("WORKSPACE_CSS", rollout)
        for element in ("summarybar", "three-col", "steps", "hero", "verdict"):
            self.assertIn(element, rollout)
        common = source("src/page_advisory_shared_ui.py")
        self.assertIn("from page_rollout_workspace_ui import WORKSPACE_CSS", common)
        self.assertIn("def service_overview(", common)
        self.assertIn("def case_header(", common)

    def test_investment_has_same_main_and_report_navigation_as_rollout(self):
        rollout = source("src/page_advisory_rollout.py")
        investment = source("src/page_advisory_investment.py")
        for section in ("overview", "assess", "decision", "history"):
            self.assertIn('"' + section + '"', rollout)
            self.assertIn('"' + section + '"', investment)
        for detail in ("verdict", "actions", "evidence"):
            self.assertIn('"' + detail + '"', rollout)
            self.assertIn('"' + detail + '"', investment)
        for title in ("About this service", "New assessment", "Decision brief",
                      "My history", "Executive actions", "Evidence & report"):
            self.assertIn(title, investment)
        self.assertIn("service_overview(", investment)
        self.assertIn("case_header(", investment)
        self.assertIn("WORKSPACE_CSS + PRIVATE_CSS", investment)
        self.assertIn("_report_nav()", investment)

    def test_scorecard_reuses_core_shell_and_preserves_specialized_tools(self):
        scorecard = source("src/page_advisory_scorecard_experience.py")
        for title in ("About this service", "Decision brief", "My history",
                      "Verdict & portfolio", "Executive actions", "Evidence & report",
                      "Portfolio options", "Decision record", "Assessment criteria"):
            self.assertIn(title, scorecard)
        self.assertIn("WORKSPACE_CSS + CSS", scorecard)
        self.assertIn("service_overview(", scorecard)
        self.assertIn("case_header(", scorecard)
        self.assertIn("st.pills(", scorecard)
        self.assertNotIn("section=st.selectbox(", scorecard)
        self.assertIn("render_new_analysis_request(token,uid,anchor)", scorecard)
        self.assertIn("Approved analyses", scorecard)

    def test_access_rules_are_not_conflated(self):
        rollout = source("src/page_advisory_rollout.py")
        scorecard = source("src/page_advisory_scorecard_workspace.py")
        investment = source("src/page_advisory_investment.py")
        self.assertIn("_entitlements(token,uid)", rollout)
        self.assertIn("if not access:", rollout)
        self.assertIn("_read_workspaces(token,uid)", scorecard)
        self.assertIn("if not workspaces:", scorecard)
        self.assertIn("_history(token, uid)", investment)
        self.assertNotIn("_entitlements(token,uid)", investment)


if __name__ == "__main__":
    unittest.main()
