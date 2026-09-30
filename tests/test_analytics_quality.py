from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnalyticsQualityContractTests(unittest.TestCase):
    def test_quality_rpc_is_versioned_and_wired_into_dashboard(self) -> None:
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")
        sql = (ROOT / "sql/analytics_hiring_intelligence_v1.sql").read_text(encoding="utf-8")

        self.assertIn('HIRING_INTELLIGENCE_RPC = "careersite_hiring_intelligence_v1"', dashboard)
        self.assertIn("Quality & intent", dashboard)
        self.assertIn("Analysis-eligible", dashboard)
        self.assertIn("Evidence progression", dashboard)
        self.assertIn("Qualified parent channels", dashboard)

        self.assertIn("careersite_hiring_intelligence_v1", sql)
        self.assertIn("tracking_version", sql)
        self.assertIn("suspected_automation", sql)
        self.assertIn("analysis_eligible", sql)
        self.assertIn("evidence_verified", sql)
        self.assertIn("hiring_intent", sql)
        self.assertIn("normalized_channel", sql)
        self.assertNotIn("DELETE FROM PUBLIC.CAREERSITE_ANALYTICS_EVENTS", sql.upper())

    def test_session_rollover_can_emit_a_new_page_view(self) -> None:
        client = (ROOT / "src/site_analytics.py").read_text(encoding="utf-8")

        self.assertIn("win.__jairAnalyticsLastDocumentView = null;", client)
        self.assertIn("if (reset && win.__jairAnalyticsRecordCurrentView)", client)
        self.assertIn("win.__jairAnalyticsSend(\'page_view\')", client)

    def test_repeated_browser_errors_are_deduplicated(self) -> None:
        telemetry = (ROOT / "src/site_behavior_telemetry_v2.py").read_text(encoding="utf-8")

        self.assertIn("error:${state.signature}:js_error:", telemetry)
        self.assertIn("error:${state.signature}:promise_rejection:", telemetry)
        self.assertIn("if (state.signalKeys.has(signalKey)) return;", telemetry)
        self.assertIn("state.signalKeys.add(signalKey);", telemetry)

    def test_linkedin_sources_are_normalized_but_campaign_detail_is_retained(self) -> None:
        sql = (ROOT / "sql/analytics_hiring_intelligence_v1.sql").read_text(encoding="utf-8")

        self.assertIn("LIKE \'linkedin%\'", sql)
        self.assertIn("THEN \'LinkedIn\'", sql)
        self.assertIn("source_raw", sql)
        self.assertIn("campaign_raw", sql)


if __name__ == "__main__":
    unittest.main()
