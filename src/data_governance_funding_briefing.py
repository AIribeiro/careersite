from __future__ import annotations

"""Original decision-first reader for the data-governance investment briefing.

The Content Studio article remains the source for full editorial text and
primary references. This module supplies the issue-specific executive scan
and a responsive explanatory model. No third-party art is reproduced.
"""

from html import escape

from site_components import nav, footer
from thinking_core import THINKING_CSS


FUNDING_CSS = r"""<style>
.site .dgf-reader{background:#f5f3ef;color:#20394b}
.site .dgf-hero{padding:clamp(35px,5vw,78px) 0 clamp(32px,5vw,67px);background:radial-gradient(ellipse at 89% 13%,#305165 0%,#122b40 64%);color:#fff;border-top:4px solid #bd8d68}
.site .dgf-eyebrow{display:block;color:#e3b68e;text-transform:uppercase;letter-spacing:.16em;font:800 10px/1.5 Arial,sans-serif}
.site .dgf-hero .briefing-reader-back{display:inline-block;margin:0 0 31px;color:#e6d6c8;text-decoration:none}
.site .dgf-hero h1{font:500 clamp(35px,5.4vw,66px)/1.08 Georgia,serif;color:#fff;max-width:880px;letter-spacing:-.025em;margin:14px 0 19px}
.site .dgf-deck{font:400 clamp(15px,1.75vw,19px)/1.62 Arial,sans-serif;color:#dbe6e9;max-width:795px;margin:0}
.site .dgf-hero-meta{font:700 11px/1.5 Arial,sans-serif;color:#d3aa89;letter-spacing:.05em;margin:21px 0 0}
.site .dgf-scan{display:grid;grid-template-columns:1.45fr 1fr;gap:28px;background:#fffdf9;border:1px solid #ddd8d1;border-left:5px solid #ba8057;padding:clamp(20px,3.4vw,36px);margin-top:-2px}
.site .dgf-scan h2{font:500 clamp(26px,3vw,38px)/1.17 Georgia,serif;margin:8px 0 12px;color:#1a3447}
.site .dgf-scan p{font:400 14px/1.65 Arial,sans-serif;color:#405662;margin:0}
.site .dgf-scan .dgf-eyebrow,.site .dgf-content-head .dgf-eyebrow{color:#8e5939}
.site .dgf-scan-side{border-left:1px solid #dcded9;padding:3px 0 3px 23px}
.site .dgf-scan-side strong{display:block;font:800 10px/1.4 Arial,sans-serif;color:#9b6846;text-transform:uppercase;letter-spacing:.12em;margin-bottom:9px}
.site .dgf-scan-side p{font-weight:600;color:#263e4e}
.site .dgf-bridge{margin:24px 0 23px;padding:clamp(20px,3vw,34px);background:#173347;border:1px solid #395669;color:#fff}
.site .dgf-map-head{display:flex;justify-content:space-between;align-items:start;gap:16px;margin-bottom:21px}
.site .dgf-map-head h2{font:500 clamp(25px,3vw,37px)/1.16 Georgia,serif;color:#fff;margin:7px 0 5px}
.site .dgf-map-head p{font:400 13px/1.6 Arial,sans-serif;color:#c7d8df;margin:0;max-width:680px}
.site .dgf-map-index{font:500 44px/1 Georgia,serif;color:#bf9678;opacity:.8}
.site .dgf-bridge-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
.site .dgf-node{min-width:0;min-height:151px;background:#203e51;border:1px solid #557283;padding:20px 14px 15px;position:relative}
.site .dgf-node:not(:last-child):after{content:"";position:absolute;right:-9px;top:50%;width:9px;height:2px;background:#d0a482;z-index:2}
.site .dgf-node b{display:block;font:850 10px/1.4 Arial,sans-serif;color:#e9bd9b;letter-spacing:.1em;margin-bottom:11px}
.site .dgf-node strong{display:block;font:500 21px/1.2 Georgia,serif;color:#fff;margin-bottom:11px}
.site .dgf-node p{font:400 12px/1.55 Arial,sans-serif;color:#d5e0e5;margin:0}
.site .dgf-bridge-footer{margin-top:14px;background:#e5c2a2;color:#25394a;display:flex;gap:16px;align-items:center;padding:13px 17px}
.site .dgf-bridge-footer strong{font:800 10px/1.4 Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap}
.site .dgf-bridge-footer p{font:700 13px/1.5 Arial,sans-serif;margin:0}
.site .dgf-map-caption{font:400 11px/1.6 Arial,sans-serif;color:#c3d2d8;margin:13px 0 0}
.site .dgf-paths{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin-bottom:26px}
.site .dgf-path{background:#fffdf9;border:1px solid #dadbd6;border-top:4px solid #779486;padding:18px}
.site .dgf-path:nth-child(2){border-top-color:#bb955d}.site .dgf-path:nth-child(3){border-top-color:#a16f62}
.site .dgf-path span{display:block;font:800 10px/1.4 Arial,sans-serif;color:#936944;letter-spacing:.09em;text-transform:uppercase}
.site .dgf-path h3{font:500 23px/1.2 Georgia,serif;color:#203a4b;margin:8px 0}
.site .dgf-path p{font:400 12px/1.58 Arial,sans-serif;color:#4c5e68;margin:0}
.site .dgf-content{background:#fffdf9;border:1px solid #e0ddd6;padding:clamp(22px,4vw,49px);max-width:100%;margin-bottom:22px}
.site .dgf-content-head{border-bottom:1px solid #dadbd4;margin-bottom:23px;padding-bottom:19px}
.site .dgf-content-head h2{font:500 clamp(27px,3.3vw,37px)/1.18 Georgia,serif;color:#173449;margin:9px 0 9px}
.site .dgf-content-head p{font:400 13px/1.6 Arial,sans-serif;color:#66727a;margin:0}
.site .dgf-content .article-body{max-width:780px;margin:0 auto;font:400 15px/1.8 Arial,sans-serif;color:#304b5b}
.site .dgf-content .article-body h2{font:500 clamp(24px,3vw,31px)/1.24 Georgia,serif;color:#193b4e;margin:36px 0 12px}
.site .dgf-content .article-body h3{font:600 19px/1.35 Georgia,serif;color:#3e5b68;margin:22px 0 8px}
.site .dgf-content .article-body p{margin:0 0 17px}
.site .dgf-content .article-body a{color:#966542;text-decoration:underline;text-underline-offset:2px}
.site .dgf-content .article-body li{padding-left:5px;margin-bottom:9px}
.site .dgf-content .article-body li::marker{color:#ae7958}
.site .dgf-content .article-body strong{color:#193b4d}
.site .dgf-next{display:grid;grid-template-columns:1.15fr auto;gap:24px;align-items:center;background:#183549;color:#fff;padding:clamp(22px,3vw,34px);margin-bottom:24px}
.site .dgf-next h2{font:500 27px/1.2 Georgia,serif;color:#fff;margin:8px 0}
.site .dgf-next p{font:400 13px/1.6 Arial,sans-serif;color:#d5e2e8;margin:0;max-width:680px}
.site .dgf-next a{display:inline-block;padding:14px 19px;background:#e7be9a;color:#193548!important;text-decoration:none!important;font:800 12px/1.4 Arial,sans-serif;white-space:nowrap}
.site .dgf-share{padding:3px 0 26px}
@media(max-width:850px){.site .dgf-scan{grid-template-columns:1fr}.site .dgf-scan-side{border-left:0;border-top:1px solid #dcded9;padding:16px 0 0}.site .dgf-bridge-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.site .dgf-node:nth-child(2):after{display:none}.site .dgf-node{min-height:130px}.site .dgf-next{grid-template-columns:1fr}.site .dgf-next a{justify-self:start}}
@media(max-width:650px){.site .dgf-hero{padding:31px 0 38px}.site .dgf-hero .briefing-reader-back{margin-bottom:25px}.site .dgf-map-index{display:none}.site .dgf-bridge-grid,.site .dgf-paths{grid-template-columns:1fr}.site .dgf-node{min-height:0;padding:15px}.site .dgf-node:after{display:none!important}.site .dgf-bridge-footer{display:block}.site .dgf-bridge-footer p{margin-top:5px}.site .dgf-content{padding:21px 18px}.site .dgf-content .article-body{font-size:14px}.site .dgf-next a{width:100%;box-sizing:border-box;text-align:center}}
</style>"""


def funding_briefing_article(
    article, tags: str, source: str, share_footer: str,
    cms_css: str, briefings_css: str, contact_html: str,
    infographic_html: str = "",
) -> str:
    """A complete independent publication route with original decision visual."""
    title = escape(article.title)
    deck = escape(article.subtitle or article.excerpt)
    read_minutes = escape(str(article.read_minutes))
    published_label = escape(article.published_label)
    bridge = (
        '<section class="dgf-bridge" aria-label="Four-stage evidence bridge for a data governance investment" '
        'data-analytics-section="briefings-funding-bridge">'
        '<div class="dgf-map-head"><div><span class="dgf-eyebrow">The funding bridge</span>'
        '<h2>From business friction to investable proof.</h2>'
        '<p>Follow this sequence before choosing a platform or launching an enterprise programme.</p></div>'
        '<span class="dgf-map-index" aria-hidden="true">04</span></div>'
        '<div class="dgf-bridge-grid">'
        '<div class="dgf-node"><b>01 / EXPOSURE</b><strong>Name the loss</strong>'
        '<p>Where does a broken decision or workflow consume capacity, damage trust or create unacceptable risk?</p></div>'
        '<div class="dgf-node"><b>02 / CAUSE</b><strong>Test the cause</strong>'
        '<p>Is the defect in the data, its definition, access, ownership or the process itself?</p></div>'
        '<div class="dgf-node"><b>03 / CONTROL</b><strong>Change the source</strong>'
        '<p>Which minimum ownership, rule, process or technology change prevents recurrence?</p></div>'
        '<div class="dgf-node"><b>04 / PROOF</b><strong>Measure changed work</strong>'
        '<p>Did exception handling, decision quality, time, exposure or operating cost actually improve?</p></div>'
        '</div><div class="dgf-bridge-footer"><strong>Investment gate</strong>'
        '<p>Only release further funding when the owner, cost and operating evidence support it.</p></div>'
        '<p class="dgf-map-caption">Original decision model by Jair Ribeiro. The four stages are a management test, not a formal data-management standard.</p>'
        '</section>'
    )
    decisions = (
        '<section class="dgf-paths" aria-label="Funding outcomes" data-analytics-section="briefings-funding-outcomes">'
        '<div class="dgf-path"><span>Decision 01</span><h3>Approve a bounded step</h3>'
        '<p>Material business exposure, a credible cause, an accountable owner and a measurable trial—or a required control with defined minimum scope.</p></div>'
        '<div class="dgf-path"><span>Decision 02</span><h3>Fund the diagnosis</h3>'
        '<p>There is a real problem, but causality, a suitable control or the economic case is still uncertain.</p></div>'
        '<div class="dgf-path"><span>Decision 03</span><h3>Withhold expansion</h3>'
        '<p>The test does not improve the business outcome, a simpler fix exists or recurring costs outweigh the supported benefit.</p></div>'
        '</section>'
    )
    return (
        THINKING_CSS + cms_css + briefings_css + FUNDING_CSS + nav("thinking")
        + '<main class="briefing-reader dgf-reader">'
        '<section class="dgf-hero" data-analytics-section="briefing-reader-introduction"><div class="container">'
        '<a class="briefing-reader-back" href="?page=briefings" target="_self">← All Executive AI Briefings</a>'
        '<span class="dgf-eyebrow">Executive AI Briefing / Investment & governance</span>'
        f'<h1>{title}</h1><p class="dgf-deck">{deck}</p>'
        f'<p class="dgf-hero-meta">Jair Ribeiro · {read_minutes} min read · {published_label}</p>'
        '</div></section>'
        '<section class="section paper briefing-reader-body"><div class="container">'
        '<section class="dgf-scan" data-analytics-section="briefing-reader-summary">'
        '<div><span class="dgf-eyebrow">The executive judgment</span>'
        '<h2>Fund a business result, not a governance label.</h2>'
        '<p>Approve a targeted control where the exposure is established and the cause is understood. '
        'Where evidence is missing, invest in finding the cause first—not a larger programme.</p></div>'
        '<div class="dgf-scan-side"><strong>The next move</strong>'
        '<p>Ask for a dated baseline, one accountable business owner, the least costly credible remedy '
        'and a review date before committing the next funding tranche.</p></div></section>'
        + (infographic_html or bridge) + decisions
        + '<article class="dgf-content" data-analytics-section="briefing-reader-full-article">'
        '<div class="dgf-content-head"><span class="dgf-eyebrow">The full briefing</span>'
        '<h2>Build the case from evidence.</h2>'
        '<p>Business exposure, full cost, accountable ownership and the conditions for the next decision.</p></div>'
        f'<div class="article-body">{article.content_html}{tags}{source}</div></article>'
        '<section class="dgf-next" data-analytics-section="briefing-reader-contact">'
        '<div><span class="dgf-eyebrow">From investment claim to decision</span>'
        '<h2>Have a governance proposal to challenge?</h2>'
        '<p>Bring one operating failure, its current evidence and the investment being proposed. '
        'That is enough to start a more useful executive discussion.</p></div>'
        '<a href="?page=contact" target="_self" data-hq-event="briefing_reader_contact">Discuss the decision →</a>'
        '</section><div class="dgf-share">' + share_footer + '</div>'
        '</div></section>' + contact_html + '</main>' + footer()
    )
