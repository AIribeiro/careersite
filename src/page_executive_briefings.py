from __future__ import annotations

"""Executive AI Briefings: an editorial series inside the Thinking portfolio.

Published content comes from the existing first-party Content Studio/CMS.
Unpublished topics are editorial questions, never fictitious live articles.
"""

from html import escape

from site_components import nav, footer, journey_next
from site_cms import fetch_published_articles, article_relative_url

BRIEFING_KIND = "Executive Briefing"
FIRST_SLUG = "ai-capabilities-executive-decisions"

NEXT_QUESTIONS = (
    ("02", "Choosing AI autonomy", "When should AI recommend, and when should it act?"),
    ("03", "Enterprise knowledge & RAG", "Can we rely on answers connected to internal knowledge?"),
    ("04", "Redesigning work", "Should we automate the existing process or rethink it?"),
    ("05", "Moving beyond pilots", "What must be ready before an AI solution expands?"),
    ("06", "Measuring AI value", "How do we know whether performance has actually changed?"),
)

BRIEFINGS_CSS = r'''<style>
.site .briefings-hero{padding:85px 0 78px}
.site .briefings-hero h1{max-width:1040px;font-size:clamp(43px,6vw,74px)}
.site .briefings-hero .briefings-deck{max-width:800px;color:#cbd3dd;font-size:19px;line-height:1.65;margin:24px 0 0}
.site .briefings-index{font:800 11px/1.4 Inter,Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:var(--copper)}
.site .briefings-lead{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(290px,.7fr);gap:28px;align-items:stretch}
.site .briefings-feature{background:#111d2d;color:#fff;padding:clamp(28px,4vw,52px);display:flex;flex-direction:column;min-height:360px}
.site .briefings-feature .briefings-index{color:#efba98}
.site .briefings-feature h2{font:500 clamp(32px,4vw,50px)/1.12 Georgia,serif;letter-spacing:-.03em;margin:26px 0 18px}
.site .briefings-feature p{font-size:16px;line-height:1.75;color:#cbd3dd;max-width:650px;margin:0 0 24px}
.site .briefings-feature .briefings-read{margin-top:auto;display:inline-flex;align-self:start;padding:14px 18px;border:1px solid #d7a47c;color:#fff;text-decoration:none;font-size:13px;font-weight:750}
.site .briefings-feature .briefings-read:hover,.site .briefings-feature .briefings-read:focus-visible{background:#d7a47c;color:#111d2d}
.site .briefings-feature .briefings-date{font-size:11px;color:#afbac8;margin:20px 0 0}
.site .briefings-side{padding:32px;background:#e8dfd2;border-top:4px solid var(--copper)}
.site .briefings-side h3{font:500 29px/1.2 Georgia,serif;margin:16px 0}
.site .briefings-side p{font-size:15px;line-height:1.75;color:#434b54}
.site .briefings-side strong{display:block;margin:20px 0 0;font-size:13px;line-height:1.6}
.site .briefings-map-head{display:flex;gap:36px;justify-content:space-between;align-items:end;margin-bottom:28px}
.site .briefings-map-head h2{font:500 clamp(33px,4vw,47px)/1.12 Georgia,serif;max-width:710px;margin:0}
.site .briefings-map-head p{max-width:410px;font-size:15px;line-height:1.7;color:var(--muted)}
.site .briefings-map{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.site .briefings-capability{min-width:0;border:1px solid var(--line);background:#fffdf8;padding:23px;min-height:208px}
.site .briefings-capability span{display:block;font-size:10px;letter-spacing:.11em;text-transform:uppercase;font-weight:800;color:#a85a35}
.site .briefings-capability h3{font:500 28px/1.16 Georgia,serif;margin:18px 0 10px}
.site .briefings-capability p{font-size:14px;line-height:1.65;color:var(--muted);margin:0}
.site .briefings-note{margin:22px 0 0;font-size:13px;line-height:1.7;color:var(--muted)}
.site .briefings-queue{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line)}
.site .briefings-question{padding:25px;background:#fffdf8}
.site .briefings-question span{font-size:10px;letter-spacing:.12em;color:var(--copper);font-weight:800}
.site .briefings-question h3{font:500 24px/1.2 Georgia,serif;margin:12px 0}
.site .briefings-question p{color:var(--muted);font-size:14px;line-height:1.65;margin:0}
.site .briefings-others{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:20px}
.site .briefings-other{display:block;border:1px solid var(--line);padding:25px;background:#fffdf8;text-decoration:none}
.site .briefings-other h3{margin:12px 0;font:500 23px/1.2 Georgia,serif}
.site .briefings-other p{color:var(--muted);font-size:14px;line-height:1.65}
.site .briefings-other span{font-size:11px;color:var(--copper);font-weight:800}
.site .briefings-home-strip{background:#ede3d5;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:30px 0}
.site .briefings-home-inner{display:flex;justify-content:space-between;align-items:center;gap:28px}
.site .briefings-home-inner h2{font:500 25px/1.18 Georgia,serif;margin:6px 0 7px}
.site .briefings-home-inner p{font-size:13px;line-height:1.65;color:#535b64;margin:0}
.site .briefings-home-inner>a{flex:0 0 auto;font-size:12px;font-weight:750;text-decoration:none;border-bottom:1px solid var(--copper);padding:10px 0}
@media(max-width:850px){.site .briefings-lead{grid-template-columns:1fr}.site .briefings-map{grid-template-columns:repeat(2,minmax(0,1fr))}.site .briefings-map-head{display:block}.site .briefings-map-head p{max-width:650px}}
@media(max-width:650px){.site .briefings-hero{padding:65px 0}.site .briefings-hero .briefings-deck{font-size:16px}.site .briefings-feature{min-height:0}.site .briefings-map,.site .briefings-queue,.site .briefings-others{grid-template-columns:1fr}.site .briefings-capability{min-height:0}.site .briefings-home-inner{display:block}.site .briefings-home-inner>a{display:inline-block;margin-top:10px}}
@media(prefers-reduced-motion:reduce){.site .briefings-feature .briefings-read{transition:none}}
</style>'''

CAPABILITIES = (
    ("Predict", "Machine learning", "Recognize patterns and estimate likely outcomes."),
    ("Interpret", "Deep learning and perception", "Work with complex text, images, sound and signals."),
    ("Generate", "Generative AI and LLMs", "Produce and transform language or other content."),
    ("Ground", "Retrieval-augmented generation", "Bring relevant enterprise sources into a response."),
    ("Act", "Agentic systems", "Choose and carry out permitted steps using tools."),
    ("Govern", "Ownership and evidence", "Apply oversight, permissions and measurement across all capabilities."),
)


def published_briefings():
    try:
        return tuple(
            article for article in fetch_published_articles()
            if article.kind.strip().casefold() == BRIEFING_KIND.casefold()
        )
    except (RuntimeError, ValueError, TimeoutError):
        return ()


def home_briefings_strip() -> str:
    return BRIEFINGS_CSS + '''<section class="briefings-home-strip" data-analytics-section="home-executive-briefings">
    <div class="container briefings-home-inner"><div><span class="briefings-index">Executive AI Briefings</span>
    <h2>AI explained through the decisions leaders face.</h2>
    <p>Short operating perspectives on capability, ownership, risk and business value.</p></div>
    <a href="?page=briefings" target="_self" data-hq-event="briefings_home_open">Explore the briefings →</a>
    </div></section>'''


def executive_briefings() -> str:
    items = published_briefings()
    featured = next((item for item in items if item.slug == FIRST_SLUG), items[0] if items else None)
    if featured:
        featured_html = (
            '<span class="briefings-index">Published briefing · Start here</span>'
            f'<h2>{escape(featured.title)}</h2>'
            f'<p>{escape(featured.subtitle or featured.excerpt)}</p>'
            f'<a class="briefings-read" href="{escape(article_relative_url(featured), quote=True)}" '
            f'target="_self" data-hq-event="briefings_featured_open" '
            f'data-hq-content-slug="{escape(featured.slug, quote=True)}">Read the briefing →</a>'
            f'<div class="briefings-date">{escape(featured.published_label)} · {featured.read_minutes} min read</div>'
        )
    else:
        featured_html = (
            '<span class="briefings-index">Editorial introduction</span>'
            '<h2>Choose the capability the business needs.</h2>'
            '<p>Business capability, decision rights and proof of value come before the choice of model, workflow or agent.</p>'
            '<a class="briefings-read" href="#briefings-capability-map" data-hq-event="briefings_map_open">Explore the decision map →</a>'
        )
    capabilities = ''.join(
        '<article class="briefings-capability">'
        f'<span>{escape(category)}</span><h3>{escape(name)}</h3><p>{escape(description)}</p>'
        '</article>'
        for category, name, description in CAPABILITIES
    )
    next_questions = ''.join(
        '<article class="briefings-question">'
        f'<span>{escape(number)} · Editorial direction</span>'
        f'<h3>{escape(title)}</h3><p>{escape(question)}</p>'
        '</article>'
        for number, title, question in NEXT_QUESTIONS
    )
    others = ''.join(
        '<a class="briefings-other" href="'
        + escape(article_relative_url(article), quote=True)
        + '" target="_self" data-hq-event="briefings_article_open" data-hq-content-slug="'
        + escape(article.slug, quote=True) + '">'
        + '<span>Executive AI Briefing</span>'
        + f'<h3>{escape(article.title)}</h3><p>{escape(article.excerpt)}</p>'
        + f'<span>Read · {article.read_minutes} min →</span></a>'
        for article in items if not featured or article.slug != featured.slug
    )
    other_section = (
        '<section class="section white" data-analytics-section="briefings-library"><div class="container">'
        '<div class="head"><div><p class="eyebrow">Briefing library</p><h2>More executive questions.</h2></div>'
        '<p>Published briefings from the same editorial series.</p></div>'
        f'<div class="briefings-others">{others}</div></div></section>'
    ) if others else ''
    return (
        BRIEFINGS_CSS + nav("thinking") +
        '<main><section class="pagehero briefings-hero" data-analytics-section="briefings-introduction">'
        '<div class="container"><p class="eyebrow">Thinking · Executive AI Briefings</p>'
        '<h1>AI, explained through business decisions.</h1>'
        '<p class="briefings-deck">Plain-language explanations shaped by enterprise operating experience: '
        'what AI can do, which choices matter, who owns the consequences and what must change '
        'before an organization can rely on it.</p></div></section>'
        '<section class="section paper" data-analytics-section="briefings-featured"><div class="container">'
        '<div class="briefings-lead"><article class="briefings-feature">'
        + featured_html +
        '</article><aside class="briefings-side"><span class="briefings-index">The operating perspective</span>'
        '<h3>The latest technology is not always the right solution.</h3>'
        '<p>I look at a capability through the work it is expected to change, the data and ownership '
        'behind it, the trade-offs involved and the evidence required to justify continued investment.</p>'
        '<strong>Explain the technology. Question the assumptions. Make the decision clearer.</strong>'
        '</aside></div></div></section>'
        '<section class="section white" id="briefings-capability-map" data-analytics-section="briefings-capability-map">'
        '<div class="container"><div class="briefings-map-head"><div><p class="eyebrow">An original decision map</p>'
        '<h2>Different capabilities. Different operating choices.</h2></div>'
        '<p>Use the descriptions to frame the business problem. Capabilities overlap and can be combined; '
        'this is not a ladder of sophistication or a universal maturity model.</p></div>'
        f'<div class="briefings-map">{capabilities}</div>'
        '<p class="briefings-note">AI is the broader discipline. Machine learning includes deep learning; '
        'generative AI frequently relies on deep learning, with LLMs as a language-focused model class. '
        'RAG is a grounding approach, and agentic systems may combine several of these capabilities. '
        'Governance belongs across the entire system.</p></div></section>'
        + other_section +
        '<section class="section paper" data-analytics-section="briefings-editorial-roadmap"><div class="container">'
        '<div class="head"><div><p class="eyebrow">Questions to explore next</p><h2>Where the conversation goes.</h2></div>'
        '<p>These are planned editorial subjects, not published briefings or service packages.</p></div>'
        f'<div class="briefings-queue">{next_questions}</div></div></section>'
        '<section class="section white"><div class="container"><div class="head">'
        '<div><p class="eyebrow">Behind the perspective</p><h2>Grounded in enterprise work.</h2></div>'
        '<p>The ideas here are informed by work across enterprise AI and Data strategy, '
        'portfolio decisions, governance, adoption and cross-functional operations. '
        'Illustrative scenarios are not claims about confidential employer projects.</p></div>'
        '<div class="actions"><a class="btn dark" href="?page=impact" target="_self" '
        'data-hq-event="briefings_leadership_open">Explore AI Leadership →</a>'
        '<a class="btn dark" href="?page=ai-data-governance" target="_self" '
        'data-hq-event="briefings_governance_open">Explore AI & Data Governance →</a>'
        '</div></div></section>'
        + journey_next("thinking") + '</main>' + footer()
    )
