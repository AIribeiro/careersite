"""Colleague and manager recommendations for the About page.

The source is the supplied LinkedIn recommendation archive in data/. The public
page includes the full wording for each recommendation, but only the four most
relevant recent recommendations are prominent; older endorsements remain easy
to open. No network requests, client scripts or profile images.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from html import escape
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "linkedin_recommendations.json"

RECOMMENDATIONS_CSS = """<style>
.site .about-recommendations{background:#f5f1eb;padding:70px 0 76px;border-block:1px solid #dfd7ce}
.site .about-rec-header{display:flex;align-items:end;justify-content:space-between;gap:28px;margin-bottom:28px}
.site .about-rec-header h2{font:500 clamp(32px,4vw,49px)/1.08 Georgia,serif;letter-spacing:-.025em;max-width:760px;margin:0;color:#1c2c3d}
.site .about-rec-intro{font:400 14px/1.65 Arial,sans-serif;color:#55616e;max-width:850px;margin:18px 0 0}
.site .about-rec-count{display:inline-block;color:#95623e;font:800 11px/1.4 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;border-bottom:1px solid #bc9879;padding-bottom:9px}
.site .about-rec-featured{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:stretch}
.site .about-rec-card{display:flex;flex-direction:column;min-width:0;border:1px solid #e0d9d2;border-top:3px solid #b9815e;background:#fffdf9;padding:28px 29px 25px}
.site .about-rec-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
.site .about-rec-type{font:800 10px/1.5 Arial,sans-serif;letter-spacing:.11em;text-transform:uppercase;color:#a66e4b}
.site .about-rec-date{font:650 11px/1.5 Arial,sans-serif;color:#7a8590;white-space:nowrap}
.site .about-rec-card h3{font:500 clamp(24px,2.65vw,30px)/1.18 Georgia,serif;letter-spacing:-.01em;color:#1c3045;margin:16px 0 7px}
.site .about-rec-role{font:650 12px/1.5 Arial,sans-serif;color:#3e5367;margin:0;overflow-wrap:anywhere}
.site .about-rec-rel{font:500 11px/1.55 Arial,sans-serif;color:#687685;margin:10px 0 0}
.site .about-rec-pull{font:500 18px/1.55 Georgia,serif;color:#2e3f4b;max-width:660px;margin:20px 0 19px}
.site .about-rec-actions{display:flex;gap:15px;flex-wrap:wrap;margin-top:auto;border-top:1px solid #e7dfd7;padding-top:15px}
.site .about-rec-link{font:750 12px/1.4 Arial,sans-serif;color:#34516e!important;text-decoration:underline!important;text-underline-offset:4px}
.site .about-rec-card details{width:100%;margin:0}
.site .about-rec-card summary{cursor:pointer;color:#8f5937;font:750 12px/1.5 Arial,sans-serif;list-style-position:inside}
.site .about-rec-card details[open] summary{margin-bottom:13px}
.site .about-rec-full{padding:15px 0 0;margin-top:15px;border-top:1px solid #ece5dd}
.site .about-rec-full p{font:400 13px/1.75 Arial,sans-serif;white-space:pre-line;margin:0;color:#46525d}
.site .about-rec-language{font:600 10px/1.5 Arial,sans-serif;color:#82909a;display:block;margin-top:10px}\n.site .about-rec-translation{margin:12px 0 0!important;font:400 12px/1.6 Arial,sans-serif;color:#596b76}
.site .about-rec-archive{margin-top:24px;padding:23px 27px;border:1px solid #d8cec4;background:#fefcf9}
.site .about-rec-archive>summary{cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:20px;color:#263f54;font:500 22px/1.35 Georgia,serif}
.site .about-rec-archive>summary::marker{color:#9c6a4a}
.site .about-rec-archive>summary small{font:700 11px/1.4 Arial,sans-serif;color:#8b6b56;white-space:nowrap}
.site .about-rec-archive[open]>summary{padding-bottom:19px;border-bottom:1px solid #e0d7cb}
.site .about-rec-subgroup{margin:26px 0 7px}
.site .about-rec-subgroup h3{font:500 25px/1.2 Georgia,serif;margin:0 0 11px;color:#1e3245}
.site .about-rec-subgroup>p{font:400 12px/1.6 Arial,sans-serif;color:#67737c;margin:0 0 12px}
.site .about-rec-list{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px}
.site .about-rec-item{min-width:0;background:#fff;border:1px solid #e8e1d9;padding:17px 19px}
.site .about-rec-item>summary{cursor:pointer;list-style-position:outside;margin-left:15px}
.site .about-rec-item .about-rec-item-name{font:500 19px/1.25 Georgia,serif;color:#243b51}
.site .about-rec-item .about-rec-item-meta{display:block;margin:6px 0 0;font:500 11px/1.45 Arial,sans-serif;color:#697784}
.site .about-rec-item[open]{grid-column:span 1;border-color:#c7ae96}
.site .about-rec-item-body{margin-top:17px;padding-top:15px;border-top:1px solid #e8e0d9}
.site .about-rec-item-body .about-rec-role{margin-bottom:9px}
.site .about-rec-item-body .about-rec-full{border-top:0;padding-top:0;margin-top:12px}
.site .about-rec-item-body .about-rec-link{display:inline-block;margin-top:12px}
.site .about-rec-note{margin:18px 0 0;color:#6f7882;font:400 11px/1.6 Arial,sans-serif}
@media(max-width:800px){.site .about-rec-header{display:block}.site .about-rec-count{margin-top:18px}.site .about-rec-featured,.site .about-rec-list{grid-template-columns:minmax(0,1fr)}.site .about-rec-card{padding:24px}.site .about-rec-archive{padding:18px}.site .about-rec-archive>summary{font-size:19px}.site .about-rec-archive>summary small{white-space:normal}}
@media(max-width:480px){.site .about-recommendations{padding:42px 0 47px}.site .about-rec-top{flex-direction:column;gap:4px}.site .about-rec-pull{font-size:17px}.site .about-rec-archive>summary{display:block}.site .about-rec-archive>summary small{display:block;margin-top:7px}}
</style>"""


@lru_cache(maxsize=1)
def load_recommendations() -> tuple[dict[str, object], ...]:
    data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    return tuple(item for item in data["reviews"] if item.get("name") and item.get("quote"))


def _h(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _date(value: str) -> str:
    return date.fromisoformat(value).strftime("%-d %B %Y")


def _excerpt(quote: str, max_chars: int = 205) -> str:
    normalized = " ".join(quote.split())
    if len(normalized) <= max_chars:
        return normalized
    cut = normalized.rfind(" ", 0, max_chars)
    return normalized[:cut if cut > 80 else max_chars].rstrip(" ,;") + "…"


def _profile_link(item: dict[str, object]) -> str:
    url = str(item.get("profile_url") or "")
    if url.startswith(("https://www.linkedin.com/in/", "https://pl.linkedin.com/in/",
                       "https://se.linkedin.com/in/", "https://in.linkedin.com/in/",
                       "https://it.linkedin.com/in/", "https://uk.linkedin.com/in/")):
        return (
            f'<a class="about-rec-link" href="{_h(url)}" target="_blank" '
            f'rel="noopener noreferrer" data-hq-event="about_recommendation_profile">'
            'LinkedIn profile ↗</a>'
        )
    # Do not pretend that search results are an authenticated person profile.
    name = str(item["name"])
    search = "https://www.linkedin.com/search/results/people/?keywords=" + quote(name)
    return (
        f'<a class="about-rec-link" href="{_h(search)}" target="_blank" '
        f'rel="noopener noreferrer" data-hq-event="about_recommendation_search">'
        'Find on LinkedIn ↗</a>'
    )


def _quote(item: dict[str, object]) -> str:
    quote = _h(item["quote"])
    note = str(item.get("language_note") or "")
    lang = f'<span class="about-rec-language">{_h(note)}</span>' if note else ""
    translation = str(item.get("translation") or "")
    translated = (
        f'<p class="about-rec-translation"><strong>English translation:</strong> {_h(translation)}</p>'
        if translation else ""
    )
    return f'<div class="about-rec-full"><p>{quote}</p>{lang}{translated}</div>'


def _featured(item: dict[str, object]) -> str:
    return (
        '<article class="about-rec-card">'
        '<div class="about-rec-top"><span class="about-rec-type">Professional recommendation</span>'
        f'<time class="about-rec-date" datetime="{_h(item["date"])}">{_h(_date(str(item["date"])))}</time></div>'
        f'<h3>{_h(item["name"])}</h3>'
        f'<p class="about-rec-role">{_h(item["role"])}</p>'
        f'<p class="about-rec-rel">{_h(item["relationship"])}</p>'
        f'<p class="about-rec-pull">“{_h(_excerpt(str(item["quote"])))}”</p>'
        '<div class="about-rec-actions">'
        '<details><summary>Read the complete recommendation</summary>'
        f'{_quote(item)}</details>'
        f'{_profile_link(item)}</div></article>'
    )


def _archive_item(item: dict[str, object]) -> str:
    return (
        '<details class="about-rec-item">'
        f'<summary><span class="about-rec-item-name">{_h(item["name"])}</span>'
        f'<span class="about-rec-item-meta">{_h(_date(str(item["date"])))} · {_h(item["relationship"])}</span></summary>'
        '<div class="about-rec-item-body">'
        f'<p class="about-rec-role">{_h(item["role"])}</p>'
        f'{_quote(item)}'
        f'{_profile_link(item)}</div></details>'
    )


def recommendations_section() -> str:
    records = load_recommendations()
    lead_order = {
        "Claes Sandros": 0,
        "Anna Börjesson Sandberg": 1,
        "Kumara Datta": 2,
        "Jim Edwards": 3,
    }
    featured = sorted(
        (item for item in records if item.get("featured")),
        key=lambda item: lead_order.get(str(item["name"]), 99),
    )
    remaining = [item for item in records if not item.get("featured")]
    groups = (
        ("Community & leadership", "Volunteering, developing others, and cross-cultural work."),
        ("Enterprise technology & collaboration", "Earlier management, technical delivery, and cross-functional work."),
    )
    archives = []
    for heading, description in groups:
        items = [item for item in remaining if item.get("group") == heading]
        if not items:
            continue
        archives.append(
            '<section class="about-rec-subgroup">'
            f'<h3>{_h(heading)}</h3><p>{_h(description)}</p>'
            f'<div class="about-rec-list">{"".join(_archive_item(item) for item in items)}</div>'
            '</section>'
        )

    return (
        RECOMMENDATIONS_CSS
        + '<section class="about-recommendations" id="recommendations" '
        'data-analytics-section="about-professional-recommendations">'
        '<div class="container">'
        '<header class="about-rec-header"><div>'
        '<p class="eyebrow">Independent perspectives · Colleagues and managers</p>'
        '<h2>What people who have worked with me say.</h2>'
        '<p class="about-rec-intro">These recommendations come from managers, colleagues, '
        'cross-functional partners and community collaborators. Their words offer an '
        'outside view of how I work with people, lead AI conversations, and approach '
        'responsibility. The original recommendation text is available for every entry.</p>'
        '</div>'
        f'<span class="about-rec-count">{len(records)} recommendations</span>'
        '</header>'
        f'<div class="about-rec-featured">{"".join(_featured(item) for item in featured)}</div>'
        '<details class="about-rec-archive">'
        f'<summary>Earlier professional and community recommendations <small>{len(remaining)} recommendations · Open archive</small></summary>'
        + "".join(archives) +
        '<p class="about-rec-note">Dates and working relationships reflect the recommendation '
        'information supplied from LinkedIn. Role descriptions are reproduced from that record. '
        'A “Find on LinkedIn” link means the direct profile could not be confirmed.</p>'
        '</details></div></section>'
    )
