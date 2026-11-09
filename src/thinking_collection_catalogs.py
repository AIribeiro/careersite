"""Matching, independently paginated Weekly AI and Executive Briefing catalogues.

Rendered from the same published CMS records as the Articles collection. Reuse
the existing Articles highlight/card/pagination classes and preserve original
section anchors for the Thinking readership-based ordering controller.
"""

from __future__ import annotations

from hashlib import sha256
from html import escape
from math import ceil
from urllib.parse import urlencode

from thinking_core import query_value

PAGE_SIZE = 4
ATTRIBUTION_PARAMS = (
    "source", "role", "utm_source", "utm_medium", "utm_campaign", "utm_content"
)

COLLECTION_CSS = """<style>
/* The Articles editorial system, extended to Weekly AI and Executive Briefings. */
.site .thinking-collection.cms-latest{padding-block:clamp(66px,7vw,100px)}
.site .thinking-collection .head{margin-bottom:clamp(26px,3vw,38px)}
.site .thinking-collection .head h2{max-width:610px;text-wrap:balance}
.site .thinking-collection .cms-thinking-highlight{margin:0 0 38px}
.site .thinking-collection .home-featured-topline p{margin-top:0}
.site .thinking-collection .home-featured-media{
  display:block;position:relative;overflow:hidden;background:#142a3e;min-height:250px
}
.site .thinking-collection .home-featured-media img{
  display:block;width:100%;height:100%;object-fit:contain;object-position:center;background:#142a3e
}
.site .thinking-collection .home-featured-art-fallback{
  position:relative;isolation:isolate;overflow:hidden;box-sizing:border-box;
  display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:13px;
  width:100%;height:100%;min-height:250px;padding:clamp(25px,4vw,45px);
  background:radial-gradient(circle at 87% 24%,rgba(199,146,106,.24),transparent 39%),
    linear-gradient(135deg,#102538,#24475e);
  color:#f3e1d2;text-align:left
}
.site .thinking-collection .home-featured-art-fallback:after{
  content:"";position:absolute;right:-38px;top:-60px;width:240px;height:240px;
  border:1px solid rgba(230,190,160,.22);border-radius:50%;z-index:-1
}
.site .thinking-collection .collection-art-kicker{
  color:#e6b28d;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase
}
.site .thinking-collection .collection-art-topic{
  color:#d0dce6;font:700 11px/1.4 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase
}
.site .thinking-collection .collection-art-title{
  max-width:540px;color:#fff8ef;font:500 clamp(22px,3vw,43px)/1.10 Georgia,serif;
  letter-spacing:-.025em;overflow-wrap:break-word;display:-webkit-box;
  -webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden
}
.site .thinking-collection .cms-article-card .cms-thinking-thumb{
  margin:0!important;aspect-ratio:16/9!important;width:100%;max-width:100%;
  background:#11263a;overflow:hidden;flex:0 0 auto
}
.site .thinking-collection .cms-article-card .cms-thinking-thumb img{
  width:100%!important;height:100%!important;object-fit:contain!important;
  object-position:center!important
}
.site .thinking-collection .cms-article-card .cms-thinking-thumb .home-featured-art-fallback{
  min-height:0;height:100%;gap:8px;padding:clamp(17px,2.5vw,28px)
}
.site .thinking-collection .cms-article-card .collection-art-title{
  font-size:clamp(20px,2vw,28px);-webkit-line-clamp:3
}
.site .thinking-collection .cms-article-card .collection-art-kicker{font-size:8px}
.site .thinking-collection .cms-article-card .collection-art-topic{font-size:9px}
.site .thinking-collection .cms-article-card .cms-article-card-body{min-width:0}
.site .thinking-collection .cms-article-card h3{overflow-wrap:break-word}
.site .thinking-collection .cms-catalog-footer{padding-top:18px}
.site .thinking-collection .thinking-catalog-other-link{
  display:inline-flex;margin-top:16px;font-size:12px;font-weight:750;
  color:#2b4960;text-decoration:underline;text-underline-offset:3px
}
.site .thinking-collection .home-featured-audio{
  margin:12px 0 0;font-size:12px;font-weight:700
}
.site .thinking-collection .home-featured-audio a{
  color:#f1c8a9!important;text-decoration:underline;text-underline-offset:3px
}
.site .thinking-collection .thinking-catalog-empty{
  padding:26px;border:1px solid #dfd4c8;color:#596776;background:#fffdfa
}
@media(max-width:760px){
  .site .thinking-collection.cms-latest{padding-block:55px}
  .site .thinking-collection .home-featured-media{min-height:195px}
  .site .thinking-collection .home-featured-art-fallback{min-height:195px}
  .site .thinking-collection .cms-thinking-highlight{margin-bottom:29px}
  .site .thinking-collection .cms-catalog-footer{gap:12px}
}
</style>"""


def _published_date(article) -> str:
    return str(article.published_at or article.updated_at or article.created_at or "")


def _description(article) -> str:
    text = (article.excerpt or article.subtitle or "").strip()
    return text if text else "An executive perspective on decisions, responsibilities and business outcomes."


def _image_url(article, kind: str) -> str:
    from site_cms import effective_header_image_url
    if kind == "weekly_ai":
        if article.header_image_url:
            return article.header_image_url
        # Streamlit Cloud does not always expose the app-local /weekly-ai-cover
        # route. Serve checked-in covers using the same raw GitHub media origin
        # that reliably serves photographs elsewhere in this portfolio.
        from thinking_weekly_brief import _published_cover_bytes
        data = _published_cover_bytes(article.slug)
        if data is not None:
            digest = sha256(data).hexdigest()[:12]
            return (
                "https://raw.githubusercontent.com/AIribeiro/careersite/main/"
                f"static/weekly-ai/{article.slug}.png?v={digest}"
            )
        return ""
    url = effective_header_image_url(article)
    # App-local CMS media can be unavailable in the deployed Streamlit context.
    # A styled fallback is preferable to a browser's broken-image placeholder.
    from site_cms import BASE_URL
    if url.startswith((f"{BASE_URL}/cms-header/", f"{BASE_URL}/cms-social/")):
        return ""
    return url


def _art(article, kind: str, *, featured: bool) -> str:
    url = _image_url(article, kind)
    if url:
        return (
            f'<img src="{escape(url, quote=True)}" '
            f'alt="{escape(article.header_image_alt or article.title, quote=True)}" '
            f'loading="{"eager" if featured else "lazy"}" decoding="async">'
        )
    label = "WEEKLY AI" if kind == "weekly_ai" else "EXECUTIVE AI BRIEFING"
    return (
        '<span class="home-featured-art-fallback" role="img" '
        f'aria-label="{escape(article.title, quote=True)}">'
        f'<span class="collection-art-kicker">{escape(label)}</span>'
        f'<span class="collection-art-topic">{escape(article.topic)}</span>'
        f'<strong class="collection-art-title">{escape(article.title)}</strong>'
        '</span>'
    )


def _meta(article, counts: dict[str, int] | None) -> str:
    from site_cms import article_read_count_label
    return (
        f"{escape(article.published_label)} · {max(1, int(article.read_minutes))} min read"
        f" · {article_read_count_label(article.slug, counts)}"
    )


def _feature(article, kind: str, counts: dict[str, int] | None) -> str:
    from site_cms import article_relative_url
    href = escape(article_relative_url(article), quote=True)
    slug = escape(article.slug, quote=True)
    label = "Latest weekly edition" if kind == "weekly_ai" else "Highlighted briefing"
    description = (
        "The newest Friday perspective." if kind == "weekly_ai"
        else "Chosen from recent publication and reader interest."
    )
    listen = ""
    if kind == "weekly_ai":
        from weekly_ai_audio import audio_url
        if audio_url(article.slug):
            listen = (
                '<p class="home-featured-audio">'
                f'<a href="{href}#weekly-ai-audio" target="_self" '
                f'data-hq-event="thinking_weekly_ai_highlight_listen" '
                f'data-hq-content-slug="{slug}">Listen to this edition →</a></p>'
            )
    return (
        '<div class="cms-thinking-highlight thinking-collection-highlight" '
        f'data-analytics-section="thinking-{kind}-highlight">'
        '<div class="home-featured-topline">'
        f'<p class="eyebrow">{label}</p><p>{description}</p></div>'
        '<article class="home-featured-story">'
        f'<a class="home-featured-media" href="{href}" target="_self" '
        f'data-hq-event="thinking_{kind}_highlight_image" data-hq-content-slug="{slug}" '
        f'aria-label="Read {escape(article.title, quote=True)}">'
        + _art(article, kind, featured=True)
        + '</a><div class="home-featured-copy">'
        f'<p class="home-featured-kind">{escape(article.kind)} · {escape(article.topic)}</p>'
        f'<h3><a href="{href}" target="_self" '
        f'data-hq-event="thinking_{kind}_highlight_title" data-hq-content-slug="{slug}">'
        f'{escape(article.title)}</a></h3>'
        f'<p class="home-featured-deck">{escape(article.subtitle or _description(article))}</p>'
        f'<p class="home-featured-date">{_meta(article, counts)}</p>'
        f'<a class="home-featured-read" href="{href}" target="_self" '
        f'data-hq-event="thinking_{kind}_highlight_open" data-hq-content-slug="{slug}">'
        'Read highlighted edition <span aria-hidden="true">→</span></a>'
        + listen
        + '</div></article></div>'
    )


def _card(article, kind: str, counts: dict[str, int] | None) -> str:
    from site_cms import article_relative_url
    href = escape(article_relative_url(article), quote=True)
    slug = escape(article.slug, quote=True)
    return (
        f'<a class="recent-card cms-article-card" href="{href}" target="_self" '
        f'data-hq-event="thinking_{kind}_edition_open" data-hq-content-slug="{slug}">'
        '<div class="cms-thinking-thumb">' + _art(article, kind, featured=False)
        + '</div><div class="cms-article-card-body">'
        f'<div class="kicker">{escape(article.kind)} · {escape(article.topic)}</div>'
        f'<h3>{escape(article.title)}</h3>'
        f'<p class="cms-article-excerpt">{escape(_description(article))}</p>'
        f'<div class="read">{_meta(article, counts)} →</div>'
        '</div></a>'
    )


def _page_number(raw: str, pages: int) -> int:
    try:
        return max(1, min(int(raw), pages))
    except (TypeError, ValueError, OverflowError):
        return 1


def _page_href(kind: str, page: int) -> str:
    """Preserve the other two collections' pages and existing campaign tags."""
    import streamlit as st
    own = "weekly_page" if kind == "weekly_ai" else "briefings_page"
    keep = ("weekly_page", "briefings_page", "articles_page") + ATTRIBUTION_PARAMS
    params = [("page", "thinking")]
    for name in keep:
        raw = st.query_params.get(name, "")
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        value = str(raw).strip()[:120]
        if name == own or not value:
            continue
        if name in ("weekly_page", "briefings_page", "articles_page"):
            if not value.isdecimal() or int(value) < 1:
                continue
        params.append((name, value))
    params.append((own, str(page)))
    anchor = "weekly-ai" if kind == "weekly_ai" else "thinking-briefings"
    return escape("?" + urlencode(params) + "#" + anchor, quote=True)


def _pagination(kind: str, total: int, selected: int, pages: int) -> str:
    label = "Weekly AI" if kind == "weekly_ai" else "Executive AI Briefings"
    def link(page: int, caption: str) -> str:
        return (
            f'<a href="{_page_href(kind, page)}" target="_self" '
            f'data-hq-event="thinking_{kind}_catalog_page" '
            f'data-collection-page="{page}">{escape(caption)}</a>'
        )
    parts = []
    if selected > 1:
        parts.append(link(selected - 1, "← Previous"))
    visible = set(range(max(1, selected - 1), min(pages, selected + 1) + 1))
    visible.update((1, pages))
    previous = 0
    for number in sorted(visible):
        if previous and number - previous > 1:
            parts.append('<span class="catalog-page-ellipsis" aria-hidden="true">…</span>')
        parts.append(
            f'<span class="catalog-page-current" aria-current="page">{number}</span>'
            if number == selected else link(number, str(number))
        )
        previous = number
    if selected < pages:
        parts.append(link(selected + 1, "Next →"))
    first = (selected - 1) * PAGE_SIZE + 1 if total else 0
    last = min(selected * PAGE_SIZE, total)
    return (
        f'<div class="cms-catalog-footer"><p>Showing {first}–{last} of {total} '
        f'{escape(label)} editions · Four per page · Featured edition above</p>'
        f'<nav class="cms-pagination" aria-label="{escape(label, quote=True)} pages">'
        + "".join(parts) + '</nav></div>'
    )


def _collection(kind: str, published: tuple, counts: dict[str, int] | None) -> str:
    from site_cms import select_auto_featured_article
    from thinking_weekly_brief import is_weekly_brief, sorted_editions
    if kind == "weekly_ai":
        items = sorted_editions(list(published))
        featured = items[0] if items else None
        title = "The AI week, through a leadership lens."
        description = (
            "A concise Friday perspective on what changed in AI, why it matters "
            "for enterprises and what leaders should examine next."
        )
        eyebrow = "Weekly AI · Friday perspective"
        heading = "Previous editions"
        section_id, section_event, page_key = "weekly-ai", "weekly-ai-feature", "weekly_page"
        empty = "The Weekly AI archive begins with the first published edition."
    else:
        items = sorted(
            (a for a in published if a.kind.strip().casefold() == "executive briefing"),
            key=lambda a: (_published_date(a), a.slug), reverse=True,
        )
        featured = select_auto_featured_article(items, counts)
        title = "Clarity before the next AI decision."
        description = (
            "Briefings for executives deciding what to fund, govern, delegate or scale. "
            "Each examines the business choice, the trade-offs and the evidence to request."
        )
        eyebrow = "Executive AI Briefings · A decision-first series"
        heading = "All executive briefings"
        section_id, section_event, page_key = (
            "thinking-briefings", "thinking-executive-briefings", "briefings_page"
        )
        empty = "Executive AI Briefings will appear here as they are published."
    others = [a for a in items if featured is None or a.slug != featured.slug]
    # As with the Articles collection, prefer popular items when reads are
    # available. The stable publication-date order settles equal counts.
    if counts is not None and kind != "weekly_ai":
        others.sort(key=lambda a: max(0, counts.get(a.slug, 0)), reverse=True)
    pages = max(1, ceil(len(others) / PAGE_SIZE))
    selected = _page_number(query_value(page_key), pages)
    start = (selected - 1) * PAGE_SIZE
    visible = others[start:start + PAGE_SIZE]
    catalog = (
        '<div class="recent-grid">' + "".join(_card(a, kind, counts) for a in visible) + '</div>'
        + _pagination(kind, len(others), selected, pages)
        if others else f'<p class="thinking-catalog-empty">{escape(empty)}</p>'
    )
    return (
        f'<section class="section white cms-latest thinking-collection thinking-collection--{kind}" '
        f'id="{section_id}" data-analytics-section="{section_event}"><div class="container">'
        '<div class="head"><div>'
        f'<p class="eyebrow">{eyebrow}</p><h2>{title}</h2></div><p>{description}</p></div>'
        + (_feature(featured, kind, counts) if featured is not None else '')
        + (f'<div class="cms-listing-head"><p class="eyebrow">{heading}</p>'
           '<p>Browse the full collection, four at a time.</p></div>' if others else '')
        + catalog
        + ('<a class="thinking-catalog-other-link" href="?page=thinking&amp;weekly_ai=archive" '
           'target="_self" data-hq-event="thinking_weekly_full_archive">'
           'View the complete Weekly AI archive →</a>' if kind == "weekly_ai" and items else '')
        + ('<a class="thinking-catalog-other-link" href="?page=briefings" '
           'target="_self" data-hq-event="thinking_briefings_library_open">'
           'Explore the Executive AI Briefings library →</a>'
           if kind == "briefings" and items else '')
        + '</div></section>'
    )


def inject_thinking_collections(
    document: str, published: tuple, *, read_counts: dict[str, int] | None = None
) -> str:
    """Replace the old oversized panels with two complete CMS catalogues."""
    import re
    briefings = _collection("briefings", published, read_counts)
    weekly = _collection("weekly_ai", published, read_counts)
    # The old static briefings feature is an isolated section without nested
    # sections; replace only that element and leave articles and other content.
    marker = re.compile(
        r'<section class="section paper" id="thinking-briefings"'
        r'[^>]*>.*?</section>', re.S
    )
    if marker.search(document):
        document = marker.sub(lambda _: briefings, document, count=1)
    elif 'id="thinking-briefings"' not in document and 'id="thinking-articles"' in document:
        document = document.replace(
            '<section class="section white" id="thinking-articles">',
            briefings + '<section class="section white" id="thinking-articles">', 1
        )
    # Insert Weekly AI immediately after the Thinking introduction. The
    # browser's existing hourly ranking controller will move both collections
    # alongside Articles, keeping the three anchor IDs unchanged.
    if 'id="weekly-ai"' not in document:
        hero = document.find('<section class="pagehero">')
        end = document.find('</section>', hero) if hero >= 0 else -1
        if end >= 0:
            end += len('</section>')
            document = document[:end] + weekly + document[end:]
    return COLLECTION_CSS + document
