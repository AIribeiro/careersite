from __future__ import annotations

import unittest
from unittest.mock import patch

from site_cms import CmsArticle, inject_cms_landing
from thinking_weekly_brief import (
    inject_weekly_brief_landing,
    is_weekly_brief,
    render_weekly_brief_article,
)


def brief(**kwargs):
    values = dict(
        id="weekly-1", title="WEEKLY AI — Signal", slug="weekly-ai-2026-10-11",
        subtitle="Five verified stories", excerpt="Five verified stories and a leadership signal.",
        kind="Weekly Brief", category="Weekly AI", status="published",
        published_at="2026-10-11T09:00:00+00:00", read_minutes=1,
        content_html="<p>Verified story <a href=\"https://example.com\">Publisher</a></p>"
    )
    values.update(kwargs)
    return CmsArticle(**values)


class WeeklyAiBriefingTests(unittest.TestCase):
    def test_recognition_is_exact_to_separate_news_from_articles(self):
        self.assertTrue(is_weekly_brief(brief()))
        self.assertFalse(is_weekly_brief(brief(kind="Article")))
        self.assertFalse(is_weekly_brief(brief(category="AI Governance")))

    def test_missing_edition_does_not_add_blank_section(self):
        self.assertEqual(inject_weekly_brief_landing("<main>Content</main>", []), "<main>Content</main>")

    def test_landing_has_one_minute_cta_and_archive(self):
        html = inject_weekly_brief_landing("<main>Content</main>", [
            brief(), brief(id="older", title="Prior edition", slug="weekly-ai-2026-10-04",
                           published_at="2026-10-04T08:00:00+00:00")
        ])
        self.assertIn('id="weekly-ai"', html)
        self.assertIn("Start reading · 1 min", html)
        self.assertIn("Previous editions", html)
        self.assertIn("weekly-ai-2026-10-11", html)
        self.assertIn("weekly-ai-2026-10-04", html)

    def test_brief_reader_is_compact_and_has_source_credit(self):
        html = render_weekly_brief_article(brief(), "<footer>Share</footer>")
        self.assertIn("Curated by Jair Ribeiro", html)
        self.assertIn("Publisher", html)
        self.assertIn("checked against linked publishers", html)
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
            '<section class="section paper"><div class="container"><div class="head">'
            '<div><p class="eyebrow">Current questions</p></div></div></section>'
            '<section class="section white"><div class="container"><div class="head">'
            '<div><p class="eyebrow">More leadership questions</p></div></div></section>'
        )
        rendered = inject_cms_landing(original)
        self.assertIn('id="weekly-ai"', rendered)
        self.assertIn("Normal Article", rendered)
        self.assertEqual(rendered.count('data-hq-event="cms_article_open"'), 1)


if __name__ == "__main__":
    unittest.main()
