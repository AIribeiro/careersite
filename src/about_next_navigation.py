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


# The About design is reused as a contextual, three-route continuation across
# the other main portfolio pages. Each destination excludes the current page.
# The secondary action leads to Contact, except on Contact where it returns Home.
PAGE_CONTINUATIONS = {
    "about": (
        "From the story to the work.",
        "You’ve read a little about my journey. These are three ways to explore "
        "the responsibilities, choices and perspectives behind my work in AI and Data.",
        DESTINATIONS,
        "Would you rather start a conversation?", "Get in touch", "contact",
    ),
    "impact": (
        "Continue from the experience.",
        "Explore how I approach accountability and adoption, read my perspectives, "
        "or learn more about the person behind the work.",
        (
            Destination("01", "Governance & adoption", "How I make AI work",
                        "The approach to ownership, decision rights and responsible AI use.",
                        "Explore governance", "ai-data-governance", "impact_next_governance"),
            Destination("02", "Writing & perspectives", "How I think",
                        "Articles, Weekly AI and executive perspectives on AI decisions.",
                        "Explore Thinking", "thinking", "impact_next_thinking"),
            Destination("03", "Personal perspective", "The journey behind the work",
                        "The international experiences and influences that shaped my approach.",
                        "Explore About", "about", "impact_next_about"),
        ),
        "Want to discuss a leadership challenge?", "Get in touch", "contact",
    ),
    "ai-data-governance": (
        "Connect the principles to practice.",
        "Follow the governance perspective into real leadership responsibilities, "
        "focused executive briefings or the wider professional story.",
        (
            Destination("01", "Leadership experience", "What I’ve led",
                        "Enterprise responsibilities and decisions behind AI and Data work.",
                        "Explore experience", "impact", "governance_next_impact"),
            Destination("02", "Executive decision guides", "Explore the briefings",
                        "Focused perspectives on governance, agents, accountability and business value.",
                        "Read briefings", "briefings", "governance_next_briefings"),
            Destination("03", "Personal perspective", "The journey behind the work",
                        "A little more about the experiences and values behind this approach.",
                        "Explore About", "about", "governance_next_about"),
        ),
        "Working through a similar governance question?", "Get in touch", "contact",
    ),
    "thinking": (
        "Go beyond the articles.",
        "Connect these perspectives with the experience behind them, explore "
        "the operating approach, or read a focused executive briefing.",
        (
            Destination("01", "Leadership experience", "What I’ve led",
                        "Responsibilities, decisions and practical enterprise contributions.",
                        "Explore experience", "impact", "thinking_next_impact"),
            Destination("02", "Governance & adoption", "How I approach the work",
                        "Ownership, accountability and adoption in everyday operations.",
                        "Explore governance", "ai-data-governance", "thinking_next_governance"),
            Destination("03", "Executive decision guides", "Explore the briefings",
                        "Short, focused analysis of choices facing enterprise AI leaders.",
                        "Read briefings", "briefings", "thinking_next_briefings"),
        ),
        "Have a question or perspective to share?", "Get in touch", "contact",
    ),
    "contact": (
        "Explore before we talk.",
        "If you’d like more context first, these sections show the experience, "
        "thinking and practical approach behind my work.",
        (
            Destination("01", "Leadership experience", "What I’ve led",
                        "Selected contributions and responsibilities across enterprise AI and Data.",
                        "Explore experience", "impact", "contact_next_impact"),
            Destination("02", "Governance & adoption", "How I approach the work",
                        "Operating choices for responsible AI use and sustained adoption.",
                        "Explore governance", "ai-data-governance", "contact_next_governance"),
            Destination("03", "Writing & perspectives", "How I think",
                        "Articles, Weekly AI and executive perspectives on AI leadership.",
                        "Explore Thinking", "thinking", "contact_next_thinking"),
        ),
        "Or return to the portfolio overview.", "Back to Home", "home",
    ),
}


def about_next_navigation(page: str = "about") -> str:
    """Render a contextual closing navigation in the established About design."""
    if page not in PAGE_CONTINUATIONS:
        raise ValueError(f"Unsupported portfolio continuation page: {page}")
    heading, description, destinations, prompt, secondary_label, secondary_page = PAGE_CONTINUATIONS[page]
    prefix = "about" if page == "about" else (
        "governance" if page == "ai-data-governance" else page
    )
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
            '</span>'
            '</a>'
        )

    secondary_event = f"{prefix}_next_{'contact' if secondary_page == 'contact' else 'home'}"
    return (
        f'<section class="about-next" id="{prefix}-continue" '
        f'data-analytics-section="{prefix}-next-destinations" '
        f'aria-labelledby="{prefix}-next-title">'
        '<div class="container">'
        '<div class="about-next-header">'
        '<div><p class="eyebrow">Where to next?</p>'
        f'<h2 id="{prefix}-next-title">{escape(heading)}</h2></div>'
        f'<p>{escape(description)}</p>'
        '</div>'
        '<nav class="about-next-grid" aria-label="Continue exploring the portfolio">'
        + "".join(cards) + '</nav>'
        '<div class="about-next-contact">'
        f'<span>{escape(prompt)}</span>'
        f'<a href="?page={escape(secondary_page, quote=True)}" target="_self" '
        f'data-hq-event="{secondary_event}">{escape(secondary_label)} '
        '<span aria-hidden="true">↗</span></a>'
        '</div></div></section>'
    )
