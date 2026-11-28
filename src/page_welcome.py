"""Portfolio welcome page for direct professional introductions."""
from __future__ import annotations

from html import escape
from site_assets import HERO_URI, EMAIL, LINKEDIN
from site_components import nav, footer

_GUIDE = (
    ("01", "Leadership experience", "AI leadership in practice", "Selected cases covering AI product development, portfolio decisions and adoption across international organizations.", "impact", "Explore AI leadership"),
    ("02", "Governance & adoption", "Making AI work in organizations", "How business ownership, responsible use and practical controls support AI adoption in everyday work.", "ai-data-governance", "Explore governance"),
    ("03", "Articles & perspectives", "Perspectives on enterprise AI", "Original articles and Weekly AI on business decisions, emerging technology and what they mean for organizations.", "thinking", "Read articles & perspectives"),
    ("04", "Executive AI Briefings", "AI decisions for business leaders", "Clear explanations and practical decision guides on AI investment, architecture, governance and readiness.", "briefings", "Explore executive briefings"),
    ("05", "Executive advisory", "Practical decision support", "Tools for assessing AI opportunities and planning next steps, with selected complimentary advisory conversations.", "advisory", "Explore advisory"),
    ("06", "Professional journey", "An international career", "From enterprise technology to AI and Data leadership across Italy, Poland and Sweden.", "about", "Explore career background"),
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
<div><p class="eyebrow">Enterprise AI · Data · Leadership</p>
<h1>Good to connect.<span>Enterprise AI, in practice.</span></h1>
<p class="deck">Thank you for taking the time to visit. This portfolio brings together the work I’ve led across enterprise AI and Data, from strategy and investment decisions to product development, governance and adoption.</p>
<p class="deck">You’ll also find articles, executive briefings and practical resources on the decisions organizations face when putting AI to work.</p>
<div class="actions"><a class="btn primary" href="?page=impact" target="_self" data-hq-event="welcome_hero_impact">Explore AI leadership →</a><a class="btn text" href="?page=home" target="_self" data-hq-event="welcome_hero_home">Portfolio home →</a></div></div>
<div class="portrait"><img src="{HERO_URI}" alt="Jair Ribeiro contributing to an executive AI panel" loading="eager" fetchpriority="high" decoding="async"><div class="note"><span>Operating perspective</span><strong>Working AI needs a business owner, a useful workflow and a team ready to operate it.</strong></div></div>
</div></section>
<section class="section paper" data-analytics-section="welcome-portfolio-guide"><div class="container">
<p class="eyebrow">Explore the portfolio</p><div class="head"><h2>Start with what interests you.</h2><p>A short guide to the work, ideas and resources you’ll find here.</p></div>
<div class="grid3">{cards}</div>
</div></section>
<section class="section white" data-analytics-section="welcome-quick-links"><div class="container"><p class="eyebrow">Quick access</p>
<div class="grid3">
<article class="card"><span class="org">Career profile</span><h3>Career profile &amp; CV</h3><p>Download a CV for professional review or an online application.</p><a class="btn text" href="?page=cv" target="_self" data-hq-event="welcome_cv">CV downloads →</a></article>
<article class="card"><span class="org">Reading</span><h3>Premium Reader Library</h3><p>Complimentary access to full briefings and selected publications through reader registration.</p><a class="btn text" href="?page=readers" target="_self" data-hq-event="welcome_readers">Open the library →</a></article>
<article class="card"><span class="org">Direct conversation</span><h3>Get in touch</h3><p>Continue the conversation by email or LinkedIn.</p><a class="btn text" href="?page=contact" target="_self" data-hq-event="welcome_contact">Contact options →</a></article>
</div></div></section>
<section class="cta" data-analytics-section="welcome-connect"><div class="container ctain"><div><h2>Let’s stay in touch.</h2><p>If you’re exploring an AI or Data mandate, working through a business decision or simply interested in exchanging perspectives, I’d welcome the conversation.</p></div><div class="actions"><a class="btn ghost" href="mailto:{EMAIL}" data-hq-event="email_welcome">Email me →</a><a class="btn ghost" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_welcome">LinkedIn ↗</a></div></div></section>
</main>{footer()}'''
