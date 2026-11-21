"""Automatic homepage release tracking for every deployed portfolio update."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import home_whats_new as news
import sync_portfolio_releases as feed


SHA = "a" * 40
TIME = "2026-11-21T13:10:00+01:00"


class AutomaticPortfolioUpdatesTests(unittest.TestCase):
    def test_existing_public_page_update_has_real_page_and_no_internal_message(self):
        updated = feed.changed_update_item(("src/page_presence.py",), SHA, TIME)
        self.assertEqual(updated["key"], "update:" + SHA)
        self.assertEqual(updated["type"], "Page updated")
        self.assertEqual(updated["title"], "Speaking & Publications")
        self.assertEqual(updated["href"], "?page=presence")
        self.assertEqual(updated["cta"], "View the update")
        self.assertNotIn("source file", updated["description"].lower())
        self.assertEqual(updated["date"], TIME)

    def test_advisory_service_change_is_visible_and_links_to_real_service(self):
        updated = feed.changed_update_item(
            ("src/page_advisory_market_signals.py", "src/page_advisory_market_review.py"),
            SHA, TIME,
        )
        self.assertEqual(updated["href"], "?page=advisory-market-signals")
        self.assertEqual(updated["title"], "Swedish AI & Data Market Review")

    def test_shared_styles_or_unmatched_runtime_changes_are_safe_generic_updates(self):
        updated = feed.changed_update_item(
            ("src/site_styles.py", "src/page_owner_advisory_management.py"), SHA, TIME
        )
        self.assertEqual(updated["type"], "Portfolio updated")
        self.assertEqual(updated["href"], "?page=home")
        self.assertNotIn("owner", updated["description"].lower())
        self.assertNotIn("admin", updated["description"].lower())

    def test_multiple_public_pages_produce_truthful_generic_banner(self):
        updated = feed.changed_update_item(
            ("src/page_presence.py", "src/page_about.py"), SHA, TIME
        )
        self.assertEqual(updated["title"], "Latest portfolio improvements")
        self.assertEqual(updated["href"], "?page=home")

    def test_changes_are_detected_by_deployed_paths_not_tests_or_feed_self_commit(self):
        mock_names = (
            "src/page_presence.py\n"
            "images/profile.png\n"
            "docs/internal.md\n"
            "tests/test_home_auto_updates.py\n"
            ".github/workflows/home-whats-new.yml\n"
            "data/portfolio_release_feed.json\n"
        ).encode()
        with patch.object(feed.subprocess, "check_output", return_value=mock_names.decode()):
            paths = feed.changed_public_files("before", "after")
        self.assertEqual(paths, ("images/profile.png", "src/page_presence.py"))
        self.assertIsNone(feed.changed_update_item((), SHA, TIME))

    def test_release_update_feed_idempotent_for_single_commit_and_real_timestamp(self):
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "portfolio_release_feed.json"
            destination.write_text(json.dumps({"schema_version": 1, "items": []}))
            with patch.object(feed, "FEED", destination), \
                 patch.object(feed, "new_release_items", return_value=[]), \
                 patch.object(feed, "changed_public_files",
                              return_value=("src/page_presence.py",)), \
                 patch.object(feed.subprocess, "check_output", return_value=TIME + "\n"):
                self.assertEqual(feed.update_feed("before", SHA), 1)
                self.assertEqual(feed.update_feed("before", SHA), 0)
            rows = json.loads(destination.read_text())["items"]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["key"], "update:" + SHA)
            self.assertEqual(rows[0]["href"], "?page=presence")

    def test_new_page_and_credential_releases_keep_precedence(self):
        release = {
            "key": "page:presence", "type": "New page", "title": "Speaking & Publications",
            "description": "Selected externally documented presentations and publications.",
            "date": TIME, "href": "?page=presence", "cta": "Explore the page",
        }
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "portfolio_release_feed.json"
            destination.write_text(json.dumps({"schema_version": 1, "items": []}))
            with patch.object(feed, "FEED", destination), \
                 patch.object(feed, "new_release_items", return_value=[release]), \
                 patch.object(feed, "changed_public_files",
                              side_effect=AssertionError("No generic update for a new page")), \
                 patch.object(feed.subprocess, "check_output", return_value=TIME + "\n"):
                self.assertEqual(feed.update_feed("before", SHA), 1)
            self.assertEqual(json.loads(destination.read_text())["items"][0]["key"], "page:presence")

    def test_curated_existing_page_updates_are_no_longer_filtered_out(self):
        with TemporaryDirectory() as folder:
            data = Path(folder) / "data"
            data.mkdir()
            (data / "portfolio_release_feed.json").write_text(json.dumps({"items": [{
                "key": "update:" + SHA, "type": "Page updated",
                "title": "AI & Data Governance", "date": TIME,
                "href": "?page=ai-data-governance",
                "description": "Updated page and current framework for enterprise AI decisions.",
                "cta": "View the update",
            }]}))
            with patch.object(news, "ROOT", Path(folder)), \
                 patch.object(news, "_credential_items", return_value=()):
                chosen = news.latest_local_release(
                    datetime(2026, 11, 21, 15, tzinfo=timezone.utc)
                )
        self.assertEqual(chosen.href, "?page=ai-data-governance")
        self.assertEqual(chosen.type, "Page updated")

    def test_workflow_runs_on_every_push_without_a_file_path_filter(self):
        workflow = (ROOT / ".github/workflows/portfolio-release-feed.yml").read_text()
        self.assertIn("push:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertNotIn("\n    paths:\n", workflow)
        self.assertIn("concurrency:", workflow)
        self.assertIn("git pull --rebase origin main", workflow)


if __name__ == "__main__":
    unittest.main()
