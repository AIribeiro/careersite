"""A deliberate next step for readers who reach the end of About.

Keep links static and dependable. This is navigation, not a rotating article
recommendation or a second Home page.
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


DESTINATIONS = (
    Destination(
        "01",
        "Leadership experience",
        "What I’ve led",
        "Selected responsibilities, trade-offs and contributions from enterprise AI and Data work.",
        "Explore experience",
        "impact",
        "about_next_impact",
    ),
    Destination(
        "02",
        "Governance & adoption",
        "How I approach the work",
        "The operating choices behind ownership, responsible use and bringing AI into everyday work.",
        "Explore governance",
        "ai-data-governance",
        "about_next_governance",
    ),
    Destination(
        "03",
        "Writing & perspectives",
        "How I think",
        "Articles, Weekly AI and Executive AI Briefings on the decisions facing business leaders.",
        "Explore Thinking",
        "thinking",
        "about_next_thinking",
    ),
)


def about_next_navigation() -> str:
    cards = []
    for dest in DESTINATIONS:
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
            '</span>'
            '</a>'
        )

    return (
        '<section class="about-next" id="about-continue" '
        'data-analytics-section="about-next-destinations" '
        'aria-labelledby="about-next-title">'
        '<div class="container">'
        '<div class="about-next-header">'
        '<div><p class="eyebrow">Where to next?</p>'
        '<h2 id="about-next-title">From the story to the work.</h2></div>'
        '<p>You’ve read a little about my journey. These are three ways '
        'to explore the responsibilities, choices and perspectives '
        'behind my work in AI and Data.</p>'
        '</div>'
        '<nav class="about-next-grid" aria-label="Continue exploring the portfolio">'
        + "".join(cards) + '</nav>'
        '<div class="about-next-contact">'
        '<span>Would you rather start a conversation?</span>'
        '<a href="?page=contact" target="_self" '
        'data-hq-event="about_next_contact">Get in touch '
        '<span aria-hidden="true">↗</span></a>'
        '</div></div></section>'
    )
