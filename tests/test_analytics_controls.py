from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class AnalyticsControlTests(unittest.TestCase):
    def test_short_reporting_windows_are_public_and_read_only(self) -> None:
        import page_analytics

        self.assertEqual(page_analytics.REPORTING_WINDOW_LABELS["last_hour"], "Last hour")
        self.assertEqual(page_analytics.REPORTING_WINDOW_LABELS["today"], "Today")
        source = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        self.assertIn("index=0", source)

        hour_payload = page_analytics._dashboard_payload("last_hour")
        today_payload = page_analytics._dashboard_payload("today")
        month_payload = page_analytics._dashboard_payload("30d")

        self.assertEqual(hour_payload["p_window"], "last_hour")
        self.assertEqual(today_payload["p_window"], "today")
        self.assertEqual(
            month_payload,
            {
                "p_token": page_analytics.PUBLIC_DASHBOARD_TOKEN,
                "p_days": 30,
                "p_window": "days",
            },
        )

        source = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        self.assertNotIn("Access code", source)
        self.assertNotIn("Open analytics", source)
        self.assertNotIn("Log out", source)
        self.assertNotIn("Reset analytics to a new zero baseline", source)
        self.assertNotIn("_reset_analytics", source)
        self.assertNotIn("site_admin_auth", source)
        self.assertNotIn("site_admin_store", source)

    def test_extended_first_party_metrics_are_present(self) -> None:
        client = (ROOT / "src/site_analytics.py").read_text(encoding="utf-8")
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")

        for token in (
            "engagement_ping",
            "device_type",
            "browser_family",
            "os_family",
            "language",
            "timezone",
            "viewport_width",
            "screen_width",
            "connection_type",
            "session_elapsed_ms",
            "engaged_ms",
        ):
            self.assertIn(token, client)

        for label in (
            "Career site intelligence",
            "Session trend",
            "Depth of exploration",
            "Device mix",
            "Operating systems",
            "Country",
            "Browser language",
            "Job-search sources",
            "Active time distribution",
            "Sessions by hour",
            "Sessions by weekday",
        ):
            self.assertIn(label, dashboard)

        self.assertIn("No raw IP addresses", dashboard)
        self.assertIn("Duration unconfirmed", dashboard)
        self.assertIn("median_active_seconds", dashboard)
        self.assertIn("avg_active_seconds", dashboard)
        self.assertIn('DASHBOARD_RPC = "careersite_analytics_dashboard_v2"', dashboard)
        self.assertIn("FIRST_HEARTBEAT_MS = 5000", client)
        self.assertIn("HEARTBEAT_MS = 10000", client)
        self.assertIn("SESSION_TIMEOUT_MS = 30 * 60 * 1000", client)
        self.assertIn("jair_hq_last_active_v3", client)
        self.assertIn("st.vega_lite_chart", dashboard)
        self.assertNotIn("st.dataframe", dashboard)
        self.assertNotIn("localStorage", client)

    def test_duration_format_never_labels_positive_subsecond_time_as_zero(self) -> None:
        import page_analytics

        self.assertEqual(page_analytics._seconds(0), "—")
        self.assertEqual(page_analytics._seconds(0.03), "<1s")
        self.assertEqual(page_analytics._seconds(0.9), "<1s")
        self.assertEqual(page_analytics._seconds(1.1), "1s")

    def test_dashboard_has_no_user_authentication_gate(self) -> None:
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        wrapper = (ROOT / "src/page_analytics_v2.py").read_text(encoding="utf-8")
        article = (ROOT / "src/page_article_analytics.py").read_text(encoding="utf-8")

        self.assertIn('PUBLIC_DASHBOARD_TOKEN = "public-readonly-v1"', dashboard)
        self.assertNotIn("careersite_analytics_access_code", dashboard)
        self.assertNotIn("careersite_analytics_reset_pending", dashboard)
        self.assertNotIn("Access code", dashboard)
        self.assertNotIn("access_code", article)
        self.assertNotIn("careersite_analytics_access_code", wrapper)
        self.assertIn("render_article_analytics()", wrapper)



if __name__ == "__main__":
    unittest.main()
