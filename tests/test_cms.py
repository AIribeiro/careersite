from __future__ import annotations

import unittest
from io import BytesIO

from PIL import Image
from unittest.mock import patch

from site_cms import CmsArticle, article_preview_url, bundled_header_bytes, cms_share_document, effective_header_image_url, embedded_header_image_src, generate_metadata, inject_cms_landing, normalize_header_image, sanitize_article_html, slugify


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

    def test_latest_article_uses_bundled_generated_header(self) -> None:
        slug = "ai-has-too-many-owners-and-thats-why-nobody-owns-the-outcome"
        article = CmsArticle(title="AI Has Too Many Owners", slug=slug)
        data = bundled_header_bytes(slug)
        self.assertIsNotNone(data)
        self.assertGreater(len(data or b""), 20_000)
        self.assertEqual((data or b"")[:4], b"RIFF")
        self.assertEqual((data or b"")[8:12], b"WEBP")
        self.assertEqual(
            effective_header_image_url(article),
            f"https://jairribeiro-ai.streamlit.app/cms-header/{slug}.webp?v=e51f18261592",
        )

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
