"""A rotating Home preview drawn from published Thinking and Executive Briefings.

The Home selection is independent of Thinking's latest/most-read ranking.
Each render samples the eligible published catalog; Weekly AI is separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from secrets import choice


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
    content_type: str = "article"


def current_home_article() -> HomeArticlePreview:
    """Select one published Thinking article or Executive AI Briefing per render.

    CMS publication status is authoritative. The legacy Thinking catalog remains
    an editorial fallback during a CMS outage, and it rotates independently too.
    """
    from site_cms import (
        article_relative_url,
        cms_feature_image_url,
        fetch_published_articles,
    )
    from thinking_weekly_brief import is_weekly_brief

    try:
        published = fetch_published_articles()
    except (RuntimeError, ValueError, TimeoutError):
        published = ()

    eligible = tuple(
        article for article in published
        if article.status == "published"
        and article.slug.strip()
        and article.title.strip()
        and not is_weekly_brief(article)
    )
    if eligible:
        selected = choice(eligible)
        is_briefing = selected.kind.strip().casefold() == "executive briefing"
        return HomeArticlePreview(
            slug=selected.slug,
            title=selected.title,
            deck=selected.subtitle.strip() or selected.excerpt.strip(),
            kind_topic=selected.kind_topic,
            published_label=selected.published_label,
            read_minutes=selected.read_minutes,
            href=article_relative_url(selected),
            image_url=cms_feature_image_url(selected),
            image_alt=selected.header_image_alt or selected.title,
            content_type="briefing" if is_briefing else "article",
        )

    from thinking_articles import article_relative_url as legacy_relative_url
    from thinking_articles import article_social_image_url, published_articles

    legacy = choice(tuple(published_articles()))
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
    """Render the compact editorial tile ahead of Home's contact CTA."""
    article = current_home_article()
    is_briefing = article.content_type == "briefing"

    title = escape(article.title)
    deck = escape(article.deck)
    kind = escape(article.kind_topic)
    published = escape(article.published_label)
    href = escape(article.href, quote=True)
    image_url = escape(article.image_url, quote=True)
    image_alt = escape(article.image_alt, quote=True)
    content_type = "briefing" if is_briefing else "article"
    read_label = "Read the briefing" if is_briefing else "Read the article"
    aria_label = escape(f"Read {article.title}", quote=True)
    slug = escape(article.slug, quote=True)

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
        '<p>Thinking articles and Executive AI Briefings on the decisions shaping enterprise AI.</p>'
        '</div>'
        '<article class="home-featured-story">'
        f'<a class="home-featured-media" href="{href}" target="_self" '
        f'data-hq-event="home_featured_article_image" data-hq-content-slug="{slug}" '
        f'data-hq-content-type="{content_type}" '
        f'aria-label="{aria_label}">{image}</a>'
        '<div class="home-featured-copy">'
        f'<p class="home-featured-kind">{kind}</p>'
        f'<h2><a href="{href}" target="_self" data-hq-event="home_featured_article_title" '
        f'data-hq-content-slug="{slug}" data-hq-content-type="{content_type}">{title}</a></h2>'
        f'<p class="home-featured-deck">{deck}</p>'
        f'<p class="home-featured-date">{published} · {article.read_minutes} min read</p>'
        f'<a class="home-featured-read" href="{href}" target="_self" '
        f'data-hq-event="home_featured_article_open" data-hq-content-type="{content_type}" '
        f'data-hq-content-slug="{slug}">{read_label} <span aria-hidden="true">→</span></a>'
        '</div></article>'
        '<nav class="home-featured-paths" aria-label="Explore my writing">'
        '<span>Explore the collections</span>'
        '<a href="?page=thinking" target="_self" data-hq-event="home_writing_thinking">Thinking articles <span aria-hidden="true">→</span></a>'
        '<a href="?page=briefings" target="_self" data-hq-event="home_writing_briefings">Executive AI Briefings <span aria-hidden="true">→</span></a>'
        '</nav>'
        '</div></section>'
    )
