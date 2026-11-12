"""Article early-access entitlements and public-preview regression coverage."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_access import (
    article_is_locked, first_published_at, is_editorial_article, unlock_at,
)
from article_reader_preview import render_public_article_preview
from site_cms import CmsArticle, render_cms_article


class ArticleEarlyAccessTests(unittest.TestCase):
    @staticmethod
    def fixture(published_at="2099-01-01T12:00:00+00:00", kind="Article"):
        html = (
            "<h2>The executive argument</h2>"
            "<p>Leaders approving AI must test the operating capacity, "
            "not just the expected benefit. Assign a decision owner, "
            "define the results and name the specialists who can deliver "
            "the proposed change while continuing the rest of their work.</p>"
            "<p>The work is worth prioritizing only when the assumptions, "
            "capacity and consequences are explicit and the executive "
            "team has considered what other commitments would be delayed.</p>"
            "<h2>Operational decisions and evidence</h2>"
            "<p>PRIVATE_SECTION_72619 Detailed operating evidence and "
            "the decision gates that the full article examines. "
            + ("The organization must establish accountable decisions. " * 30)
            + "</p>"
        )
        return CmsArticle(
            slug="capacity-and-decisions",
            title="Capacity and Decisions",
            kind=kind, status="published",
            published_at=published_at,
            updated_at="2100-01-01T00:00:00+00:00",
            subtitle="What decision owners must know before approving AI work.",
            excerpt="Business capacity belongs in the investment decision.",
            content_html=html,
        )

    def test_exact_168_hour_expiry_and_update_does_not_restart(self):
        published = datetime(2026, 11, 12, 12, tzinfo=timezone.utc)
        item = self.fixture(published.isoformat())
        expiry = published + timedelta(days=7)
        self.assertTrue(article_is_locked(item, now=published))
        self.assertTrue(article_is_locked(item, now=expiry - timedelta(microseconds=1)))
        self.assertFalse(article_is_locked(item, now=expiry))
        self.assertFalse(article_is_locked(item, now=expiry + timedelta(days=1)))
        self.assertEqual(first_published_at(item), published)
        self.assertEqual(unlock_at(item), expiry)

    def test_only_editorial_articles_qualify(self):
        for kind in ("Article", "Point of view", "Decision note",
                     "Field note", "Framework"):
            self.assertTrue(is_editorial_article(self.fixture(kind=kind)))
        for kind in ("Executive Briefing", "Weekly Brief"):
            self.assertFalse(is_editorial_article(self.fixture(kind=kind)))
            self.assertFalse(article_is_locked(self.fixture(kind=kind)))

    def test_missing_publication_date_fails_closed(self):
        self.assertTrue(article_is_locked(self.fixture(published_at="")))
        self.assertTrue(article_is_locked(self.fixture(published_at="invalid timestamp")))

    def test_public_summary_contains_original_text_not_private_body(self):
        article = self.fixture()
        html = render_public_article_preview(article, "1 January 2099 · 4 min")
        self.assertIn("Public executive summary", html)
        self.assertIn("Business capacity belongs in the investment decision", html)
        self.assertIn("Leaders approving AI must test", html)
        self.assertIn("Open to everyone from", html)
        self.assertIn("?page=thinking&amp;article=capacity-and-decisions&amp;access=1", html)
        self.assertNotIn("PRIVATE_SECTION_72619", html)

    def test_anonymous_recent_article_has_summary_but_not_full_body(self):
        article = self.fixture()
        with (
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session", return_value=(None, None)),
        ):
            rendered = render_cms_article(article)
        self.assertIn("Public executive summary", rendered)
        self.assertNotIn("PRIVATE_SECTION_72619", rendered)

    def test_registered_reader_can_read_recent_article(self):
        article = self.fixture()
        with (
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session",
                  return_value=({"access_token": "fake"}, {"id": "reader"})),
        ):
            rendered = render_cms_article(article)
        self.assertIn("PRIVATE_SECTION_72619", rendered)

    def test_article_more_than_seven_days_old_is_public_without_auth(self):
        article = self.fixture(published_at="2026-10-01T12:00:00+00:00")
        with (
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session", return_value=(None, None)) as session,
        ):
            rendered = render_cms_article(article)
        self.assertIn("PRIVATE_SECTION_72619", rendered)
        session.assert_not_called()


if __name__ == "__main__":
    unittest.main()
