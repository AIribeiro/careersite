from __future__ import annotations

import unittest
from io import BytesIO

from PIL import Image
from unittest.mock import patch

from site_cms import CmsArticle, article_preview_url, bundled_header_bytes, cms_share_document, cms_social_image_url, effective_header_image_url, embedded_header_image_src, enrich_article_internal_links, generate_metadata, inject_cms_landing, normalize_header_image, render_cms_social_image, sanitize_article_html, slugify


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

    def test_latest_article_has_no_stale_bundled_header(self) -> None:
        slug = "ai-has-too-many-owners-and-thats-why-nobody-owns-the-outcome"
        article = CmsArticle(title="AI Has Too Many Owners", slug=slug)
        self.assertIsNone(bundled_header_bytes(slug))
        self.assertEqual(effective_header_image_url(article), "")

    def test_data_url_header_overrides_bundled_art_for_editor_preview(self) -> None:
        slug = "ai-has-too-many-owners-and-thats-why-nobody-owns-the-outcome"
        data_url = "data:image/webp;base64,UklGRg=="
        article = CmsArticle(title="Preview art", slug=slug, header_image_url=data_url)
        self.assertEqual(embedded_header_image_src(article), data_url)

    def test_uploaded_header_overrides_bundled_art_for_live_cards(self) -> None:
        slug = "ai-has-too-many-owners-and-thats-why-nobody-owns-the-outcome"
        uploaded = (
            "https://example.supabase.co/storage/v1/object/public/"
            "careersite-article-images/article/new-header.webp"
        )
        article = CmsArticle(title="Updated art", slug=slug, header_image_url=uploaded)
        self.assertEqual(embedded_header_image_src(article), uploaded)

    def test_article_enrichment_adds_signature_and_two_relevant_portfolio_links(self) -> None:
        body = (
            "<p>Enterprise AI is moving quickly, but AI governance and business value "
            "still depend on how the organization works in practice.</p>"
        )
        enriched = enrich_article_internal_links(body)

        self.assertIn('href="?page=enterprise"', enriched)
        self.assertIn('href="?page=governance"', enriched)
        self.assertNotIn('href="?page=consulting"', enriched)
        self.assertIn('class="article-signature"', enriched)
        self.assertIn('href="?page=impact"', enriched)
        self.assertTrue(enriched.rstrip().endswith("</div>"))

    def test_article_enrichment_is_idempotent_and_does_not_nest_existing_links(self) -> None:
        body = (
            '<p><a href="?page=enterprise" target="_self">Enterprise AI</a> '
            "works with AI adoption and AI governance.</p>"
        )
        first = enrich_article_internal_links(body)
        second = enrich_article_internal_links(first)

        self.assertEqual(first, second)
        self.assertEqual(first.count('class="article-signature"'), 1)
        self.assertEqual(first.count('href="?page=impact"'), 1)
        self.assertNotIn("<a href="?page=enterprise" target="_self"><a", first)

    def test_header_normalizer_preserves_full_source_on_two_to_one_canvas(self) -> None:
        source = Image.new("RGB", (600, 900), "white")
        source.putpixel((0, 0), (255, 0, 0))
        source.putpixel((599, 899), (0, 0, 255))
        raw = BytesIO()
        source.save(raw, format="PNG")

        normalized = normalize_header_image(raw.getvalue(), "image/png")
        with Image.open(BytesIO(normalized)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1600, 800))

    def test_featured_cms_article_replaces_primary_and_has_header_fallback(self) -> None:
        article = CmsArticle(
            id="new-article",
            title="New featured article",
            slug="new-featured-article",
            subtitle="A leadership argument.",
            excerpt="A leadership argument.",
            category="AI Operating Model",
            kind="Article",
            status="published",
            featured=True,
            read_minutes=4,
            published_at="2026-09-23T16:18:20+00:00",
        )
        document = (
            '<article class="featured-thinking"><h2>Old featured article</h2></article>'
            '<section class="section white"><div class="container"><div class="head">'
            '<div><p class="eyebrow">Recent thinking</p>'
        )
        with patch("site_cms.fetch_published_articles", return_value=(article,)):
            rendered = inject_cms_landing(document)

        self.assertIn("New featured article", rendered)
        self.assertNotIn("Old featured article", rendered)
        self.assertIn("cms-fallback-cover", rendered)
        self.assertIn("?page=thinking&amp;article=new-featured-article", rendered)

    def test_cms_social_image_is_article_specific_png(self) -> None:
        article = CmsArticle(
            title="When AI Stops Assisting and Starts Working, the Enterprise Has a Different Problem",
            slug="when-ai-stops-assisting-and-starts-working-the-enterprise-has-a-different-problem",
            social_title="When AI Stops Assisting and Starts Working, the Enterprise Has a Different Problem",
            social_description="AI is moving from helping with work to carrying work forward.",
            category="Enterprise AI",
            kind="Point of view",
            updated_at="2026-09-26T07:50:06+00:00",
        )
        url = cms_social_image_url(article)
        self.assertIn("/cms-social/when-ai-stops-assisting-and-starts-working-the-enterprise-has-a-different-problem.png?v=", url)
        data = render_cms_social_image(article)
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (1200, 627))

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
        self.assertIn('/cms-social/a-cms-article.png?v=', document)
        self.assertIn('property="og:image:width" content="1200"', document)
        self.assertIn('property="og:image:height" content="627"', document)


if __name__ == "__main__":
    unittest.main()
