"""Permanent short article links, served by a static first-party Pages bridge.

The Streamlit Cloud wrapper does not reliably expand a root ?go= alias;
registered public links instead redirect from GitHub Pages directly to the
native Streamlit article URL with complete channel attribution. Registered
codes never change owners and do not require a third-party URL shortener.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

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
    rows.extend((code, slug, channel, target) for code, slug, channel, _campaign, _story, target in _weekly_ai_shortlinks())
    return tuple(rows)

_WAI_REGISTRY = Path(__file__).with_name("weekly_ai_shortlink_registry.json")


def _weekly_ai_shortlinks() -> tuple[tuple[str, str, str, str, str, str], ...]:
    """Registered (code, slug, channel, campaign, story, tracked target).

    Only published, source-verified issues belong in this author-curated file.
    The Pages publisher materializes one static redirect for every code.
    """
    if not _WAI_REGISTRY.exists():
        return ()
    payload = json.loads(_WAI_REGISTRY.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str, str, str, str]] = []
    seen: set[str] = set()
    for edition in payload["editions"]:
        year, week = int(edition["iso_year"]), int(edition["iso_week"])
        date.fromisocalendar(year, week, 1)  # ISO year/week boundary validation
        slug = str(edition["slug"])
        if not re.fullmatch(r"weekly-ai-\\d{4}-\\d{2}-\\d{2}", slug):
            raise ValueError("Invalid Weekly AI publication slug")
        keys = list(edition["story_keys"])
        if not 3 <= len(keys) <= 5 or len(keys) != len(set(keys)):
            raise ValueError("Weekly AI needs 3–5 distinct verified story keys")
        campaign = f"weekly_ai_{year}_w{week}"
        for position, story in enumerate(keys, 1):
            if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,79}", story):
                raise ValueError("Invalid Weekly AI story key")
            for suffix, channel in (("x", "x"), ("t", "threads")):
                code = f"w{year}{week:02d}{position}{suffix}"
                target = make_distribution_link(
                    f"{PUBLIC_SITE}/?page=thinking&article={slug}",
                    channel=channel, campaign=campaign, content=story, role="weeklyai",
                )
                rows.append((code, slug, channel, campaign, story, target))
        code = f"w{year}{week:02d}0l"
        linkedin_campaign = f"{campaign}_wednesday"
        target = make_distribution_link(
            f"{PUBLIC_SITE}/?page=thinking&article={slug}",
            channel="linkedin", campaign=linkedin_campaign,
            content="weekly_perspective", role="weeklyai",
        )
        rows.append((code, slug, "linkedin", linkedin_campaign, "weekly_perspective", target))
        for code, *_ in rows:
            if code in seen:
                raise ValueError(f"Duplicate permanent Weekly AI short code: {code}")
            seen.add(code)
    return tuple(rows)


def weekly_ai_short_link(
    slug: str, channel: str, *, campaign: str, content: str, role: str = "weeklyai"
) -> str | None:
    """Never invent an alias: return only an exact registered source/campaign/story."""
    if role != "weeklyai":
        return None
    for code, row_slug, row_channel, row_campaign, row_content, _target in _weekly_ai_shortlinks():
        if (slug, channel, campaign, content) == (
            row_slug, row_channel, row_campaign, row_content
        ):
            return f"{SHORT_BASE}/{code}/"
    return None

