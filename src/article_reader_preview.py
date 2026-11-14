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
from thinking_core import THINKING_CSS


def render_public_article_preview(article, read_metadata: str = "") -> str:
    slug = quote(str(article.slug or ""), safe="")
    title = escape(str(article.title or "Article"))
    subtitle = escape(str(article.subtitle or article.excerpt or "").strip())
    published_summary = str(article.excerpt or "").strip()
    # A question-led CMS summary earns a provocative heading; statement-led
    # summaries retain a neutral, executive-relevant heading.
    opening_sentence = re.search(r"[.!?](?:\\s|$)", published_summary)
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

    body = "".join(f"<p>{escape(p)}</p>" for p in sections)
    heads = next_edition_sections(str(article.content_html or ""), limit=4)
    inside = (
        "<ul>" + "".join(f"<li>{escape(head)}</li>" for head in heads) + "</ul>"
        if heads else
        "<p>The full argument, supporting evidence and practical implications.</p>"
    )
    destination = "?page=thinking&amp;article=" + escape(slug, quote=True) + "&amp;access=1"

    return (
        THINKING_CSS + PREVIEW_CSS + nav("thinking")
        + '<main class="briefing-preview article-early-preview">'
        '<section class="briefing-preview-hero" data-analytics-section="article-early-access-intro">'
        '<div class="container"><a class="briefing-preview-back" href="?page=thinking" target="_self">'
        '← All Articles</a>'
        '<span class="briefing-preview-index">Article · Premium Reader edition</span>'
        f'<h1>{title}</h1><p class="briefing-preview-deck">{subtitle}</p>'
        f'<div class="briefing-preview-meta">{escape(str(read_metadata))} · By Jair Ribeiro</div>'
        '</div></section>'
        '<section class="briefing-preview-body" data-analytics-section="article-executive-summary">'
        '<div class="container"><div class="briefing-preview-grid">'
        '<article class="briefing-preview-copy"><div class="briefing-preview-decision">'
        '<span class="briefing-preview-small-head">Public executive summary</span>'
        f'<h2>{escape(summary_heading)}</h2>'
        + body + '</div></article>'
        '<aside class="briefing-preview-aside">'
        '<strong>Inside the complete article</strong>' + inside
        + '<p>Premium Reader access includes the full article.</p>'
        '</aside></div>'
        '<section class="briefing-unlock" data-analytics-section="article-reader-free-access">'
        '<div class="briefing-unlock-inner"><div><p class="eyebrow">'
        'Complimentary registered-reader access</p>'
        '<h2>Read the complete article now.</h2>'
        '<p>Explore the full reasoning, practical implications and references. '
        'Your complimentary account also opens every Executive AI Briefing '
        'and the latest Weekly AI edition.</p></div>'
        '<ul class="briefing-unlock-benefits">'
        '<li>Read the complete article immediately</li>'
        '<li>Use one account across Articles and Executive AI Briefings</li>'
        '<li>Continue reading with your existing Premium Reader account</li>'
        '</ul></div><div class="briefing-unlock-actions">'
        f'<a class="briefing-unlock-primary" href="{destination}" target="_self" '
        'data-hq-event="article_unlock_register">Read full article · Free</a>'
        f'<a class="briefing-unlock-secondary" href="{destination}&amp;signin=1" target="_self" '
        'data-hq-event="article_unlock_signin">Already registered? Sign in</a>'
        '</div><p class="briefing-unlock-note">'
        'Free account. No payment details. Editorial emails are optional.'
        '</p></section></div></section></main>' + footer()
    )
