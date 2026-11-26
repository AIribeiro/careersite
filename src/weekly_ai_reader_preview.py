"""Public, genuinely useful Weekly AI opening for the current Premium week."""
from __future__ import annotations

from html import escape
from urllib.parse import quote

from briefing_reader_preview import PREVIEW_CSS, opening_paragraphs
from site_components import footer, nav
from reader_access_invitation import reader_access_invitation
from thinking_core import THINKING_CSS
from thinking_weekly_brief import WEEKLY_CSS, edition_week, _headline


def render_current_week_public_preview(article) -> str:
    """Render only public context and a bounded excerpt; never embed full HTML."""
    slug = escape(quote(str(article.slug or ""), safe=""), quote=True)
    title = escape(_headline(article))
    subtitle = escape(str(article.subtitle or article.excerpt or ""))
    year, week, _, _ = edition_week(article)
    summary = str(article.excerpt or article.subtitle or "").strip()
    extracted = opening_paragraphs(str(article.content_html or ""), max_words=90)
    parts = [summary] if summary else []
    # Prefer the first substantive, original editorial paragraph. A Weekly AI
    # edition is short; use the existing bounded excerpt so the full collection
    # of stories, links and leadership signal does not enter anonymous HTML.
    if extracted and extracted[0].casefold() not in {p.casefold() for p in parts}:
        parts.append(extracted[0])
    if not parts:
        parts.append("The public summary is temporarily unavailable for this edition.")
    paragraphs = "".join("<p>" + escape(p) + "</p>" for p in parts)
    target = "?page=thinking&amp;article=" + slug + "&amp;access=1"
    return (
        THINKING_CSS + WEEKLY_CSS + PREVIEW_CSS + nav("thinking")
        + '<main class="briefing-preview weekly-ai-premium-preview">'
        '<section class="briefing-preview-hero" data-analytics-section="weekly-ai-premium-intro">'
        '<div class="container">'
        '<a class="briefing-preview-back" href="?page=thinking#weekly-ai" target="_self">← Weekly AI</a>'
        '<span class="briefing-preview-index">Weekly AI · Week ' + str(week) + ' · ' + str(year)
        + ' · Latest edition · Free to read with an account</span>'
        + '<h1>' + title + '</h1>'
        + '<p class="briefing-preview-deck">' + subtitle + '</p>'
        + '</div></section>'
        '<section class="briefing-preview-body" data-analytics-section="weekly-ai-premium-summary">'
        '<div class="container"><div class="briefing-preview-grid">'
        '<article class="briefing-preview-copy"><div class="briefing-preview-decision">'
        '<span class="briefing-preview-small-head">Public executive summary</span>'
        '<h2>What deserves attention this week</h2>'
        + paragraphs
        + '</div></article>'
        '<aside class="briefing-preview-aside">'
        '<strong>The full Weekly AI edition</strong>'
        '<p>Read the selected developments, linked original reporting and '
        'leadership implications. Listen to the narrated version when available.</p>'
        '<p>This edition opens to everyone once the next Weekly AI edition is published.</p>'
        '</aside></div>'
        + reader_access_invitation("weekly_ai", target,
            section="weekly-ai-reader-free-access",
            register_event="weekly_ai_premium_access",
            signin_event="weekly_ai_premium_signin")
        + '</div></section></main>' + footer()
    )
