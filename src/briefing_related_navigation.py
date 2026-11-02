from __future__ import annotations

"""Contextual next-reading paths for Executive AI Briefings.

The editorial graph explains why the next read matters, while a conservative
topic-based fallback supports future releases. Recommendations are resolved
against published CMS records only; the current edition is never returned.
"""

from html import escape
import re
from typing import Iterable


# Written as decision continuations rather than a static list of popular posts.
# Relevance stays stable as new editions are published; missing or unpublished
# references are skipped and filled by the topic-based fallback.
EDITORIAL_PATHS: dict[str, tuple[tuple[str, str], ...]] = {
    "ai-capabilities-executive-decisions": (
        (
            "seven-questions-for-better-ai-decisions",
            "Now challenge whether the proposed capability solves the right problem.",
        ),
        (
            "ai-governance-explained-to-executives",
            "See what ownership and controls are needed before the system can act.",
        ),
    ),
    "seven-questions-for-better-ai-decisions": (
        (
            "data-governance-what-deserves-funding",
            "Turn the evidence you requested into a defensible investment decision.",
        ),
        (
            "data-governance-vs-ai-governance-executive-decisions",
            "Separate the evidence the data owner and AI owner need to provide.",
        ),
    ),
    "ai-governance-explained-to-executives": (
        (
            "data-governance-vs-ai-governance-executive-decisions",
            "Clarify where information ownership ends and AI assurance begins.",
        ),
        (
            "eu-ai-act-what-executives-must-decide",
            "Connect the operating controls to role-specific legal obligations.",
        ),
    ),
    "eu-ai-act-what-executives-must-decide": (
        (
            "ai-governance-explained-to-executives",
            "Translate the regulatory assessment into operating controls.",
        ),
        (
            "data-governance-vs-ai-governance-executive-decisions",
            "Understand the two evidence streams behind a release decision.",
        ),
    ),
    "data-governance-what-deserves-funding": (
        (
            "data-governance-vs-ai-governance-executive-decisions",
            "Distinguish the data investment from assurance of AI-enabled work.",
        ),
        (
            "seven-questions-for-better-ai-decisions",
            "Pressure-test the assumptions before committing more funding.",
        ),
    ),
    "data-governance-vs-ai-governance-executive-decisions": (
        (
            "ai-governance-explained-to-executives",
            "Move from the ownership boundary to practical operating controls.",
        ),
        (
            "data-governance-what-deserves-funding",
            "Build the investment case for the information controls you need.",
        ),
    ),
}

EDITORIAL_INTROS: dict[str, str] = {
    "ai-capabilities-executive-decisions": (
        "Once the capability is clear, test whether the work justifies it and what controls it needs."
    ),
    "seven-questions-for-better-ai-decisions": (
        "The questions reveal the uncertainty. Continue into evidence, ownership and funding."
    ),
    "ai-governance-explained-to-executives": (
        "The control architecture is only the start. Clarify overlapping responsibilities and obligations."
    ),
    "eu-ai-act-what-executives-must-decide": (
        "Regulatory classification informs the decision; operating ownership makes it real."
    ),
    "data-governance-what-deserves-funding": (
        "A funded control still needs clear boundaries, operational ownership and a review."
    ),
    "data-governance-vs-ai-governance-executive-decisions": (
        "Separate responsibilities are useful only when the business can approve and govern the work."
    ),
}

DEFAULT_RATIONALE = (
    "Continue the decision with another executive perspective on ownership, evidence and action."
)
_SKIP_WORDS = {
    "and", "the", "from", "when", "what", "which", "with", "for", "into", "about",
    "that", "this", "have", "need", "your", "their", "will", "data", "executive",
    "briefing", "briefings", "explained", "decisions", "decision",
}


def _tokens(article) -> set[str]:
    pieces = [
        str(getattr(article, "title", "") or ""),
        str(getattr(article, "subtitle", "") or ""),
        str(getattr(article, "category", "") or ""),
        " ".join(getattr(article, "keywords", ()) or ()),
    ]
    return {
        token for token in re.findall(r"[a-z0-9]+", " ".join(pieces).lower())
        if len(token) > 3 and token not in _SKIP_WORDS
    }


def _eligible(current, published: Iterable) -> dict[str, object]:
    current_slug = str(getattr(current, "slug", "") or "")
    choices: dict[str, object] = {}
    for article in published:
        slug = str(getattr(article, "slug", "") or "")
        if (
            not slug
            or slug == current_slug
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
            or str(getattr(article, "kind", "")).strip().casefold() != "executive briefing"
            or str(getattr(article, "status", "")).strip().casefold() != "published"
            or not str(getattr(article, "title", "")).strip()
        ):
            continue
        choices.setdefault(slug, article)
    return choices


def related_briefings(current, published: Iterable, *, limit: int = 2) -> list[tuple[object, str]]:
    """Return 0–2 unique published next reads with their editorial rationale."""
    if limit <= 0:
        return []
    limit = min(2, limit)
    eligible = _eligible(current, published)
    recommendations: list[tuple[object, str]] = []
    seen: set[str] = set()

    def add(slug: str, reason: str) -> None:
        if slug in eligible and slug not in seen and len(recommendations) < limit:
            recommendations.append((eligible[slug], reason))
            seen.add(slug)

    for slug, reason in EDITORIAL_PATHS.get(str(getattr(current, "slug", "") or ""), ()):
        add(slug, reason)

    if len(recommendations) < limit:
        source_tokens = _tokens(current)
        remaining = [article for slug, article in eligible.items() if slug not in seen]
        remaining.sort(
            key=lambda article: (
                -len(source_tokens & _tokens(article)),
                -int(bool(source_tokens & _tokens(article))),
                str(getattr(article, "title", "")).casefold(),
                str(getattr(article, "slug", "")),
            )
        )
        for article in remaining:
            add(article.slug, DEFAULT_RATIONALE)

    return recommendations


RELATED_CSS = """<style>
.site .ebr-related{background:#f3f1ec;border-top:1px solid #d8d6d0;padding:clamp(38px,5vw,70px) 0 clamp(48px,6vw,78px);color:#1d374a}
.site .ebr-related-inner{max-width:1150px;margin-inline:auto;padding-inline:clamp(18px,3vw,32px)}
.site .ebr-related-head{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;margin-bottom:23px}
.site .ebr-related-kicker{font:800 10px/1.4 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#966a49;display:block;margin-bottom:10px}
.site .ebr-related-head h2{font:500 clamp(29px,3.6vw,43px)/1.16 Georgia,serif;color:#19384b;margin:0 0 10px}
.site .ebr-related-head p{font:400 14px/1.6 Arial,sans-serif;color:#4b6371;max-width:680px;margin:0}
.site .ebr-related-more{flex-shrink:0;font:800 12px/1.4 Arial,sans-serif;color:#8b5c3b!important;text-decoration:none!important;border-bottom:1px solid #b98d6d;padding:8px 0;white-space:nowrap}
.site .ebr-related-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.site .ebr-related-card{min-width:0;display:flex;flex-direction:column;background:#fffefa;text-decoration:none!important;border:1px solid #dedbd4;border-top:4px solid #a27755;border-radius:4px;padding:clamp(21px,2.4vw,29px);box-shadow:0 10px 26px rgba(21,45,60,.045);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.site .ebr-related-card:nth-child(2){border-top-color:#467883}
.site .ebr-related-card:hover{transform:translateY(-3px);border-color:#9d8977;box-shadow:0 18px 36px rgba(21,45,60,.10)}
.site .ebr-related-card:focus-visible,.site .ebr-related-more:focus-visible{outline:3px solid #2b6f8a;outline-offset:4px}
.site .ebr-related-step{font:800 10px/1.4 Arial,sans-serif;letter-spacing:.12em;color:#95694b;text-transform:uppercase;margin-bottom:13px}
.site .ebr-related-card h3{font:500 clamp(21px,2.25vw,28px)/1.22 Georgia,serif!important;color:#1d3d4f!important;margin:0 0 13px!important;overflow-wrap:anywhere}
.site .ebr-related-card p{font:400 13px/1.6 Arial,sans-serif;color:#536774!important;margin:0 0 23px;flex:1}
.site .ebr-related-card-bottom{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-top:15px;border-top:1px solid #e3e2db}
.site .ebr-related-time{font:700 11px/1.5 Arial,sans-serif;color:#687982}
.site .ebr-related-action{font:800 12px/1.45 Arial,sans-serif;color:#8b5d3e}
@media(max-width:800px){.site .ebr-related-head{display:block}.site .ebr-related-more{display:inline-block;margin-top:15px}}
@media(max-width:650px){.site .ebr-related-grid{grid-template-columns:1fr}.site .ebr-related{padding:31px 0 50px}.site .ebr-related-card{padding:22px}}
@media(prefers-reduced-motion:reduce){.site .ebr-related-card{transition:none}.site .ebr-related-card:hover{transform:none}}
</style>"""


def render_related_briefings(current, published: Iterable) -> str:
    """Premium contextual end-of-briefing navigation. No draft links or self-links."""
    if str(getattr(current, "kind", "")).strip().casefold() != "executive briefing":
        return ""
    if str(getattr(current, "status", "")).strip().casefold() != "published":
        return ""

    recs = related_briefings(current, published)
    from site_cms import article_relative_url

    cards = []
    for index, (article, reason) in enumerate(recs, start=1):
        url = escape(article_relative_url(article), quote=True)
        slug = escape(str(article.slug), quote=True)
        title = escape(str(article.title))
        read_time = max(1, int(getattr(article, "read_minutes", 1) or 1))
        cards.append(
            f'<a class="ebr-related-card" href="{url}" target="_self" '
            'data-hq-event="briefing_related_open" '
            f'data-hq-content-slug="{slug}" '
            f'aria-label="Read next briefing: {escape(str(article.title), quote=True)}">'
            f'<span class="ebr-related-step">Recommended {index:02d}</span>'
            f'<h3>{title}</h3>'
            f'<p>{escape(reason)}</p>'
            '<span class="ebr-related-card-bottom">'
            f'<span class="ebr-related-time">{read_time} min read</span>'
            '<strong class="ebr-related-action">Read briefing →</strong>'
            '</span></a>'
        )

    if not cards:
        return ""

    intro = EDITORIAL_INTROS.get(str(getattr(current, "slug", "") or ""),
        "Continue from this decision to the next question of ownership, evidence or business value."
    )
    return (
        RELATED_CSS
        + '<section class="ebr-related" data-analytics-section="briefings-related-reading" '
        'aria-labelledby="ebr-related-heading">'
        '<div class="ebr-related-inner">'
        '<div class="ebr-related-head"><div>'
        '<span class="ebr-related-kicker">The executive reading path</span>'
        '<h2 id="ebr-related-heading">Where to go next</h2>'
        f'<p>{escape(intro)}</p>'
        '</div>'
        '<a class="ebr-related-more" href="?page=briefings" target="_self" '
        'data-hq-event="briefing_related_library">Explore the briefing library →</a>'
        '</div>'
        '<div class="ebr-related-grid" role="navigation" '
        'aria-label="Recommended Executive AI Briefings">'
        + "".join(cards)
        + '</div></div></section>'
    )


def insert_related_navigation(document: str, current, published: Iterable) -> str:
    """Insert the reading path before the shared final contact footer.

    All independent readers close with the 'Have an AI choice that needs a
    clearer answer?' section. That call to action must remain the final
    content section, followed only by the site footer.
    """
    if 'data-analytics-section="briefings-related-reading"' in document:
        return document
    related = render_related_briefings(current, published)
    if not related:
        return document
    main, main_close, trailing = document.rpartition("</main>")
    if not main_close:
        return document
    contact_anchor = (
        '<section class="briefings-conversation" '
        'data-analytics-section="briefings-contact">'
    )
    lead, marker, contact_and_after = main.rpartition(contact_anchor)
    if marker:
        return lead + related + marker + contact_and_after + main_close + trailing
    # Safety fallback for a future reader without the standard contact footer.
    # Keep the document intact rather than adding an unexpected second CTA.
    return main + related + main_close + trailing
