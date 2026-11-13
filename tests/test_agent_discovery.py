"""Regression contracts for the public, metadata-only agent discovery layer."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_discovery import (
    PUBLIC_ORIGIN, agents_text, catalogue_json, llms_text,
    markdown_summary, open_edition_markdown, plain_text, public_catalogue, robots_text, safe_slug,
)


def article(slug, kind="Article", published_at="2026-10-01T12:00:00Z", **kwargs):
    values = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "kind": kind,
        "category": "Weekly AI" if kind == "Weekly Brief" else "AI Governance",
        "published_at": published_at,
        "status": "published",
        "excerpt": "Public executive introduction only.",
        "subtitle": "Public subtitle",
        "meta_description": "Public description",
        "content_html": "PRIVATE_EDITORIAL_BODY_NEVER_IN_AGENT_FEED",
        "aside_html": "PRIVATE_EDITORIAL_ASIDE",
        "email": "PRIVATE_READER_ADDRESS@example.org",
        "keywords": ("private",),
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


class AgentDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)

    def test_access_policies_follow_publication_not_a_hardcoded_week(self):
        sources = [
            article("old-article", published_at="2026-10-01T12:00:00Z"),
            article("new-article", published_at="2026-11-12T12:00:00Z"),
            article("premium-brief", kind="Executive Briefing"),
            article("weekly-ai-2026-11-06", kind="Weekly Brief", published_at="2026-11-06T18:00:00Z"),
            article("weekly-ai-2026-11-13", kind="Weekly Brief", published_at="2026-11-13T18:00:00Z"),
            article("hidden-draft", status="draft"),
        ]
        data = public_catalogue(sources, now=self.now)
        access = {item["slug"]: item["access"] for item in data["content"]}
        self.assertEqual(access["old-article"], "open")
        self.assertEqual(access["new-article"], "premium")
        self.assertEqual(access["premium-brief"], "premium")
        self.assertEqual(access["weekly-ai-2026-11-06"], "open")
        self.assertEqual(access["weekly-ai-2026-11-13"], "premium")
        self.assertNotIn("hidden-draft", access)

    def test_premium_readable_summary_never_reveals_full_body(self):
        item = article("executive-decision", kind="Executive Briefing")
        data = public_catalogue([item], now=self.now)
        response = catalogue_json(data)
        summary = markdown_summary(data["content"][0])
        llms = llms_text(data)
        for output in (response, summary, llms):
            self.assertNotIn("PRIVATE_EDITORIAL_BODY_NEVER_IN_AGENT_FEED", output)
            self.assertNotIn("PRIVATE_EDITORIAL_ASIDE", output)
            self.assertNotIn("PRIVATE_READER_ADDRESS@example.org", output)
        self.assertIn("free registration", summary)
        self.assertEqual(json.loads(response)["count"], 1)


    def test_complete_markdown_only_for_confirmed_open_publication(self):
        older = article(
            "an-older-article",
            published_at="2026-10-01T12:00:00Z",
            content_html="<h2>Executive argument</h2><p>Full public decision text.</p>"
                         "<figure>HIDDEN_FIGURE_ASSET</figure>"
                         "<script>HIDDEN_SCRIPT</script>",
        )
        latest = article("latest-article", published_at="2026-11-12T12:00:00Z")
        published = (older, latest)
        items = {it["slug"]: it for it in public_catalogue(published, now=self.now)["content"]}
        open_markdown = open_edition_markdown(items["an-older-article"], older, published, now=self.now)
        self.assertIn("## Full public edition", open_markdown)
        self.assertIn("Full public decision text.", open_markdown)
        self.assertNotIn("HIDDEN_FIGURE_ASSET", open_markdown)
        self.assertNotIn("HIDDEN_SCRIPT", open_markdown)
        gated = open_edition_markdown(items["latest-article"], latest, published, now=self.now)
        self.assertNotIn("## Full public edition", gated)
        changed = article("an-older-article", status="draft", content_html="LEAKED_AFTER_UNPUBLISH")
        self.assertNotIn("LEAKED_AFTER_UNPUBLISH",
                         open_edition_markdown(items["an-older-article"], changed, published, now=self.now))

    def test_slug_html_and_url_safety(self):
        self.assertEqual(safe_slug("Valid-Slug"), "valid-slug")
        self.assertEqual(safe_slug("../../private"), "")
        self.assertEqual(safe_slug("my_slug"), "")
        self.assertEqual(plain_text("<p>Public <strong>context</strong></p>"), "Public context")
        data = public_catalogue([article("legitimate-brief", kind="Executive Briefing")], now=self.now)
        self.assertEqual(data["content"][0]["url"],
                         PUBLIC_ORIGIN + "/?page=briefing&article=legitimate-brief")
        self.assertEqual(data["content"][0]["markdown_url"],
                         PUBLIC_ORIGIN + "/agent/content/legitimate-brief.md")

    def test_legacy_fallback_deduplication_and_partial_marking(self):
        cms = article("an-existing-piece")
        legacy = [
            SimpleNamespace(slug="an-existing-piece", title="duplicate", topic="Governance",
                            standfirst="legacy duplicate", published_iso="2026-09-01"),
            SimpleNamespace(slug="legacy-piece", title="Legacy", topic="AI",
                            standfirst="Original synopsis", published_iso="2026-09-01"),
        ]
        data = public_catalogue([cms], legacy, now=self.now, catalogue_status="partial")
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["catalogue_status"], "partial")
        self.assertEqual([it["slug"] for it in data["content"]].count("an-existing-piece"), 1)

    def test_agent_instructions_do_not_promise_authentication_or_training_rights(self):
        guide = agents_text()
        robots = robots_text()
        self.assertIn("no training", guide.lower())
        self.assertIn("/agent/catalog.json", guide)
        self.assertIn("Disallow: /readers-admin", robots)
        self.assertIn("Disallow: /owner-auth/", robots)
        self.assertIn("Sitemap: https://jairribeiro.com/sitemap.xml", robots)
        self.assertIn("# Jair Ribeiro", llms_text(public_catalogue([], now=self.now)))


if __name__ == "__main__":
    unittest.main()
