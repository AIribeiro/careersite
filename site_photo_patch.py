from __future__ import annotations

"""Validate and expose the curated leadership photography.

The public image set is rebuilt from four specific original conference photos.
This layer maps those derivatives to page roles and deliberately avoids generic
collage, city or legacy-media fallbacks for primary leadership placements.
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
        return "data:image/webp;base64," + base64.b64encode(blob).decode("ascii")
    except (OSError, ValueError, SyntaxError):
        return ""


# Exact editorial mapping.
# Home / enterprise: wide AI-panel conversation.
hero = _uri("jair-hero-executive.webp")
ai_panel = _uri("jair-ai-panel.webp") or hero

# Leadership Impact / speaking: active executive contribution with handheld mic.
workshop = _uri("jair-leadership-workshop.webp")
panel_dialogue = _uri("jair-panel-dialogue.webp") or workshop or hero

# Thinking: tighter conference portrait on the red stage.
thinking = _uri("jair-thinking-panel.webp") or panel_dialogue or hero

# About: vertical seated conference portrait in the grey blazer.
about = _uri("jair-about-bw.webp") or thinking or hero

if hero:
    assets.HERO_URI = hero
    assets.PROFILE_URI = hero
if ai_panel:
    assets.AI_PANEL_URI = ai_panel
if workshop:
    assets.WORKSHOP_URI = workshop
if panel_dialogue:
    assets.PANEL_DIALOGUE_URI = panel_dialogue
    assets.SPEAKING_URI = panel_dialogue
if thinking:
    assets.THINKING_PANEL_URI = thinking
if about:
    assets.ABOUT_BW_URI = about
