"""Executive editorial navigation for the Home page.

Four intentional entry points, with local SVG line art. No remote icon fonts,
scripts or external image requests are required for the navigation to render.
"""
from __future__ import annotations

from html import escape
from typing import NamedTuple


class Pathway(NamedTuple):
    key: str
    number: str
    label: str
    title: str
    description: str
    context: str
    cta: str
    route: str
    event: str


PATHWAYS = (
    Pathway(
        "impact", "01", "Experience & impact", "What I’ve led",
        "Leadership responsibilities, decisions and practical contributions "
        "across international enterprise settings.",
        "Leadership evidence", "Explore my experience", "impact",
        "journey_home_impact",
    ),
    Pathway(
        "governance", "02", "Governance & adoption", "How I make AI work",
        "How I approach ownership, decision rights, governance and adoption "
        "so AI can become part of everyday business operations.",
        "Operating perspective", "Explore governance", "ai-data-governance",
        "journey_home_governance",
    ),
    Pathway(
        "thinking", "03", "Articles & perspectives", "How I think",
        "Weekly AI, Executive AI Briefings and longer perspectives on "
        "the choices facing enterprise AI and Data leaders.",
        "Published perspectives", "Explore Thinking", "thinking",
        "journey_home_thinking",
    ),
    Pathway(
        "about", "04", "My journey", "Who I am",
        "The places I’ve called home, the experiences that shaped me, "
        "and a little about life beyond my professional roles.",
        "Beyond the job title", "Explore my story", "about",
        "journey_home_about",
    ),
)

# Bespoke 32px line work: an enterprise decision grid, safeguarded authority,
# an open publication, and an international route. All paths are decorative.
ICON_PATHS = {
    "impact": (
        '<rect x="4.5" y="4.5" width="9" height="9" rx="1.6"/>'
        '<rect x="18.5" y="4.5" width="9" height="9" rx="1.6"/>'
        '<rect x="4.5" y="18.5" width="9" height="9" rx="1.6"/>'
        '<path d="M19 24l3-3 2.1 2.1 4.4-5.1"/>'
    ),
    "governance": (
        '<path d="M16 3.5 26.5 8v7.9c0 6-4.4 10.5-10.5 12.6C9.9 26.4 5.5 21.9 5.5 15.9V8L16 3.5Z"/>'
        '<path d="m11.2 16 3.2 3.2 6.5-7"/>'
    ),
    "thinking": (
        '<path d="M16 8.5c-3.2-2.4-6.7-2.7-11-2.1v18.3c4.5-.7 8.2-.3 11 2.2 2.8-2.5 6.5-2.9 11-2.2V6.4c-4.3-.6-7.8-.3-11 2.1Z"/>'
        '<path d="M16 8.5v17.4M8.5 12.3c1.5 0 3 .3 4.1.8M19.5 13.1c1.4-.5 2.7-.8 4-.8"/>'
    ),
    "about": (
        '<circle cx="16" cy="16" r="12.3"/>'
        '<path d="M3.7 16h24.6M16 3.7c-3.5 3.2-5.4 7.3-5.4 12.3S12.5 25.1 16 28.3M16 3.7c3.5 3.2 5.4 7.3 5.4 12.3s-1.9 9.1-5.4 12.3"/>'
        '<path d="M7.3 8.1h17.4M7.3 23.9h17.4"/>'
    ),
}


def _icon(kind: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" '
        'viewBox="0 0 32 32" fill="none" stroke="currentColor" '
        'stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round" '
        'focusable="false" aria-hidden="true">'
        + ICON_PATHS[kind] + '</svg>'
    )


def home_pathways() -> str:
    """Return the self-contained, clickable four-way Home editorial index."""
    cards = []
    for path in PATHWAYS:
        cards.append(
            f'<a class="journey-card home-pathway-card home-pathway-card--{path.key}" '
            f'href="?page={escape(path.route, quote=True)}" target="_self" '
            f'data-hq-event="{escape(path.event, quote=True)}" '
            f'aria-label="{escape(path.cta, quote=True)}">'
            '<div class="home-pathway-top">'
            f'<span class="home-pathway-icon" aria-hidden="true">{_icon(path.key)}</span>'
            f'<span class="home-pathway-number" aria-hidden="true">{path.number}</span>'
            '</div>'
            '<div class="home-pathway-body">'
            f'<span class="journey-step">{escape(path.label)}</span>'
            f'<h3>{escape(path.title)}</h3>'
            f'<p>{escape(path.description)}</p>'
            '</div>'
            '<div class="home-pathway-footer">'
            f'<span class="home-pathway-context">{escape(path.context)}</span>'
            '<span class="home-pathway-cta">'
            f'{escape(path.cta)}'
            '<span class="home-pathway-arrow" aria-hidden="true">↗</span>'
            '</span></div>'
            '</a>'
        )

    return (
        '<section class="section paper journey-section home-pathways" '
        'data-analytics-section="home-choose-your-path" '
        'aria-labelledby="home-pathways-title">'
        '<div class="container">'
        '<div class="journey-intro home-pathways-intro">'
        '<div class="home-pathways-heading">'
        '<p class="eyebrow">Explore the portfolio</p>'
        '<h2 id="home-pathways-title">AI strategy is only the beginning.</h2>'
        '<span class="home-pathways-heading-rule" aria-hidden="true"></span>'
        '</div>'
        '<div class="home-pathways-context">'
        '<p>I’m Jair Ribeiro. My focus is the leadership work that follows: '
        'choosing which AI and Data opportunities deserve attention, '
        'making ownership explicit, and helping organizations turn technology '
        'into changes in everyday operations. This portfolio brings together '
        'what I’ve led, how I approach governance and adoption, the perspectives '
        'I publish, and the personal journey behind my work.</p>'
        '<div class="home-pathways-index" aria-hidden="true">'
        '<span>Four perspectives</span>'
        '<span>One career, seen from different angles</span>'
        '</div>'
        '</div>'
        '</div>'
        '<nav class="journey-grid home-pathways-grid" aria-label="Explore the portfolio">'
        + ''.join(cards) + '</nav>'
        '</div></section>'
    )
