"""Regression checks for source-locked Article video placement (no network needed)."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import article_reader_video as video  # noqa: E402


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _article(**changes):
    base = dict(
        slug="enterprise-ai-explained-beyond-models-and-agents",
        kind="Article",
        status="published",
        title="Enterprise AI Explained",
        subtitle="A leadership guide",
        excerpt="Public excerpt.",
        content_html="<p>Private main text (must not appear in video markup)</p>",
        published_at="2026-11-21T13:31:17.636324+00:00",
    )
    base.update(changes)
    return SimpleNamespace(**base)


def _manifest(article, **changes):
    prefix = "https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/"
    slug = article.slug
    base = {
        "slug": slug,
        "state": "published_verified",
        "owner_approved": True,
        "media_verified": True,
        "published_at": article.published_at,
        "content_sha256": _hash(article.content_html),
        "title_sha256": _hash(article.title),
        "subtitle_sha256": _hash(article.subtitle),
        "excerpt_sha256": _hash(article.excerpt),
        "video": {"url": prefix+"portfolio-public-videos/thinking-articles/"+slug+"/episode/web-sha.mp4",
                  "sha256": "a"*64, "bytes": 3383041, "mime": "video/mp4"},
        "poster": {"url": prefix+"careersite-article-images/thinking-articles/"+slug+"/episode/poster-sha.png",
                   "sha256": "b"*64, "mime": "image/png"},
    }
    base.update(changes)
    return base


def test_active_manifest_renders_one_playable_16x9_player(monkeypatch):
    article = _article()
    monkeypatch.setattr(video, "_manifest", lambda slug: _manifest(article))
    markup = video.render_article_video(article)
    assert markup.count("<video ") == 1
    assert 'controls playsinline preload="metadata"' in markup
    assert 'width="1920" height="1080"' in markup
    assert 'aspect-ratio:16/9' in markup
    assert 'object-fit:contain' in markup
    assert "Private main text" not in markup


def test_fail_closed_if_not_uploaded_or_not_verified(monkeypatch):
    article = _article()
    for bad in ({"state": "awaiting_media_verification"}, {"media_verified": False},
                {"owner_approved": False}):
        monkeypatch.setattr(video, "_manifest", lambda slug, bad=bad: _manifest(article, **bad))
        assert video.render_article_video(article) == ""


def test_material_source_revision_invalidates_video(monkeypatch):
    article = _article()
    manifest = _manifest(article)
    monkeypatch.setattr(video, "_manifest", lambda slug: manifest)
    assert video.render_article_video(_article(content_html="<p>Later rewritten full article</p>")) == ""
    assert video.render_article_video(_article(excerpt="Changed summary")) == ""
    assert video.render_article_video(_article(published_at="2026-11-22T13:31:17+00:00")) == ""


def test_never_render_briefing_or_weekly(monkeypatch):
    article = _article()
    monkeypatch.setattr(video, "_manifest", lambda slug: _manifest(article))
    assert video.render_article_video(_article(kind="Executive Briefing")) == ""
    assert video.render_article_video(_article(kind="Weekly Brief")) == ""
    assert video.render_article_video(_article(status="draft")) == ""


def test_rejects_unapproved_media_host(monkeypatch):
    article = _article()
    manifest = _manifest(article)
    manifest["video"]["url"] = "https://example.invalid/file.mp4"
    monkeypatch.setattr(video, "_manifest", lambda slug: manifest)
    assert video.render_article_video(article) == ""


def test_public_preview_and_full_article_have_distinct_safe_hooks():
    root = Path(__file__).resolve().parents[1] / "src"
    preview = (root/"article_reader_preview.py").read_text(encoding="utf-8")
    full = (root/"site_cms.py").read_text(encoding="utf-8")
    assert preview.index("+ render_article_video(article)") < preview.index("+ reader_access_invitation(")
    renderer = full[full.index("def render_cms_article("):]
    assert renderer.index("{render_article_video(article)}") < renderer.index('{article.content_html}')
