from __future__ import annotations

"""Runtime-safe photography loader.

The public site prefers selected photography in /images, but every image is
validated before it is exposed to page modules. If a repository derivative is
missing or damaged, fall back to the last-known-valid media already stored in
the repository. This keeps media failures from becoming broken browser images.
"""

import base64
import io
import zipfile
from functools import lru_cache
from pathlib import Path

from PIL import Image

import site_assets as assets

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "images"


def _mime(blob: bytes) -> str:
    if blob.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if blob.startswith(b"RIFF") and blob[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def _blob_uri(blob: bytes) -> str:
    if not blob:
        return ""
    try:
        with Image.open(io.BytesIO(blob)) as image:
            image.verify()
    except (OSError, ValueError, SyntaxError):
        return ""
    return f"data:{_mime(blob)};base64,{base64.b64encode(blob).decode('ascii')}"


def _file_uri(name: str) -> str:
    try:
        return _blob_uri((IMAGE_DIR / name).read_bytes())
    except OSError:
        return ""


@lru_cache(maxsize=1)
def _legacy_media() -> dict[str, bytes]:
    media: dict[str, bytes] = {}

    # Original application media bundle retained in the repository.
    parts = sorted((ROOT / "payload_parts").glob("part_*.b64"))
    if parts:
        try:
            encoded = "".join(p.read_text(encoding="ascii") for p in parts)
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
                for name in bundle.namelist():
                    if name.startswith("assets/") and not name.endswith("/"):
                        media[Path(name).name] = bundle.read(name)
        except (ValueError, zipfile.BadZipFile, OSError):
            pass

    # Higher-quality media bundle used by earlier working deployments.
    hq = ROOT / "hq_media.zip"
    if hq.exists():
        try:
            with zipfile.ZipFile(hq) as bundle:
                for name in bundle.namelist():
                    if not name.endswith("/"):
                        media[Path(name).name] = bundle.read(name)
        except (zipfile.BadZipFile, OSError):
            pass

    # Standalone panel asset assembled from text-safe repository parts.
    panel_parts = sorted((ROOT / "asset_parts").glob("panel.webp.part*.b64"))
    if panel_parts:
        try:
            encoded = "".join(p.read_text(encoding="ascii") for p in panel_parts)
            media["panel.webp"] = base64.b64decode(encoded)
        except (ValueError, OSError):
            pass

    return media


def _fallback_uri(*names: str) -> str:
    media = _legacy_media()
    for name in names:
        uri = _blob_uri(media.get(name, b""))
        if uri:
            return uri
    return ""


# Prefer the curated derivatives. The fallbacks below are the same repository
# media that kept the site working before the derivative-only loader was added.
hero = _file_uri("jair-hero-executive.webp") or _fallback_uri(
    "panel.webp", "impact19-header.png", "career-collage.webp"
)
panel = _file_uri("jair-panel-dialogue.webp") or _fallback_uri(
    "panel.webp", "impact19-header.png", "career-collage.webp"
)
thinking = (
    _file_uri("jair-ai-panel.webp")
    or _file_uri("jair-thinking-panel.webp")
    or _fallback_uri("panel.webp", "impact19-header.png", "career-collage.webp")
)
ai_panel = _file_uri("jair-ai-panel.webp") or panel or hero
about = _file_uri("jair-about-bw.webp") or _fallback_uri(
    "site-icon.png", "panel.webp", "impact19-header.png"
) or hero

# Always replace the unvalidated URIs created by site_assets when we have a
# verified source. Optional delivery patches may still replace these later with
# verified higher-resolution derivatives.
if hero:
    assets.HERO_URI = hero
    assets.PROFILE_URI = hero
if panel:
    assets.PANEL_DIALOGUE_URI = panel
    assets.SPEAKING_URI = panel
if thinking:
    assets.THINKING_PANEL_URI = thinking
if ai_panel:
    assets.AI_PANEL_URI = ai_panel
    assets.WORKSHOP_URI = ai_panel
if about:
    assets.ABOUT_BW_URI = about
