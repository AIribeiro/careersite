from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from site_cms import CmsArticle, inject_cms_landing
from thinking_weekly_brief import (
    WEEKLY_ARCHIVE_URL,
    edition_label,
    edition_week,
    inject_weekly_brief_landing,
    is_weekly_brief,
    render_weekly_brief_archive,
    render_weekly_brief_article,
    sorted_editions,
)


def brief(**kwargs):
    values = dict(
        id="weekly-1", title="WEEKLY AI — From Adoption to Accountable Action",
        slug="weekly-ai-2026-10-11", subtitle="Five verified stories",
        excerpt="Five verified stories and a leadership signal.",
        kind="Weekly Brief", category="Weekly AI", status="published",
        published_at="2026-10-11T09:00:00+00:00", read_minutes=1,
        content_html='<p>Verified story <a href="https://example.com">Publisher</a></p>'
    )
    values.update(kwargs)
    return CmsArticle(**values)


class WeeklyAiBriefingTests(unittest.TestCase):
    def test_recognition_is_exact_to_separate_news_from_articles(self):
        self.assertTrue(is_weekly_brief(brief()))
        self.assertFalse(is_weekly_brief(brief(kind="Article")))
        self.assertFalse(is_weekly_brief(brief(category="AI Governance")))

    def test_iso_week_number_for_sunday_pilot(self):
        year, week, start, end = edition_week(brief())
        self.assertEqual((year, week), (2026, 41))
        self.assertEqual(start, date(2026, 10, 5))
        self.assertEqual(end, date(2026, 10, 11))
        self.assertEqual(edition_label(brief()), "Week 41 · 2026")

    def test_monday_release_labels_previous_covered_week(self):
        monday = brief(slug="weekly-ai-2026-10-19")
        self.assertEqual(edition_week(monday), (2026, 42, date(2026, 10, 12), date(2026, 10, 18)))

    def test_iso_year_handles_new_year_boundary(self):
        first_monday = brief(slug="weekly-ai-2027-01-04")
        self.assertEqual(edition_week(first_monday), (2026, 53, date(2026, 12, 28), date(2027, 1, 3)))
        archive = render_weekly_brief_archive([first_monday])
        self.assertIn("Week 53 · 2026", archive)
        self.assertIn("28 December 2026–3 January 2027", archive)

    def test_missing_edition_does_not_add_blank_section(self):
        self.assertEqual(inject_weekly_brief_landing("<main>Content</main>", []), "<main>Content</main>")

    def test_main_feature_precedes_thinking_intro_and_archive_is_always_available(self):
        original = '<nav>Navigation</nav><main><section class="pagehero">Essays</section></main>'
        html = inject_weekly_brief_landing(original, [brief()])
        self.assertLess(html.index('id="weekly-ai"'), html.index('class="pagehero"'))
        self.assertIn("Calendar week", html)
        self.assertNotIn("Swedish", html)
        self.assertNotIn("oktober", html)
        self.assertIn("Week · 2026", html)
        self.assertIn("5–11 October 2026", html)
        self.assertIn("Start reading · 1 min", html)
        self.assertIn("Browse all weeks (1)", html)
        self.assertIn("Previous editions", html)
        self.assertIn(WEEKLY_ARCHIVE_URL.replace("&", "&amp;"), html)

    def test_previous_editions_show_separate_week_labels_and_links(self):
        html = inject_weekly_brief_landing("<main>Content</main>", [
            brief(),
            brief(id="older", title="Prior edition", slug="weekly-ai-2026-10-04",
                  published_at="2026-10-04T08:00:00+00:00"),
        ])
        self.assertIn('id="weekly-ai"', html)
        self.assertIn("Previous editions", html)
        self.assertIn("Week 40 · 2026", html)
        self.assertIn("weekly-ai-2026-10-11", html)
        self.assertIn("weekly-ai-2026-10-04", html)

    def test_archive_contains_current_issue_even_if_no_previous_weeks(self):
        archive = render_weekly_brief_archive([brief()])
        self.assertIn("The weekly archive", archive)
        self.assertIn("Week 41 · 2026", archive)
        self.assertIn("5–11 October 2026", archive)
        self.assertNotIn("Swedish", archive)
        self.assertIn("weekly-ai-2026-10-11", archive)
        self.assertIn("From Adoption to Accountable Action", archive)

    def test_archive_groups_editions_by_iso_year(self):
        first = brief(slug="weekly-ai-2027-01-04", id="cross-year")
        second = brief(slug="weekly-ai-2027-01-11", id="next-year")
        archive = render_weekly_brief_archive([first, second])
        self.assertIn('<h2>2026</h2>', archive)
        self.assertIn('<h2>2027</h2>', archive)
        self.assertIn("Week 53 · 2026", archive)
        self.assertIn("Week 1 · 2027", archive)

    def test_identical_iso_weeks_are_not_repeated_and_drafts_are_excluded(self):
        editions = sorted_editions([
            brief(id="one"),
            brief(id="duplicate", slug="weekly-ai-2026-10-10"),
            brief(id="draft", slug="weekly-ai-2026-10-19", status="draft"),
        ])
        self.assertEqual(len(editions), 1)

    def test_reader_contains_iso_week_direct_publisher_and_archive_link(self):
        html = render_weekly_brief_article(brief(), "<footer>Share</footer>")
        self.assertIn("Curated by Jair Ribeiro", html)
        self.assertIn("Week 41 · 2026", html)
        self.assertIn("Publisher", html)
        self.assertIn("Personally curated by Jair Ribeiro", html)
        self.assertIn("add my own perspective", html)
        self.assertNotIn("Selected from Google Alerts", html)
        self.assertIn("Browse all Weekly AI editions", html)
        self.assertNotIn("cms-article-image", html)

    @patch("site_cms.fetch_published_articles")
    def test_briefs_are_not_repeated_in_latest_articles(self, fetch):
        fetch.return_value = (
            brief(),
            CmsArticle(id="a2", title="Normal Article", slug="normal-article",
                       excerpt="Normal essay", kind="Article", category="AI Adoption",
                       status="published", published_at="2026-10-10T10:00:00+00:00"),
        )
        original = (
            '<main><article class="featured-thinking"><h2>Earlier feature</h2></article>'
            '<section class="pagehero">Thinking</section>'
            '<section class="section paper"><div class="container"><div class="head">'
            '<div><p class="eyebrow">Current questions</p></div></div></section>'
            '<section class="section white"><div class="container"><div class="head">'
            '<div><p class="eyebrow">More leadership questions</p></div></div></section></main>'
        )
        rendered = inject_cms_landing(original)
        self.assertIn('id="weekly-ai"', rendered)
        self.assertIn("Normal Article", rendered)
        # With a single eligible essay, it occupies the auto-highlight slot;
        # Weekly AI must still appear only in its own editorial feature.
        self.assertIn('class="featured-thinking cms-featured-thinking"', rendered)
        self.assertEqual(rendered.count('data-hq-event="cms_article_open"'), 0)


if __name__ == "__main__":
    unittest.main()
