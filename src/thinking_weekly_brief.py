from __future__ import annotations

import base64
import re
from datetime import date, timedelta
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from site_cms import CmsArticle


BRIEF_KIND = "Weekly Brief"
BRIEF_CATEGORY = "Weekly AI"
SWEDISH_MONTHS = (
    "", "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
)
WEEKLY_ARCHIVE_URL = "?page=thinking&weekly_ai=archive"
WEEKLY_IMAGE_FILE = Path(__file__).resolve().parents[1] / "assets" / "weekly_ai_evergreen_visual.webp"


@lru_cache(maxsize=1)
def _weekly_header_image_uri() -> str:
    """Embed the original evergreen artwork crop without external hosting or stale week text."""
    try:
        payload = WEEKLY_IMAGE_FILE.read_bytes()
    except OSError:
        return ""
    return "data:image/webp;base64," + base64.b64encode(payload).decode("ascii")




def is_weekly_brief(article: "CmsArticle") -> bool:
    """Only the dedicated weekly news format is lifted from the regular essay feed."""
    return (
        (article.kind or "").strip().casefold() == BRIEF_KIND.casefold()
        and (article.category or "").strip().casefold() == BRIEF_CATEGORY.casefold()
    )


def _issue_date(article: "CmsArticle") -> date:
    """Issue date, not email arrival time or last-edited CMS timestamp."""
    found = re.fullmatch(r"weekly-ai-(\d{4}-\d{2}-\d{2})", article.slug or "")
    raw = found.group(1) if found else (
        article.published_at or article.created_at or article.updated_at or ""
    )[:10]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.today()


def edition_week(article: "CmsArticle") -> tuple[int, int, date, date]:
    """Swedish ISO week *covered* by the briefing.

    Monday publications report the completed previous week. The pilot was
    published on Sunday 2026-10-11 and therefore covers ISO week 41 itself.
    ISO week-year is distinct from Gregorian publication year near New Year.
    """
    publication_date = _issue_date(article)
    covered = publication_date - timedelta(days=1) if publication_date.weekday() == 0 else publication_date
    monday = covered - timedelta(days=covered.weekday())
    iso_year, iso_week, _ = monday.isocalendar()
    return iso_year, iso_week, monday, monday + timedelta(days=6)


def _swedish_range(start: date, end: date, *, include_year: bool = True) -> str:
    if start.year == end.year and start.month == end.month:
        dates = f"{start.day}–{end.day} {SWEDISH_MONTHS[end.month]}"
    elif start.year == end.year:
        dates = (
            f"{start.day} {SWEDISH_MONTHS[start.month]}–"
            f"{end.day} {SWEDISH_MONTHS[end.month]}"
        )
    else:
        dates = (
            f"{start.day} {SWEDISH_MONTHS[start.month]} {start.year}–"
            f"{end.day} {SWEDISH_MONTHS[end.month]} {end.year}"
        )
        include_year = False
    return dates + (f" {end.year}" if include_year else "")


def edition_label(article: "CmsArticle") -> str:
    year, week, _, _ = edition_week(article)
    return f"Week {week} · {year}"


def _headline(article: "CmsArticle") -> str:
    return re.sub(r"^\s*weekly\s+ai\s*[—–:\-]\s*", "", article.title or "", flags=re.I).strip()


def sorted_editions(briefs: list["CmsArticle"]) -> list["CmsArticle"]:
    """One public edition per ISO week in descending covered-week order."""
    published = [brief for brief in briefs if brief.status == "published" and is_weekly_brief(brief)]
    ordered = sorted(
        published,
        key=lambda brief: (edition_week(brief)[2], brief.published_at or brief.updated_at or ""),
        reverse=True,
    )
    seen: set[tuple[int, int]] = set()
    unique = []
    for brief in ordered:
        year, week, _, _ = edition_week(brief)
        if (year, week) not in seen:
            unique.append(brief)
            seen.add((year, week))
    return unique


WEEKLY_CSS = """
<style>
/* A standalone editorial feature, deliberately separate from regular article tiles. */
.weekly-ai-section{padding:28px 0 42px!important;background:#f8f5ef!important}
.weekly-ai-brand{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(230px,.7fr);
  min-height:260px;overflow:hidden;background:#0c1829;color:#f9f5ef;border:1px solid #233b50;
  box-shadow:0 10px 25px rgba(13,29,48,.10)}
.weekly-ai-brand-copy{padding:clamp(25px,3.2vw,46px);display:flex;flex-direction:column;justify-content:center}
.weekly-ai-brand-eyebrow{font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#e2a278;margin:0 0 9px}
.weekly-ai-brand h2{font:500 clamp(44px,6vw,86px)/.97 Georgia,serif;
  letter-spacing:-.045em;color:#fff;margin:0 0 14px}
.weekly-ai-brand h2 span{color:#d99669}
.weekly-ai-brand-strap{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.21em;color:#f3c29c;margin:0 0 14px}
.weekly-ai-brand-intro{font-size:15px;line-height:1.65;color:#d2d9e0;max-width:600px;margin:0}
.weekly-ai-brand-art{width:100%;height:100%;min-height:260px;max-height:340px;object-fit:cover;object-position:center 53%;display:block;filter:saturate(.9)}
.weekly-ai-brand-placeholder{background:radial-gradient(circle at 60% 35%,#366280,#0d2237 60%,#091421 100%)}
.weekly-ai-feature{margin-top:0}
.weekly-ai-feature h3{font:500 clamp(31px,3.4vw,44px)/1.12 Georgia,serif;letter-spacing:-.02em;
  color:#fff;margin:15px 0 14px}
.weekly-ai-feature{position:relative;isolation:isolate;overflow:hidden;background:#142437;color:#faf8f4;
  border-top:4px solid #b9794c;box-shadow:0 24px 46px rgba(13,29,48,.16);
  display:grid;grid-template-columns:minmax(0,1.5fr) minmax(230px,.65fr);gap:0}
.weekly-ai-main{padding:clamp(27px,4vw,58px);min-width:0}
.weekly-ai-overline{display:flex;align-items:center;gap:11px;flex-wrap:wrap;
  font-size:11px;font-weight:750;letter-spacing:.15em;color:#e8b68d;text-transform:uppercase}
.weekly-ai-overline span{width:26px;height:2px;display:inline-block;background:#c18b5f}
.weekly-ai-feature h2{font:500 clamp(34px,4.3vw,59px)/1.05 Georgia,serif;
  letter-spacing:-.025em;margin:17px 0 15px;color:#fff}
.weekly-ai-feature .weekly-ai-headline{max-width:680px;margin:0 0 12px;
  font:500 clamp(19px,2.25vw,29px)/1.24 Georgia,serif;color:#f0e1d1}
.weekly-ai-feature .weekly-ai-description{max-width:730px;font-size:15px;line-height:1.67;
  color:#d0d8df;margin:0 0 25px}
.weekly-ai-actions{display:flex;gap:17px;align-items:center;flex-wrap:wrap}
.weekly-ai-action{background:#e8c5a3;color:#16273a!important;padding:13px 19px;
  border-radius:2px;text-decoration:none!important;font-size:12px;font-weight:850;
  display:inline-flex;align-items:center;min-height:44px}
.weekly-ai-action:hover,.weekly-ai-action:focus-visible{background:#fff0df}
.weekly-ai-archive-link{color:#f2dcc5!important;text-decoration:underline;text-underline-offset:5px;
  font-weight:750;font-size:12px;min-height:44px;display:inline-flex;align-items:center}
.weekly-ai-side{border-left:1px solid rgba(255,255,255,.16);padding:clamp(26px,3.5vw,50px) clamp(22px,3vw,42px);
  background:rgba(255,255,255,.045);display:flex;flex-direction:column;justify-content:center}
.weekly-ai-side-label{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:#bac5ce}
.weekly-ai-number{font:500 clamp(79px,11vw,143px)/.97 Georgia,serif;letter-spacing:-.055em;color:#fff;margin:5px 0 9px}
.weekly-ai-number small{font:800 12px/1.2 system-ui,sans-serif;letter-spacing:.13em;
  text-transform:uppercase;display:block;color:#ecc3a0;margin:11px 0 0}
.weekly-ai-dates{font-size:13px;line-height:1.65;color:#d8dfe5;margin-bottom:22px}
.weekly-ai-history{border-top:1px solid rgba(255,255,255,.19);padding-top:17px}
.weekly-ai-history p{font-size:11px;text-transform:uppercase;font-weight:800;letter-spacing:.11em;
  color:#ecc3a0;margin:0 0 9px}
.weekly-ai-history a{display:block;color:#f4f0ed!important;font-size:12px;padding:6px 0;
  text-decoration:none!important;line-height:1.45}
.weekly-ai-history a:hover{text-decoration:underline!important}
.weekly-ai-history a span{color:#bfc9d0}
.weekly-ai-history .weekly-ai-history-empty{color:#c0c9d0;font-size:12px;line-height:1.55;margin:0}
.weekly-ai-audio{margin:12px 0 30px;padding:22px;border:1px solid #d8c7b6;border-left:4px solid #b9794c;background:#fcfaf7}
.weekly-ai-audio-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#7d553d;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:13px}
.weekly-ai-audio audio{width:100%;min-height:45px}
.weekly-ai-audio p{font-size:12px!important;color:#5a6975!important;line-height:1.45!important;margin:12px 0 0!important}
.weekly-ai-reader{max-width:840px;margin:auto;padding:40px 0 60px}
.weekly-ai-back{font-size:12px;color:#506073!important;text-decoration:none!important}
.weekly-ai-label{margin:27px 0 11px;color:#9d643e;font-size:12px;font-weight:850;
  letter-spacing:.11em;text-transform:uppercase}
.weekly-ai-reader h1{font:500 clamp(34px,5vw,58px)/1.12 Georgia,serif;color:#172a40;margin:0 0 15px}
.weekly-ai-subtitle{font-size:18px;line-height:1.5;color:#57616c;max-width:780px}
.weekly-ai-bylines{font-size:12px;color:#66717d;margin:16px 0 27px}
.weekly-ai-body{background:#fff;border:1px solid #e5ded4;border-top:3px solid #b9794c;
  padding:clamp(22px,4vw,41px)}
.weekly-ai-body p{font-size:16px;line-height:1.7;color:#283540;margin:0 0 17px}
.weekly-ai-body strong{color:#162b42}
.weekly-ai-body a{color:#905e3b;font-weight:650}
.weekly-ai-source-note{font-size:12px!important;color:#66717b!important;
  margin:20px 0!important;padding-top:14px;border-top:1px solid #eee7dd}
.weekly-ai-reader .article-share{margin-top:30px}
.weekly-ai-archive-page{padding-top:34px!important}
.weekly-ai-archive-heading{max-width:860px;padding-bottom:25px}
.weekly-ai-archive-heading h1{font:500 clamp(38px,5vw,60px)/1.11 Georgia,serif;
  color:#172a40;margin:20px 0 13px}
.weekly-ai-archive-heading p{font-size:16px;color:#58636c;line-height:1.7;max-width:670px}
.weekly-ai-year{margin:22px 0 40px}
.weekly-ai-year-heading{display:flex;align-items:baseline;gap:15px;border-bottom:1px solid #d9d3ca;
  padding-bottom:10px;margin-bottom:18px}
.weekly-ai-year-heading h2{font:500 30px/1.1 Georgia,serif;margin:0;color:#172a40}
.weekly-ai-year-heading span{font-size:12px;color:#63717b}
.weekly-ai-archive-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.weekly-ai-issue{display:block;background:#fff;border:1px solid #ded7cd;padding:23px;
  min-width:0;text-decoration:none!important;transition:border-color .12s}
.weekly-ai-issue:hover,.weekly-ai-issue:focus-visible{border-color:#b9794c}
.weekly-ai-issue .weekly-ai-issue-week{display:block;color:#aa663b;letter-spacing:.1em;
  text-transform:uppercase;font-weight:850;font-size:11px}
.weekly-ai-issue .weekly-ai-issue-dates{display:block;color:#64717b;font-size:12px;margin:7px 0 16px}
.weekly-ai-issue h3{color:#172a40;font:500 23px/1.18 Georgia,serif;margin:0 0 12px}
.weekly-ai-issue p{color:#5b6570;font-size:13px;line-height:1.55;margin:0 0 16px}
.weekly-ai-issue .weekly-ai-issue-cta{font-size:12px;color:#31506d;font-weight:800}
@media(max-width:1020px){.weekly-ai-archive-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){
  .weekly-ai-section{padding:14px 0 28px!important}
  .weekly-ai-brand{grid-template-columns:1fr;min-height:0}
  .weekly-ai-brand-copy{padding:26px 24px}
  .weekly-ai-brand h2{font-size:clamp(42px,12vw,65px)}
  .weekly-ai-brand-strap{font-size:11px;letter-spacing:.13em}
  .weekly-ai-brand-intro{font-size:14px}
  .weekly-ai-brand-art{max-height:120px;min-height:120px;object-position:center 44%}
  .weekly-ai-feature{grid-template-columns:minmax(0,1fr)}
  .weekly-ai-main{padding:27px 24px 26px}
  .weekly-ai-feature h2{font-size:42px;margin:13px 0}
  .weekly-ai-feature .weekly-ai-headline{font-size:23px}
  .weekly-ai-side{border-left:0;border-top:1px solid rgba(255,255,255,.16);
    padding:17px 24px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);column-gap:15px;align-items:start}
  .weekly-ai-side-label{grid-column:1}
  .weekly-ai-number{grid-column:1;font-size:68px;line-height:1;margin:4px 0 0}
  .weekly-ai-number small{font-size:10px;margin:2px 0 0}
  .weekly-ai-dates{grid-column:2;grid-row:2;margin:6px 0 0;font-size:12px}
  .weekly-ai-history{grid-column:1/-1;margin-top:13px;padding-top:12px}
  .weekly-ai-actions{gap:11px}
  .weekly-ai-reader{padding:24px 0 42px}
  .weekly-ai-archive-grid{grid-template-columns:minmax(0,1fr)}
  .weekly-ai-archive-page{padding-top:22px!important}
}
</style>
"""


def inject_weekly_brief_landing(document: str, briefs: list["CmsArticle"]) -> str:
    """Position the latest issue first, immediately under Thinking navigation."""
    editions = sorted_editions(briefs)
    if not editions:
        return document

    from site_cms import article_relative_url

    latest, *older = editions
    year, week, start, end = edition_week(latest)
    link = escape(article_relative_url(latest), quote=True)
    newest_link = escape(WEEKLY_ARCHIVE_URL, quote=True)
    from weekly_ai_audio import audio_url
    listen_cta = (
        '<a class="weekly-ai-archive-link" href="' + link + '#weekly-ai-audio" '
        'target="_self" data-hq-content-slug="' + escape(latest.slug, quote=True) + '" '
        'data-hq-event="weekly_ai_listen_open">Listen · audio →</a>'
        if audio_url(latest.slug) else ''
    )
    count = len(editions)
    if older:
        recent_items = "".join(
            '<a href="' + escape(article_relative_url(item), quote=True)
            + '" target="_self" data-hq-content-slug="' + escape(item.slug, quote=True) + '" data-hq-event="weekly_ai_previous_open">'
            + escape(edition_label(item))
            + ' <span>· ' + escape(_headline(item)) + '</span></a>'
            for item in older[:2]
        )
    else:
        recent_items = '<p class="weekly-ai-history-empty">The archive begins with this edition. New weeks will appear here automatically.</p>'
    feature = (
        '<section class="section weekly-ai-section" id="weekly-ai" data-analytics-section="weekly-ai-feature" aria-label="Weekly AI briefing">'
        '<div class="container">'
        '<div class="weekly-ai-brand">'
        '<div class="weekly-ai-brand-copy">'
        '<div class="weekly-ai-brand-eyebrow">THINKING · QUICK CONTEXT</div>'
        '<h2>WEEKLY <span>AI</span></h2>'
        '<p class="weekly-ai-brand-strap">A one-minute briefing</p>'
        '<p class="weekly-ai-brand-intro">Selected AI developments, original sources and practical leadership context. A new edition every week.</p>'
        '</div>'
        + ('<img class="weekly-ai-brand-art" src="' + _weekly_header_image_uri() 
           + '" alt="AI briefing artwork: digital globe and modern laptop in a workplace" loading="eager" decoding="async">'
           if _weekly_header_image_uri() else '<div class="weekly-ai-brand-art weekly-ai-brand-placeholder" aria-hidden="true"></div>')
        + '</div>'
        '<div class="weekly-ai-feature">'
        '<div class="weekly-ai-main">'
        '<div class="weekly-ai-overline"><span aria-hidden="true"></span> WEEKLY AI · QUICK CONTEXT</div>'
        '<h3>Latest edition.</h3>'
        '<p class="weekly-ai-headline">' + escape(_headline(latest)) + '</p>'
        '<p class="weekly-ai-description">' + escape(latest.excerpt or latest.subtitle) + '</p>'
        '<div class="weekly-ai-actions">'
        '<a class="weekly-ai-action" href="' + link + '" target="_self" data-hq-content-slug="' + escape(latest.slug, quote=True) + '" data-hq-event="weekly_ai_open">'
        'Start reading · 1 min →</a>'
        + listen_cta
        + '<a class="weekly-ai-archive-link" href="' + newest_link
        + '" target="_self" data-hq-event="weekly_ai_archive_open">'
        'Browse all weeks (' + str(count) + ') →</a></div></div>'
        '<div class="weekly-ai-side">'
        '<div class="weekly-ai-side-label">Swedish calendar week</div>'
        '<div class="weekly-ai-number">' + str(week) + '<small>Week · ' + str(year) + '</small></div>'
        '<div class="weekly-ai-dates">' + escape(_swedish_range(start, end)) + '<br>1 min read</div>'
        '<div class="weekly-ai-history"><p>Previous editions</p>' + recent_items + '</div>'
        '</div></div></div></section>'
    )
    # The feature must be seen before the essay introduction, not buried below Latest articles.
    anchor = "<main>"
    if anchor in document:
        return WEEKLY_CSS + document.replace(anchor, anchor + feature, 1)
    return WEEKLY_CSS + feature + document


def render_weekly_brief_archive(briefs: list["CmsArticle"]) -> str:
    """A permanent, fully populated public archive grouped by Swedish ISO week-year."""
    from site_cms import article_relative_url
    from site_components import footer, nav
    from thinking_core import THINKING_CSS

    editions = sorted_editions(briefs)
    years: dict[int, list["CmsArticle"]] = {}
    for article in editions:
        year, _, _, _ = edition_week(article)
        years.setdefault(year, []).append(article)

    sections = []
    for year, items in years.items():
        links = []
        for article in items:
            _, week, start, end = edition_week(article)
            link = escape(article_relative_url(article), quote=True)
            links.append(
                '<a class="weekly-ai-issue" href="' + link + '" target="_self"'
                ' data-hq-content-slug="' + escape(article.slug, quote=True) + '" data-hq-event="weekly_ai_archive_issue_open">'
                '<span class="weekly-ai-issue-week">Week ' + str(week) + ' · ' + str(year) + '</span>'
                '<span class="weekly-ai-issue-dates">' + escape(_swedish_range(start, end)) + '</span>'
                '<h3>' + escape(_headline(article)) + '</h3>'
                '<p>' + escape(article.excerpt or article.subtitle) + '</p>'
                '<span class="weekly-ai-issue-cta">Read · 1 min →</span></a>'
            )
        sections.append(
            '<section class="weekly-ai-year" aria-label="Weekly AI ' + str(year) + '">'
            '<div class="weekly-ai-year-heading"><h2>' + str(year) + '</h2><span>'
            + str(len(items)) + ' ' + ('week' if len(items) == 1 else 'weeks')
            + '</span></div><div class="weekly-ai-archive-grid">'
            + ''.join(links) + '</div></section>'
        )
    if not editions:
        sections.append(
            '<p>The first weekly edition has not been published yet.</p>'
        )
    return (
        THINKING_CSS + WEEKLY_CSS + nav("thinking")
        + '<main><section class="section paper weekly-ai-archive-page" data-analytics-section="weekly-ai-archive">'
        '<div class="container"><div class="weekly-ai-archive-heading">'
        '<a class="weekly-ai-back" href="?page=thinking#weekly-ai" target="_self">← Back to Thinking</a>'
        '<div class="weekly-ai-label">WEEKLY AI · EVERY EDITION</div>'
        '<h1>The weekly archive.</h1>'
        '<p>One-minute briefings on the most consequential AI developments for enterprise leaders. '
        'Each edition is labeled by the Swedish week it covers, with direct links to the original sources.</p>'
        '</div>' + ''.join(sections) + '</div></section></main>' + footer()
    )


def render_weekly_brief_article(article: "CmsArticle", share_footer: str) -> str:
    """Source-first reader, with the same Swedish ISO week label as its archive entry."""
    from site_components import footer, nav
    from thinking_core import THINKING_CSS
    from weekly_ai_audio import audio_player_html

    year, week, start, end = edition_week(article)
    return (
        THINKING_CSS + WEEKLY_CSS + nav("thinking")
        + '<main><section class="section paper" data-analytics-section="weekly-ai-reader"><div class="container">'
        '<div class="weekly-ai-reader">'
        '<a class="weekly-ai-back" href="?page=thinking#weekly-ai" target="_self">← Back to Thinking</a>'
        '<div class="weekly-ai-label">WEEKLY AI · Week ' + str(week) + ' · ' + str(year) + '</div>'
        '<h1>' + escape(_headline(article)) + '</h1>'
        '<p class="weekly-ai-subtitle">' + escape(article.subtitle or article.excerpt) + '</p>'
        '<div class="weekly-ai-bylines">' + escape(_swedish_range(start, end))
        + ' · 1 min read · Curated by ' + escape(article.author_name) + '</div>'
        + audio_player_html(article.slug)
        + '<article class="weekly-ai-body">' + article.content_html
        + '<p class="weekly-ai-source-note">Personally curated by Jair Ribeiro. I review the reporting, choose the developments '
        'I consider most relevant, and add my own perspective on what they mean for enterprise AI '
        'leadership. Original reporting remains credited to its publishers.</p></article>'
        '<p><a class="weekly-ai-back" href="' + escape(WEEKLY_ARCHIVE_URL, quote=True)
        + '" target="_self">← Browse all Weekly AI editions</a></p>'
        + share_footer + '</div></div></section></main>' + footer()
    )
