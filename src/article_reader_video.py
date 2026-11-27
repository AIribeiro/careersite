"""Approved, source-locked Thinking Article video player.

The manifest remains disabled until the exact owner-approved video and poster
are uploaded to durable public storage and their anonymous delivery is verified.
The reader policy and article CMS body are never modified by this component.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from article_access import is_editorial_article

ROOT = Path(__file__).resolve().parents[1] / "static" / "article-videos"
_SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_HOST = "rnqweoxtynelfirffmlr.supabase.co"
_VIDEO_PREFIX = "/storage/v1/object/public/portfolio-public-videos/thinking-articles/"
_POSTER_PREFIX = "/storage/v1/object/public/careersite-article-images/thinking-articles/"

ARTICLE_VIDEO_CSS = """<style>
.article-video-feature{background:#f6f4f0;padding:clamp(24px,4vw,54px) 0;border-top:1px solid #e2d9cc;border-bottom:1px solid #e2d9cc}
.article-video-feature .article-video-container{width:min(1120px,calc(100% - 40px));margin-inline:auto}
.article-video-feature .article-video-kicker{font:700 11px/1.45 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#a37450;margin:0 0 8px}
.article-video-feature h2{font:500 clamp(23px,3vw,34px)/1.2 Georgia,serif;color:#1c2b3a;margin:0 0 18px}
.article-video-feature .article-video-frame{width:100%;aspect-ratio:16/9;overflow:hidden;border:1px solid #d7d2cc;border-radius:12px;background:#19293a;box-shadow:0 12px 32px #10263b22}
.article-video-feature video{width:100%;height:100%;aspect-ratio:16/9;object-fit:contain;display:block;background:#19293a}
.article-video-feature .article-video-credit{font:500 12px/1.6 system-ui,sans-serif;color:#525f6b;margin:10px 0 0}
.article-video-feature .article-video-credit a{color:#8d6347;text-decoration:underline;text-underline-offset:3px}
@media(max-width:560px){.article-video-feature .article-video-container{width:calc(100% - 28px)}.article-video-feature .article-video-frame{border-radius:6px}.article-video-feature{padding:24px 0}}
</style>"""


def _sha_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _approved_public_url(value: object, prefix: str, slug: str) -> bool:
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    if parts.scheme != "https" or parts.query or parts.fragment or ".." in parts.path:
        return False
    if parts.netloc == _HOST:
        return parts.path.startswith(prefix + slug + "/")
    # One fixed, approved immutable Pages release. Preserve the existing
    # Supabase allowlist and reject arbitrary Pages paths and other articles.
    if parts.netloc == "airibeiro.github.io" and slug == "how-to-build-an-ai-literate-organization":
        base = "/careersite/public-media/thinking-articles/" + slug + "/20261125-fd1409953395/"
        expected = "web-fd1409953395.mp4" if prefix == _VIDEO_PREFIX else "poster-a5d06a73832f.png"
        return parts.path == base + expected
    if parts.netloc == "airibeiro.github.io" and slug == "before-you-hire-your-next-ai-engineer-who-is-leading-your-enterprise-ai":
        base = "/careersite/public-media/thinking-articles/" + slug + "/20261127-10971877f74e/"
        expected = "web-10971877f74e.mp4" if prefix == _VIDEO_PREFIX else "poster-24d721d86696.png"
        return parts.path == base + expected
    return False


def _manifest(slug: str) -> dict | None:
    if not _SAFE_SLUG.fullmatch(slug):
        return None
    try:
        data = json.loads((ROOT / slug / "manifest.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _source_matches(article, manifest: dict) -> bool:
    checks = {
        "content_sha256": str(getattr(article, "content_html", "") or ""),
        "title_sha256": str(getattr(article, "title", "") or ""),
        "subtitle_sha256": str(getattr(article, "subtitle", "") or ""),
        "excerpt_sha256": str(getattr(article, "excerpt", "") or ""),
    }
    if any(not _SHA.fullmatch(str(manifest.get(k, ""))) or _sha_text(v) != manifest[k]
           for k, v in checks.items()):
        return False
    try:
        expected = datetime.fromisoformat(str(manifest["published_at"]).replace("Z", "+00:00"))
        current = datetime.fromisoformat(str(getattr(article, "published_at", "")).replace("Z", "+00:00"))
        if expected.tzinfo is None or current.tzinfo is None:
            return False
        return expected.astimezone(timezone.utc) == current.astimezone(timezone.utc)
    except (ValueError, TypeError, KeyError):
        return False


def render_article_video(article) -> str:
    """A single player for both anonymous preview and full Article render paths."""
    if not is_editorial_article(article) or str(getattr(article, "status", "")) != "published":
        return ""
    slug = str(getattr(article, "slug", "") or "")
    manifest = _manifest(slug)
    if not manifest or manifest.get("slug") != slug or manifest.get("state") != "published_verified":
        return ""
    if (manifest.get("owner_approved") is not True
        or manifest.get("media_verified") is not True
        or not _source_matches(article, manifest)):
        return ""
    video = manifest.get("video") or {}
    poster = manifest.get("poster") or {}
    if (not _SHA.fullmatch(str(video.get("sha256", "")))
        or not _SHA.fullmatch(str(poster.get("sha256", "")))
        or not isinstance(video.get("bytes"), int) or video["bytes"] <= 0
        or video.get("mime") != "video/mp4"
        or poster.get("mime") != "image/png"
        or not _approved_public_url(video.get("url"), _VIDEO_PREFIX, slug)
        or not _approved_public_url(poster.get("url"), _POSTER_PREFIX, slug)):
        return ""
    if slug == "before-you-hire-your-next-ai-engineer-who-is-leading-your-enterprise-ai" and (urlsplit(video["url"]).netloc == "airibeiro.github.io" or urlsplit(poster["url"]).netloc == "airibeiro.github.io"):
        if (video["sha256"] != "10971877f74e3b2c2cba722ef260fb1b62e2c4ea3c2c568313e7ed03fbfac549"
            or poster["sha256"] != "24d721d86696326b380cc11cb7e1d271089cba7b595cd8b65e4a1e522f33458b"
            or video["bytes"] != 3942344 or poster.get("bytes") != 77643):
            return ""
    video_url = escape(video["url"], quote=True)
    poster_url = escape(poster["url"], quote=True)
    label = escape(str(manifest.get("video_title") or "Enterprise AI explained"), quote=True)
    return (
        ARTICLE_VIDEO_CSS
        + '<section class="article-video-feature" data-analytics-section="article-video-explainer">'
        + '<div class="article-video-container">'
        + '<p class="article-video-kicker">Watch the article explained</p>'
        + '<h2 id="article-video-heading">' + escape(str(manifest.get("player_heading") or "From AI demonstration to dependable business work")) + '</h2>'
        + '<div class="article-video-frame"><video controls playsinline preload="metadata" '
          'width="1920" height="1080" aria-label="' + label + '" '
          'poster="' + poster_url + '">'
        + '<source src="' + video_url + '" type="video/mp4">'
        + 'Your browser cannot play this video. '
          '<a href="' + video_url + '" target="_blank" rel="noopener noreferrer">Open the video</a>.'
        + '</video></div>'
        + '<p class="article-video-credit">Narrated by Jair Ribeiro · Captions included · '
          '<a href="' + video_url + '" target="_blank" rel="noopener noreferrer">Open video separately</a></p>'
        + '</div></section>'
    )
