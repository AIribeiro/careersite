from __future__ import annotations

import html

from site_assets import BRAND_ICON_URI, CV_URI, LINKEDIN, MEDIUM, EMAIL


CV_DOWNLOAD_NAME = "Jair_Ribeiro_CV.pdf"


MOBILE_NAV_CSS = """
<style>
.site .mobile-menu{display:none}
@media(max-width:700px), (max-device-width:700px){
 .site .nav{position:relative;overflow:visible}
 .site .nav .navin{display:flex;flex-wrap:nowrap!important;align-items:center;
   justify-content:space-between;gap:10px;min-height:64px;min-width:0;
   width:calc(100% - 26px);max-width:100%}
 .site .nav .brand{min-width:0;flex:0 1 auto!important}
 .site .nav .brand strong{font-size:15px;white-space:nowrap}
 .site .nav .brand img{flex-shrink:0}
 .site .nav .navin>.links{display:none!important}
 .site .nav .mobile-menu{display:block;position:relative;flex:0 0 auto;z-index:1100}
 .site .nav .mobile-menu>summary{display:flex;align-items:center;justify-content:center;
   gap:9px;min-width:88px;min-height:44px;list-style:none;cursor:pointer;
   border:1px solid rgba(255,255,255,.3);border-radius:4px;
   padding:9px 13px;color:#f7f8fa;background:#1c2c40;
   font:700 13px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
 .site .nav .mobile-menu>summary::-webkit-details-marker{display:none}
 .site .nav .mobile-menu>summary:focus-visible{outline:2px solid #e2aa83;outline-offset:3px}
 .site .nav .mobile-menu[open]>summary{background:#2c4058}
 .site .nav .mobile-menu-links{display:none}
 .site .nav .mobile-menu[open] .mobile-menu-links{display:flex;flex-direction:column;
   position:absolute;right:0;top:calc(100% + 7px);z-index:1200;
   width:min(306px,calc(100vw - 30px));max-height:74vh;
   overflow-y:auto;overscroll-behavior:contain;
   padding:9px;background:#101d2e;border:1px solid #506175;
   box-shadow:0 18px 28px rgba(0,0,0,.3)}
 .site .nav .mobile-menu-links .link{display:flex!important;width:100%;
   min-height:42px;justify-content:flex-start!important;align-items:center;
   white-space:normal!important;line-height:1.4;padding:10px 13px!important;
   font-size:13px!important;text-align:left}
 .site .nav .mobile-menu-links .link.on{background:#293d53;color:#fff!important}
 .site .nav .mobile-menu-links .contactlink{margin-top:4px}
}
</style>
"""


def nav(active: str) -> str:
    # Give signed-in readers a persistent account destination. No secrets or
    # email addresses are placed into HTML; unverified visitors see no link.
    try:
        import streamlit as st
        signed_in = isinstance(st.session_state.get("reader_native_session"), dict)
        member_link = (
            '<a class="link' + (' on' if active == "readers" else '') +
            '" href="?page=readers" target="_self" '
            'data-hq-event="reader_member_nav">My Library</a>'
            if signed_in else ""
        )
        has_advisory = signed_in and st.session_state.get("advisory_member") is True
        advisory_account_link = (
            '<a class="link' + (' on' if active == "advisory-access" else '') +
            '" href="?page=advisory-access" target="_self" '
            'data-hq-event="advisory_member_nav">' +
            ('My Advisory' if has_advisory else 'Advisory account') + '</a>'
            if has_advisory or active == "advisory-access" else ""
        )
    except (RuntimeError, AttributeError, KeyError):
        member_link = ""
        advisory_account_link = ""
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

    menu_links = (
        f'{link("home", "Home")}'
        f'{link("analytics", "Analytics") if active == "analytics" else ""}'
        f'{link("impact", "AI Leadership")}'
        f'{link("ai-data-governance", "AI & Data Governance")}'
        f'{link("thinking", "Thinking")}'
        f'{member_link}'
        f'{link("advisory", "Advisory")}'
        f'{advisory_account_link}'
        f'{link("about", "About")}'
        f'<a class="link contactlink{" on" if active == "contact" else ""}" '
        f'style="{top_item_style}" href="?page=contact" target="_self" '
        f'data-hq-event="contact_nav">Contact</a>'
    )
    return (
        MOBILE_NAV_CSS
        + '<nav class="nav"><div class="navin" style="flex-wrap:wrap;padding:6px 0">'
        + f'<a class="brand" style="flex:0 0 auto" href="?page=home" target="_self">{brand_icon}'
        + '<div><strong>Jair Ribeiro</strong><span>Enterprise AI &amp; Data Leader</span></div></a>'
        + '<div class="links" style="flex:1 1 560px;min-width:0;align-items:center;justify-content:flex-end">'
        + menu_links + '</div>'
        + '<details class="mobile-menu"><summary><span aria-hidden="true">☰</span> Menu</summary>'
        + '<div class="mobile-menu-links" aria-label="Mobile navigation">'
        + menu_links + '</div></details>'
        + '</div></nav>'
    )


def footer() -> str:
    cv = f'<a href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_footer">Download CV ↓</a>' if CV_URI else ""
    return f'''<footer class="footer"><div class="container"><div class="footertop"><div><strong>Jair Ribeiro</strong><p>Enterprise AI &amp; Data · Gothenburg, Sweden · International experience.</p></div><div class="footerlinks"><a href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_footer">LinkedIn ↗</a><a href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_footer">Medium ↗</a><a href="?page=briefings" target="_self" data-hq-event="briefings_footer">Executive AI Briefings →</a><a href="?page=advisory" target="_self" data-hq-event="advisory_footer">Executive Advisory</a><a href="?page=privacy" target="_self" data-hq-event="privacy_footer">Privacy &amp; data</a><a href="mailto:{EMAIL}" data-hq-event="email_footer">Email</a>{cv}</div></div><div class="copy">© 2026 Jair Ribeiro · Gothenburg, Sweden</div></div></footer>'''


def opportunity() -> str:
    return '''<section class="cta"><div class="container ctain"><div><h2>Working on a similar enterprise AI or data problem?</h2><p>If you face a decision on AI investment, governance or adoption, I consider a limited number of focused pro-bono discussions. Requests are reviewed individually.</p></div><a class="btn ghost" href="?page=advisory" target="_self" data-hq-event="advisory_opportunity">Explore pro-bono advisory →</a></div></section>'''


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