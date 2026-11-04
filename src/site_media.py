from __future__ import annotations

"""Publish curated public photography through the repository CDN, independent of the Streamlit application's ASGI media routes."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

import site_assets as assets

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "images"
PUBLIC_IMAGE_BASE = "https://raw.githubusercontent.com/AIribeiro/careersite/main/images"


@lru_cache(maxsize=64)
def _uri(name: str, max_width: int = 1280) -> str:
    """Return a browser-cacheable URL that does not depend on app-side routes."""
    path = IMAGE_DIR / name
    if not path.is_file():
        return ""
    try:
        version = sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""
    return f"{PUBLIC_IMAGE_BASE}/{quote(name, safe='/')}?v={version}"

# Curated page-to-image mapping. The intent is to reinforce the message of each
# page with authentic evidence of executive presence, facilitation and thought
# leadership rather than treating photography as decoration.
hero = _uri("54907620908_f7c872f825_o.jpg", 1280)
workshop = _uri("IMG_0777.jpg", 1280)
ai_panel = _uri("54549047980_f668a9ffde_o Copy.JPG", 960)
panel_dialogue = _uri("1700157848740.jpg", 1280)
thinking = _uri("IMG_8281.jpg", 960)
portrait = _uri("pixelup_1683528862014.jpg", 960)
contact = _uri("profile_red_bg.jpg.jpg", 960)
brand_icon = _uri("profile_red_bg.jpg.jpg", 160)
presence_thinkers360 = _uri("presence_thinkers360_top50.png", 640)
presence_global_ambassador = _uri("presence_global_ai_ambassador.jpg", 640)
presence_ai_learning = _uri("presence_ai_learning_sessions.jpg", 640)
presence_dfm_2023 = _uri("presence_digitalfirst_2023_cover.jpg", 640)
eitca_eu_banner = _uri("eitca_eu_banner.webp", 640)
openai_ai_leadership = _uri("credentials/openai_ai_leadership_premium.jpg", 640)
databricks_genai_fundamentals_badge = _uri("credentials/databricks_genai_fundamentals.png", 640)
microsoft_leadership_innovation_diploma = _uri("credentials/microsoft_leadership_innovation_diploma.png", 640)
hbr_business_savvy_diploma = _uri("credentials/hbr_business_savvy_2026.webp", 640)
credly_cognitive_practitioner = _uri("credly/cognitive_practitioner.png", 640)
credly_ai_agents_rag_langchain = _uri("credly/ai_agents_rag_langchain.png", 640)
credly_genai_product_managers = _uri("credly/genai_product_managers.png", 640)
credly_genai_foundation_models = _uri("credly/genai_foundation_models.png", 640)
credly_data_privacy = _uri("credly/data_privacy_fundamentals.png", 640)
credly_design_thinking_cocreator = _uri("credly/enterprise_design_thinking_cocreator.png", 640)
credly_azure_ai = _uri("credly/azure_ai_fundamentals.png", 640)
credly_azure_data = _uri("credly/azure_data_fundamentals.png", 640)

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
