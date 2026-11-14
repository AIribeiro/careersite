"""Articles: latest-published Premium plus minimum seven-day exclusivity."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_access import (
    article_is_locked, first_published_at, is_editorial_article,
    latest_editorial_article_slug, public_access_explanation, unlock_at,
)
from article_reader_preview import render_public_article_preview
from site_cms import CmsArticle, render_cms_article


class ArticleAccessTests(unittest.TestCase):
    @staticmethod
    def fixture(
        published_at="2026-11-12T12:00:00+00:00",
        *, slug="capacity-and-decisions", kind="Article", status="published",
    ):
        content = (
            "<h2>The executive argument</h2>"
            "<p>Leaders approving AI must test operating capacity, "
            "not just the expected benefit. Assign a decision owner, define "
            "results and name the people who can deliver the proposed change "
            "alongside their operational commitments.</p>"
            "<p>The business case must account for the work that other "
            "priorities would displace before the investment is approved.</p>"
            "<h2>Operational decisions and evidence</h2>"
            "<p>PRIVATE_SECTION_72619 Detailed operating evidence and "
            "the decision gates that the full article examines. "
            + ("The organization needs accountable decisions. " * 30)
            + "</p>"
        )
        return CmsArticle(
            slug=slug, title="Capacity and Decisions", kind=kind,
            status=status, published_at=published_at,
            updated_at="2100-01-01T00:00:00+00:00",
            subtitle="What leaders should know before authorizing AI work.",
            excerpt="Business capacity belongs in the investment decision.",
            content_html=content,
        )

    def setUp(self):
        self.day0 = datetime(2026, 11, 12, 12, tzinfo=timezone.utc)
        self.previous = self.fixture(
            "2026-11-01T12:00:00+00:00", slug="previous-article",
        )
        self.latest = self.fixture(
            "2026-11-12T12:00:00+00:00", slug="latest-article",
        )

    def test_latest_stays_premium_after_seven_days_without_successor(self):
        catalogue = [self.previous, self.latest]
        for days in (0, 7, 30, 365):
            with self.subTest(days=days):
                self.assertTrue(article_is_locked(
                    self.latest, published=catalogue,
                    now=self.day0 + timedelta(days=days),
                ))
        self.assertFalse(article_is_locked(
            self.previous, published=catalogue,
            now=self.day0 + timedelta(days=30),
        ))

    def test_publication_of_new_article_unlocks_older_if_seven_days_passed(self):
        catalogue = [self.previous, self.latest]
        self.assertEqual(latest_editorial_article_slug(catalogue), self.latest.slug)
        self.assertFalse(article_is_locked(
            self.previous, published=catalogue, now=self.day0,
        ))
        self.assertTrue(article_is_locked(
            self.latest, published=catalogue, now=self.day0 + timedelta(days=10),
        ))
        successor = self.fixture(
            "2026-11-25T12:00:00+00:00", slug="newer-article",
        )
        catalogue.append(successor)
        self.assertFalse(article_is_locked(
            self.latest, published=catalogue,
            now=self.day0 + timedelta(days=13),
        ))
        self.assertTrue(article_is_locked(
            successor, published=catalogue,
            now=self.day0 + timedelta(days=100),
        ))

    def test_successor_within_seven_days_does_not_prematurely_open_previous(self):
        successor = self.fixture(
            "2026-11-14T12:00:00+00:00", slug="two-days-later",
        )
        catalogue = [self.latest, successor]
        expiry = self.day0 + timedelta(days=7)
        self.assertTrue(article_is_locked(
            self.latest, published=catalogue, now=expiry - timedelta(microseconds=1),
        ))
        self.assertFalse(article_is_locked(
            self.latest, published=catalogue, now=expiry,
        ))
        self.assertEqual(unlock_at(self.latest), expiry)

    def test_no_new_article_at_seven_day_boundary_remains_premium(self):
        expiry = self.day0 + timedelta(days=7)
        for when in (expiry, expiry + timedelta(days=8)):
            self.assertTrue(article_is_locked(
                self.latest, published=[self.latest], now=when,
            ))

    def test_draft_and_other_formats_do_not_release_latest(self):
        draft = self.fixture(
            "2026-11-25T12:00:00+00:00",
            slug="unpublished-draft", status="draft",
        )
        briefing = self.fixture(
            "2026-11-26T12:00:00+00:00",
            slug="new-briefing", kind="Executive Briefing",
        )
        weekly = self.fixture(
            "2026-11-27T12:00:00+00:00",
            slug="weekly-ai-2026-11-27", kind="Weekly Brief",
        )
        self.assertTrue(article_is_locked(
            self.latest, published=[self.previous, self.latest, draft, briefing, weekly],
            now=self.day0 + timedelta(days=100),
        ))
        self.assertFalse(article_is_locked(briefing))
        self.assertFalse(article_is_locked(weekly))
        self.assertFalse(article_is_locked(draft))

    def test_article_subtypes_share_one_latest_publication_sequence(self):
        point_of_view = self.fixture(
            "2026-11-15T12:00:00+00:00",
            slug="point-of-view-new", kind="Point of view",
        )
        self.assertEqual(
            latest_editorial_article_slug([self.previous, self.latest, point_of_view]),
            point_of_view.slug,
        )
        for kind in ("Article", "Decision note", "Field note", "Framework"):
            self.assertTrue(is_editorial_article(self.fixture(kind=kind)))
        self.assertTrue(is_editorial_article(point_of_view))

    def test_revisions_and_featured_flags_do_not_change_original_order(self):
        self.previous.featured = True
        self.previous.updated_at = "2105-02-01T00:00:00+00:00"
        self.assertEqual(
            latest_editorial_article_slug([self.latest, self.previous]),
            self.latest.slug,
        )
        self.assertEqual(first_published_at(self.latest), self.day0)

    def test_unavailable_publication_metadata_fails_closed(self):
        with patch("site_cms.fetch_published_articles", side_effect=RuntimeError("unavailable")):
            self.assertTrue(article_is_locked(
                self.latest, now=self.day0 + timedelta(days=40),
            ))
        self.assertTrue(article_is_locked(
            self.latest, published=[], now=self.day0 + timedelta(days=40),
        ))
        self.assertTrue(article_is_locked(self.fixture(published_at="invalid")))

    def test_public_preview_does_not_promise_false_public_release_date(self):
        html = render_public_article_preview(self.latest, "12 November 2026 · 4 min")
        self.assertIn("Public executive summary", html)
        self.assertIn("Business capacity belongs in the investment decision", html)
        self.assertIn("Leaders approving AI must test", html)
        self.assertIn("Free registration gives you the complete article", html)
        self.assertNotIn("once a newer Article has been published", html)
        self.assertNotIn("seven days", html.lower())
        self.assertNotIn("Open to everyone from", html)
        self.assertNotIn("PRIVATE_SECTION_72619", html)
        self.assertIn("article=latest-article&amp;access=1", html)
        self.assertIn("first seven days", public_access_explanation(self.latest))

    def test_anonymous_latest_article_even_after_day_seven_only_shows_summary(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=[self.previous, self.latest]),
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session", return_value=(None, None)),
        ):
            rendered = render_cms_article(self.latest)
        self.assertIn("Public executive summary", rendered)
        self.assertNotIn("PRIVATE_SECTION_72619", rendered)

    def test_existing_reader_sees_full_latest_article(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=[self.previous, self.latest]),
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session",
                  return_value=({"access_token": "fake"}, {"id": "reader"})),
        ):
            rendered = render_cms_article(self.latest)
        self.assertIn("PRIVATE_SECTION_72619", rendered)

    def test_previous_older_article_public_without_login(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=[self.previous, self.latest]),
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("page_reader_native._session") as session,
        ):
            rendered = render_cms_article(self.previous)
        self.assertIn("PRIVATE_SECTION_72619", rendered)
        session.assert_not_called()

    def test_all_executive_briefings_remain_permanently_premium(self):
        briefing = self.fixture(
            "2018-05-01T00:00:00+00:00",
            slug="historic-briefing", kind="Executive Briefing",
        )
        with (
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("site_cms.fetch_published_articles", return_value=[briefing, self.latest]),
            patch("page_reader_native._session", return_value=(None, None)),
            patch("briefing_reader_preview.render_public_briefing_preview",
                  return_value="PUBLIC_BRIEFING_SUMMARY"),
            patch("briefing_related_navigation.insert_related_navigation",
                  side_effect=lambda html, *_args: html),
        ):
            rendered = render_cms_article(briefing)
        self.assertEqual(rendered, "PUBLIC_BRIEFING_SUMMARY")
        self.assertNotIn("PRIVATE_SECTION_72619", rendered)

    def test_reader_registration_origin_not_duplicated(self):
        from reader_membership import _register_profile
        user = {
            "id": "reader", "email": "reader@example.com",
            "user_metadata": {
                "reader_first_name": "Reader",
                "reader_acquisition_source": "articles",
                "reader_editorial_opt_in": False,
            },
        }
        with (
            patch("reader_membership._get_profile", return_value=None),
            patch("reader_membership._request_json",
                  side_effect=lambda *a, **kw: [kw["payload"]]),
            patch("reader_membership._log_consent") as consent,
        ):
            profile = _register_profile({"access_token": "token"}, user)
        self.assertEqual(profile["acquisition_source"], "articles")
        self.assertFalse(profile["newsletter_opt_in"])
        consent.assert_not_called()
        existing = {"user_id": "reader", "acquisition_source": "briefing_pdf"}
        with (
            patch("reader_membership._get_profile", return_value=existing),
            patch("reader_membership._request_json") as write,
        ):
            profile = _register_profile({"access_token": "token"}, user)
        self.assertIs(profile, existing)
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
