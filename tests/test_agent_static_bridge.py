"""Static GitHub Pages discovery mirror: public-only and stable canonical links."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agent_discovery import public_catalogue
from scripts.build_agent_discovery_static import (
    DEFAULT_SHARE_BASE,
    write_static_discovery,
)


class StaticAgentBridgeTests(unittest.TestCase):
    def _items(self):
        published = (
            SimpleNamespace(
                slug="how-to-govern-portfolio-decisions",
                title="How to Govern Portfolio Decisions",
                kind="Executive Briefing",
                category="AI Governance",
                published_at="2026-11-13T10:00:00Z",
                status="published",
                excerpt="Public executive summary.",
                content_html="NEVER_DISTRIBUTE_PREMIUM_BODY",
            ),
            SimpleNamespace(
                slug="draft-not-public",
                title="Not Published",
                kind="Executive Briefing",
                category="AI Governance",
                published_at="2026-11-13T10:00:00Z",
                status="draft",
                excerpt="DRAFT_MUST_BE_HIDDEN",
                content_html="NEVER_DISTRIBUTE_DRAFT_BODY",
            ),
        )
        return public_catalogue(published, catalogue_status="complete")

    def test_static_public_mirror_contains_only_summaries_and_branded_canonical_urls(self):
        with TemporaryDirectory() as location:
            directory = Path(location)
            catalogue = write_static_discovery(directory, self._items(), DEFAULT_SHARE_BASE)
            self.assertEqual(catalogue["count"], 1)
            self.assertEqual(catalogue["content_policy"], "summary_only")
            self.assertTrue(catalogue["generated_at"])
            self.assertEqual(
                catalogue["content"][0]["url"],
                "https://jairribeiro.com/?page=briefing&article=how-to-govern-portfolio-decisions",
            )
            self.assertEqual(
                catalogue["content"][0]["markdown_url"],
                DEFAULT_SHARE_BASE + "/agent/content/how-to-govern-portfolio-decisions.md",
            )
            self.assertNotIn("DRAFT_MUST_BE_HIDDEN", json.dumps(catalogue))
            summary = (directory / "agent/content/how-to-govern-portfolio-decisions.md").read_text()
            self.assertIn("Public executive summary.", summary)
            self.assertNotIn("NEVER_DISTRIBUTE_PREMIUM_BODY", summary)
            self.assertNotIn("Full public edition", summary)
            self.assertIn(DEFAULT_SHARE_BASE + "/agent/catalog.json",
                          (directory / "llms.txt").read_text())
            self.assertIn(DEFAULT_SHARE_BASE + "/agent/catalog.json",
                          (directory / "agents.md").read_text())

    def test_rejects_partial_or_unapproved_publish_locations(self):
        with TemporaryDirectory() as location:
            catalogue = self._items()
            catalogue["catalogue_status"] = "partial"
            with self.assertRaises(RuntimeError):
                write_static_discovery(Path(location), catalogue, DEFAULT_SHARE_BASE)
            catalogue["catalogue_status"] = "complete"
            with self.assertRaises(ValueError):
                write_static_discovery(Path(location), catalogue, "https://example.org/careersite")
            with self.assertRaises(ValueError):
                write_static_discovery(Path(location), catalogue, "http://airibeiro.github.io/careersite")


if __name__ == "__main__":
    unittest.main()
