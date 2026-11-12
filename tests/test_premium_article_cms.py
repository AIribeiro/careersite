"""Regression checks for premium Article authoring, previews and first release."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from premium_article_editorial import (
    is_editorial_format, opening_editorial_paragraphs,
    public_intro_preview_paragraphs, needs_first_publication_review,
    premium_article_issues,
)
from article_reader_preview import render_public_article_preview
from site_cms import CmsArticle, save_article, change_article_status


INTRO_ONE = (
    "Finding enterprise information is no longer the difficult part. "
    "When two sources contradict each other, executives still need someone "
    "with an explicit mandate to decide which instruction can guide work. "
    "A retrieved citation does not mean the source is approved, current, "
    "or suitable for the employee's particular decision."
)
INTRO_TWO = (
    "AI can make older inconsistencies more visible while making their "
    "consequences easier to overlook. An organization should establish "
    "ownership, review dates, and an escalation route for conflicting "
    "guidance rather than treating the search result as business authority. "
    "The choice is between faster discovery and accountable decisions, "
    "not between AI access and unnecessary bureaucracy."
)
PRIVATE_DETAIL = "REGISTERED_ANALYSIS_SECTION_59284"
BODY = (
    "<p>" + INTRO_ONE + "</p>"
    "<p>" + INTRO_TWO + "</p>"
    "<h2>Business ownership and authority</h2>"
    "<p>" + PRIVATE_DETAIL + " " +
    "Conflicting sources need a decision owner and a real review path. " * 30 +
    "</p><h2>What leaders should test</h2>"
    "<p>Source approval, permissions, effective dates and disagreement handling.</p>"
)
EXCERPT = (
    "An enterprise assistant may retrieve conflicting guidance with perfect "
    "citations. That does not establish which instruction is authoritative. "
    "Executives need source ownership, review responsibilities and a route "
    "to resolve disagreements before AI answers guide consequential work."
)


def article(**changes):
    values = dict(
        title="Who Decides What AI Can Trust?",
        kind="Article",
        slug="who-decides-what-ai-can-trust",
        status="draft",
        published_at="",
        created_at="2026-11-12T16:00:00+00:00",
        subtitle=(
            "Enterprise AI makes knowledge easier to find but can only be "
            "trusted when business authority and accountability are clear."
        ),
        excerpt=EXCERPT,
        content_html=BODY,
    )
    values.update(changes)
    return CmsArticle(**values)


class PremiumArticleCmsTests(unittest.TestCase):
    def test_article_formats_not_briefings_or_weekly(self):
        for kind in ("Article", "Point of view", "Decision note", "Field note", "Framework"):
            self.assertTrue(is_editorial_format(kind))
        self.assertFalse(is_editorial_format("Executive Briefing"))
        self.assertFalse(is_editorial_format("Weekly Brief"))

    def test_first_publication_only_preserves_existing_articles(self):
        self.assertTrue(needs_first_publication_review(article()))
        self.assertFalse(needs_first_publication_review(article(
            published_at="2026-11-11T10:00:00+00:00"
        )))
        self.assertFalse(needs_first_publication_review(article(
            created_at="2026-10-20T10:00:00+00:00"
        )))
        self.assertFalse(needs_first_publication_review(article(legacy_key="old-story")))

    def test_content_with_genuine_public_opening_passes(self):
        self.assertEqual(premium_article_issues(article()), ())
        self.assertEqual(opening_editorial_paragraphs(BODY), (INTRO_ONE, INTRO_TWO))

    def test_missing_public_summary_and_opening_blocks_publication(self):
        incomplete = article(
            subtitle="Too vague", excerpt="Read more",
            content_html="<h2>The real answer</h2><p>" + PRIVATE_DETAIL + "</p>",
        )
        issues = " ".join(premium_article_issues(incomplete))
        self.assertIn("subtitle", issues)
        self.assertIn("executive summary", issues)
        self.assertIn("two complete", issues)
        with patch("site_cms._request_json") as request:
            with self.assertRaisesRegex(ValueError, "public executive introduction"):
                save_article("fake-admin", CmsArticle(**{
                    **incomplete.__dict__, "status": "published"
                }))
            request.assert_not_called()

    def test_missing_section_boundary_is_rejected_for_new_work(self):
        doc = article(content_html="<p>" + INTRO_ONE + "</p><p>" + INTRO_TWO + "</p>")
        self.assertIn("section heading", " ".join(premium_article_issues(doc)))

    def test_public_preview_cannot_reach_full_article_section(self):
        preview = public_intro_preview_paragraphs(BODY)
        self.assertTrue(preview)
        self.assertIn("Finding enterprise information", " ".join(preview))
        self.assertNotIn(PRIVATE_DETAIL, " ".join(preview))
        public = render_public_article_preview(article(), "12 November 2026 · 4 min")
        self.assertIn("Public executive summary", public)
        self.assertIn(EXCERPT, public)
        self.assertNotIn(PRIVATE_DETAIL, public)
        self.assertIn("Business ownership and authority", public)

    def test_owner_preview_public_and_full_are_independent_of_auth(self):
        from page_admin import _preview_document
        with patch("site_cms._public_reads_or_none", return_value={}):
            public = _preview_document(article(), audience="public")
            complete = _preview_document(article(), audience="full")
        self.assertIn("Public executive summary", public)
        self.assertNotIn(PRIVATE_DETAIL, public)
        self.assertIn(PRIVATE_DETAIL, complete)

    def test_one_click_publish_cannot_bypass_first_release_checks(self):
        draft = article(excerpt="", status="draft")
        data = dict(draft.__dict__)
        data["id"] = "test-id"
        with patch("site_cms._request_json", return_value=[data]) as request:
            with self.assertRaisesRegex(ValueError, "Premium Article publication blocked"):
                change_article_status("fake-admin", "test-id", "published")
            request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
