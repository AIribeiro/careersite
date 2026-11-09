"""Consistent end-of-page navigation for the portfolio's core pages.

The section is adapted to the page being read and never recommends itself.
All cards are first-party links and share the same tested CSS design.
"""
from __future__ import annotations

from html import escape
from typing import NamedTuple


class Destination(NamedTuple):
    number: str
    category: str
    title: str
    description: str
    call_to_action: str
    page: str
    analytics_event: str


# Preserve the originally published About routes, wording and analytics events.
DESTINATIONS = (
    Destination("01", "Leadership experience", "What I’ve led",
                "Selected responsibilities, trade-offs and contributions from enterprise AI and Data work.",
                "Explore experience", "impact", "about_next_impact"),
    Destination("02", "Governance & adoption", "How I approach the work",
                "The operating choices behind ownership, responsible use and bringing AI into everyday work.",
                "Explore governance", "ai-data-governance", "about_next_governance"),
    Destination("03", "Writing & perspectives", "How I think",
                "Articles, Weekly AI and Executive AI Briefings on the decisions facing business leaders.",
                "Explore Thinking", "thinking", "about_next_thinking"),
)

# Shared destination vocabulary. A destination is selected only when it is not
# the active page, avoiding confusing self-links.
_CARDS = {
    "impact": ("Leadership experience", "What I’ve led",
               "The responsibilities, choices and evidence behind my enterprise AI and Data work.",
               "Explore experience"),
    "ai-data-governance": ("Governance & adoption", "How I approach the work",
                           "How ownership, decision rights and practical controls support responsible AI use.",
                           "Explore governance"),
    "thinking": ("Writing & perspectives", "How I think",
                 "Articles, Weekly AI and Executive AI Briefings on enterprise AI decisions.",
                 "Explore Thinking"),
    "briefings": ("Executive AI Briefings", "Decisions for leaders",
                  "Focused executive guides to choices around governance, value and adoption.",
                  "Read the briefings"),
    "about": ("The personal journey", "Who I am",
              "The places, cultures and experiences that have shaped my work with people.",
              "Explore my story"),
}

# Three destinations per page, ordered to serve a realistic next intent.
_PAGE_ROUTES = {
    "impact": ("ai-data-governance", "thinking", "about"),
    "ai-data-governance": ("impact", "briefings", "about"),
    "thinking": ("impact", "ai-data-governance", "about"),
    "contact": ("impact", "ai-data-governance", "thinking"),
}

_PAGE_COPY = {
    "about": (
        "From the story to the work.",
        "You’ve read a little about my journey. These are three ways to explore "
        "the responsibilities, choices and perspectives behind my work in AI and Data.",
    ),
    "impact": (
        "Explore the thinking behind the experience.",
        "The experience is one part of the picture. Continue with the governance "
        "choices, published perspectives or the personal story behind the work.",
    ),
    "ai-data-governance": (
        "Connect governance with the wider picture.",
        "Explore the experience behind this approach, decisions covered in "
        "Executive AI Briefings or the professional journey that shaped my perspective.",
    ),
    "thinking": (
        "Beyond the articles.",
        "Explore the leadership experience, operating approach and personal journey "
        "behind the perspectives shared here.",
    ),
    "contact": (
        "A little more context before we connect.",
        "If you would like to explore the work first, these three destinations "
        "offer a practical view of my experience, approach and published perspectives.",
    ),
}


def _destinations_for(page: str) -> tuple[Destination, ...]:
    if page == "about":
        return DESTINATIONS
    if page not in _PAGE_ROUTES:
        raise ValueError(f"Unsupported portfolio navigation page: {page}")
    return tuple(
        Destination(f"{index:02d}", *_CARDS[route], route, f"{page}_next_{route.replace('-', '_')}")
        for index, route in enumerate(_PAGE_ROUTES[page], 1)
    )


def portfolio_next_navigation(page: str) -> str:
    """Render the same three-card closing design, tailored to the current page."""
    if page not in _PAGE_COPY:
        raise ValueError(f"Unsupported portfolio navigation page: {page}")
    destinations = _destinations_for(page)
    title, introduction = _PAGE_COPY[page]
    cards = []
    for dest in destinations:
        cards.append(
            f'<a class="about-next-card" href="?page={escape(dest.page, quote=True)}" '
            f'target="_self" data-hq-event="{escape(dest.analytics_event, quote=True)}">'
            '<span class="about-next-card-head">'
            f'<span class="about-next-card-category">{escape(dest.category)}</span>'
            f'<span class="about-next-card-number" aria-hidden="true">{dest.number}</span>'
            '</span>'
            f'<strong class="about-next-card-title">{escape(dest.title)}</strong>'
            f'<span class="about-next-card-description">{escape(dest.description)}</span>'
            '<span class="about-next-card-action">'
            f'<span>{escape(dest.call_to_action)}</span>'
            '<span class="about-next-card-arrow" aria-hidden="true">↗</span>'
            '</span></a>'
        )

    # Contact itself has clear direct-contact actions in its own footer;
    # repeating a Contact CTA in the closing navigator would go nowhere.
    if page == "contact":
        secondary = (
            '<span>Interested in the person behind the work?</span>'
            '<a href="?page=about" target="_self" '
            'data-hq-event="contact_next_about">Read About '
            '<span aria-hidden="true">↗</span></a>'
        )
    else:
        secondary = (
            '<span>Would you rather start a conversation?</span>'
            '<a href="?page=contact" target="_self" '
            f'data-hq-event="{page}_next_contact">Get in touch '
            '<span aria-hidden="true">↗</span></a>'
        )
    return (
        f'<section class="about-next portfolio-next" id="{escape(page, quote=True)}-continue" '
        f'data-analytics-section="{escape(page, quote=True)}-next-destinations" '
        f'aria-labelledby="{escape(page, quote=True)}-next-title">'
        '<div class="container">'
        '<div class="about-next-header">'
        '<div><p class="eyebrow">Where to next?</p>'
        f'<h2 id="{escape(page, quote=True)}-next-title">{escape(title)}</h2></div>'
        f'<p>{escape(introduction)}</p>'
        '</div>'
        '<nav class="about-next-grid" aria-label="Continue exploring the portfolio">'
        + "".join(cards) + '</nav>'
        f'<div class="about-next-contact">{secondary}</div>'
        '</div></section>'
    )


def about_next_navigation() -> str:
    """Backwards-compatible About renderer used by the live About page."""
    return portfolio_next_navigation("about")
