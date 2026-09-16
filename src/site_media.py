from __future__ import annotations

"""Bind curated production photography directly from the repository /images folder."""

import base64
import mimetypes
from pathlib import Path

import site_assets as assets

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "images"


def _uri(name: str) -> str:
    """Return the original repository image bytes without recompression."""
    path = IMAGE_DIR / name
    try:
        blob = path.read_bytes()
    except OSError:
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(blob).decode('ascii')}"


# Curated page-to-image mapping. The intent is to reinforce the message of each
# page with authentic evidence of executive presence, facilitation and thought
# leadership rather than treating photography as decoration.
hero = _uri("54907620908_f7c872f825_o.jpg")
workshop = _uri("IMG_0777.jpg")
ai_panel = _uri("54549047980_f668a9ffde_o Copy.JPG")
panel_dialogue = _uri("1700157848740.jpg")
thinking = _uri("IMG_8281.jpg")
portrait = _uri("pixelup_1683528862014.jpg")
contact = _uri("profile_red_bg.jpg.jpg")
brand_icon = contact

if hero:
    assets.HERO_URI = hero
    assets.PROFILE_URI = hero
if workshop:
    assets.WORKSHOP_URI = workshop
if ai_panel:
    assets.AI_PANEL_URI = ai_panel
if panel_dialogue:
    assets.PANEL_DIALOGUE_URI = panel_dialogue
    assets.SPEAKING_URI = panel_dialogue
if thinking:
    assets.THINKING_PANEL_URI = thinking
if portrait:
    assets.ABOUT_BW_URI = portrait
if contact:
    assets.CONTACT_URI = contact
if brand_icon:
    assets.BRAND_ICON_URI = brand_icon
