"""Guard meaningful What's New releases and avoid generic deployment notices."""
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
TIME = "2026-11-23T13:00:00+01:00"
ROUTES = 'PUBLIC_VALID = {"home", "presence", "advisory-market-signals", "about"}\n'
APPROVED = {
    "id": "presence-new-conference",
    "status": "published",
    "type": "Page update",
    "page": "presence",
    "title": "New speaking and publication records",
    "description": (
        "Explore newly documented conference speaking contributions and "
        "published work on responsible AI and enterprise data leadership."
    ),
    "cta": "See speaking & publications",
}


def fake_source(rev, path, *, manifest=None):
    if path == "main.py":
        return ROUTES
    if path == feed.ANNOUNCEMENTS:
        if rev == "before":
            return json.dumps({"items": []})
        return json.dumps({"items": manifest or []})
    return ""


class MeaningfulPortfolioUpdateTests(unittest.TestCase):
    def test_routine_code_change_has_no_announcement(self):
        with TemporaryDirectory() as folder:
            target = Path(folder) / "portfolio_release_feed.json"
            target.write_text(json.dumps({"schema_version": 1, "items": []}))
            with patch.object(feed, "FEED", target), \
                 patch.object(feed, "new_release_items", return_value=[]), \
                 patch.object(feed, "declared_release_items", return_value=[]), \
                 patch.object(feed.subprocess, "check_output", return_value=TIME+"\n"):
                self.assertEqual(feed.update_feed("before", SHA), 0)
            self.assertEqual(json.loads(target.read_text())["items"], [])

    def test_specific_approved_update_has_a_real_destination_and_helpful_copy(self):
        with patch.object(feed, "git_file",
                          side_effect=lambda rev, path: fake_source(
                              rev, path, manifest=[APPROVED])):
            items = feed.declared_release_items("before", "after", TIME)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["key"], "editorial:presence-new-conference")
        self.assertEqual(items[0]["href"], "?page=presence")
        self.assertEqual(items[0]["title"], APPROVED["title"])
        self.assertEqual(items[0]["description"], APPROVED["description"])
        self.assertEqual(items[0]["cta"], APPROVED["cta"])
        self.assertNotIn("improvements", items[0]["description"])

    def test_approval_is_required_and_existing_approvals_do_not_reannounce(self):
        for field, value in (
            ("status", "draft"),
            ("page", "home"),
            ("page", "analytics"),
            ("page", "made-up-page"),
            ("title", "Updated"),
            ("description", "Changes have been made."),
            ("cta", "View the update"),
        ):
            row = dict(APPROVED, **{field: value})
            with patch.object(feed, "git_file",
                              side_effect=lambda rev, path: fake_source(
                                  rev, path, manifest=[row])):
                self.assertEqual(feed.declared_release_items("before", "after", TIME),
                                 [], f"Should reject: {field}={value}")
        old = json.dumps({"items": [APPROVED]})
        with patch.object(feed, "git_file",
                          side_effect=lambda rev, path: (
                              ROUTES if path == "main.py" else old
                          )):
            self.assertEqual(feed.declared_release_items("before", "after", TIME), [])

    def test_no_self_link_or_generic_deployment_entry_can_be_featured(self):
        bad = [{
            "key": "update:" + SHA, "type": "Portfolio updated",
            "title": "Latest portfolio improvements",
            "description": "Updates to the portfolio are available across its pages and services.",
            "date": TIME, "href": "?page=home", "cta": "Explore the portfolio"
        }, {
            "key": "editorial:self-reference", "type": "Page update",
            "title": "The homepage has been updated",
            "description": "Visit the homepage to see the updated homepage. " * 2,
            "date": TIME, "href": "?page=home", "cta": "View the update"
        }]
        with TemporaryDirectory() as folder:
            path = Path(folder)/"data"
            path.mkdir()
            (path/"portfolio_release_feed.json").write_text(
                json.dumps({"items": bad+[{
                    "key": "page:presence", "type": "New page",
                    "title": "Speaking & Publications", "date": "2026-11-18T20:33:29+01:00",
                    "description": (
                        "Selected speaking, publications and externally documented "
                        "contributions in enterprise AI leadership and governance."
                    ),
                    "href": "?page=presence", "cta": "See speaking & publications"
                }]}))
            with patch.object(news, "ROOT", Path(folder)), \
                 patch.object(news, "_credential_items", return_value=()):
                item = news.latest_local_release(
                    datetime(2026, 11, 23, 13, tzinfo=timezone.utc))
        self.assertEqual(item.title, "Speaking & Publications")
        self.assertEqual(item.href, "?page=presence")

    def test_new_page_and_credentials_are_still_eligible(self):
        old = "PUBLIC_VALID = {'home'}\n"
        new = "PUBLIC_VALID = {'home','presence'}\nTITLES={'presence':'Speaking & Publications | Jair Ribeiro'}\n"
        meta = "DESCRIPTIONS={'presence':'Selected speaking, publications and externally documented contributions across enterprise AI, Data and responsible governance.'}\n"
        def source(rev, path):
            if path == "main.py":
                return old if rev == "before" else new
            if path == "src/site_meta.py":
                return meta
            return ""
        with patch.object(feed, "git_file", side_effect=source):
            items = feed.new_release_items("before", "after", TIME)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["key"], "page:presence")
        self.assertEqual(items[0]["href"], "?page=presence")
        self.assertNotEqual(items[0]["cta"], "Explore the portfolio")

    def test_workflow_checks_every_push_but_only_publishes_a_qualifying_release(self):
        workflow = (ROOT/".github/workflows/portfolio-release-feed.yml").read_text()
        self.assertIn("branches: [main]", workflow)
        self.assertNotIn("\n    paths:\n", workflow)
        self.assertIn("python scripts/sync_portfolio_releases.py", workflow)
        self.assertIn("git diff --quiet -- data/portfolio_release_feed.json", workflow)

if __name__ == "__main__":
    unittest.main()
