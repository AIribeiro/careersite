"""Regression contracts for internal QA and browser-automation filtering.

These tests intentionally avoid IP-based identity or a persistent visitor fingerprint.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TrafficQualityTests(unittest.TestCase):
    def test_production_smoke_is_tagged_on_every_navigation(self):
        workflow = (ROOT / ".github/workflows/p0-production-health.yml").read_text(encoding="utf-8")
        self.assertIn("source=internal_qa&role=smoke", workflow)
        self.assertIn("page.goto(qa_url(os.environ", workflow)
        self.assertIn("page.goto(qa_url(base + query)", workflow)
        self.assertIn("page.goto(qa_url(base + \"?page=briefing", workflow)
        self.assertIn("page.goto(qa_url(base)", workflow)

    def test_browser_collector_emits_only_coarse_automation_signal(self):
        client = (ROOT / "src/site_analytics.py").read_text(encoding="utf-8")
        self.assertIn("browser_automation: Boolean(win.navigator && win.navigator.webdriver === true)", client)
        self.assertNotIn("user_agent: nav.userAgent", client)
        self.assertNotIn("ip_address:", client)

    def test_raw_telemetry_is_retained_and_filtered_reports_are_read_only(self):
        folder = ROOT / "supabase/migrations"
        source = (folder / "20261113130548_separate_internal_qa_from_portfolio_reporting.sql").read_text(encoding="utf-8")
        signals = (folder / "20261113130748_exclude_high_confidence_browser_automation.sql").read_text(encoding="utf-8")
        audit = (folder / "20261113130943_traffic_quality_audit_rpc.sql").read_text(encoding="utf-8")

        self.assertIn("security_invoker=true", source)
        self.assertIn("careersite_reporting_events_v1", source)
        self.assertIn("careersite_internal_qa_sessions_v1", source)
        self.assertIn("careersite_suspected_automation_sessions_v1", signals)
        self.assertIn("NOT coalesce(e.browser_automation,false)", signals)
        self.assertIn("ENABLE ROW LEVEL SECURITY", source)
        self.assertIn("ENABLE ROW LEVEL SECURITY", signals)
        self.assertNotIn("DELETE FROM", source.upper() + signals.upper() + audit.upper())
        self.assertIn("unclassified_sessions", audit)
        self.assertIn("internal_qa_sessions", audit)
        self.assertIn("suspected_automation_sessions", audit)

    def test_owner_analytics_explains_funnel_and_traffic_quality(self):
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        self.assertIn('TRAFFIC_QUALITY_RPC = "careersite_traffic_quality_audit_v1"', dashboard)
        self.assertIn("Traffic integrity", dashboard)
        self.assertIn("Internal QA excluded", dashboard)
        self.assertIn("Suspected automation excluded", dashboard)
        self.assertIn("Unclassified sessions", dashboard)
        self.assertIn("not verified human visitors", dashboard)


if __name__ == "__main__":
    unittest.main()
