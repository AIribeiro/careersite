"""The browser privacy contract is exercised in test_privacy_controls."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserCollectorTests(unittest.TestCase):
    def test_collector_is_opt_in_only_and_minimal(self):
        source = (ROOT / "src" / "site_analytics.py").read_text(encoding="utf-8")
        self.assertIn("CONSENT_GATE_JS", source)
        self.assertIn("jair_statistics_choice_v1", source)
        self.assertIn("if (choice() !== 'yes')", source)
        self.assertIn("if (choice() !== 'yes' || !allowed.has(eventName))", source)
        self.assertIn("data-stats-choice", source)
        self.assertIn("tracking_version: 6", source)
        for event in ("section_attention", "cta_hesitation", "ux_signal",
                      "performance_metric", "engagement_ping"):
            taxonomy = source.split("ALLOWED_EVENTS = (", 1)[1].split(")", 1)[0]
            self.assertNotIn('"' + event + '"', taxonomy)


if __name__ == "__main__":
    unittest.main()
