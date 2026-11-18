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


# Use Streamlit's documented static-media handler. Custom ASGI paths can be
# intercepted by the branded frame/proxy and return non-video content.
STATIC_MEDIA_ORIGIN = "https://jairribeiro-ai.streamlit.app"
GITHUB_MEDIA_ROOT = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/"
    "static/briefing-videos"
)


def _url(asset_name: str) -> str:
    version = MEDIA_SHA256[asset_name][:12]
    return (
        f"{STATIC_MEDIA_ORIGIN}/app/static/briefing-videos/"
        f"{BRIEFING_VIDEO_SLUG}/{asset_name}?v={version}"
    )


def _backup_url() -> str:
    return f"{GITHUB_MEDIA_ROOT}/{BRIEFING_VIDEO_SLUG}/preview.mp4"


def render_briefing_video_preview(slug: str) -> str:
    """Compact, no-autoplay video placed inside the editorial text column."""
    if (public_preview_media_path(slug, "preview.mp4") is None or
            public_preview_media_path(slug, "poster.jpg") is None):
        return ""
    return (
        PREVIEW_VIDEO_CSS
        + '<section class="briefing-preview-video" data-analytics-section="briefing-public-video" '
          'aria-labelledby="briefing-preview-video-title">'
        '<span class="eyebrow" id="briefing-preview-video-title">Watch the executive explainer · 1 min 45 sec</span>'
        '<div class="briefing-preview-video-player">'
        '<video controls playsinline preload="metadata" width="1920" height="1080" '
        'aria-label="Scaling AI Across the Enterprise: executive explainer narrated by Jair Ribeiro" '
        'poster="' + _url("poster.jpg") + '">'
        '<source src="' + _url("preview.mp4") + '" type="video/mp4">'
        '<source src="' + _backup_url() + '" type="video/mp4">'
        '<p class="briefing-video-fallback">Your browser cannot play the embedded video. '
        '<a href="' + _url("preview.mp4") + '" target="_blank" rel="noopener">Open the video in a new tab</a>.</p>'
        '</video></div>'
        '<p class="briefing-video-credit">Narrated by Jair Ribeiro · Captions included · '
        '<a href="' + _url("preview.mp4") + '" target="_blank" rel="noopener">Open video separately</a></p>'
        '</section>'
    )
