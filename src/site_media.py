from __future__ import annotations

"""Load and prepare the curated production photography for high-quality display."""

import base64
import io
import zipfile
from pathlib import Path

from PIL import Image, ImageFilter

import site_assets as assets

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "assets" / "site_photos_bundle"

# The source bundle is intentionally compact. These targets correspond to the
# largest useful display sizes in the site layout and avoid asking the browser
# to enlarge compressed source pixels on high-DPI screens.
DISPLAY_TARGETS: dict[str, int] = {
    "hero.avif": 1600,
    "keynote.avif": 1600,
    "ai-panel.avif": 1600,
    "thinking.avif": 1200,
    "portrait.avif": 1000,
}


def _load_bundle() -> dict[str, bytes]:
    media: dict[str, bytes] = {}
    parts = sorted(BUNDLE_DIR.glob("part_*.b64"))
    if not parts:
        return media
    try:
        encoded = "".join(p.read_text(encoding="ascii") for p in parts)
        payload = base64.b64decode(encoded, validate=True)
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


def _prepare_for_display(blob: bytes, source_name: str) -> bytes:
    """Reduce visible compression grain and create a clean high-DPI WebP.

    This deliberately does not invent detail. A very light smoothing pass is
    applied before Lanczos resampling, followed by restrained sharpening after
    resize. The result prevents another aggressive lossy encode from becoming
    visible in faces, gradients and dark backgrounds.
    """
    if not blob:
        return b""
    try:
        with Image.open(io.BytesIO(blob)) as source:
            image = source.convert("RGB")

        # Sub-pixel smoothing suppresses block/ringing noise without producing
        # the waxy look of a heavy denoise filter.
        image = image.filter(ImageFilter.GaussianBlur(radius=0.22))

        target_width = DISPLAY_TARGETS.get(source_name, image.width)
        if image.width < target_width:
            scale = target_width / image.width
            target_size = (target_width, max(1, round(image.height * scale)))
            image = image.resize(target_size, Image.Resampling.LANCZOS)

        image = image.filter(
            ImageFilter.UnsharpMask(radius=0.55, percent=32, threshold=4)
        )

        rendered = io.BytesIO()
        image.save(rendered, format="WEBP", quality=94, method=6)
        return rendered.getvalue()
    except (OSError, ValueError, SyntaxError):
        return blob


def _uri(media: dict[str, bytes], name: str) -> str:
    blob = _prepare_for_display(media.get(name, b""), name)
    if not blob:
        return ""
    return f"data:image/webp;base64,{base64.b64encode(blob).decode('ascii')}"


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
