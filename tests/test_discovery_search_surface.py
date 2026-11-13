"""AI discovery publishing: only public metadata is indexed or notified."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.discovery_search_surface import PAGES_BASE, write_search_surface
from scripts.indexnow_discovery import BASE, create_key_file, diff, notify


class SearchDiscoveryTests(TestCase):
    def catalogue(self):
        return {
            "catalogue_status": "complete",
            "count": 2,
            "content": [
                {
                    "slug": "permitted-ai-use",
                    "title": "From Governed Data to Permitted AI Use",
                    "summary": 'How executives decide what AI may use; review <risk>. & "controls"',
                    "type": "executive_briefing",
                    "topic": "Governance",
                    "access": "premium",
                    "published": "2026-11-13",
                    "url": "https://jairribeiro.com/?page=briefing&article=permitted-ai-use",
                    "content_html": "<p>PRIVATE_PREMIUM_COPY</p>",
                    "aside_html": "PRIVATE_ASIDE",
                },
                {
                    "slug": "public-perspective",
                    "title": "Public Perspective",
                    "summary": "Public summary, not complete article",
                    "type": "article",
                    "topic": "Enterprise AI",
                    "access": "open",
                    "published": "2026-10-15",
                    "url": "https://jairribeiro.com/?page=thinking&article=public-perspective",
                    "content_html": "PRIVATE_UNEXPORTED_FULL_BODY",
                },
            ],
        }

    def test_crawlable_index_feed_sitemap_and_crawler_rules_never_export_private_bodies(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            r = write_search_surface(root, self.catalogue(), PAGES_BASE)
            self.assertEqual(r["count"], 2)
            self.assertEqual(len(r["manifest"]), 2)
            files = [
                root / "discover/index.html",
                root / "discover/permitted-ai-use/index.html",
                root / "discover/public-perspective/index.html",
                root / "sitemap.xml",
                root / "feed.xml",
                root / "robots.txt",
                root / "agent/publication-state.json",
            ]
            for file in files:
                self.assertTrue(file.is_file(), str(file))
            body = "".join(f.read_text(encoding="utf-8") for f in files)
            self.assertNotIn("PRIVATE_PREMIUM_COPY", body)
            self.assertNotIn("PRIVATE_UNEXPORTED_FULL_BODY", body)
            self.assertNotIn("PRIVATE_ASIDE", body)
            self.assertIn("OAI-SearchBot", body)
            self.assertIn("https://ai.jairribeiro.com/sitemap.xml", body)
            self.assertIn("https://airibeiro.github.io/careersite/discover/permitted-ai-use/", body)
            self.assertIn("&lt;risk&gt;", body)
            self.assertNotIn("<risk>", body)
            self.assertIn("Registration is required", body)
            self.assertIn('rel="canonical"', body)
            self.assertIn('"@type":"Article"', body)
            self.assertNotIn("/go/", (root / "sitemap.xml").read_text())

    def test_disallow_partial_catalogue_and_incorrect_host(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                write_search_surface(Path(td), self.catalogue(), "https://example.com")
            partial = self.catalogue()
            partial["catalogue_status"] = "partial"
            with self.assertRaises(RuntimeError):
                write_search_surface(Path(td), partial, PAGES_BASE)

    def test_manifest_detects_metadata_edits_not_draft_bodies(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            first = write_search_surface(root, self.catalogue(), PAGES_BASE)["manifest"]
            changed = self.catalogue()
            changed["content"][0]["content_html"] = "ANOTHER_PRIVATE_BODY"
            second = write_search_surface(root, changed, PAGES_BASE)["manifest"]
            self.assertEqual(first, second)
            changed["content"][0]["summary"] = "Updated public description"
            third = write_search_surface(root, changed, PAGES_BASE)["manifest"]
            report = diff({"status": "complete", "records": first},
                          {"version": 1, "canonical_discovery_base": BASE, "records": third})
            self.assertEqual((report["added"], report["updated"], report["removed"]), (0, 1, 0))
            self.assertEqual(report["changed_urls"], [BASE + "/discover/permitted-ai-use/"])
            self.assertEqual(notify(report, ""), 0)
            self.assertEqual(diff({"status": "unavailable", "records": {}},
                                  {"version": 1, "canonical_discovery_base": BASE, "records": third})["status"],
                             "unavailable")

    def test_unconfigured_indexnow_key_does_not_publish_or_send(self):
        with TemporaryDirectory() as td:
            create_key_file(Path(td), "")
            self.assertEqual(list(Path(td).iterdir()), [])
            with self.assertRaises(ValueError):
                create_key_file(Path(td), "../traversal")


if __name__ == "__main__":
    import unittest
    unittest.main()
