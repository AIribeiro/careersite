"""Latest-published Weekly AI Premium Reader contracts and regression checks."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_cms import CmsArticle, render_cms_article
from weekly_ai_reader_access import latest_weekly_ai_slug, weekly_ai_is_premium
from weekly_ai_reader_preview import render_current_week_public_preview


def weekly(day: str = "2026-11-06") -> CmsArticle:
    text = (
        "<h2>Business development</h2>"
        "<p>Executive leadership needs to decide which AI signals deserve "
        "attention and what evidence supports the position. Leaders should "
        "examine the impact on processes, ownership, capacity and risk before "
        "committing resources or changing the way their teams work. "
        + ("Accountability comes before deployment. " * 25)
        + "</p><h2>The full set of developments</h2>"
        "<p>MEMBER_ONLY_WEEKLY_DETAIL_7819 "
        + ("Supporting analysis belongs to the complete edition. " * 25)
        + "</p>"
    )
    return CmsArticle(
        title="Weekly AI — Executive decisions",
        slug="weekly-ai-" + day,
        kind="Weekly Brief",
        category="Weekly AI",
        status="published",
        published_at=day + "T19:00:00+01:00",
        subtitle="A decision-first weekly perspective.",
        excerpt="What developments mean for enterprise leaders.",
        content_html=text,
        author_name="Jair Ribeiro",
    )


class LatestEditionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.week43 = weekly("2026-10-23")
        self.week44 = weekly("2026-10-30")
        self.week45 = weekly("2026-11-06")
        self.week46 = weekly("2026-11-13")

    def test_week_45_stays_premium_without_published_week_46(self):
        published = (self.week43, self.week44, self.week45)
        self.assertEqual(latest_weekly_ai_slug(published), self.week45.slug)
        self.assertTrue(weekly_ai_is_premium(self.week45, published=published))
        self.assertFalse(weekly_ai_is_premium(self.week44, published=published))
        self.assertFalse(weekly_ai_is_premium(self.week43, published=published))

    def test_week_45_becomes_public_only_when_week_46_published(self):
        previous = (self.week45, self.week44)
        current = (self.week46, self.week45, self.week44)
        self.assertTrue(weekly_ai_is_premium(self.week45, published=previous))
        self.assertFalse(weekly_ai_is_premium(self.week45, published=current))
        self.assertTrue(weekly_ai_is_premium(self.week46, published=current))

    def test_calendar_year_rollover_does_not_unlock_latest_issue(self):
        december = weekly("2026-12-25")
        self.assertTrue(weekly_ai_is_premium(december, published=[december]))
        january = weekly("2027-01-01")
        self.assertFalse(weekly_ai_is_premium(december, published=[december, january]))
        self.assertTrue(weekly_ai_is_premium(january, published=[december, january]))

    def test_unpublished_draft_does_not_replace_latest_issue(self):
        draft = weekly("2026-11-13")
        draft.status = "draft"
        # Even if the caller supplies an unfiltered mixture, the catalogue
        # ignores drafts and keeps the latest actually published issue locked.
        self.assertTrue(weekly_ai_is_premium(
            self.week45, published=[self.week44, self.week45, draft]))
        self.assertFalse(weekly_ai_is_premium(
            draft, published=[self.week44, self.week45, draft]))

    def test_non_weekly_content_is_never_affected(self):
        ordinary = weekly()
        ordinary.kind = "Article"
        self.assertFalse(weekly_ai_is_premium(ordinary, published=[ordinary]))

    def test_catalogue_lookup_failure_fails_closed(self):
        with patch("site_cms.fetch_published_articles", side_effect=RuntimeError("offline")):
            self.assertTrue(weekly_ai_is_premium(self.week45))

    def test_empty_catalogue_does_not_open_selected_weekly_body(self):
        self.assertTrue(weekly_ai_is_premium(self.week45, published=[]))


class LatestEditionRenderingTests(unittest.TestCase):
    def setUp(self):
        self.week44 = weekly("2026-10-30")
        self.week45 = weekly("2026-11-06")
        self.published = (self.week44, self.week45)

    def test_credible_public_summary_excludes_body_and_audio(self):
        html = render_current_week_public_preview(self.week45)
        self.assertIn("Public executive summary", html)
        self.assertIn("What developments mean for enterprise leaders.", html)
        self.assertIn("Executive leadership needs to decide", html)
        self.assertIn("once the next Weekly AI edition is published", html)
        self.assertNotIn("Monday", html)
        self.assertNotIn("MEMBER_ONLY_WEEKLY_DETAIL_7819", html)
        self.assertNotIn("<audio", html)
        self.assertNotIn("weekly-ai-audio/", html)
        self.assertIn("weekly-ai-2026-11-06&amp;access=1", html)

    def test_unauthenticated_week_45_restricted_by_published_catalogue(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=self.published),
            patch("page_reader_native._session", return_value=(None, None)),
            patch("thinking_weekly_brief.render_weekly_brief_article") as full,
        ):
            html = render_cms_article(self.week45)
        self.assertIn("Public executive summary", html)
        self.assertNotIn("MEMBER_ONLY_WEEKLY_DETAIL_7819", html)
        full.assert_not_called()

    def test_existing_reader_sees_week_45_full(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=self.published),
            patch("page_reader_native._session",
                  return_value=({"access_token": "example"}, {"id": "reader"})),
            patch("thinking_weekly_brief.render_weekly_brief_article",
                  return_value="FULL_WEEK45") as full,
        ):
            html = render_cms_article(self.week45)
        self.assertEqual(html, "FULL_WEEK45")
        full.assert_called_once()

    def test_week_44_public_even_without_reader_session(self):
        with (
            patch("site_cms.fetch_published_articles", return_value=self.published),
            patch("page_reader_native._session") as session,
            patch("thinking_weekly_brief.render_weekly_brief_article",
                  return_value="OPEN_WEEK44"),
        ):
            html = render_cms_article(self.week44)
        self.assertEqual(html, "OPEN_WEEK44")
        session.assert_not_called()

    def test_older_week_opens_on_newer_publication_not_calendar_rollover(self):
        with (
            patch("site_cms.fetch_published_articles",
                  return_value=(*self.published, weekly("2026-11-13"))),
            patch("page_reader_native._session") as session,
            patch("thinking_weekly_brief.render_weekly_brief_article",
                  return_value="OPEN_WEEK45"),
        ):
            html = render_cms_article(self.week45)
        self.assertEqual(html, "OPEN_WEEK45")
        session.assert_not_called()

    def test_featured_week45_hides_direct_audio_controls(self):
        from thinking_collection_catalogs import _feature
        with (
            patch("site_cms.fetch_published_articles", return_value=self.published),
            patch("thinking_collection_catalogs._image_url", return_value=""),
            patch("weekly_ai_audio.audio_url") as audio,
        ):
            html = _feature(self.week45, "weekly_ai", None)
        self.assertIn("Read the latest edition's public preview", html)
        audio.assert_not_called()

    def test_archive_marks_latest_week45_premium_and_week44_open(self):
        from thinking_weekly_brief import render_weekly_brief_archive
        with patch("site_cms._public_reads_or_none", return_value={}):
            html = render_weekly_brief_archive(self.published)
        self.assertEqual(html.count("Latest edition · Premium Reader"), 1)
        self.assertIn("Open access", html)
        self.assertIn("Read the public summary", html)

    def test_shared_account_origin_and_consent(self):
        from reader_membership import _register_profile
        user = {
            "id": "weekly-reader", "email": "weekly@example.com",
            "user_metadata": {
                "reader_acquisition_source": "weekly_ai",
                "reader_editorial_opt_in": False, "reader_first_name": "A",
            },
        }
        with (
            patch("reader_membership._get_profile", return_value=None),
            patch("reader_membership._request_json",
                  side_effect=lambda *a, **kw: [kw["payload"]]),
            patch("reader_membership._log_consent") as consent,
        ):
            profile = _register_profile({"access_token": "token"}, user)
        self.assertEqual(profile["acquisition_source"], "weekly_ai")
        self.assertFalse(profile["newsletter_opt_in"])
        consent.assert_not_called()


if __name__ == "__main__":
    unittest.main()
