"""Canonical first-party portfolio distribution links.

Campaign tags are asserted only on links deliberately generated for a known
distribution channel. Browser referrers and existing untagged visits are never
fabricated or retroactively rewritten.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PUBLIC_SITE = "https://jairribeiro-ai.streamlit.app"
CHANNEL_MEDIA = {
    "linkedin": "social",
    "threads": "social",
    "x": "social",
    "facebook": "social",
    "whatsapp": "messaging",
    "email": "email",
    "cv": "document",
    "outreach": "outreach",
    "application": "referral",
}
_ALIASES = {"thre": "threads", "twitter": "x", "fb": "facebook"}
_TRACKING_KEYS = {"source", "src", "utm_source", "utm_medium", "utm_campaign",
                  "utm_content"}
_CAMPAIGN_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,99}$")


def canonical_channel(channel: str) -> str:
    name = str(channel).strip().lower()
    name = _ALIASES.get(name, name)
    if name not in CHANNEL_MEDIA:
        raise ValueError("Unsupported portfolio distribution channel.")
    return name


def canonical_campaign(value: str) -> str:
    name = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if not _CAMPAIGN_RE.fullmatch(name):
        raise ValueError("Campaign must be a 1-100 character non-personal label.")
    return name


def make_distribution_link(
    destination: str,
    *,
    channel: str,
    campaign: str,
    content: str = "",
    role: str = "",
) -> str:
    """Build one truthful channel-tagged URL to the real portfolio destination.

    Preserve page and article identifiers; replace conflicting old campaign
    parameters. No arbitrary external destinations or personal identifiers.
    """
    channel = canonical_channel(channel)
    campaign = canonical_campaign(campaign)
    target = urlsplit(str(destination).strip())
    if target.scheme != "https" or target.hostname != "jairribeiro-ai.streamlit.app" \
            or target.port is not None or target.username is not None \
            or target.password is not None:
        raise ValueError("Destination must be the public portfolio site.")
    if target.path not in ("", "/", "/~/+/"):
        raise ValueError("Unsupported portfolio destination path.")
    original = parse_qsl(target.query, keep_blank_values=False)
    params = [(key, val) for key, val in original
              if key.lower() not in _TRACKING_KEYS and key.lower() != "role"]
    params.extend((
        ("source", channel),
        ("utm_source", channel),
        ("utm_medium", CHANNEL_MEDIA[channel]),
        ("utm_campaign", campaign),
    ))
    if content:
        clean = str(content).strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,99}", clean):
            raise ValueError("Content tag must be a short non-personal slug.")
        params.append(("utm_content", clean))
    if role:
        clean_role = canonical_campaign(role)
        params.append(("role", clean_role))
    return urlunsplit(("https", target.netloc, target.path or "/", urlencode(params), ""))


def article_distribution_link(
    article_url: str, channel: str, *, campaign: str = "thinking",
    content_slug: str = "",
) -> str:
    return make_distribution_link(
        article_url, channel=channel, campaign=campaign, content=content_slug,
    )
