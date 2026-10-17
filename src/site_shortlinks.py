"""Permanent short article links, served by a static first-party Pages bridge.

The Streamlit Cloud wrapper does not reliably expand a root ?go= alias;
registered public links instead redirect from GitHub Pages directly to the
native Streamlit article URL with complete channel attribution. Registered
codes never change owners and do not require a third-party URL shortener.
"""
from __future__ import annotations

from site_campaign_links import CHANNEL_MEDIA, PUBLIC_SITE, make_distribution_link

SHORT_BASE = "https://airibeiro.github.io/careersite/go"

# Author-curated immutable aliases. Never recycle a code for another destination.
# Channel is part of the code, allowing disjoint source attribution.
_SHORT_ARTICLES: dict[str, str] = {
    "d": "ai-is-turning-data-definitions-into-a-leadership-problem",
    "e": "if-ai-does-the-routine-work-how-will-we-develop-the-next-experts",
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
    return f"{SHORT_BASE}/{prefix}{suffix}/"

def registered_short_links() -> tuple[tuple[str, str, str, str], ...]:
    """Enumerate code, article slug, channel, and immutable tracked target.

    Used by GitHub Pages publishing, tests, and the editorial distribution
    workflow. Only pre-registered article/channel pairs can produce a URL.
    """
    rows: list[tuple[str, str, str, str]] = []
    for prefix, slug in sorted(_SHORT_ARTICLES.items()):
        for suffix, channel in _SHORT_CHANNELS.items():
            target = make_distribution_link(
                f"{PUBLIC_SITE}/?page=thinking&article={slug}",
                channel=channel, campaign="thinking", content=slug, role="article",
            )
            rows.append((prefix + suffix, slug, channel, target))
    return tuple(rows)

