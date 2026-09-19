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
        self.assertIn("new zero baseline", source)
        self.assertIn("Persistent analytics reset baseline", source)
        self.assertIn("Events before this timestamp are excluded from every reporting window", source)
        self.assertIn("Confirm reset to zero", source)
        self.assertIn("Cancel reset", source)
        self.assertIn("_reset_analytics", source)
        self.assertIn("remaining_events", source)
        self.assertIn("reset_at", source)

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

    def test_admin_login_persists_until_explicit_logout(self) -> None:
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        auth = (ROOT / "src/site_admin_auth.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn("ANALYTICS_SESSION_COOKIE", dashboard)
        self.assertIn("st.context.cookies", dashboard)
        self.assertIn("Sign in once on this browser", dashboard)
        self.assertIn('st.link_button("Log out", "/_analytics/logout"', dashboard)
        self.assertNotIn('st.button("Lock"', dashboard)

        self.assertIn("careersite_analytics_issue_session", auth)
        self.assertIn("careersite_analytics_revoke_session", auth)
        self.assertIn("10 * 365 * 24 * 60 * 60", auth)

        self.assertIn('Route("/_analytics/login", _analytics_login, methods=["POST"])', app)
        self.assertIn('Route("/_analytics/logout", _analytics_logout, methods=["GET", "POST"])', app)
        self.assertIn("httponly=True", app)
        self.assertIn("secure=True", app)
        self.assertIn('samesite="strict"', app)
        self.assertIn("response.delete_cookie", app)


if __name__ == "__main__":
    unittest.main()
