from __future__ import annotations

"""Runtime-safe photography loader.

The public site stores its selected photography in /images. File byte size is not
a quality signal: efficiently encoded WebP files can be small while retaining
adequate pixel dimensions. This module validates actual decodability with Pillow
and then overrides the legacy URI constants before page modules import them.
"""

import base64
import io
from pathlib import Path

from PIL import Image

import site_assets as assets

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "images"


def _uri(name: str) -> str:
    path = IMAGE_DIR / name
    try:
        blob = path.read_bytes()
        with Image.open(io.BytesIO(blob)) as image:
            image.verify()
        return f"data:image/webp;base64,{base64.b64encode(blob).decode('ascii')}"
    except (OSError, ValueError, SyntaxError):
        return ""


hero = _uri("jair-hero-executive.webp")
panel = _uri("jair-panel-dialogue.webp")
thinking = _uri("jair-ai-panel.webp") or _uri("jair-thinking-panel.webp")
ai_panel = _uri("jair-panel-dialogue.webp")
about = _uri("jair-about-bw.webp") or thinking or hero

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
