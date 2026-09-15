from __future__ import annotations

"""Final public delivery layer for media and the downloadable CV.

This module runs after the legacy runtime patches and before page modules import
asset constants. It deliberately uses verified repository binaries for public
delivery so Streamlit proxy/static-path behaviour cannot corrupt downloads.
"""

import base64
import io
from pathlib import Path

from PIL import Image

import site_assets as assets

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "images"

CV_FILENAME = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
CV_PATH = ROOT / "static" / CV_FILENAME
CV_PUBLIC_URL = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/static/"
    + CV_FILENAME
)


def _webp_uri(name: str) -> str:
    path = IMAGE_DIR / name
    try:
        blob = path.read_bytes()
        with Image.open(io.BytesIO(blob)) as image:
            image.verify()
        return "data:image/webp;base64," + base64.b64encode(blob).decode("ascii")
    except (OSError, ValueError, SyntaxError):
        return ""


def _grayscale_portrait_uri(name: str) -> str:
    """Create a crisp 4:5 editorial portrait from a high-resolution source."""
    path = IMAGE_DIR / name
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            width, height = image.size
            target_ratio = 4 / 5
            current_ratio = width / height
            if current_ratio > target_ratio:
                crop_width = int(height * target_ratio)
                left = max(0, (width - crop_width) // 2)
                image = image.crop((left, 0, left + crop_width, height))
            else:
                crop_height = int(width / target_ratio)
                top = max(0, (height - crop_height) // 2)
                image = image.crop((0, top, width, top + crop_height))
            image = image.convert("L").convert("RGB")
            image.thumbnail((1400, 1750), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            image.save(out, format="WEBP", quality=90, method=6)
        return "data:image/webp;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    except (OSError, ValueError, SyntaxError):
        return ""


hero = _webp_uri("jair-hero-executive.webp")
panel = _webp_uri("jair-panel-dialogue.webp")
ai_panel = _webp_uri("jair-ai-panel.webp")
about = _grayscale_portrait_uri("jair-hero-executive.webp")

# Use only the replacement high-resolution sources. This also corrects the old
# cross-wiring where Thinking used the AI-panel file and AI-panel used dialogue.
if hero:
    assets.HERO_URI = hero
    assets.PROFILE_URI = hero
if panel:
    assets.PANEL_DIALOGUE_URI = panel
    assets.SPEAKING_URI = panel
if ai_panel:
    assets.AI_PANEL_URI = ai_panel
    assets.THINKING_PANEL_URI = ai_panel
    assets.WORKSHOP_URI = ai_panel
if about:
    assets.ABOUT_BW_URI = about

# Keep local bytes available for validation, but deliver the public download from
# GitHub's raw immutable repository content path rather than Streamlit's proxy.
try:
    cv_bytes = CV_PATH.read_bytes()
    if cv_bytes.startswith(b"%PDF") and len(cv_bytes) > 4000:
        assets.CV_BYTES = cv_bytes
except OSError:
    pass
assets.CV_URI = CV_PUBLIC_URL
