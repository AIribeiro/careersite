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


def current_home_article(*, exclude_slug: str = "") -> HomeArticlePreview:
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
        # On a reader page, suggest another publication whenever possible.
        alternatives = tuple(item for item in eligible if item.slug != exclude_slug)
        selected = choice(alternatives if alternatives else eligible)
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

    legacy_pool = tuple(published_articles())
    alternatives = tuple(item for item in legacy_pool if item.slug != exclude_slug)
    legacy = choice(alternatives if alternatives else legacy_pool)
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
    # Legacy /social and generated /cms-* endpoints are not guaranteed to
    # resolve from the Community Cloud browser, even when local ASGI tests pass.
    # Preserve independently hosted editorial assets; otherwise use the
    # intentional graphic cover instead of a broken <img>.
    image_source = article.image_url
    if image_source.startswith((
        "https://jairribeiro-ai.streamlit.app/social/",
        "https://jairribeiro-ai.streamlit.app/cms-header/",
        "https://jairribeiro-ai.streamlit.app/cms-social/",
    )):
        image_source = ""
    image_url = escape(image_source, quote=True)
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
        '<a href="?page=thinking#weekly-ai" target="_self" data-hq-event="home_writing_weekly_ai">Weekly AI <span aria-hidden="true">→</span></a>'
        '<a href="?page=briefings" target="_self" data-hq-event="home_writing_briefings">Executive AI Briefings <span aria-hidden="true">→</span></a>'
        '</nav>'
        '</div></section>'
    )



def home_weekly_ai_strip() -> str:
    """Compact, image-free discovery point. Thinking stays the canonical parent page.

    Always lead to the latest issue within Thinking, rather than linking to a
    static slug that will become stale at the next Friday publication.
    """
    return '''<style>
.home-weekly-bridge{background:#f8f5ef;padding:8px 0 22px}
.home-weekly-bridge-inner{display:grid;grid-template-columns:104px minmax(0,1fr) auto;align-items:center;gap:25px;background:#fff;border:1px solid #d8d2c9;border-left:4px solid #bb8460;padding:22px 28px;box-shadow:0 9px 23px rgba(13,29,48,.055)}
.home-weekly-mark{display:flex;flex-direction:column;gap:0;padding-right:22px;border-right:1px solid #dfd9d2;color:#17304a;font:850 13px/1.1 Arial,sans-serif;letter-spacing:.14em}
.home-weekly-mark strong{font:500 48px/.94 Georgia,serif;letter-spacing:-.06em;color:#b57951}
.home-weekly-copy{min-width:0}
.home-weekly-copy small{display:block;margin-bottom:6px;color:#9a633c;font:800 10px/1.3 Arial,sans-serif;letter-spacing:.09em;text-transform:uppercase}
.home-weekly-copy h2{font:500 clamp(22px,2.3vw,30px)/1.16 Georgia,serif;letter-spacing:-.025em;color:#192d42;margin:0 0 5px}
.home-weekly-copy p{margin:0;color:#596570;font:400 13px/1.5 Arial,sans-serif}
.home-weekly-open{display:inline-flex;white-space:nowrap;align-items:center;justify-content:center;min-height:44px;box-sizing:border-box;padding:12px 18px;color:#fff!important;background:#1a334b;text-decoration:none!important;font:750 12px/1.4 Arial,sans-serif;transition:background .15s}
.home-weekly-open:hover,.home-weekly-open:focus-visible{background:#315573}
@media(max-width:850px){.home-weekly-bridge-inner{grid-template-columns:90px minmax(0,1fr);gap:18px;padding:21px}.home-weekly-mark{padding-right:15px}.home-weekly-open{grid-column:2;justify-self:start}}
@media(max-width:560px){.home-weekly-bridge-inner{grid-template-columns:1fr;gap:12px;padding:20px}.home-weekly-mark{flex-direction:row;align-items:baseline;gap:7px;border-right:0;border-bottom:1px solid #dfd9d2;padding:0 0 12px}.home-weekly-mark strong{font-size:33px}.home-weekly-open{grid-column:1;width:100%}}
@media(prefers-reduced-motion:reduce){.home-weekly-open{transition:none}}
</style>
<section class="home-weekly-bridge" data-analytics-section="home-weekly-ai-promo" aria-label="Weekly AI leadership perspective">
<div class="container"><div class="home-weekly-bridge-inner">
<div class="home-weekly-mark" aria-hidden="true"><span>WEEKLY</span><strong>AI</strong></div>
<div class="home-weekly-copy"><small>Every Friday · One-minute read or listen</small><h2>The AI week, through a leadership lens.</h2><p>What changed, why it matters to the enterprise, and what leaders should examine next.</p></div>
<a class="home-weekly-open" href="?page=thinking#weekly-ai" target="_self" data-hq-event="home_weekly_ai_open">Read this week’s perspective →</a>
</div></div></section>'''


def compact_writing_footer(*, exclude_slug: str = "") -> str:
    """A restrained editorial continuation for public pages.

    The small cover is CSS-only on purpose: CMS cover images are much too large
    and may be unavailable in cross-page footers. A deterministic typographic
    cover prevents broken assets, full-size images and layout shifts.
    """
    article = current_home_article(exclude_slug=exclude_slug)
    is_briefing = article.content_type == "briefing"
    href = escape(article.href, quote=True)
    slug = escape(article.slug, quote=True)
    title = escape(article.title)
    deck = escape(article.deck)
    published = escape(article.published_label)
    kind = "Executive AI Briefing" if is_briefing else "Thinking article"
    cover_label = "BRIEFING" if is_briefing else "THINKING"
    content_type = "briefing" if is_briefing else "article"
    read_label = "Read briefing" if is_briefing else "Read article"
    readable_title = escape(article.title, quote=True)

    return (
        '<section class="writing-footer" data-analytics-section="site-writing-footer" '
        'aria-label="From my writing">'
        '<div class="container writing-footer-inner">'
        f'<a class="writing-footer-art" href="{href}" target="_self" '
        f'data-hq-event="writing_footer_image" data-hq-content-slug="{slug}" '
        f'data-hq-content-type="{content_type}" '
        f'aria-label="Read {readable_title}">'
        '<span class="writing-footer-art-rule" aria-hidden="true"></span>'
        '<span class="writing-footer-art-mark" aria-hidden="true">AI</span>'
        f'<span class="writing-footer-art-label" aria-hidden="true">{cover_label}</span>'
        '</a>'
        '<div class="writing-footer-copy">'
        '<div class="writing-footer-overline"><span>From my writing</span>'
        f'<span class="writing-footer-separator" aria-hidden="true">/</span><span>{kind}</span></div>'
        f'<h2><a href="{href}" target="_self" title="{readable_title}" '
        f'data-hq-event="writing_footer_title" data-hq-content-slug="{slug}" '
        f'data-hq-content-type="{content_type}">{title}</a></h2>'
        f'<p class="writing-footer-deck">{deck}</p>'
        f'<span class="writing-footer-meta">{published} · {article.read_minutes} min read</span>'
        '</div>'
        '<div class="writing-footer-action">'
        f'<a class="writing-footer-open" href="{href}" target="_self" '
        f'data-hq-event="writing_footer_open" '
        f'data-hq-content-slug="{slug}" data-hq-content-type="{content_type}">'
        f'{read_label} <span aria-hidden="true">↗</span></a>'
        '<nav aria-label="Writing collections">'
        '<a href="?page=thinking" target="_self" data-hq-event="writing_footer_thinking">Thinking</a>'
        '<a href="?page=thinking#weekly-ai" target="_self" data-hq-event="writing_footer_weekly_ai">Weekly AI</a>'
        '<a href="?page=briefings" target="_self" data-hq-event="writing_footer_briefings">Briefings</a>'
        '</nav></div></div></section>'
    )


def inject_writing_footer(document: str, page: str, *, article_slug: str = "") -> str:
    """Attach the compact feature once, within main and above the site footer.

    Executive Briefings retain the decision-contact block as their final
    editorial section, so insert the writing strip just before that block.
    """
    if page in {"home", "analytics", "admin"} or 'data-analytics-section="site-writing-footer"' in document:
        return document
    if "<main" not in document or "</main>" not in document:
        return document

    feature = compact_writing_footer(exclude_slug=article_slug)
    briefing_contact = '<section class="briefings-conversation"'
    if briefing_contact in document:
        return document.replace(briefing_contact, feature + briefing_contact, 1)

    index = document.rfind("</main>")
    return document[:index] + feature + document[index:]
