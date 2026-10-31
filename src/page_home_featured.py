"""A quiet, editorial Home preview of the current Thinking highlight.

Selection is shared with the Thinking CMS landing: latest eligible publication
within 24 hours, otherwise most-read. No independent Home ranking, pinned
article or stale hardcoded title.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import quote


@dataclass(frozen=True)
class HomeArticlePreview:
    slug: str
    title: str
    deck: str
    kind_topic: str
    published_label: str
    read_minutes: int
    href: str
    image_url: str
    image_alt: str


def current_home_article() -> HomeArticlePreview:
    """Resolve the same currently highlighted article as Thinking.

    The legacy Thinking primary is used only when its CMS overlay is absent
    or temporarily unavailable, matching the landing-page fallback.
    """
    from site_cms import (
        _public_reads_or_none,
        article_relative_url,
        cms_feature_image_url,
        fetch_published_articles,
        select_auto_featured_article,
    )

    try:
        published = fetch_published_articles()
    except (RuntimeError, ValueError, TimeoutError):
        published = ()

    if published:
        featured = select_auto_featured_article([article for article in published if article.kind != "Executive Briefing"], _public_reads_or_none())
        if featured is not None:
            return HomeArticlePreview(
                slug=featured.slug,
                title=featured.title,
                deck=featured.subtitle.strip() or featured.excerpt.strip(),
                kind_topic=featured.kind_topic,
                published_label=featured.published_label,
                read_minutes=featured.read_minutes,
                href=article_relative_url(featured),
                image_url=cms_feature_image_url(featured),
                image_alt=featured.header_image_alt or featured.title,
            )

    from thinking_articles import article_by_key, article_relative_url as legacy_relative_url, article_social_image_url
    from thinking_landing import CURRENT_PRIMARY

    legacy = article_by_key(CURRENT_PRIMARY)
    return HomeArticlePreview(
        slug=legacy.slug,
        title=legacy.title,
        deck=legacy.standfirst,
        kind_topic=legacy.kind_topic,
        published_label=legacy.published_label,
        read_minutes=legacy.read_minutes,
        href=legacy_relative_url(legacy),
        image_url=article_social_image_url(legacy),
        image_alt=f"Article cover: {legacy.title}",
    )


def home_featured_article() -> str:
    """Render a premium editorial tile immediately ahead of Home's contact CTA."""
    article = current_home_article()

    title = escape(article.title)
    deck = escape(article.deck)
    kind = escape(article.kind_topic)
    published = escape(article.published_label)
    href = escape(article.href, quote=True)
    image_url = escape(article.image_url, quote=True)
    image_alt = escape(article.image_alt, quote=True)

    image = (
        f'<img src="{image_url}" alt="{image_alt}" loading="lazy" decoding="async">'
        if article.image_url else
        '<span class="home-featured-art-fallback" aria-hidden="true">AI · Data · Leadership</span>'
    )
    return (
        '<section class="section home-featured" data-analytics-section="home-featured-article">'
        '<div class="container">'
        '<div class="home-featured-topline">'
        '<p class="eyebrow">From my writing</p>'
        '<p>A perspective from my Thinking portfolio.</p>'
        '</div>'
        '<article class="home-featured-story">'
        f'<a class="home-featured-media" href="{href}" target="_self" '
        f'data-hq-event="home_featured_article_image" data-hq-content-slug="{escape(article.slug, quote=True)}" '
        f'aria-label="Read {escape(article.title, quote=True)}">{image}</a>'
        '<div class="home-featured-copy">'
        f'<p class="home-featured-kind">{kind}</p>'
        f'<h2><a href="{href}" target="_self" data-hq-event="home_featured_article_title" '
        f'data-hq-content-slug="{escape(article.slug, quote=True)}">{title}</a></h2>'
        f'<p class="home-featured-deck">{deck}</p>'
        f'<p class="home-featured-date">{published} · {article.read_minutes} min read</p>'
        f'<a class="home-featured-read" href="{href}" target="_self" '
        f'data-hq-event="home_featured_article_open" '
        f'data-hq-content-slug="{escape(article.slug, quote=True)}">Read the article <span aria-hidden="true">→</span></a>'
        '</div></article></div></section>'
    )
