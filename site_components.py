from __future__ import annotations

import html

from site_assets import PROFILE_URI, CV_URI, LINKEDIN, MEDIUM, EMAIL

def nav(active: str) -> str:
    def link(page: str, label: str) -> str:
        cls = "link on" if page == active else "link"
        return f'<a class="{cls}" href="?page={page}" target="_self">{html.escape(label)}</a>'
    return f'''<nav class="nav"><div class="navin"><a class="brand" href="?page=home" target="_self"><img src="{PROFILE_URI}" alt="Jair Ribeiro"><div><strong>Jair Ribeiro</strong><span>Senior AI &amp; Data Leader</span></div></a><div class="links">{link("home","Home")}{link("impact","Leadership Impact")}{link("thinking","Thinking")}{link("about","About")}<a class="link contactlink{' on' if active=='contact' else ''}" href="?page=contact" target="_self">Contact</a></div></div></nav>'''


def footer() -> str:
    cv = f'<a href="{CV_URI}" download="Jair_Ribeiro_Master_CV_2026.pdf">Download CV ↓</a>' if CV_URI else ""
    return f'''<footer class="footer"><div class="container"><div class="footertop"><div><strong>Jair Ribeiro</strong><p>Enterprise AI and Data leadership focused on strategy, operating models, governance, adoption and measurable business value. Based in Gothenburg, Sweden.</p></div><div class="footerlinks"><a href="{LINKEDIN}" target="_blank">LinkedIn ↗</a><a href="{MEDIUM}" target="_blank">Medium ↗</a><a href="mailto:{EMAIL}">Email</a>{cv}</div></div><div class="rolelinks"><span>Role lenses</span><a href="?page=enterprise" target="_self">Enterprise AI &amp; Data Leadership</a><a href="?page=transformation" target="_self">AI Transformation &amp; Capability</a><a href="?page=consulting" target="_self">Business-Driven AI &amp; Consulting</a></div><div class="copy">© 2026 Jair Ribeiro · Gothenburg, Sweden</div></div></footer>'''


def opportunity() -> str:
    return '''<section class="cta"><div class="container ctain"><div><h2>When AI and data need to become an operating capability — not another experiment.</h2><p>I’m particularly interested in senior leadership mandates where strategy, data, governance, adoption and operating-model design have to work together. If that sounds close to the problem you are solving, I’m always interested in a good conversation.</p></div><a class="btn ghost" href="?page=contact" target="_self">Discuss a leadership opportunity →</a></div></section>'''


VALUES = [
    ("01","AI Strategy & Portfolio","Connect enterprise priorities with realistic AI opportunities, investment choices, ownership and portfolio discipline."),
    ("02","Operating Models & CoEs","Create the roles, decision rights, lifecycle and collaboration model needed to move beyond disconnected experiments."),
    ("03","Adoption & Capability","Translate AI into practical work, build literacy close to the business and help people use new capabilities with confidence."),
    ("04","Governance & Responsible Scale","Build governance as an operating mechanism for ownership, evidence, escalation and trust — not simply another approval layer."),
    ("05","Data & Analytics Foundations","Connect AI ambition with data quality, stewardship, analytics, architecture and the enterprise realities that determine scalability."),
    ("06","Business Value & Execution","Move conversations from possibility to prioritization, practical delivery and evidence that the business can defend."),
]

THOUGHTS = [
    ("Strategy","Strategy Alignment","Why enterprise AI choices need to start with business priorities, portfolio trade-offs and clear ownership.","https://lnkd.in/eFNiAX8M"),
    ("Value","AI ROI","Moving beyond activity metrics to value realization, evidence and the discipline of proving where AI is paying back.","https://lnkd.in/ekQqQdgf"),
    ("Organization","Operating Model","How roles, decision rights and team design determine whether successful AI work becomes repeatable enterprise capability.","https://lnkd.in/e7yrc6zh"),
    ("Governance","AI Governance","Governance as a practical system for ownership, evidence and escalation — not a collection of gates that slows useful work.","https://lnkd.in/eJ8EHKHQ"),
    ("Data","Data Readiness","Why access, quality, semantics and ownership of data often decide whether AI can scale long before model choice does.","https://lnkd.in/ezmrefxC"),
    ("Capability","Talent & Upskilling","Building AI capability without replacing expert judgment: literacy, new skills, confidence and learning close to the work itself.","https://lnkd.in/ez9xAzWb"),
    ("Adoption","Change Management","Training is not adoption. The real measure is whether workflows, decisions and everyday behavior actually change.","https://lnkd.in/ew5mtJKv"),
    ("Autonomy","Agentic AI","What changes when AI systems can plan, coordinate and act — and why accountability has to evolve with that autonomy.","https://lnkd.in/dYmKgQCi"),
]


def card_grid(items: list[tuple[str,str,str]]) -> str:
    return "".join(f'<article class="card"><span class="n">{n}</span><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></article>' for n,t,d in items)


def thought_grid(items: list[tuple[str,str,str,str]], cls: str = "thoughts") -> str:
    cards = []
    for topic,title,desc,url in items:
        card_cls = "thought" if cls == "thoughts" else "article"
        cards.append(f'<a class="{card_cls}" href="{url}" target="_blank" rel="noopener"><span class="topic">{html.escape(topic)}</span><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><span class="read">Read article ↗</span></a>')
    return f'<div class="{cls}">' + "".join(cards) + "</div>"
