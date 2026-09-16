from __future__ import annotations

"""Load the curated production photography from the canonical asset bundle."""

import base64
import io
import zipfile
from pathlib import Path

from PIL import Image

import site_assets as assets

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "assets" / "site_photos_bundle"


def _load_bundle() -> dict[str, bytes]:
    media: dict[str, bytes] = {}
    parts = sorted(BUNDLE_DIR.glob("part_*.b64"))
    if not parts:
        return media
    try:
        encoded = "".join(p.read_text(encoding="ascii") for p in parts)
        payload = base64.b64decode(encoded)
        with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
            for name in bundle.namelist():
                if name.endswith("/"):
                    continue
                blob = bundle.read(name)
                with Image.open(io.BytesIO(blob)) as image:
                    image.verify()
                media[Path(name).name] = blob
    except (OSError, ValueError, zipfile.BadZipFile, SyntaxError):
        return {}
    return media


def _mime(blob: bytes) -> str:
    if blob.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if blob.startswith(b"RIFF") and len(blob) >= 12 and blob[8:12] == b"WEBP":
        return "image/webp"
    if len(blob) >= 12 and blob[4:12] in (b"ftypavif", b"ftypavis"):
        return "image/avif"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "application/octet-stream"


def _uri(media: dict[str, bytes], name: str) -> str:
    blob = media.get(name, b"")
    if not blob:
        return ""
    return f"data:{_mime(blob)};base64,{base64.b64encode(blob).decode('ascii')}"


media = _load_bundle()

hero = _uri(media, "hero.avif")
keynote = _uri(media, "keynote.avif")
ai_panel = _uri(media, "ai-panel.avif")
thinking = _uri(media, "thinking.avif")
portrait = _uri(media, "portrait.avif")

if hero:
    assets.HERO_URI = hero
    assets.PROFILE_URI = hero
if keynote:
    assets.WORKSHOP_URI = keynote
if ai_panel:
    assets.AI_PANEL_URI = ai_panel
    assets.PANEL_DIALOGUE_URI = ai_panel
    assets.SPEAKING_URI = ai_panel
if thinking:
    assets.THINKING_PANEL_URI = thinking
if portrait:
    assets.ABOUT_BW_URI = portrait
