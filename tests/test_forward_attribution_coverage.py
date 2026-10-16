"""Forward-only UTM medium capture, owner-only attribution quality reporting."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class MediumTelemetryTests(unittest.TestCase):
    def test_both_browser_trackers_capture_store_and_send_utm_medium(self):
        for path in ("site_analytics.py", "site_article_analytics.py"):
            with self.subTest(path=path):
                source = (ROOT / "src" / path).read_text()
                self.assertIn("params.get('utm_medium')", source)
                self.assertIn("utm_medium: incomingMedium || attribution.utm_medium", source)
                self.assertIn("utm_medium: attribution.utm_medium || null", source)
                self.assertIn("utm_medium: null", source)
                self.assertIn("slice(0, 32)", source)

    def test_generated_links_populate_existing_utm_medium(self):
        from site_campaign_links import make_distribution_link
        from urllib.parse import urlsplit, parse_qs

        for channel, expected in (
            ("linkedin", "social"), ("threads", "social"),
            ("whatsapp", "messaging"), ("email", "email"),
            ("cv", "document"), ("outreach", "outreach"),
        ):
            url = make_distribution_link(
                "https://jairribeiro-ai.streamlit.app/?page=thinking",
                channel=channel, campaign="thinking",
            )
            params = parse_qs(urlsplit(url).query)
            self.assertEqual(params["utm_medium"], [expected])


class AttributionMonitoringTests(unittest.TestCase):
    def test_report_only_uses_authenticated_owner_session(self):
        import page_attribution_coverage as module
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps({
            "overview": {"sessions": 0},
            "monitoring_started_at": "2026-10-16T18:00:00Z",
            "daily": [],
        }).encode()
        with patch.object(module, "owner_rpc_headers", return_value={
            "Authorization": "Bearer verified-owner-jwt",
            "apikey": "public-test-key",
        }) as authorized, patch.object(module.request, "urlopen",
                                      return_value=response) as opened:
            result = module.fetch_attribution_coverage(30)
            self.assertEqual(result["overview"]["sessions"], 0)
            authorized.assert_called_once()
            actual_request = opened.call_args.args[0]
            self.assertEqual(actual_request.headers["Authorization"],
                             "Bearer verified-owner-jwt")
            self.assertIn("careersite_attribution_coverage_v1",
                          actual_request.full_url)
        with self.assertRaises(ValueError):
            module.fetch_attribution_coverage(999)

    def test_dashboard_handles_zero_events_after_activation(self):
        from streamlit.testing.v1 import AppTest
        payload = {
            "monitoring_started_at": "2026-10-16T18:12:00Z",
            "overview": {
                "sessions": 0, "tagged": 0, "referrer_only": 0,
                "unknown": 0, "identifiable_pct": None,
            },
            "daily": [],
        }
        with patch("page_attribution_coverage.fetch_attribution_coverage",
                   return_value=payload):
            at = AppTest.from_string(
                "from page_attribution_coverage import render_attribution_coverage\n"
                "render_attribution_coverage()\n"
            ).run(timeout=20)
        self.assertFalse(at.exception)
        self.assertTrue(any("No eligible new content sessions" in x.value
                            for x in at.info))

    def test_content_session_counters_and_medium_reconciliation(self):
        from streamlit.testing.v1 import AppTest
        payload = {
            "monitoring_started_at": "2026-10-16T18:12:00Z",
            "overview": {
                "sessions": 5, "tagged": 3, "referrer_only": 1,
                "unknown": 1, "identifiable_pct": 80.0,
                "tagged_with_medium_pct": 66.7,
                "tagged_with_campaign_pct": 100.0,
                "medium_count": 2, "campaign_count": 3,
                "source_conflicts": 0,
            },
            "daily": [
                {"day": "2026-10-16", "sessions": 5, "tagged": 3,
                 "referrer_only": 1, "unknown": 1, "identifiable_pct": 80.0},
            ],
            "sources": [{"source": "linkedin", "sessions": 3}],
        }
        with patch("page_attribution_coverage.fetch_attribution_coverage",
                   return_value=payload):
            at = AppTest.from_string(
                "from page_attribution_coverage import render_attribution_coverage\n"
                "render_attribution_coverage()\n"
            ).run(timeout=20)
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric), 5)
        self.assertEqual(at.metric[0].value, "80.0%")
        self.assertEqual(at.metric[3].value, "66.7%")

    def test_owner_navigation_and_schema_migration_are_private(self):
        from page_admin import _PRIVATE_VIEW_ROUTES
        from page_analytics_v2 import _resolve_workspace
        self.assertEqual(_PRIVATE_VIEW_ROUTES["attribution"], "Attribution quality")
        self.assertEqual(_resolve_workspace("private", False), "public")
        sql = (ROOT / "supabase/migrations/"
               "20261016_forward_attribution_medium_and_coverage.sql").read_text()
        for expected in (
            "ADD COLUMN IF NOT EXISTS utm_medium",
            "careersite_attribution_coverage_epoch",
            "SECURITY DEFINER",
            "auth.uid()",
            "REVOKE EXECUTE",
            "FROM PUBLIC, anon",
            "GROUP BY e.session_id",
            "utm_medium",
        ):
            self.assertIn(expected, sql)
        self.assertNotIn("UPDATE public.careersite_analytics_events", sql)


if __name__ == "__main__":
    unittest.main()
