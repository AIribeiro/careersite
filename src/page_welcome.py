"""Personal portfolio entrypoint for direct professional introductions."""
from __future__ import annotations

from html import escape
from site_assets import HERO_URI, EMAIL, LINKEDIN
from site_components import nav, footer

_GUIDE = (
    ("01", "Leadership experience", "What I’ve led", "Selected enterprise AI and Data responsibilities, decisions and contributions across international organizations.", "impact", "Explore my AI leadership"),
    ("02", "Governance & adoption", "How I approach the work", "My approach to AI ownership, responsible use, adoption and making capabilities work in everyday operations.", "ai-data-governance", "Explore governance"),
    ("03", "Articles & perspectives", "How I think", "Original writing and Weekly AI on the decisions that shape enterprise AI, data and technology.", "thinking", "Read my perspectives"),
    ("04", "Executive AI Briefings", "For business leaders", "Focused explanations and decision guides on AI investment, architecture, governance and organizational readiness.", "briefings", "Explore executive briefings"),
    ("05", "Executive advisory", "Work through a decision", "Practical decision-support resources and selected pro-bono advisory conversations. Requests are reviewed individually.", "advisory", "Explore advisory"),
    ("06", "Professional journey", "The person behind the work", "My international career, background and the experiences that shaped how I work with people and technology.", "about", "Read my story"),
)

def welcome() -> str:
    cards = "".join(
        f'<article class="card"><span class="org">{number} · {escape(category)}</span>'
        f'<h3>{escape(title)}</h3><p>{escape(description)}</p>'
        f'<a class="btn text" href="?page={route}" target="_self" data-hq-event="welcome_{route.replace("-", "_")}">{escape(action)} →</a></article>'
        for number, category, title, description, route, action in _GUIDE
    )
    return f'''{nav("welcome")}<main>
<section class="hero" data-analytics-section="welcome-introduction"><div class="container heroin">
<div><p class="eyebrow">A personal introduction · Enterprise AI &amp; Data</p>
<h1>Good to connect.<span>Welcome to my portfolio.</span></h1>
<p class="deck">Thank you for taking a moment to visit. I’m Jair Ribeiro, an enterprise AI and Data leader based in Gothenburg, Sweden. I built this portfolio to share the work I’ve led, how I think about AI in organizations, and what I’ve learned about making technology useful in practice.</p>
<p class="deck">Whether our conversation started with a professional opportunity, a shared interest in AI, or simply an introduction, I hope you find something useful here.</p>
<div class="actions"><a class="btn primary" href="?page=impact" target="_self" data-hq-event="welcome_hero_impact">Explore my AI leadership →</a><a class="btn text" href="?page=home" target="_self" data-hq-event="welcome_hero_home">Portfolio home →</a></div></div>
<div class="portrait"><img src="{HERO_URI}" alt="Jair Ribeiro contributing to an executive AI panel" loading="eager" decoding="async"><div class="note"><span>My operating perspective</span><strong>AI creates value when people can use it, teams can own it and leaders can make informed decisions about it.</strong></div></div>
</div></section>
<section class="section paper" data-analytics-section="welcome-portfolio-guide"><div class="container">
<p class="eyebrow">A short guide</p><div class="head"><h2>Find what matters to you.</h2><p>There’s no need to read everything. Start with the area closest to your interest, and explore from there.</p></div>
<div class="grid3">{cards}</div>
</div></section>
<section class="section white" data-analytics-section="welcome-quick-links"><div class="container"><p class="eyebrow">Looking for something specific?</p>
<div class="grid3">
<article class="card"><span class="org">Career profile</span><h3>My CV</h3><p>Choose the downloadable CV that best suits your purpose.</p><a class="btn text" href="?page=cv" target="_self" data-hq-event="welcome_cv">CV downloads →</a></article>
<article class="card"><span class="org">Reading</span><h3>Premium Reader Library</h3><p>Complimentary registration for complete briefings and selected current publications.</p><a class="btn text" href="?page=readers" target="_self" data-hq-event="welcome_readers">Open the library →</a></article>
<article class="card"><span class="org">Direct conversation</span><h3>Get in touch</h3><p>For a conversation about enterprise AI, leadership or a shared professional interest.</p><a class="btn text" href="?page=contact" target="_self" data-hq-event="welcome_contact">Contact options →</a></article>
</div></div></section>
<section class="cta" data-analytics-section="welcome-connect"><div class="container ctain"><div><h2>Let’s keep the conversation going.</h2><p>If something here connects with your work or a question you’re exploring, feel free to reach out. I would be glad to hear from you.</p></div><div class="actions"><a class="btn ghost" href="mailto:{EMAIL}" data-hq-event="email_welcome">Email me →</a><a class="btn ghost" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_welcome">LinkedIn ↗</a></div></div></section>
</main>{footer()}'''
