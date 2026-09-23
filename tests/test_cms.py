from __future__ import annotations

import unittest

from site_cms import CmsArticle, article_preview_url, cms_share_document, generate_metadata, sanitize_article_html, slugify


class CareersiteCmsTests(unittest.TestCase):
    def test_slugify_is_stable_and_url_safe(self) -> None:
        self.assertEqual(slugify("AI Governance: Scale & Accountability"), "ai-governance-scale-accountability")

    def test_metadata_generation_produces_editable_publish_fields(self) -> None:
        body = """
        <p>Enterprise AI governance should make accountability explicit before a use case scales.</p>
        <p>The operating model, data ownership, adoption and business value all matter when moving from pilot to production.</p>
        """ * 8
        metadata = generate_metadata("AI Governance Beyond the Pilot", body, has_image=True)
        self.assertTrue(metadata["slug"].startswith("ai-governance"))
        self.assertTrue(metadata["seo_title"])
        self.assertTrue(metadata["meta_description"])
        self.assertGreaterEqual(len(metadata["keywords"]), 1)
        self.assertGreaterEqual(len(metadata["hashtags"]), 1)
        self.assertTrue(all(str(tag).startswith("#") for tag in metadata["hashtags"]))
        self.assertGreaterEqual(int(metadata["read_minutes"]), 1)
        self.assertIn("Header image", str(metadata["header_image_alt"]))

    def test_article_html_sanitizer_strips_scripts(self) -> None:
        cleaned = sanitize_article_html(
            '<h2>Safe heading</h2><script>alert("x")</script>'
            '<p onclick="evil()">Text <a href="https://example.com">link</a></p>'
        )
        self.assertNotIn("<script", cleaned)
        self.assertNotIn("onclick=", cleaned)
        self.assertIn("<h2>Safe heading</h2>", cleaned)
        self.assertIn('rel="noopener noreferrer"', cleaned)

    def test_article_preview_url_uses_test_attribution(self) -> None:
        article = CmsArticle(title="Preview", slug="preview-article")
        self.assertEqual(
            article_preview_url(article),
            "https://jairribeiro-ai.streamlit.app/thinking/preview-article?source=application&role=Test",
        )

    def test_share_document_contains_article_metadata(self) -> None:
        article = CmsArticle(
            title="A CMS Article",
            slug="a-cms-article",
            content_html="<p>Body</p>",
            excerpt="A concise article excerpt.",
            seo_title="A CMS Article | Jair Ribeiro",
            meta_description="A concise article excerpt.",
            category="Enterprise AI",
            kind="Point of view",
            status="published",
            published_at="2026-09-23T12:00:00+00:00",
            updated_at="2026-09-23T12:10:00+00:00",
            keywords=("Enterprise AI", "AI Strategy"),
        )
        document = cms_share_document(article)
        self.assertIn('property="og:type" content="article"', document)
        self.assertIn("A CMS Article", document)
        self.assertIn("/thinking/a-cms-article", document)
        self.assertIn('type="application/ld+json"', document)


if __name__ == "__main__":
    unittest.main()
