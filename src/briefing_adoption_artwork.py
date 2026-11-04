from __future__ import annotations

"""Local, self-contained Executive AI Adoption images.

Streamlit Cloud may serve the portfolio from different runtime paths. A static
HTTP URL can work in a local test yet break in the published st.html reader.
Use a bounded, cached, in-document data URI instead. No HTTP call is made
during page rendering and only this briefing's image is loaded on demand.
"""

from functools import lru_cache
from pathlib import Path
import base64

_ASSETS = Path(__file__).resolve().parents[1] / "static"
_IMAGES = {
    "desktop": (
        "briefing-ai-adoption-studio.webp",
        "briefing-ai-adoption-studio.png",
    ),
    "mobile": (
        "briefing-ai-adoption-studio-mobile.webp",
        "briefing-ai-adoption-studio-mobile.png",
    ),
    "thumbnail": (
        "briefing-ai-adoption-studio-thumbnail.webp",
        "briefing-ai-adoption-studio.webp",
        "briefing-ai-adoption-studio.png",
    ),
}


@lru_cache(maxsize=3)
def artwork_data_uri(variant: str) -> str:
    """Return a cached, verified data URI with no browser/network dependency."""
    if variant not in _IMAGES:
        return ""
    for name in _IMAGES[variant]:
        try:
            data = (_ASSETS / name).read_bytes()
        except OSError:
            continue
        if not (1024 < len(data) < 3_000_000):
            continue
        if name.endswith(".webp"):
            if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
                continue
            mime = "image/webp"
        elif name.endswith(".png"):
            if not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
                continue
            mime = "image/png"
        else:
            continue
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    return ""
