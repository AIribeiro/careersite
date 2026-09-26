from __future__ import annotations

import unittest

from site_cms import CmsArticle, _article_payload, sanitize_article_html
from site_cms_links import enrich_article_html, refresh_article_html


class CmsAutoLinkTests(unittest.TestCase):
    def test_adds_two_distinct_context_links_and_author_signature(self) -> None:
        body = (
            "<p>Enterprise AI is moving quickly, but AI governance has to stay practical.</p>"
            "<p>Business value still depends on what changes in the real workflow.</p>"
        )

        enriched = enrich_article_html(body)

        self.assertEqual(enriched.count('data-hq-event="article_internal_'), 3)
        self.assertIn('href="?page=enterprise"', enriched)
        self.assertIn('href="?page=governance"', enriched)
        self.assertNotIn('href="?page=consulting"', enriched)
        self.assertIn('href="?page=impact"', enriched)
        self.assertIn(">Jair Ribeiro</a>", enriched)

    def test_is_idempotent(self) -> None:
        body = (
            "<p>Enterprise AI and AI governance have to work together in practice.</p>"
            "<p>AI adoption only matters when workflows actually change.</p>"
        )
        first = enrich_article_html(body)
        second = enrich_article_html(first)

        self.assertEqual(first, second)
        self.assertEqual(first.count('data-hq-event="article_internal_'), 3)
        self.assertEqual(first.count(">Jair Ribeiro</a>"), 1)

    def test_does_not_nest_or_rewrite_existing_links(self) -> None:
        body = (
            '<p><a href="https://example.com">Enterprise AI</a> can support AI adoption '
            "when the operating model is clear.</p>"
        )

        enriched = enrich_article_html(body)

        self.assertIn('<a href="https://example.com">Enterprise AI</a>', enriched)
        self.assertNotIn('<a href="https://example.com"><a', enriched)
        self.assertIn('href="?page=transformation"', enriched)
        self.assertIn('href="?page=governance"', enriched)

    def test_only_links_article_copy_not_headings(self) -> None:
        body = (
            "<h2>AI governance</h2>"
            "<p>Responsible AI becomes useful when enterprise AI decisions are practical.</p>"
        )

        enriched = enrich_article_html(body)

        self.assertIn("<h2>AI governance</h2>", enriched)
        self.assertIn('href="?page=governance"', enriched)
        self.assertIn('href="?page=enterprise"', enriched)

    def test_existing_trailing_author_name_is_linked_in_place(self) -> None:
        body = "<p>Closing thought.</p><p><strong>Jair Ribeiro</strong></p>"

        enriched = enrich_article_html(body)

        self.assertEqual(enriched.count("Jair Ribeiro"), 1)
        self.assertIn('href="?page=impact"', enriched)
        self.assertFalse(enriched.endswith('class="article-signature"'))

    def test_refresh_recalculates_links_for_published_article_update(self) -> None:
        original = enrich_article_html(
            "<p>Enterprise AI needs practical AI governance.</p>"
        )
        edited = (
            original
            .replace(">Enterprise AI</a>", ">operational discipline</a>")
            .replace(">AI governance</a>", ">AI adoption</a>")
            .replace("</p>", " and business value.</p>", 1)
        )

        refreshed = refresh_article_html(edited)

        self.assertIn('href="?page=transformation"', refreshed)
        self.assertIn('href="?page=consulting"', refreshed)
        self.assertNotIn('data-hq-event="article_internal_enterprise"', refreshed)
        self.assertNotIn('data-hq-event="article_internal_governance"', refreshed)
        self.assertEqual(refreshed.count('href="?page=impact"'), 1)

        published = CmsArticle(
            id="published-1",
            title="Updated",
            status="published",
            content_html=edited,
        )
        payload = _article_payload(published)
        saved_html = str(payload["content_html"])
        self.assertIn('href="?page=transformation"', saved_html)
        self.assertIn('href="?page=consulting"', saved_html)

    def test_payload_enriches_new_cms_article_but_not_legacy_article(self) -> None:
        body = "<p>Enterprise AI needs practical AI governance.</p>"
        article = CmsArticle(title="Test", content_html=body)
        payload = _article_payload(article)

        self.assertIn('href="?page=enterprise"', str(payload["content_html"]))
        self.assertIn('href="?page=governance"', str(payload["content_html"]))
        self.assertIn('href="?page=impact"', str(payload["content_html"]))

        legacy = CmsArticle(title="Legacy", content_html=body, legacy_key="old-article")
        legacy_payload = _article_payload(legacy)
        self.assertEqual(legacy_payload["content_html"], sanitize_article_html(body))


if __name__ == "__main__":
    unittest.main()
