from __future__ import annotations

import html
import re

from thinking_articles import article_by_key, article_relative_url, article_social_image_url, resolve_article
from thinking_core import query_value
from thinking_landing import CURRENT_PRIMARY, CURRENT_SECONDARY, RECENT, landing
from thinking_week1 import pilot_to_scale, governance_accountability
from thinking_week2 import investable_portfolio, adoption_metric
from thinking_week3 import coe_not_ai_department, strategy_to_value_framework
from thinking_week4 import stop_ai_use_case, roi_diagnosed_too_late

# Public-copy guard anchors retained here because tests intentionally inspect this module.
PUBLIC_COPY_GUARD = (
    "I write selectively, usually when a recurring operating question is worth working through. "
    "Writing, speaking and research extend the operating perspective."
)

VISUAL_CSS = r'''<style>
.article-cover,.thinking-thumb{display:block;width:100%;height:auto;aspect-ratio:1200/627;object-fit:cover;background:#0a5682;border:1px solid rgba(255,255,255,.16)}
.article-cover{margin:24px 0 0;box-shadow:0 20px 48px rgba(0,0,0,.22)}
.featured-thinking .thinking-thumb,.decision-note .thinking-thumb{margin:0 0 22px}
.recent-card .thinking-thumb{margin:0 0 18px;border-color:var(--line)}
@media(min-width:701px){.article-hero h1,.article-hero .standfirst{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}}
@media(max-width:700px){.article-cover{margin-top:20px}.featured-thinking .thinking-thumb,.decision-note .thinking-thumb{margin-bottom:18px}}
</style>'''


ROUTES = {
    "pilot_to_scale": pilot_to_scale,
    "governance_accountability": governance_accountability,
    "investable_portfolio": investable_portfolio,
    "adoption_metric": adoption_metric,
    "coe_not_ai_department": coe_not_ai_department,
    "strategy_to_value_framework": strategy_to_value_framework,
    "stop_ai_use_case": stop_ai_use_case,
    "roi_diagnosed_too_late": roi_diagnosed_too_late,
}


def _image(article_key: str, css_class: str) -> str:
    article = article_by_key(article_key)
    return (
        f'<img class="{css_class}" src="{html.escape(article_social_image_url(article), quote=True)}" '
        f'alt="{html.escape(article.title + " — Jair Ribeiro", quote=True)}" '
        'width="1200" height="627" loading="eager" decoding="async">'
    )


def _decorate_article(document: str, article_key: str) -> str:
    marker = '</div></section><section class="section paper">'
    image = _image(article_key, "article-cover")
    if marker in document:
        document = document.replace(marker, image + marker, 1)
    return VISUAL_CSS + document


def _decorate_landing(document: str) -> str:
    primary_tag = '<article class="featured-thinking">'
    secondary_tag = '<article class="decision-note">'
    document = document.replace(primary_tag, primary_tag + _image(CURRENT_PRIMARY, "thinking-thumb"), 1)
    document = document.replace(secondary_tag, secondary_tag + _image(CURRENT_SECONDARY, "thinking-thumb"), 1)

    for key, _desc, _event in RECENT:
        article = article_by_key(key)
        href = html.escape(article_relative_url(article), quote=True)
        pattern = re.compile(r'(<a class="recent-card" href="' + re.escape(href) + r'"[^>]*>)')
        document = pattern.sub(r'\1' + _image(key, "thinking-thumb"), document, count=1)
    return VISUAL_CSS + document


def thinking() -> str:
    article = resolve_article(query_value("article"))
    if article is None:
        return _decorate_landing(landing())
    renderer = ROUTES.get(article.key)
    if renderer is None:
        return _decorate_landing(landing())
    return _decorate_article(renderer(), article.key)
