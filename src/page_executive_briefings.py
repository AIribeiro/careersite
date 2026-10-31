from __future__ import annotations

"""Decision-first Executive AI Briefings, with original graphical artwork.

Only published Content Studio records are presented as published briefings.
Original article bodies, citations and attribution remain available on demand.
"""

from html import escape

from briefings_visual import PROMO_CSS, briefing_icon, briefing_visual
from site_assets import EMAIL
from site_components import nav, footer, journey_next
from site_cms import fetch_published_articles, article_relative_url

BRIEFING_KIND = "Executive Briefing"
FIRST_SLUG = "ai-capabilities-executive-decisions"

# Capability categories are complementary tools, not a ladder of sophistication.
CAPABILITIES = (
    ("Predict", "Pattern-based estimates", "What forecast changes a business decision?", "chart"),
    ("Interpret", "Signals and context", "Which complex inputs need to be understood?", "search"),
    ("Generate", "Content and language", "Which work requires a draft, not a final decision?", "spark"),
    ("Ground", "Enterprise knowledge", "Which trusted sources must support the answer?", "layers"),
    ("Act", "Permitted actions", "What may the system do without another approval?", "workflow"),
    ("Govern", "Accountable use", "Who owns the outcome, controls and evidence?", "shield"),
)

# This editorial synopsis is specific to the first briefing. Unpublished future
# briefings receive a neutral fallback and never inherit this issue's claims.
FIRST_DECISION = {
    "call": "Start with the decision, not the model.",
    "move": "Select one business process, define the outcome to improve and name the owner before choosing an AI capability.",
    "checks": (
        ("Business outcome", "What will improve in cost, quality, speed or productivity?", "target"),
        ("Permission to act", "Is AI informing, recommending or executing—and who approves?", "shield"),
        ("Evidence of value", "How will changed work and its results be measured?", "chart"),
    ),
}

BRIEFINGS_CSS = r'''<style>
.site .briefings-index{font:800 10px/1.45 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#ac663e}
.site .briefings-hero{padding:65px 0 63px}
.site .briefings-hero h1{max-width:940px;font-size:clamp(42px,5.4vw,68px)}
.site .briefings-hero .briefings-deck{max-width:790px;color:#cbd3dd;font-size:17px;line-height:1.6;margin:22px 0 0}
.site .briefings-principles{display:flex;gap:9px;flex-wrap:wrap;margin-top:26px}
.site .briefings-principles span{font:750 11px/1.4 Arial,sans-serif;color:#ecd9ca;border:1px solid rgba(237,190,153,.4);padding:8px 12px}
.site .briefings-overview{padding:50px 0 54px}
.site .briefings-lead{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(300px,.8fr);gap:18px;align-items:stretch}
.site .briefings-feature{min-width:0;background:#13253a;color:#fff;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 18px 40px rgba(14,27,41,.12)}
.site .briefings-feature-art{height:216px;overflow:hidden;border-bottom:1px solid rgba(235,190,149,.22)}
.site .briefings-feature-art .briefing-visual{display:block;width:100%;height:100%;object-fit:cover}
.site .briefings-feature-content{padding:30px 35px 34px;display:flex;flex-direction:column;flex:1}
.site .briefings-feature .briefings-index{color:#e3b58e}
.site .briefings-feature h2{font:500 clamp(28px,3.4vw,39px)/1.11 Georgia,serif;letter-spacing:-.025em;margin:15px 0}
.site .briefings-feature p{font-size:14px;line-height:1.65;color:#c8d3dd;max-width:660px;margin:0 0 20px}
.site .briefings-feature .briefings-read{margin-top:auto;display:inline-flex;align-self:flex-start;align-items:center;min-height:43px;padding:11px 17px;background:#e8bd99;color:#152335!important;text-decoration:none!important;font-size:12px;font-weight:850}
.site .briefings-feature .briefings-read:hover,.site .briefings-feature .briefings-read:focus-visible{background:#fff1e4}
.site .briefings-feature .briefings-date{font-size:11px;color:#aebdcb;margin:16px 0 0}
.site .briefings-method{padding:33px 31px;background:#eae2d7;border:1px solid rgba(17,21,27,.13)}
.site .briefings-method h3{font:500 clamp(26px,3vw,34px)/1.17 Georgia,serif;margin:11px 0 22px}
.site .briefings-method p{font-size:14px;line-height:1.66;color:#525b64;margin:0}
.site .briefings-method-row{display:grid;grid-template-columns:35px 1fr;gap:14px;padding:15px 0;border-top:1px solid #cec3b4;align-items:start}
.site .briefings-method-row .briefing-icon{width:26px;height:26px;color:#98613f}
.site .briefings-method-row strong{display:block;font-size:13px;color:#253346}
.site .briefings-method-row p{font-size:12px;line-height:1.55;margin:5px 0 0}
.site .briefings-method-contact{display:inline-flex;margin-top:22px;text-decoration:none!important;border-bottom:1px solid #a86741;padding-bottom:6px;color:#283342!important;font-size:12px;font-weight:850}
.site .briefings-map-intro{display:flex;align-items:end;justify-content:space-between;gap:28px;margin-bottom:25px}
.site .briefings-map-intro h2{max-width:700px;font:500 clamp(31px,4vw,45px)/1.12 Georgia,serif;margin:9px 0 0}
.site .briefings-map-intro>p{max-width:375px;font-size:14px;line-height:1.65;color:var(--muted);margin:0}
.site .briefings-map{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.site .briefings-capability{min-width:0;display:grid;grid-template-columns:31px 1fr;gap:13px;padding:21px;background:#fffdf8;border:1px solid var(--line);min-height:150px}
.site .briefings-capability .briefing-icon{color:#aa6944;margin-top:4px}
.site .briefings-capability span{font:800 9px/1.5 Arial,sans-serif;letter-spacing:.11em;text-transform:uppercase;color:#aa6944}
.site .briefings-capability h3{font:500 23px/1.15 Georgia,serif;margin:4px 0 8px}
.site .briefings-capability p{font-size:12px;line-height:1.58;color:#58616b;margin:0}
.site .briefings-note{margin:21px 0 0;font-size:12px;line-height:1.65;color:var(--muted);max-width:950px}
.site .briefings-others{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.site .briefings-other{display:flex;flex-direction:column;gap:10px;padding:26px;background:#fffdf8;border:1px solid var(--line);text-decoration:none!important}
.site .briefings-other h3{margin:0;font:500 26px/1.18 Georgia,serif}
.site .briefings-other p{color:var(--muted);font-size:13px;line-height:1.55;margin:0}
.site .briefings-other span{font-size:10px;color:#965633;font-weight:800}
.site .briefings-questions-feature{grid-column:1/-1;position:relative;overflow:hidden;isolation:isolate;min-height:228px;border:1px solid #385367;border-top:3px solid #c58c66;padding:32px 36px;background:linear-gradient(117deg,#101f32,#1a3d50);color:#fff;align-items:flex-start;justify-content:center}
.site .briefings-questions-feature:before{content:"?";position:absolute;z-index:-1;right:9%;top:-25px;font:500 260px/1 Georgia,serif;color:rgba(221,179,144,.17)}
.site .briefings-questions-feature:after{content:"";position:absolute;right:3%;bottom:-50%;width:37%;aspect-ratio:1;border:1px solid rgba(226,185,146,.25);border-radius:50%;box-shadow:0 0 0 28px rgba(226,185,146,.04),0 0 0 60px rgba(226,185,146,.03);pointer-events:none}
.site .briefings-questions-feature span{color:#e7b793}
.site .briefings-questions-feature h3{font:500 clamp(28px,3vw,39px)/1.13 Georgia,serif;color:#fff;max-width:65%;margin:6px 0}
.site .briefings-questions-feature p{max-width:65%;font-size:14px;line-height:1.6;color:#cbd6df}
.site .briefings-questions-feature:hover,.site .briefings-questions-feature:focus-visible{border-color:#d7a47c}
@media(max-width:650px){.site .briefings-questions-feature{min-height:220px;padding:26px}.site .briefings-questions-feature h3,.site .briefings-questions-feature p{max-width:87%}.site .briefings-questions-feature:before{right:-9%;top:0;font-size:210px}}

.site .briefings-conversation{background:#102238;color:#fff;padding:48px 0}
.site .briefings-conversation-inner{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:30px;align-items:center}
.site .briefings-conversation .briefings-index{color:#e6ba98}
.site .briefings-conversation h2{font:500 clamp(31px,3.8vw,45px)/1.14 Georgia,serif;margin:10px 0}
.site .briefings-conversation p{color:#c3d0dc;line-height:1.65;font-size:14px;max-width:780px;margin:0}
.site .briefings-conversation-actions{display:flex;gap:10px;flex-wrap:wrap}
.site .briefings-conversation-actions a{display:inline-flex;align-items:center;min-height:45px;padding:12px 16px;color:#102238!important;background:#e6ba98;text-decoration:none!important;font-size:12px;font-weight:850}
.site .briefings-conversation-actions a:last-child{color:#fff!important;background:transparent;border:1px solid #8ea0b1}
.site .briefings-home-strip{background:#ede3d5;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:30px 0}
.site .briefings-home-inner{display:flex;justify-content:space-between;align-items:center;gap:28px}
.site .briefings-home-inner h2{font:500 25px/1.18 Georgia,serif;margin:6px 0 7px}
.site .briefings-home-inner p{font-size:13px;line-height:1.65;color:#535b64;margin:0}
.site .briefings-home-inner>a{flex:0 0 auto;font-size:12px;font-weight:750;text-decoration:none;border-bottom:1px solid var(--copper);padding:10px 0}
.site .briefing-reader-hero{padding:47px 0 41px;background:#102238;color:#fff}
.site .briefing-reader-hero .briefing-reader-back{display:inline-block;margin:0 0 22px;text-decoration:none!important;color:#ced7df!important;font-size:12px;font-weight:750}
.site .briefing-reader-hero h1{font:500 clamp(37px,5vw,62px)/1.06 Georgia,serif;max-width:940px;margin:12px 0 14px;letter-spacing:-.028em}
.site .briefing-reader-hero p{max-width:850px;color:#c8d2df;font-size:17px;line-height:1.58;margin:0}
.site .briefing-reader-hero .briefings-index{color:#e8bb97}
.site .briefing-reader-body{padding:43px 0 55px}
.site .briefing-reader-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(290px,.85fr);gap:20px}
.site .briefing-reader-intro{background:#fffdf8;border:1px solid var(--line);padding:32px;min-width:0}
.site .briefing-reader-intro h2{font:500 clamp(29px,3.4vw,40px)/1.14 Georgia,serif;margin:11px 0 13px}
.site .briefing-reader-intro>p{font:400 15px/1.7 Arial,sans-serif;color:#48525c;margin:0 0 22px}
.site .briefing-reader-next{margin-top:22px;padding:19px 20px;background:#ece1d4;border-left:3px solid #b76c42}
.site .briefing-reader-next strong{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8a4d30}
.site .briefing-reader-next p{font-size:14px;line-height:1.6;color:#263242;margin:8px 0 0}
.site .briefing-reader-checks{display:grid;gap:0;border-top:1px solid #d7d4ce;margin-top:19px}
.site .briefing-reader-check{display:grid;grid-template-columns:30px 1fr;gap:12px;padding:15px 0;border-bottom:1px solid #dedbd5}
.site .briefing-reader-check .briefing-icon{color:#ad6b43}
.site .briefing-reader-check strong{font-size:13px;color:#203245}
.site .briefing-reader-check p{font-size:12px;line-height:1.55;color:#58636e;margin:4px 0 0}
.site .briefing-reader-side{display:flex;flex-direction:column;gap:14px;min-width:0}
.site .briefing-reader-cover{height:230px;overflow:hidden;background:#112638}
.site .briefing-reader-cover>.cms-article-image{height:100%;margin:0}
.site .briefing-reader-cover>.cms-article-image img{height:100%;width:100%;max-height:none;object-fit:cover;margin:0;box-shadow:none}
.site .briefing-reader-cover>.cms-fallback-cover{width:100%;height:100%;min-height:0;aspect-ratio:auto;box-shadow:none}
.site .briefing-reader-cover .cms-cover-copy{width:65%;top:10%}
.site .briefing-reader-cover .cms-cover-copy strong{font-size:clamp(18px,2.1vw,29px)}
.site .briefing-reader-cover .cms-briefing-visual{transform:scale(.6);transform-origin:right top;right:1%;top:10%;width:40%}
.site .briefing-reader-cover .cms-cover-copy p{display:none}
.site .briefing-reader-contact{background:#122b40;color:#fff;padding:27px}
.site .briefing-reader-contact .briefing-icon{color:#e7b991}
.site .briefing-reader-contact h3{font:500 26px/1.15 Georgia,serif;margin:15px 0 10px}
.site .briefing-reader-contact p{font-size:13px;line-height:1.6;color:#c7d3dd;margin:0 0 20px}
.site .briefing-reader-contact a{display:inline-flex;padding:12px 16px;min-height:42px;align-items:center;text-decoration:none!important;background:#e7b991;color:#15293a!important;font-size:12px;font-weight:850}
.site .briefing-reader-contact .briefing-contact-secondary{display:block;background:transparent;color:#d6e2eb!important;padding:13px 0 0;font-size:11px;min-height:0}
.site .briefing-reader-detail{margin-top:20px;background:#fffdf8;border:1px solid var(--line)}
.site .briefing-reader-detail summary{cursor:pointer;list-style:auto;padding:22px 25px;color:#21334a;font-size:14px;font-weight:800}
.site .briefing-reader-detail summary:focus-visible{outline:3px solid #b87751;outline-offset:-4px}
.site .briefing-reader-detail .briefing-reader-research{border-top:1px solid var(--line);padding:32px;max-width:100%}
.site .briefing-reader-research.article-body{max-width:none}
.site .briefing-reader-research.article-body p{font-size:14px;line-height:1.68}
.site .briefing-reader-research.article-body h2{font-size:27px;margin:26px 0 12px}
.site .briefing-reader-research .executive-capability-grid{gap:9px}
.site .briefing-reader-research .executive-capability-card{padding:14px}
.site .briefing-reader-share{margin-top:23px;max-width:900px}
@media(max-width:950px){.site .briefings-lead,.site .briefing-reader-grid{grid-template-columns:1fr}.site .briefings-map{grid-template-columns:repeat(2,minmax(0,1fr))}.site .briefings-map-intro,.site .briefings-conversation-inner{display:block}.site .briefings-map-intro>p{margin-top:15px}.site .briefings-conversation-actions{margin-top:24px}.site .briefing-reader-cover{height:230px}}
@media(max-width:650px){.site .briefings-hero{padding:42px 0}.site .briefings-hero .briefings-deck{font-size:15px}.site .briefings-overview{padding:30px 0}.site .briefings-feature-art{height:165px}.site .briefings-feature-content,.site .briefings-method{padding:25px}.site .briefings-map{grid-template-columns:1fr}.site .briefings-capability{min-height:0;padding:17px}.site .briefings-others{grid-template-columns:1fr}.site .briefings-home-inner{display:block}.site .briefings-home-inner>a{display:inline-block;margin-top:10px}.site .briefing-reader-hero{padding:34px 0}.site .briefing-reader-hero p{font-size:14px}.site .briefing-reader-body{padding:24px 0 40px}.site .briefing-reader-intro{padding:23px}.site .briefing-reader-cover{height:190px}.site .briefing-reader-detail .briefing-reader-research{padding:20px}.site .briefings-conversation{padding:35px 0}.site .briefings-conversation-actions{display:grid}.site .briefings-conversation-actions a{justify-content:center}}
@media(prefers-reduced-motion:reduce){.site .briefings-feature .briefings-read{transition:none}}
</style>'''


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


def contact_block() -> str:
    return (
        '<section class="briefings-conversation" data-analytics-section="briefings-contact">'
        '<div class="container briefings-conversation-inner"><div>'
        '<span class="briefings-index">From reading to decision</span>'
        '<h2>Have an AI choice that needs a clearer answer?</h2>'
        '<p>These briefings frame common executive questions. Your context determines the answer. '
        'If you are weighing investment, ownership, adoption or responsible scale, '
        'contact me to discuss the actual business decision.</p></div>'
        '<div class="briefings-conversation-actions">'
        '<a href="?page=contact" target="_self" data-hq-event="briefings_contact_open">Discuss your situation →</a>'
        f'<a href="mailto:{escape(EMAIL, quote=True)}?subject=Executive%20AI%20Briefing" '
        'data-hq-event="briefings_contact_email">Email directly →</a>'
        '</div></div></section>'
    )


def executive_briefings() -> str:
    items = published_briefings()
    featured = next((item for item in items if item.slug == FIRST_SLUG), items[0] if items else None)
    if featured:
        featured_html = (
            '<span class="briefings-index">Published · Featured executive briefing</span>'
            f'<h2>{escape(featured.title)}</h2>'
            f'<p>{escape(featured.subtitle or featured.excerpt)}</p>'
            f'<a class="briefings-read" href="{escape(article_relative_url(featured), quote=True)}" '
            f'target="_self" data-hq-event="briefings_featured_open" '
            f'data-hq-content-slug="{escape(featured.slug, quote=True)}">Read the executive view →</a>'
            f'<div class="briefings-date">{escape(featured.published_label)} · {featured.read_minutes} min full briefing</div>'
        )
    else:
        featured_html = (
            '<span class="briefings-index">Start with the decision map</span>'
            '<h2>Choose the business capability, then the technology.</h2>'
            '<p>Clarify the outcome, permissions, decision owner and evidence of value before selecting a system.</p>'
            '<a class="briefings-read" href="#briefings-capability-map" data-hq-event="briefings_map_open">Explore the decision map →</a>'
        )
    capabilities = ''.join(
        '<article class="briefings-capability">' + briefing_icon(icon) + '<div>'
        f'<span>{escape(category)}</span><h3>{escape(name)}</h3>'
        f'<p>{escape(description)}</p></div></article>'
        for category, name, description, icon in CAPABILITIES
    )
    others = ''.join(
        '<a class="briefings-other' + (' briefings-questions-feature' if article.slug == 'seven-questions-for-better-ai-decisions' else '') + '" href="'
        + escape(article_relative_url(article), quote=True)
        + '" target="_self" data-hq-event="briefings_article_open" data-hq-content-slug="'
        + escape(article.slug, quote=True) + '">'
        + ('<span>New · Executive field guide</span>' if article.slug == 'seven-questions-for-better-ai-decisions' else '<span>Executive AI Briefing</span>')
        + f'<h3>{escape(article.title)}</h3><p>{escape(article.excerpt)}</p>'
        + f'<span>Read executive view →</span></a>'
        for article in items if not featured or article.slug != featured.slug
    )
    others_section = (
        '<section class="section paper" data-analytics-section="briefings-library">'
        '<div class="container"><p class="eyebrow">Published briefs</p>'
        '<h2>Other decisions worth examining.</h2>'
        f'<div class="briefings-others" style="margin-top:24px">{others}</div></div></section>'
    ) if others else ''
    return (
        BRIEFINGS_CSS + PROMO_CSS + nav("thinking")
        + '<main><section class="pagehero briefings-hero" data-analytics-section="briefings-introduction">'
        '<div class="container"><p class="eyebrow">Thinking · Executive AI Briefings</p>'
        '<h1>Better AI decisions. Less noise.</h1>'
        '<p class="briefings-deck">Short, experience-informed executive perspectives for the moments that matter: '
        'where AI can help, what risks are acceptable, who owns the result and how to know whether the work improved.</p>'
        '<div class="briefings-principles"><span>Business first</span><span>Clear trade-offs</span>'
        '<span>Accountable decisions</span></div></div></section>'
        '<section class="section paper briefings-overview" data-analytics-section="briefings-featured">'
        '<div class="container"><div class="briefings-lead"><article class="briefings-feature">'
        f'<div class="briefings-feature-art">{briefing_visual()}</div>'
        '<div class="briefings-feature-content">' + featured_html + '</div></article>'
        '<aside class="briefings-method"><span class="briefings-index">The reading experience</span>'
        '<h3>A question, a judgment, a next move.</h3>'
        + ''.join(
            '<div class="briefings-method-row">' + briefing_icon(symbol)
            + f'<div><strong>{title}</strong><p>{body}</p></div></div>'
            for symbol,title,body in (
                ("target","The decision","Understand what the business must choose."),
                ("shield","The trade-off","See what changes the answer and who is accountable."),
                ("check","The next move","Leave with a practical question or action."),
            )
        )
        + '<a href="?page=contact" class="briefings-method-contact" target="_self" '
        'data-hq-event="briefings_method_contact">Need a deeper discussion? Contact me →</a>'
        '</aside></div></div></section>'
        '<section class="section white" id="briefings-capability-map" '
        'data-analytics-section="briefings-capability-map"><div class="container">'
        '<div class="briefings-map-intro"><div><span class="briefings-index">Executive decision map</span>'
        '<h2>What capability does the decision actually require?</h2></div>'
        '<p>A quick reference to frame the choice, not an exhaustive technical taxonomy.</p></div>'
        f'<div class="briefings-map">{capabilities}</div>'
        '<p class="briefings-note">These capabilities overlap: machine learning includes deep learning; '
        'LLMs are one form of generative AI; RAG connects models with source information. '
        'Agentic systems may combine multiple approaches. Governance spans every choice; '
        'this is not a ladder of sophistication.</p></div></section>'
        + others_section + contact_block()
        + '<section class="section white" data-analytics-section="briefings-credibility"><div class="container">'
        '<span class="briefings-index">Behind the perspective</span>'
        '<h2 style="margin:12px 0;font:500 clamp(29px,4vw,43px)/1.1 Georgia,serif">'
        'Grounded in enterprise work.</h2>'
        '<p style="max-width:780px;color:var(--muted);line-height:1.7;font-size:14px">'
        'My perspective draws on enterprise AI and data strategy, investment choices, '
        'governance, adoption and cross-functional leadership. Illustrative scenarios are not '
        'claims about confidential employer projects.</p>'
        '<div class="actions"><a class="btn dark" href="?page=impact" target="_self" '
        'data-hq-event="briefings_leadership_open">Explore AI Leadership →</a>'
        '<a class="btn dark" href="?page=ai-data-governance" target="_self" '
        'data-hq-event="briefings_governance_open">AI &amp; Data Governance →</a></div>'
        '</div></section></main>' + footer()
    )


def executive_briefing_article(
    article, read_metadata: str, image: str, tags: str, source: str,
    share_footer: str, cms_css: str,
) -> str:
    """A readable executive synopsis with the complete publication optional.

    CMS remains the source of truth. The full article and references are
    preserved in a native disclosure rather than removed or rewritten.
    """
    from thinking_core import THINKING_CSS

    guide = FIRST_DECISION if article.slug == FIRST_SLUG else {
        "call": "Make the business decision explicit.",
        "move": "Name the accountable owner, decide which evidence would change your answer and test the assumption before expanding.",
        "checks": (
            ("The outcome", "What business result needs to improve?", "target"),
            ("The trade-off", "What could go wrong, and who can authorize the decision?", "shield"),
            ("The evidence", "What would justify the next investment?", "chart"),
        ),
    }
    checks = ''.join(
        '<div class="briefing-reader-check">' + briefing_icon(symbol)
        + f'<div><strong>{escape(title)}</strong><p>{escape(question)}</p></div></div>'
        for title,question,symbol in guide["checks"]
    )
    return (
        THINKING_CSS + cms_css + BRIEFINGS_CSS + nav("thinking")
        + '<main class="briefing-reader">'
        '<section class="briefing-reader-hero" data-analytics-section="briefing-reader-introduction">'
        '<div class="container"><a class="briefing-reader-back" href="?page=briefings" '
        'target="_self">← Executive AI Briefings</a>'
        '<div class="briefings-index">Executive decision brief</div>'
        f'<h1>{escape(article.title)}</h1>'
        f'<p>{escape(article.subtitle or article.excerpt)}</p></div></section>'
        '<section class="section paper briefing-reader-body" data-analytics-section="briefing-reader-summary">'
        '<div class="container"><div class="briefing-reader-grid">'
        '<article class="briefing-reader-intro"><span class="briefings-index">The executive view</span>'
        f'<h2>{escape(guide["call"])}</h2>'
        '<p>Use these three checks to turn the technology discussion into a decision with '
        'clear business ownership.</p>'
        f'<div class="briefing-reader-checks">{checks}</div>'
        '<div class="briefing-reader-next"><strong>Suggested next move</strong>'
        f'<p>{escape(guide["move"])}</p></div></article>'
        '<aside class="briefing-reader-side">'
        f'<div class="briefing-reader-cover">{image}</div>'
        '<div class="briefing-reader-contact">' + briefing_icon("compass")
        + '<h3>The right answer depends on your context.</h3>'
        '<p>This briefing frames the questions. For a specific process, investment '
        'or governance choice, a direct conversation will be more useful than another long article.</p>'
        '<a href="?page=contact" target="_self" data-hq-event="briefing_reader_contact">'
        'Discuss this decision →</a>'
        f'<a class="briefing-contact-secondary" href="mailto:{escape(EMAIL, quote=True)}'
        '?subject=Executive%20AI%20Briefing" data-hq-event="briefing_reader_email">'
        'Or email me directly →</a></div></aside></div>'
        '<details class="briefing-reader-detail" data-analytics-section="briefing-reader-depth">'
        '<summary>Want more context? Expand the explanation and source references</summary>'
        f'<div class="article-body briefing-reader-research">{article.content_html}{tags}{source}</div>'
        '</details><div class="briefing-reader-share">' + share_footer + '</div>'
        '</div></section>' + contact_block() + '</main>' + footer()
    )
