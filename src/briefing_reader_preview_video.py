"""Source-locked per-briefing video manifests for anonymous public previews.

Only a reviewed, owner-approved manifest AND byte-for-byte matching local
media files authorize a player. A missing or altered file fails closed.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

# Legacy constants retained for existing callers and historical tests.
BRIEFING_VIDEO_SLUG = "scaling-ai-across-the-enterprise-reuse-and-change"
MEDIA_SHA256 = {
    "preview.mp4": "137931fe989d415c246522c56bc42b883e3d4eec32c3a972a3b92d7637d417b9",
    "poster.jpg": "17f503e0cde04d77a57bef7647c86cb93344bad01fd1cbaed7427162ad44136e",
}
MEDIA_ROOT = Path(__file__).resolve().parents[1] / "static" / "briefing-videos"
MEDIA_DIR = MEDIA_ROOT / BRIEFING_VIDEO_SLUG

PREVIEW_VIDEO_CSS = """<style>
/* Inline editorial video. The surrounding article column sets its width. */
.site .briefing-preview-video{width:100%;max-width:100%;box-sizing:border-box;margin:0 0 clamp(25px,3vw,38px);padding:0;background:transparent;color:#173348;border:0;box-shadow:none}
.site .briefing-preview-video .eyebrow{display:block;margin:0 0 12px;color:#a05c36!important;font:850 10px/1.5 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase}
.site .briefing-preview-video-player{aspect-ratio:16/9;width:100%;overflow:hidden;background:#061522;border:1px solid #d6d1c8}
.site .briefing-preview-video-player video{display:block;width:100%;height:100%;object-fit:contain;background:#061522}
.site .briefing-preview-copy .briefing-video-credit{margin:8px 0 0;color:#65717a;font:400 10px/1.6 Georgia,"Times New Roman",serif;letter-spacing:.02em}
.site .briefing-video-fallback{color:#fff;font-size:12px}
.site .briefing-video-fallback a{color:#eac3a3!important}
.site .briefing-video-credit a{color:#975630!important;text-decoration:underline!important}
@media(max-width:600px){.site .briefing-preview-video{margin-bottom:27px}.site .briefing-preview-video .eyebrow{margin-bottom:9px}}
</style>"""

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_DIGEST = re.compile(r"[a-f0-9]{64}\Z")
_ALLOWED_ASSETS = {"preview.mp4": "web", "poster.jpg": "poster"}

@lru_cache(maxsize=64)
def _approved_manifest(slug: str) -> dict | None:
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        return None
    manifest_path = MEDIA_ROOT / slug / "video-manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        if (payload.get("schema_version") != 1
            or payload.get("slug") != slug
            or payload.get("status") != "approved"
            or payload.get("approved_by_owner") is not True
            or not _DIGEST.fullmatch(str(payload.get("article_fingerprint", "")))):
            return None
        for filename, part in _ALLOWED_ASSETS.items():
            entry = payload.get(part)
            if (not isinstance(entry, dict)
                or entry.get("file") != filename
                or not _DIGEST.fullmatch(str(entry.get("sha256", "")))):
                return None
        if not isinstance(payload.get("duration_seconds"), (int, float)):
            return None
        if not 1 <= payload["duration_seconds"] <= 600:
            return None
        return payload
    except (OSError, ValueError, TypeError):
        return None

@lru_cache(maxsize=64)
def _matches_approved_sha(path: str, expected: str) -> bool:
    try:
        digest = sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(256 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest() == expected
    except (OSError, ValueError):
        return False

def public_preview_media_path(slug: str, asset_name: str) -> Path | None:
    """Only allow two approved media basenames in an audited slug folder."""
    part = _ALLOWED_ASSETS.get(asset_name)
    manifest = _approved_manifest(slug)
    if not part or not manifest:
        return None
    expected = manifest[part]["sha256"]
    candidate = MEDIA_ROOT / slug / asset_name
    return candidate if _matches_approved_sha(str(candidate), expected) else None

# The static handler (not the intercepted legacy ASGI route) serves real MP4.
STATIC_MEDIA_ORIGIN = "https://jairribeiro-ai.streamlit.app"
GITHUB_MEDIA_ROOT = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/"
    "static/briefing-videos"
)

def _url(slug: str, name: str, digest: str) -> str:
    return (
        f"{STATIC_MEDIA_ORIGIN}/app/static/briefing-videos/"
        f"{slug}/{name}?v={digest[:12]}"
    )

def render_briefing_video_preview(slug: str, *, source_fingerprint: str | None = None) -> str:
    """One inline player, only for owner-approved, source-matching local assets."""
    manifest = _approved_manifest(slug)
    if manifest is None:
        return ""
    if source_fingerprint is not None and source_fingerprint != manifest["article_fingerprint"]:
        return ""
    if (public_preview_media_path(slug, "preview.mp4") is None
        or public_preview_media_path(slug, "poster.jpg") is None):
        return ""
    video = _url(slug, "preview.mp4", manifest["web"]["sha256"])
    poster = _url(slug, "poster.jpg", manifest["poster"]["sha256"])
    backup = f"{GITHUB_MEDIA_ROOT}/{slug}/preview.mp4"
    total = int(round(manifest["duration_seconds"]))
    label = f"{total // 60} min {total % 60:02d} sec"
    title = escape(str(manifest.get("title") or "Executive AI Briefing"), quote=True)
    return (
        PREVIEW_VIDEO_CSS
        + '<section class="briefing-preview-video" data-analytics-section="briefing-public-video" '
          'aria-labelledby="briefing-preview-video-title">'
        + '<span class="eyebrow" id="briefing-preview-video-title">Watch the executive explainer · '
        + label + '</span>'
        + '<div class="briefing-preview-video-player">'
        + '<video controls playsinline preload="metadata" width="1920" height="1080" '
        + 'aria-label="' + title + ': executive explainer narrated by Jair Ribeiro" '
        + 'poster="' + poster + '">'
        + '<source src="' + video + '" type="video/mp4">'
        + '<source src="' + backup + '" type="video/mp4">'
        + '<p class="briefing-video-fallback">Your browser cannot play the embedded video. '
        + '<a href="' + video + '" target="_blank" rel="noopener">Open the video in a new tab</a>.</p>'
        + '</video></div>'
        + '<p class="briefing-video-credit">Narrated by Jair Ribeiro · Captions included · '
        + '<a href="' + video + '" target="_blank" rel="noopener">Open video separately</a></p>'
        + '</section>'
    )
