from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from site_cms import CmsArticle


BRIEF_KIND = "Weekly Brief"
BRIEF_CATEGORY = "Weekly AI"


def is_weekly_brief(article: "CmsArticle") -> bool:
    """A separate editorial type; it should never displace a Thinking essay."""
    return (article.kind or "").strip().casefold() == BRIEF_KIND.casefold() and (
        article.category or ""
    ).strip().casefold() == BRIEF_CATEGORY.casefold()


WEEKLY_CSS = """
<style>
.weekly-ai-section{padding-top:46px;padding-bottom:46px}
.weekly-ai-panel{border:1px solid #d9d3ca;border-top:3px solid var(--copper);padding:clamp(25px,4vw,46px);background:#fff;box-shadow:0 18px 38px rgba(15,29,45,.055)}
.weekly-ai-top{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap}
.weekly-ai-top span{color:#616b73;font-size:11px;font-weight:700;letter-spacing:.10em;text-transform:uppercase}
.weekly-ai-panel h2{margin:13px 0;font:500 clamp(34px,4vw,50px)/1.09 Georgia,serif;color:#142439;letter-spacing:-.025em}
.weekly-ai-panel p{max-width:760px;color:#47515b;font-size:16px;line-height:1.6;margin:0 0 19px}
.weekly-ai-action{display:inline-block;padding:11px 18px;background:#182e46;color:#fff!important;font-size:12px;font-weight:800;text-decoration:none;border-radius:2px}
.weekly-ai-action:hover{background:#294866}
.weekly-ai-archive{margin:20px 0 0;border-top:1px solid #ebe6dd;padding-top:14px}
.weekly-ai-archive summary{cursor:pointer;color:#4b5560;font-weight:700;font-size:12px}
.weekly-ai-archive ul{list-style:none;padding:9px 0 0;margin:0}
.weekly-ai-archive li{padding:6px 0;font-size:13px}
.weekly-ai-archive li a{color:#1e3b59;text-decoration:none}
.weekly-ai-reader{max-width:880px;margin:auto;padding:45px 0 62px}
.weekly-ai-reader .weekly-ai-back{font-size:12px;color:#506073;text-decoration:none}
.weekly-ai-reader .weekly-ai-label{margin:26px 0 10px;color:#a16a42;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.10em}
.weekly-ai-reader h1{font:500 clamp(34px,5vw,57px)/1.09 Georgia,serif;color:#172a40;margin:0 0 17px}
.weekly-ai-reader .weekly-ai-subtitle{font-size:18px;line-height:1.5;color:#57616c;max-width:780px}
.weekly-ai-reader .weekly-ai-bylines{font-size:12px;color:#7a8086;margin:14px 0 30px}
.weekly-ai-reader .weekly-ai-body{background:#fff;border:1px solid #e5ded4;border-top:3px solid var(--copper);padding:clamp(20px,4vw,42px)}
.weekly-ai-reader .weekly-ai-body p{font-size:16px;line-height:1.7;color:#283540;margin:0 0 17px}
.weekly-ai-reader .weekly-ai-body strong{color:#162b42}
.weekly-ai-reader .weekly-ai-body a{color:#905e3b;font-weight:650}
.weekly-ai-reader .weekly-ai-source-note{font-size:12px!important;color:#66717b!important;margin:20px 0!important;padding-top:13px;border-top:1px solid #eee7dd}
.weekly-ai-reader .article-share{margin-top:30px}
@media(max-width:700px){.weekly-ai-section{padding-top:25px;padding-bottom:25px}.weekly-ai-reader{padding:20px 0 44px}}
</style>
"""


def inject_weekly_brief_landing(document: str, briefs: list["CmsArticle"]) -> str:
    """Add a compact editorial rail only when at least one edition is published."""
    if not briefs:
        return document

    from site_cms import article_relative_url

    editions = sorted(
        briefs,
        key=lambda item: item.published_at or item.updated_at or item.created_at,
        reverse=True,
    )
    latest, *older = editions
    link = escape(article_relative_url(latest), quote=True)
    archive = ""
    if older:
        items = "".join(
            '<li><a href="' + escape(article_relative_url(item), quote=True) + '" target="_self">'
            + escape(item.published_label) + " · " + escape(item.title) + "</a></li>"
            for item in older[:8]
        )
        archive = (
            '<details class="weekly-ai-archive"><summary>Previous editions</summary><ul>'
            + items + "</ul></details>"
        )
    section = (
        '<section class="section paper weekly-ai-section" id="weekly-ai">'
        '<div class="container"><div class="weekly-ai-panel">'
        '<div class="weekly-ai-top"><span>WEEKLY AI · QUICK CONTEXT</span><span>'
        + escape(latest.published_label)
        + ' · 1 min read</span></div>'
        '<h2>AI in one minute.</h2>'
        '<p>' + escape(latest.excerpt or latest.subtitle) + '</p>'
        '<a class="weekly-ai-action" href="' + link + '" target="_self" data-hq-event="weekly_ai_open">'
        'Start reading · 1 min →</a>'
        + archive + '</div></div></section>'
    )
    anchor = '<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Current questions</p>'
    if anchor in document:
        return WEEKLY_CSS + document.replace(anchor, section + anchor, 1)
    return WEEKLY_CSS + section + document


def render_weekly_brief_article(article: "CmsArticle", share_footer: str) -> str:
    """Source-first reading view without a large essay cover or invented attribution."""
    from site_components import footer, nav
    from thinking_core import THINKING_CSS

    return (
        THINKING_CSS + WEEKLY_CSS + nav("thinking")
        + '<main><section class="section paper"><div class="container">'
        '<div class="weekly-ai-reader">'
        '<a class="weekly-ai-back" href="?page=thinking#weekly-ai" target="_self">← Back to Thinking</a>'
        '<div class="weekly-ai-label">WEEKLY AI · QUICK CONTEXT</div>'
        '<h1>' + escape(article.title) + '</h1>'
        '<p class="weekly-ai-subtitle">' + escape(article.subtitle or article.excerpt) + '</p>'
        '<div class="weekly-ai-bylines">' + escape(article.published_label)
        + ' · 1 min read · Curated by ' + escape(article.author_name) + '</div>'
        '<article class="weekly-ai-body">' + article.content_html
        + '<p class="weekly-ai-source-note">Selected from Google Alerts and checked against linked publishers. '
        'External reporting is attributed to its original source.</p></article>'
        + share_footer + '</div></div></section></main>' + footer()
    )
