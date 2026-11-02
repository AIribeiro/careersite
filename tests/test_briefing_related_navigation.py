from __future__ import annotations

import re
import unittest
from types import SimpleNamespace

from briefing_related_navigation import (
    EDITORIAL_PATHS,
    insert_related_navigation,
    related_briefings,
    render_related_briefings,
)


SLUGS = (
    "ai-capabilities-executive-decisions",
    "seven-questions-for-better-ai-decisions",
    "ai-governance-explained-to-executives",
    "eu-ai-act-what-executives-must-decide",
    "data-governance-what-deserves-funding",
    "data-governance-vs-ai-governance-executive-decisions",
)


def article(slug: str, **overrides):
    fields = dict(
        slug=slug,
        kind="Executive Briefing",
        status="published",
        title=slug.replace("-", " ").title(),
        subtitle="Executive evidence, accountability and the next business decision",
        keywords=("Governance", "AI", "Data"),
        category="AI & Data Governance",
        read_minutes=6,
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


class ContextualBriefingNavigationTests(unittest.TestCase):
    def setUp(self):
        self.published = [article(slug) for slug in SLUGS]

    def test_every_existing_edition_has_two_distinct_contextual_next_reads(self):
        for current in self.published:
            with self.subTest(slug=current.slug):
                recommendations = related_briefings(current, self.published)
                slugs = [a.slug for a, reason in recommendations]
                self.assertEqual(len(slugs), 2)
                self.assertEqual(len(set(slugs)), 2)
                self.assertNotIn(current.slug, slugs)
                self.assertEqual(slugs, [row[0] for row in EDITORIAL_PATHS[current.slug]])
                self.assertTrue(all(len(reason) >= 30 for a, reason in recommendations))

    def test_only_live_executive_briefings_are_recommended(self):
        candidates = self.published + [
            article("internal-unpublished", status="draft"),
            article("general-news-article", kind="Article"),
            article("injected-link", title="<script>unsafe</script>", status="draft"),
        ]
        recs = related_briefings(article("unknown-executive-topic"), candidates)
        self.assertEqual(len(recs), 2)
        self.assertTrue(all(a.status == "published" and a.kind == "Executive Briefing"
                            for a, reason in recs))
        self.assertNotIn("internal-unpublished", [a.slug for a, reason in recs])
        self.assertNotIn("general-news-article", [a.slug for a, reason in recs])

    def test_future_edition_uses_topic_fallback(self):
        newcomer = article("ai-risk-ownership-and-review",
                          title="AI Risk Ownership and Review",
                          category="AI Governance",
                          keywords=("AI governance", "risk", "ownership"))
        recommendations = related_briefings(newcomer, self.published)
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(len({a.slug for a, reason in recommendations}), 2)

    def test_read_next_is_final_section_before_main_closes_and_is_idempotent(self):
        current = self.published[0]
        document = (
            '<main><section class="body">Briefing</section>'
            '<section class="contact">Contact the author</section></main>'
            '<footer>Site footer</footer>'
        )
        result = insert_related_navigation(document, current, self.published)
        self.assertEqual(result.count('data-analytics-section="briefings-related-reading"'), 1)
        self.assertIn("Where to go next", result)
        self.assertLess(result.index("Contact the author"), result.index('class="ebr-related"'))
        self.assertLess(result.index('class="ebr-related"'), result.index("</main>"))
        self.assertLess(result.index("</main>"), result.index("<footer>"))
        self.assertEqual(result, insert_related_navigation(result, current, self.published))
        self.assertEqual(result.count('data-hq-event="briefing_related_open"'), 2)

    def test_links_use_canonical_routes_and_existing_tracking_conventions(self):
        current = self.published[0]
        html = render_related_briefings(current, self.published)
        for expected, _ in EDITORIAL_PATHS[current.slug]:
            self.assertIn(f"article={expected}", html)
        self.assertIn("data-hq-content-slug=", html)
        self.assertIn('aria-label="Recommended Executive AI Briefings"', html)
        self.assertIn('data-hq-event="briefing_related_library"', html)
        self.assertIn('href="?page=briefings"', html)
        self.assertNotIn(f"article={current.slug}", html)
        self.assertIn("grid-template-columns:1fr", html)

    def test_safe_behavior_with_one_or_zero_other_published_editions(self):
        current = self.published[0]
        one = [current, self.published[1]]
        self.assertEqual(len(related_briefings(current, one)), 1)
        self.assertEqual(len(related_briefings(current, [current])), 0)
        self.assertEqual(render_related_briefings(current, [current]), "")
        doc = "<main>Only article</main>"
        self.assertEqual(insert_related_navigation(doc, current, [current]), doc)
        self.assertEqual(
            render_related_briefings(article("draft", status="draft"), self.published), ""
        )

    def test_titles_are_escaped_and_untrusted_slugs_are_skipped(self):
        current = article("new-draft-to-review", title="New decision")
        unsafe = article("valid-slug", title="<img src=x onerror=alert(1)>")
        weird = article("../bad", title="Bad route")
        html = render_related_briefings(current, [unsafe, weird])
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;img", html)
        self.assertNotIn("../bad", html)
        self.assertNotIn("javascript:", html)


if __name__ == "__main__":
    unittest.main()
