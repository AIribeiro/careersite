from __future__ import annotations

import html

from site_assets import BRAND_ICON_URI, CV_URI, LINKEDIN, MEDIUM, EMAIL


ROLE_LENSES = {
    "enterprise": "Enterprise AI & Data Leadership",
    "transformation": "AI Transformation & Adoption",
    "governance": "AI Governance & Operating Model",
    "consulting": "Business-Driven AI & Consulting",
}

CV_DOWNLOAD_NAME = "Jair_Ribeiro_CV.pdf"


def nav(active: str) -> str:
    top_item_style = "display:inline-flex!important;align-items:center;justify-content:center;white-space:nowrap"

    def link(page: str, label: str) -> str:
        cls = "link on" if page == active else "link"
        return (
            f'<a class="{cls}" style="{top_item_style}" href="?page={page}" '
            f'target="_self">{html.escape(label)}</a>'
        )

    lens_active = active in ROLE_LENSES
    lens_items = "".join(
        f'<a href="?page={page}" target="_self" '
        f'style="display:block;padding:11px 14px;color:{"#fff" if page == active else "#c9d0da"}!important;'
        f'background:{"rgba(255,255,255,.08)" if page == active else "transparent"};text-decoration:none!important;'
        f'font-size:12px;font-weight:700;line-height:1.35" data-hq-event="nav_role_{page}">'
        f'{html.escape(label)}</a>'
        for page, label in ROLE_LENSES.items()
    )
    lens_menu = (
        '<details style="position:relative;flex:0 0 auto">'
        f'<summary class="link{" on" if lens_active else ""}" '
        'style="list-style:none;cursor:pointer;user-select:none;white-space:nowrap">Role lenses ▾</summary>'
        '<div style="position:absolute;right:0;top:calc(100% + 6px);z-index:1001;'
        'min-width:270px;max-width:calc(100vw - 34px);padding:6px;background:#111b2c;'
        'border:1px solid rgba(255,255,255,.14);box-shadow:0 18px 40px rgba(0,0,0,.28)">'
        f'{lens_items}</div></details>'
    )
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
        f'{link("impact", "Leadership Impact")}'
        f'{link("thinking", "Thinking")}'
        f'{link("about", "About")}'
        f'{lens_menu}'
        f'<a class="link contactlink{" on" if active == "contact" else ""}" style="{top_item_style}" href="?page=contact" '
        'target="_self" data-hq-event="contact_nav">Contact</a>'
        '</div></div></nav>'
    )


def footer() -> str:
    cv = f'<a href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_footer">Download CV ↓</a>' if CV_URI else ""
    return f'''<footer class="footer"><div class="container"><div class="footertop"><div><strong>Jair Ribeiro</strong><p>Enterprise AI and Data leadership across strategy, operating models, governance, adoption and measurable business value. Based in Gothenburg · Sweden &amp; international mandates.</p></div><div class="footerlinks"><a href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_footer">LinkedIn ↗</a><a href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_footer">Medium ↗</a><a href="mailto:{EMAIL}" data-hq-event="email_footer">Email</a>{cv}</div></div><div class="copy">© 2026 Jair Ribeiro · Gothenburg, Sweden</div></div></footer>'''


def opportunity() -> str:
    return '''<section class="cta"><div class="container ctain"><div><h2>Senior AI and Data leadership where operating reality matters.</h2><p>My strongest fit is where strategy, portfolio choices, data, governance, adoption and ownership have to work together — and where the next useful step is a clearer decision rather than another layer of AI activity.</p></div><a class="btn ghost" href="?page=contact" target="_self" data-hq-event="contact_opportunity">Discuss a leadership opportunity →</a></div></section>'''


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