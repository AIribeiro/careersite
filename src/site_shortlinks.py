"""First-party compact article links. No external shortener or user-level tracking.

Each registered alias expands to the existing native Streamlit article route with
the complete, evidence-based distribution tags before analytics is mounted.
Unregistered aliases do not change routing or attribution.
"""
from __future__ import annotations

from site_campaign_links import CHANNEL_MEDIA, PUBLIC_SITE

# Author-curated immutable aliases. Never recycle a code for another destination.
# Channel is part of the code, allowing disjoint source attribution.
_SHORT_ARTICLES: dict[str, str] = {
    "d": "ai-is-turning-data-definitions-into-a-leadership-problem",
}
_SHORT_CHANNELS: dict[str, str] = {
    "l": "linkedin",
    "x": "x",
    "t": "threads",
    "f": "facebook",
    "w": "whatsapp",
}
_ARTICLE_PREFIX: dict[str, str] = {slug: prefix for prefix, slug in _SHORT_ARTICLES.items()}
_CHANNEL_SUFFIX: dict[str, str] = {name: suffix for suffix, name in _SHORT_CHANNELS.items()}


def expand_shortlink(code: object) -> dict[str, str] | None:
    """Expand only a preapproved short code, with no arbitrary redirect URLs."""
    if not isinstance(code, str):
        return None
    code = code.strip().lower()
    if len(code) != 2:
        return None
    slug = _SHORT_ARTICLES.get(code[0])
    channel = _SHORT_CHANNELS.get(code[1])
    if not slug or not channel:
        return None
    return {
        "page": "thinking",
        "article": slug,
        "source": channel,
        "role": "article",
        "utm_source": channel,
        "utm_medium": CHANNEL_MEDIA[channel],
        "utm_campaign": "thinking",
        "utm_content": slug,
    }


def short_article_link(slug: str, channel: str, *, campaign: str = "thinking", role: str = "article") -> str | None:
    """Return an owned short link only if its fixed destination and tags match."""
    prefix = _ARTICLE_PREFIX.get(str(slug).strip().lower())
    suffix = _CHANNEL_SUFFIX.get(str(channel).strip().lower())
    if prefix is None or suffix is None or campaign != "thinking" or role != "article":
        return None
    return f"{PUBLIC_SITE}/?go={prefix}{suffix}"
