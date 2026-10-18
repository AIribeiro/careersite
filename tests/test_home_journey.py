"""Home journey: evidence thresholds, routes and measurement contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class HomeJourneyTests(unittest.TestCase):
    def test_journey_facts_do_not_promote_clicks_into_arrivals(self) -> None:
        from page_home_journey import home_journey_findings
        report = {
            "home_landings": 100,
            "onward_sessions": 8,
            "last_7d_home_landings": 30,
            "last_7d_onward_sessions": 1,
            "navigation_clicks": 12,
            "confirmed_clicks": 5,
        }
        data = home_journey_findings(report)
        self.assertEqual(data["home"], 100)
        self.assertEqual(data["onward"], 8)
        self.assertEqual(data["no_destination"], 92)
        self.assertAlmostEqual(data["onward_rate"], .08)
        self.assertEqual(data["unconfirmed"], 7)
        self.assertAlmostEqual(data["click_confirm_rate"], 5 / 12)

    def test_no_denominator_is_unknown_not_zero_success(self) -> None:
        from page_home_journey import home_journey_findings
        data = home_journey_findings({})
        self.assertIsNone(data["onward_rate"])
        self.assertIsNone(data["click_confirm_rate"])

    def test_navigation_is_explicitly_observed(self) -> None:
        source = (ROOT / "src/site_analytics.py").read_text()
        self.assertIn('"navigation_click",', source)
        self.assertIn("destination !== originPage", source)
        self.assertIn("link.origin === win.location.origin", source)
        self.assertIn("win.__jairAnalyticsSend('navigation_click'", source)
        self.assertIn("a.journey-card", source)
        migration = (ROOT / "sql/20261018_home_journey_analytics_v1.sql").read_text()
        self.assertIn("'navigation_click'", migration)
        self.assertIn("public.careersite_analytics_dashboard_v2", migration)
        self.assertIn("confirmed_clicks", migration)

    def test_contextual_paths_from_content_pages(self) -> None:
        for source, marker in (
            ("src/page_impact.py", 'journey_next("impact")'),
            ("src/page_ai_data_governance.py", 'journey_next("governance")'),
            ("src/thinking_landing.py", 'journey_next("thinking")'),
            ("src/site_cms.py", 'journey_next("article")'),
            ("src/page_thinking.py", "journey_next('article')"),
        ):
            self.assertIn(marker, (ROOT / source).read_text(), source)

    def test_modified_python_files_parse(self) -> None:
        for source in (
            "src/page_home.py", "src/site_components.py",
            "src/page_impact.py", "src/page_ai_data_governance.py",
            "src/page_thinking.py", "src/thinking_landing.py",
            "src/site_cms.py", "src/site_styles.py",
            "src/site_analytics.py", "src/page_home_journey.py",
            "src/page_public_portfolio_overview.py",
        ):
            with self.subTest(source=source):
                ast.parse((ROOT / source).read_text(), filename=source)


if __name__ == "__main__":
    unittest.main()
