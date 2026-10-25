from __future__ import annotations

import html

from site_assets import BRAND_ICON_URI, CV_URI, LINKEDIN, MEDIUM, EMAIL


CV_DOWNLOAD_NAME = "Jair_Ribeiro_CV.pdf"


def nav(active: str) -> str:
    top_item_style = "display:inline-flex!important;align-items:center;justify-content:center;white-space:nowrap"

    def link(page: str, label: str) -> str:
        cls = "link on" if page == active else "link"
        return (
            f'<a class="{cls}" style="{top_item_style}" href="?page={page}" '
            f'target="_self">{html.escape(label)}</a>'
        )

    about_active = active == "about"
    brand_icon = (
        f'<img src="{BRAND_ICON_URI}" alt="" aria-hidden="true">'
        if BRAND_ICON_URI
        else ""
    )

    return (
        '<nav class="nav"><div class="navin" style="flex-wrap:wrap;padding:6px 0">'
        f'<a class="brand" style="flex:0 0 auto" href="?page=home" target="_self">{brand_icon}<div><strong>Jair Ribeiro</strong>'
        '<span>Enterprise AI &amp; Data Leader</span></div></a>'
        '<div class="links" style="flex:1 1 560px;min-width:0;align-items:center;justify-content:flex-end">'
        f'{link("home", "Home")}'
        f'{link("impact", "AI Leadership")}'
        f'{link("ai-data-governance", "AI & Data Governance")}'
        f'{link("thinking", "Thinking")}'
        f'{link("about", "About")}'
        f'<a class="link contactlink{" on" if active == "contact" else ""}" style="{top_item_style}" href="?page=contact" '
        'target="_self" data-hq-event="contact_nav">Contact</a>'
        '</div></div></nav>'
    )


def footer() -> str:
    cv = f'<a href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_footer">Download CV ↓</a>' if CV_URI else ""
    return f'''<footer class="footer"><div class="container"><div class="footertop"><div><strong>Jair Ribeiro</strong><p>Enterprise AI &amp; Data · Gothenburg, Sweden · International experience.</p></div><div class="footerlinks"><a href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_footer">LinkedIn ↗</a><a href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_footer">Medium ↗</a><a href="mailto:{EMAIL}" data-hq-event="email_footer">Email</a>{cv}</div></div><div class="copy">© 2026 Jair Ribeiro · Gothenburg, Sweden</div></div></footer>'''


def opportunity() -> str:
    return '''<section class="cta"><div class="container ctain"><div><h2>Working on a similar enterprise AI or data problem?</h2><p>If the context involves strategy, governance, adoption, portfolio choices or operating ownership, the experience on this site may be relevant.</p></div><a class="btn ghost" href="?page=contact" target="_self" data-hq-event="contact_opportunity">Contact →</a></div></section>'''


def journey_next(page: str) -> str:
    """Offer two relevant, optional portfolio destinations after primary content.

    Link identifiers remain stable across editorial changes, so analytics can
    compare real route selections without relying on button copy.
    """
    routes = {
        "impact": (
            ("governance", "ai-data-governance", "How I make AI work",
             "Explore operating ownership, governance and proportionate controls.",
             "Explore AI & Data Governance →"),
            ("thinking", "thinking", "How I think",
             "Read my perspectives on the decisions behind enterprise AI adoption and scale.",
             "Read my articles →"),
        ),
        "governance": (
            ("impact", "impact", "What I’ve led",
             "See where business priorities, ownership and adoption shaped my leadership work.",
             "Explore my experience →"),
            ("thinking", "thinking", "How I think",
             "Read the reasoning behind enterprise AI decisions and trade-offs.",
             "Read my articles →"),
        ),
        "thinking": (
            ("impact", "impact", "Experience behind the perspective",
             "Connect these ideas with enterprise leadership responsibilities and practical work.",
             "Explore my experience →"),
            ("governance", "ai-data-governance", "Governance in practice",
             "See how accountable AI adoption can become part of the operating model.",
             "Explore AI & Data Governance →"),
        ),
        "article": (
            ("impact", "impact", "Experience behind the perspective",
             "See how these ideas connect with my leadership experience.",
             "Explore my experience →"),
            ("governance", "ai-data-governance", "Governance in practice",
             "Explore the operating principles behind responsible AI at scale.",
             "Explore AI & Data Governance →"),
        ),
    }
    if page not in routes:
        return ""
    cards = []
    for kind, destination, title, description, label in routes[page]:
        cards.append(
            f'<a class="journey-card" href="?page={destination}" target="_self" '
            f'data-hq-event="journey_{page}_{kind}">'
            '<span class="journey-step">Continue exploring</span>'
            f'<h3>{html.escape(title)}</h3><p>{html.escape(description)}</p>'
            f'<span class="journey-link">{html.escape(label)}</span></a>'
        )
    return (
        '<section class="section paper journey-next" data-analytics-section="related-portfolio-routes">'
        '<div class="container"><div class="journey-intro"><p class="eyebrow">Explore further</p>'
        '<h2>Continue from here.</h2>'
        '<p>Follow the aspect of my work most relevant to your question.</p></div>'
        f'<div class="journey-grid">{"".join(cards)}</div></div></section>'
    )


VALUES = [
    ("01", "AI Strategy & Portfolio", "Connect enterprise priorities with realistic AI opportunities, investment choices, ownership and portfolio discipline. The important work is deciding what deserves attention, what evidence is still missing and what should not progress yet."),
    ("02", "Operating Models & CoEs", "Create the roles, decision rights, lifecycle and collaboration model needed to move beyond disconnected experiments. A useful operating model makes ownership clearer without creating a central team that becomes a bottleneck."),
    ("03", "Adoption & Capability", "Translate AI into practical work, build literacy close to the business and help people use new capabilities with confidence. Adoption becomes visible when workflows and decisions change, not simply when training is completed."),
    ("04", "Governance & Responsible Scale", "Use governance to clarify ownership, evidence, escalation and trust. The objective is to help teams understand what they need to prove before higher-risk or higher-scale use is justified."),
    ("05", "Data & Analytics Foundations", "Connect AI ambition with data quality, stewardship, analytics, architecture and the enterprise realities that determine scalability. Many apparent model problems are actually ownership, semantics or data-trust problems."),
    ("06", "Business Value & Execution", "Move conversations from possibility to prioritization, practical delivery and evidence the business can defend. Value needs a credible link between the use case, the changed decision or workflow, adoption and the outcome being measured."),
]

THOUGHTS = [
    ("Strategy", "Strategy Alignment", "Why enterprise AI choices need to start with business priorities, portfolio trade-offs and clear ownership.", "https://lnkd.in/eFNiAX8M"),
    ("Value", "AI ROI", "Moving beyond activity metrics to value realization, evidence and the discipline of proving where AI is paying back.", "https://lnkd.in/ekQqQdgf"),
    ("Organization", "Operating Model", "How roles, decision rights and team design determine whether successful AI work becomes repeatable enterprise capability.", "https://lnkd.in/e7yrc6zh"),
    ("Governance", "AI Governance", "Governance as a practical system for ownership, evidence and escalation rather than a collection of disconnected gates.", "https://lnkd.in/eJ8EHKHQ"),
    ("Data", "Data Readiness", "Why access, quality, semantics and ownership of data often decide whether AI can scale long before model choice does.", "https://lnkd.in/ezmrefxC"),
    ("Adoption", "Change Management", "Training is not adoption. The real measure is whether workflows, decisions and everyday behavior actually change.", "https://lnkd.in/ew5mtJKv"),
]


def card_grid(items: list[tuple[str, str, str]]) -> str:
    return "".join(f'<article class="card"><span class="n">{n}</span><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></article>' for n, t, d in items)


def thought_grid(items: list[tuple[str, str, str, str]], cls: str = "thoughts") -> str:
    cards = []
    for topic, title, desc, url in items:
        card_cls = "thought" if cls == "thoughts" else "article"
        cards.append(f'<a class="{card_cls}" href="{url}" target="_blank" rel="noopener" data-hq-event="article_open"><span class="topic">{html.escape(topic)}</span><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><span class="read">Read article ↗</span></a>')
    return f'<div class="{cls}">' + "".join(cards) + "</div>"