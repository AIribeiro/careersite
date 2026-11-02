from __future__ import annotations

import unittest
from unittest.mock import patch

from briefing_related_navigation import insert_related_navigation
from page_executive_briefings import executive_briefing_article
from site_cms import CmsArticle


SLUGS = (
    "ai-capabilities-executive-decisions",
    "seven-questions-for-better-ai-decisions",
    "ai-governance-explained-to-executives",
    "eu-ai-act-what-executives-must-decide",
    "data-governance-what-deserves-funding",
    "data-governance-vs-ai-governance-executive-decisions",
)


class SingleFinalContactFooterTests(unittest.TestCase):
    def test_each_existing_reader_has_one_final_contact_block(self):
        articles = [
            CmsArticle(
                slug=slug,
                title=slug.replace("-", " ").title(),
                subtitle="Business decisions, accountable owners and evidence",
                content_html="<h2>Operational reasoning</h2><p>An original executive perspective.</p>",
                kind="Executive Briefing",
                status="published",
                read_minutes=6,
                published_at="2026-11-02T12:00:00+00:00",
            )
            for slug in SLUGS
        ]
        with patch("page_executive_briefings._article_infographic", return_value=""):
            for article in articles:
                with self.subTest(slug=article.slug):
                    document = executive_briefing_article(
                        article=article,
                        read_metadata="6 min read",
                        image="",
                        tags="",
                        source="",
                        share_footer="",
                        cms_css="",
                    )
                    final = insert_related_navigation(document, article, articles)
                    self.assertEqual(
                        final.count("Have an AI choice that needs a clearer answer?"), 1
                    )
                    self.assertEqual(
                        final.count('data-analytics-section="briefings-contact"'), 1
                    )
                    self.assertEqual(final.count('data-hq-event="briefing_reader_contact"'), 0)
                    self.assertNotIn("Who owns the next decision?", final)
                    self.assertNotIn("Have a governance proposal to challenge?", final)
                    self.assertEqual(
                        final.count('data-analytics-section="briefings-related-reading"'), 1
                    )
                    self.assertLess(
                        final.index('data-analytics-section="briefings-related-reading"'),
                        final.index('data-analytics-section="briefings-contact"'),
                    )
                    self.assertLess(
                        final.index('data-analytics-section="briefings-contact"'),
                        final.rindex("</main>"),
                    )


if __name__ == "__main__":
    unittest.main()
