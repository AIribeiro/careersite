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

def _assemble_verified_video(slug: str, manifest: dict, target: Path) -> bool:
    """Recreate the approved MP4, never transcode; checks each original byte chunk.

    This is a release-transport fallback for repos whose connected publisher
    limits request size. Only active for manifests explicitly listing chunks.
    Static video response is the reconstructed exact original H.264/AAC MP4.
    """
    import os
    import tempfile
    import shutil

    web = manifest["web"]
    chunks = web.get("chunks")
    if not isinstance(chunks, list) or not (2 <= len(chunks) <= 32):
        return False
    size_expected = web.get("size_bytes")
    if not isinstance(size_expected, int) or size_expected < 10000:
        return False
    directory = MEDIA_ROOT / slug
    total = 0
    sources = []
    try:
        for i, item in enumerate(chunks):
            expected_name = "preview.mp4.part" + f"{i:02d}"
            if (not isinstance(item, dict)
                or item.get("file") != expected_name
                or not _DIGEST.fullmatch(str(item.get("sha256", "")))
                or type(item.get("size_bytes")) is not int
                or not 0 < item["size_bytes"] <= 1024 * 1024):
                return False
            chunk = directory / expected_name
            if not chunk.is_file() or chunk.stat().st_size != item["size_bytes"]:
                return False
            if not _matches_approved_sha(str(chunk), item["sha256"]):
                return False
            sources.append(chunk)
            total += item["size_bytes"]
        if total != size_expected:
            return False
        # Use the same filesystem for atomic replacement; no truncated player.
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".assembling-", suffix=".tmp", dir=directory,
            delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)
            for chunk in sources:
                with chunk.open("rb") as part:
                    shutil.copyfileobj(part, tmp, length=256 * 1024)
            tmp.flush()
            os.fsync(tmp.fileno())
        if (tmp_path.stat().st_size != size_expected
            or not _matches_approved_sha(str(tmp_path), web["sha256"])):
            tmp_path.unlink(missing_ok=True)
            return False
        os.replace(tmp_path, target)
        _matches_approved_sha.cache_clear()
        return _matches_approved_sha(str(target), web["sha256"])
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if "tmp_path" in locals():
            tmp_path.unlink(missing_ok=True)


def public_preview_media_path(slug: str, asset_name: str) -> Path | None:
    """Only vetted, source-locked approved media paths; fail closed on mismatch."""
    part = _ALLOWED_ASSETS.get(asset_name)
    manifest = _approved_manifest(slug)
    if not part or not manifest:
        return None
    expected = manifest[part]["sha256"]
    candidate = MEDIA_ROOT / slug / asset_name
    if _matches_approved_sha(str(candidate), expected):
        return candidate
    if asset_name == "preview.mp4" and _assemble_verified_video(slug, manifest, candidate):
        return candidate
    return None

# The static handler (not the intercepted legacy ASGI route) serves real MP4.
STATIC_MEDIA_ORIGIN = "https://jairribeiro-ai.streamlit.app"
GITHUB_MEDIA_ROOT = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/"
    "static/briefing-videos"
)

# Fixed public media origin. The storage object is original, approved H.264/AAC
# bytes, with a versioned filename. No ephemeral Streamlit write or proxy 307
# is required for the browser to play or seek the MP4.
_PUBLIC_VIDEO_STORAGE = (
    "https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/"
    "portfolio-public-videos/executive-briefings/"
)


def _validated_public_video_url(slug: str, manifest: dict) -> str | None:
    """Only an exact, SHA-derived, public media location is permitted."""
    web = manifest.get("web", {})
    if not isinstance(web, dict):
        return None
    digest = web.get("sha256", "")
    if not _DIGEST.fullmatch(str(digest)):
        return None
    expected = (
        f"{_PUBLIC_VIDEO_STORAGE}{slug}/preview-v1-{digest[:8]}.mp4"
    )
    return expected if web.get("public_url") == expected else None


def _url(slug: str, name: str, digest: str) -> str:
    manifest = _approved_manifest(slug)
    if manifest and _validated_public_video_url(slug, manifest):
        if name == "preview.mp4":
            return manifest["web"]["public_url"]
        if name == "poster.jpg":
            # Streamlit Community Cloud currently redirects this poster's
            # /app/static URL to sign-in (HTTP 303). Use the approved public
            # GitHub asset (HTTP 200 image/jpeg) instead.
            return f"{GITHUB_MEDIA_ROOT}/{slug}/poster.jpg?v={digest[:12]}"
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
    # A verified, source-locked public object does not depend on creating
    # preview.mp4 in the Streamlit container (which may be read-only).
    durable = _validated_public_video_url(slug, manifest)
    if (public_preview_media_path(slug, "poster.jpg") is None
        or (not durable and public_preview_media_path(slug, "preview.mp4") is None)):
        return ""
    video = durable or _url(slug, "preview.mp4", manifest["web"]["sha256"])
    poster = _url(slug, "poster.jpg", manifest["poster"]["sha256"])
    # No broken GitHub fallback when the approved binary is stored externally.
    backup = (
        f"{GITHUB_MEDIA_ROOT}/{slug}/preview.mp4"
        if not durable and manifest["web"].get("git_binary_available", True) else None
    )
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
        + ('<source src="' + backup + '" type="video/mp4">' if backup else '')
        + '<p class="briefing-video-fallback">Your browser cannot play the embedded video. '
        + '<a href="' + video + '" target="_blank" rel="noopener">Open the video in a new tab</a>.</p>'
        + '</video></div>'
        + '<p class="briefing-video-credit">Narrated by Jair Ribeiro · Captions included · '
        + '<a href="' + video + '" target="_blank" rel="noopener">Open video separately</a></p>'
        + '</section>'
    )
