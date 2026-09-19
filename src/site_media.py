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


def _base64_uri_parts(directory: str, mime: str = "image/webp") -> str:
    """Reassemble a repository-stored base64 asset from ordered text parts."""
    folder = IMAGE_DIR / directory
    try:
        parts = sorted(folder.glob("part*.txt"))
        payload = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    except OSError:
        return ""
    return f"data:{mime};base64,{payload}" if payload else ""


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
presence_thinkers360 = _uri("presence_thinkers360_top50.png")
presence_global_ambassador = _uri("presence_global_ai_ambassador.jpg")
presence_ai_learning = _uri("presence_ai_learning_sessions.jpg")
eitca_eu_banner = _base64_uri_parts("eitca_eu_banner_1280")

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
