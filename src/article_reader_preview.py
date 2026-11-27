"""Credible public executive summaries for Premium editorial Articles.

Only published excerpts and bounded opening text are rendered for anonymous
readers. No article body HTML or private editorial assets enter the DOM.
"""
from __future__ import annotations

from html import escape
import re
from urllib.parse import quote

from briefing_reader_preview import PREVIEW_CSS, opening_paragraphs, next_edition_sections
from premium_article_editorial import public_intro_preview_paragraphs
from site_components import footer, nav
from reader_access_invitation import reader_access_invitation
from article_reader_video import render_article_video
from thinking_core import THINKING_CSS


def render_public_article_preview(article, read_metadata: str = "") -> str:
    slug = quote(str(article.slug or ""), safe="")
    title = escape(str(article.title or "Article"))
    subtitle = escape(str(article.subtitle or article.excerpt or "").strip())
    published_summary = str(article.excerpt or "").strip()
    # A question-led CMS summary earns a provocative heading; statement-led
    # summaries retain a neutral, executive-relevant heading.
    opening_sentence = re.search(r"[.!?](?:\s|$)", published_summary)
    summary_heading = (
        "The uncomfortable question"
        if opening_sentence and opening_sentence.group(0).startswith("?")
        else "What's really at stake"
    )
    # For new-style Articles use only the substantive introductory paragraphs
    # that precede the first H2/H3. The generic legacy fallback preserves old
    # published records that begin immediately with a section heading.
    opening = public_intro_preview_paragraphs(str(article.content_html or ""))
    if not opening:
        opening = opening_paragraphs(str(article.content_html or ""), max_words=200)

    # The executive summary uses editorial material that actually exists,
    # rather than fabricated conclusions or marketing copy.
    sections = []
    if published_summary:
        sections.append(published_summary)
    for paragraph in opening[:3]:
        if paragraph.casefold() not in {text.casefold() for text in sections}:
            sections.append(paragraph)
        if len(sections) == 3:
            break
    if not sections:
        sections = ["The executive summary is temporarily unavailable for this article."]

    # A companion film follows the hero, including one substantive public
    # summary paragraph. The remaining authorized opening stays below the film.
    video_markup = render_article_video(article)
    hero_summary = sections[0] if video_markup else ""
    remaining = sections[1:] if video_markup else sections
    body = "".join(f"<p>{escape(p)}</p>" for p in remaining)
    lead = (
        '<p class="article-video-public-lead">' + escape(hero_summary) + '</p>'
        if hero_summary else ""
    )
    heads = next_edition_sections(str(article.content_html or ""), limit=4)
    inside = (
        "<ul>" + "".join(f"<li>{escape(head)}</li>" for head in heads) + "</ul>"
        if heads else
        "<p>The full argument, supporting evidence and practical implications.</p>"
    )
    from site_cms import reader_header_image_src
    header_url = reader_header_image_src(article)
    cover_first = bool(header_url and (header_url.startswith("https://") or header_url.startswith("data:image/webp;base64,")))
    hero_class = "briefing-preview-hero article-cover-first" if cover_first else "briefing-preview-hero"
    heading_class = ' class="article-heading-sr"' if cover_first else ""
    deck_class = "briefing-preview-deck article-heading-sr" if cover_first else "briefing-preview-deck"
    header_alt = str(getattr(article, "header_image_alt", "") or article.title or "Article cover")
    cover_picture = ""
    if cover_first:
        cover_picture = (
            '<div class="cms-article-image">'
            '<img src="' + escape(header_url, quote=True)
            + '" alt="' + escape(header_alt, quote=True)
            + '" loading="eager" decoding="async"></div>'
        )
    cover_css = (
        '<style>.site .article-early-preview .article-video-public-lead{'
        'max-width:900px;margin:18px 0 0;color:#cbd5de;font:400 clamp(15px,1.6vw,18px)/1.6 Arial,sans-serif;'
        'overflow-wrap:anywhere}</style>'
    )
    destination = "?page=thinking&amp;article=" + escape(slug, quote=True) + "&amp;access=1"

    return (
        THINKING_CSS + PREVIEW_CSS + cover_css + nav("thinking")
        + '<main class="briefing-preview article-early-preview">'
        f'<section class="{hero_class}" data-analytics-section="article-early-access-intro">'
        '<div class="container"><a class="briefing-preview-back" href="?page=thinking" target="_self">'
        '← All Articles</a>'
        '<span class="briefing-preview-index">Article · Free to read with an account</span>'
        f'<h1{heading_class}>{title}</h1><p class="{deck_class}">{subtitle}</p>'
        f'<div class="briefing-preview-meta">{escape(str(read_metadata))} · By Jair Ribeiro</div>'
        + cover_picture + lead + '</div></section>'
        + video_markup
        + '<section class="briefing-preview-body" data-analytics-section="article-executive-summary">' 
        '<div class="container"><div class="briefing-preview-grid">'
        '<article class="briefing-preview-copy"><div class="briefing-preview-decision">'
        '<span class="briefing-preview-small-head">Executive summary</span>'
        f'<h2>{escape(summary_heading)}</h2>'
        + body + '</div></article>'
        '<aside class="briefing-preview-aside">'
        '<strong>Inside the full article</strong>' + inside
        + '<p>Register for free to read the full article.</p>'
        '</aside></div>'
        + reader_access_invitation("article", destination,
            section="article-reader-free-access",
            register_event="article_unlock_register",
            signin_event="article_unlock_signin")
        + '</div></section></main>' + footer()
    )
