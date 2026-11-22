"""Regression checks for source-locked Article video placement (unittest discovery)."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import article_reader_video as video  # noqa: E402


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _article(**changes):
    values = dict(
        slug="enterprise-ai-explained-beyond-models-and-agents",
        kind="Article",
        status="published",
        title="Enterprise AI Explained",
        subtitle="A leadership guide",
        excerpt="Public excerpt.",
        content_html="<p>Private main text (must not appear in video markup)</p>",
        published_at="2026-11-21T13:31:17.636324+00:00",
    )
    values.update(changes)
    return SimpleNamespace(**values)


def _manifest(article, **changes):
    prefix = "https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/"
    slug = article.slug
    values = {
        "slug": slug,
        "state": "published_verified",
        "owner_approved": True,
        "media_verified": True,
        "published_at": article.published_at,
        "content_sha256": _hash(article.content_html),
        "title_sha256": _hash(article.title),
        "subtitle_sha256": _hash(article.subtitle),
        "excerpt_sha256": _hash(article.excerpt),
        "video": {
            "url": prefix + "portfolio-public-videos/thinking-articles/" + slug + "/episode/web-sha.mp4",
            "sha256": "a" * 64,
            "bytes": 3383041,
            "mime": "video/mp4",
        },
        "poster": {
            "url": prefix + "careersite-article-images/thinking-articles/" + slug + "/episode/poster-sha.png",
            "sha256": "b" * 64,
            "mime": "image/png",
        },
    }
    values.update(changes)
    return values


class ArticleReaderVideoTests(TestCase):
    def test_active_manifest_renders_one_playable_16x9_player(self):
        article = _article()
        with patch.object(video, "_manifest", return_value=_manifest(article)):
            markup = video.render_article_video(article)
        self.assertEqual(markup.count("<video "), 1)
        self.assertIn('controls playsinline preload="metadata"', markup)
        self.assertIn('width="1920" height="1080"', markup)
        self.assertIn('aspect-ratio:16/9', markup)
        self.assertIn('object-fit:contain', markup)
        self.assertNotIn("Private main text", markup)

    def test_replacement_heading_uses_manifest_and_escapes_html(self):
        article = _article()
        heading = "Eight Capability Families <Explained>"
        manifest = _manifest(article, player_heading=heading)
        with patch.object(video, "_manifest", return_value=manifest):
            markup = video.render_article_video(article)
        self.assertIn("Eight Capability Families &lt;Explained&gt;", markup)
        self.assertNotIn("<Explained>", markup)
        self.assertIn('id="article-video-heading"', markup)

    def test_fail_closed_if_not_uploaded_or_not_verified(self):
        article = _article()
        for bad in ({"state": "awaiting_media_verification"}, {"media_verified": False},
                    {"owner_approved": False}):
            with self.subTest(bad=bad), patch.object(video, "_manifest", return_value=_manifest(article, **bad)):
                self.assertEqual(video.render_article_video(article), "")

    def test_material_source_revision_invalidates_video(self):
        article = _article()
        with patch.object(video, "_manifest", return_value=_manifest(article)):
            self.assertEqual(video.render_article_video(_article(content_html="<p>Later revised body</p>")), "")
            self.assertEqual(video.render_article_video(_article(excerpt="Changed summary")), "")
            self.assertEqual(video.render_article_video(_article(published_at="2026-11-22T13:31:17+00:00")), "")

    def test_never_render_briefing_or_weekly(self):
        article = _article()
        with patch.object(video, "_manifest", return_value=_manifest(article)):
            self.assertEqual(video.render_article_video(_article(kind="Executive Briefing")), "")
            self.assertEqual(video.render_article_video(_article(kind="Weekly Brief")), "")
            self.assertEqual(video.render_article_video(_article(status="draft")), "")

    def test_rejects_unapproved_media_host(self):
        article = _article()
        manifest = _manifest(article)
        manifest["video"]["url"] = "https://example.invalid/file.mp4"
        with patch.object(video, "_manifest", return_value=manifest):
            self.assertEqual(video.render_article_video(article), "")

    def test_public_preview_and_full_article_have_distinct_safe_hooks(self):
        root = Path(__file__).resolve().parents[1] / "src"
        preview = (root / "article_reader_preview.py").read_text(encoding="utf-8")
        full = (root / "site_cms.py").read_text(encoding="utf-8")
        self.assertLess(preview.index("+ render_article_video(article)"), preview.index("+ reader_access_invitation("))
        renderer = full[full.index("def render_cms_article("):]
        self.assertLess(renderer.index("{render_article_video(article)}"), renderer.index("{article.content_html}"))
