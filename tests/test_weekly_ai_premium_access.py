"""Current ISO-week Weekly AI Premium Reader access and public archive contracts."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_cms import CmsArticle, render_cms_article
from weekly_ai_reader_access import weekly_ai_is_premium, weekly_ai_public_from
from weekly_ai_reader_preview import render_current_week_public_preview

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def weekly(day: str = "2026-11-13") -> CmsArticle:
    # First paragraph is substantial, but the full body must stay inaccessible
    # to anonymous browsers during the covered Stockholm ISO week.
    source_html = (
        "<h2>Business development</h2>"
        "<p>Executive leadership has to decide which technology signals justify "
        "business attention this week. The practical starting point is to "
        "understand the available evidence, the changes in operating capability, "
        "and the implications for people responsible for decisions and risk. "
        + ("Accountability is required before changing operational commitments. " * 12)
        + "</p>"
        "<h2>The full collection of developments</h2>"
        "<p>MEMBER_ONLY_WEEKLY_DETAIL_7819 "
        + ("Further analysis and original reporting belongs to the full edition. " * 18)
        + "</p>"
    )
    return CmsArticle(
        title="Weekly AI — Executive decisions this week",
        slug="weekly-ai-" + day, kind="Weekly Brief", category="Weekly AI",
        status="published", published_at=day + "T19:00:00+01:00",
        subtitle="A decision-first perspective on the week.",
        excerpt="What current developments may mean for enterprise AI.",
        content_html=source_html, author_name="Jair Ribeiro",
    )


class WeeklyAiPremiumPolicyTests(unittest.TestCase):
    def test_current_friday_issue_is_premium_through_sunday(self):
        issue = weekly()
        self.assertTrue(weekly_ai_is_premium(
            issue, now=datetime(2026, 11, 13, 20, tzinfo=STOCKHOLM)))
        self.assertTrue(weekly_ai_is_premium(
            issue, now=datetime(2026, 11, 15, 23, 59, tzinfo=STOCKHOLM)))
        self.assertFalse(weekly_ai_is_premium(
            issue, now=datetime(2026, 11, 16, 0, 0, tzinfo=STOCKHOLM)))
        self.assertEqual(weekly_ai_public_from(issue), date(2026, 11, 16))

    def test_old_week_always_public_even_without_new_current_issue(self):
        self.assertFalse(weekly_ai_is_premium(
            weekly("2026-11-06"), now=datetime(2026, 11, 13, 12, tzinfo=STOCKHOLM)))
        self.assertFalse(weekly_ai_is_premium(
            weekly("2026-11-13"), now=datetime(2026, 12, 4, 12, tzinfo=STOCKHOLM)))

    def test_legacy_monday_issue_belongs_to_previous_covered_week(self):
        issue = weekly("2026-11-09")
        self.assertFalse(weekly_ai_is_premium(
            issue, now=datetime(2026, 11, 9, 16, tzinfo=STOCKHOLM)))
        self.assertEqual(weekly_ai_public_from(issue), date(2026, 11, 9))

    def test_iso_year_rollover_keeps_same_week_premium(self):
        issue = weekly("2027-01-01")
        self.assertTrue(weekly_ai_is_premium(
            issue, now=datetime(2026, 12, 31, 23, 59, tzinfo=STOCKHOLM)))
        self.assertTrue(weekly_ai_is_premium(
            issue, now=datetime(2027, 1, 3, 23, 59, tzinfo=STOCKHOLM)))
        self.assertFalse(weekly_ai_is_premium(
            issue, now=datetime(2027, 1, 4, 0, 0, tzinfo=STOCKHOLM)))

    def test_daylight_saving_week_unlocks_at_stockholm_monday(self):
        issue = weekly("2027-03-26")
        self.assertTrue(weekly_ai_is_premium(
            issue, now=datetime(2027, 3, 28, 23, 59, tzinfo=STOCKHOLM)))
        self.assertFalse(weekly_ai_is_premium(
            issue, now=datetime(2027, 3, 29, 0, 0, tzinfo=STOCKHOLM)))

    def test_only_weekly_ai_gets_calendar_week_policy(self):
        article = weekly()
        article.kind = "Article"
        self.assertFalse(weekly_ai_is_premium(
            article, now=datetime(2026, 11, 13, 12, tzinfo=STOCKHOLM)))


class WeeklyAiPremiumRenderingTests(unittest.TestCase):
    def test_public_preview_contains_real_excerpt_and_no_full_body_or_audio(self):
        item = weekly()
        html = render_current_week_public_preview(item)
        self.assertIn("Public executive summary", html)
        self.assertIn("What current developments may mean for enterprise AI.", html)
        self.assertIn("Executive leadership has to decide", html)
        self.assertIn("16 November 2026", html)
        self.assertIn("?page=thinking&amp;article=weekly-ai-2026-11-13&amp;access=1", html)
        self.assertNotIn("MEMBER_ONLY_WEEKLY_DETAIL_7819", html)
        self.assertNotIn("<audio", html)
        self.assertNotIn("weekly-ai-audio/", html)

    def test_anonymous_current_week_cms_reader_never_emits_complete_edition(self):
        item = weekly()
        with (
            patch("weekly_ai_reader_access._stockholm_today", return_value=date(2026, 11, 13)),
            patch("page_reader_native._session", return_value=(None, None)),
            patch("thinking_weekly_brief.render_weekly_brief_article") as full,
        ):
            html = render_cms_article(item)
        self.assertIn("Public executive summary", html)
        self.assertNotIn("MEMBER_ONLY_WEEKLY_DETAIL_7819", html)
        full.assert_not_called()

    def test_authenticated_current_week_reader_gets_full_edition(self):
        item = weekly()
        with (
            patch("weekly_ai_reader_access._stockholm_today", return_value=date(2026, 11, 13)),
            patch("page_reader_native._session", return_value=({"access_token": "jwt"}, {"id": "reader"})),
            patch("thinking_weekly_brief.render_weekly_brief_article",
                  return_value="VERIFIED_FULL_WEEKLY_AI") as full,
        ):
            html = render_cms_article(item)
        self.assertEqual(html, "VERIFIED_FULL_WEEKLY_AI")
        full.assert_called_once()

    def test_anonymous_old_week_is_open_and_does_not_check_session(self):
        item = weekly("2026-11-06")
        with (
            patch("weekly_ai_reader_access._stockholm_today", return_value=date(2026, 11, 13)),
            patch("page_reader_native._session") as auth,
            patch("thinking_weekly_brief.render_weekly_brief_article",
                  return_value="PUBLIC_FULL_WEEKLY_AI"),
        ):
            html = render_cms_article(item)
        self.assertEqual(html, "PUBLIC_FULL_WEEKLY_AI")
        auth.assert_not_called()

    def test_current_week_audio_cta_hidden_from_public_collection(self):
        from thinking_collection_catalogs import _feature
        item = weekly()
        with (
            patch("weekly_ai_reader_access._stockholm_today", return_value=date(2026, 11, 13)),
            patch("thinking_collection_catalogs._image_url", return_value=""),
            patch("weekly_ai_audio.audio_url") as audio,
            patch("site_cms.article_relative_url", return_value="?page=thinking&amp;article=weekly-ai-2026-11-13"),
        ):
            html = _feature(item, "weekly_ai", None)
        self.assertIn("Read this week's public preview", html)
        self.assertNotIn("Listen to this edition", html)
        audio.assert_not_called()

    def test_archive_identifies_locked_week_and_open_week(self):
        from thinking_weekly_brief import render_weekly_brief_archive
        with (
            patch("weekly_ai_reader_access._stockholm_today", return_value=date(2026, 11, 13)),
            patch("site_cms._public_reads_or_none", return_value={}),
        ):
            html = render_weekly_brief_archive([weekly(), weekly("2026-11-06")])
        self.assertEqual(html.count("Current week · Premium Reader"), 1)
        self.assertIn("Open access", html)
        self.assertIn("Read the public summary", html)
        self.assertIn("Read · 1 min", html)

    def test_existing_article_and_briefing_policies_are_unchanged(self):
        from article_access import article_is_locked
        self.assertFalse(article_is_locked(weekly()))
        issue = weekly()
        issue.kind = "Executive Briefing"
        self.assertFalse(weekly_ai_is_premium(
            issue, now=datetime(2026, 11, 13, tzinfo=STOCKHOLM)))

    def test_weekly_origin_and_consent_remain_distinct(self):
        from reader_membership import _register_profile
        reader = {
            "id": "weekly-reader", "email": "weekly@example.com",
            "user_metadata": {
                "reader_acquisition_source": "weekly_ai",
                "reader_editorial_opt_in": False,
                "reader_first_name": "A",
            },
        }
        with (
            patch("reader_membership._get_profile", return_value=None),
            patch("reader_membership._request_json",
                  side_effect=lambda *a, **kw: [kw["payload"]]),
            patch("reader_membership._log_consent") as consent,
        ):
            profile = _register_profile({"access_token": "token"}, reader)
        self.assertEqual(profile["acquisition_source"], "weekly_ai")
        self.assertFalse(profile["newsletter_opt_in"])
        consent.assert_not_called()


if __name__ == "__main__":
    unittest.main()
