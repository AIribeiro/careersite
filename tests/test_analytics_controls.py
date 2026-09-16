from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class AnalyticsControlTests(unittest.TestCase):
    def test_short_reporting_windows_and_reset_controls_exist(self) -> None:
        import page_analytics

        self.assertEqual(page_analytics.REPORTING_WINDOW_LABELS["last_hour"], "Last hour")
        self.assertEqual(page_analytics.REPORTING_WINDOW_LABELS["today"], "Today")
        self.assertEqual(page_analytics.RESET_RPC, "careersite_analytics_reset")

        hour_payload = page_analytics._dashboard_payload("token", "last_hour")
        today_payload = page_analytics._dashboard_payload("token", "today")
        month_payload = page_analytics._dashboard_payload("token", "30d")

        self.assertEqual(hour_payload["p_window"], "last_hour")
        self.assertEqual(today_payload["p_window"], "today")
        self.assertEqual(month_payload, {"p_token": "token", "p_days": 30, "p_window": "days"})

        source = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        self.assertIn("Reset permanently deletes all stored career-site analytics events", source)
        self.assertIn("Confirm reset to zero", source)
        self.assertIn("Cancel reset", source)
        self.assertIn("_reset_analytics", source)


if __name__ == "__main__":
    unittest.main()
