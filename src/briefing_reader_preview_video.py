"""Public, source-locked media for the enterprise AI scaling briefing.

The video supplements only the anonymous public preview. It does not modify
the CMS article body, approved infographic, or reader access decisions.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

BRIEFING_VIDEO_SLUG = "scaling-ai-across-the-enterprise-reuse-and-change"
MEDIA_DIR = (Path(__file__).resolve().parents[1] / "static" / "briefing-videos" /
             BRIEFING_VIDEO_SLUG)
MEDIA_SHA256 = {
    "preview.mp4": "137931fe989d415c246522c56bc42b883e3d4eec32c3a972a3b92d7637d417b9",
    "poster.jpg": "17f503e0cde04d77a57bef7647c86cb93344bad01fd1cbaed7427162ad44136e",
}

PREVIEW_VIDEO_CSS = """<style>
.site .briefing-preview-video{margin:clamp(34px,5vw,62px) 0 0;padding:clamp(21px,3.4vw,36px);background:#0d2234;color:#fff;border:1px solid #35546a;box-shadow:0 18px 40px rgba(13,32,49,.14)}
.site .briefing-preview-video .eyebrow{color:#55d0d7!important;letter-spacing:.13em;font-size:10px;font-weight:800}
.site .briefing-preview-video h2{color:#fff;font:500 clamp(25px,3.3vw,38px)/1.16 Georgia,serif;letter-spacing:-.02em;margin:11px 0 12px}
.site .briefing-preview-video .briefing-video-description{max-width:780px;color:#cbd6df;font:400 clamp(13px,1.5vw,15px)/1.7 Arial,sans-serif;margin:0 0 22px}
.site .briefing-preview-video-player{aspect-ratio:16/9;width:100%;overflow:hidden;background:#061522;border:1px solid rgba(255,255,255,.18)}
.site .briefing-preview-video-player video{display:block;width:100%;height:100%;object-fit:contain;background:#061522}
.site .briefing-video-credit{margin:12px 0 0;color:#b5c6d2;font:600 11px/1.65 Arial,sans-serif}
.site .briefing-video-fallback{color:#fff;font-size:12px}
.site .briefing-video-fallback a{color:#eac3a3!important}
@media(max-width:600px){.site .briefing-preview-video{padding:18px 14px 22px;margin-top:30px}.site .briefing-preview-video .briefing-video-description{margin-bottom:15px}}
</style>"""


@lru_cache(maxsize=4)
def _matches_approved_sha(path: str, expected: str) -> bool:
    try:
        candidate = Path(path)
        if not candidate.is_file():
            return False
        digest = sha256()
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(256 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest() == expected
    except (OSError, ValueError):
        return False


def public_preview_media_path(slug: str, asset_name: str) -> Path | None:
    """Return only known, intact first-party assets; reject traversal and drafts."""
    if slug != BRIEFING_VIDEO_SLUG or asset_name not in MEDIA_SHA256:
        return None
    path = MEDIA_DIR / asset_name
    return path if _matches_approved_sha(str(path), MEDIA_SHA256[asset_name]) else None


def _url(asset_name: str) -> str:
    version = MEDIA_SHA256[asset_name][:12]
    return f"/briefing-preview-video/{BRIEFING_VIDEO_SLUG}/{asset_name}?v={version}"


def render_briefing_video_preview(slug: str) -> str:
    """Full-width, no-autoplay native video placed before the member CTA."""
    if (public_preview_media_path(slug, "preview.mp4") is None or
            public_preview_media_path(slug, "poster.jpg") is None):
        return ""
    return (
        PREVIEW_VIDEO_CSS
        + '<section class="briefing-preview-video" data-analytics-section="briefing-public-video" '
          'aria-labelledby="briefing-preview-video-title">'
        '<span class="eyebrow">Executive explainer · 1 min 45 sec</span>'
        '<h2 id="briefing-preview-video-title">One AI success. Two different outcomes.</h2>'
        '<p class="briefing-video-description">Why the same AI solution can improve work in one team '
        'while creating new delays in another. This short briefing introduces the decisions '
        'leaders need to make before expanding across the enterprise.</p>'
        '<div class="briefing-preview-video-player">'
        '<video controls playsinline preload="metadata" width="1920" height="1080" '
        'aria-label="Scaling AI Across the Enterprise: executive explainer narrated by Jair Ribeiro" '
        'poster="' + _url("poster.jpg") + '">'
        '<source src="' + _url("preview.mp4") + '" type="video/mp4">'
        '<p class="briefing-video-fallback">Your browser cannot play this video. '
        '<a href="' + _url("preview.mp4") + '">Open the video</a>.</p>'
        '</video></div>'
        '<p class="briefing-video-credit">Narrated by Jair Ribeiro · English subtitles included · '
        'Full decision framework in the briefing below</p>'
        '</section>'
    )
