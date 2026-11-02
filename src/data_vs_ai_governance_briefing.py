from __future__ import annotations

"""Original editorial reader: data governance and AI governance, one business decision.

The published CMS body owns the long-form perspective and authoritative citations.
The reader contributes an independent, accessible and responsive executive model.
"""

from html import escape

from site_components import nav, footer
from thinking_core import THINKING_CSS


DUAL_GOV_CSS = r"""<style>
.site .dga-reader{background:#f3f1ed;color:#233b4a}
.site .dga-hero{background:radial-gradient(ellipse at 84% 12%,#38566a 0%,#142e41 64%);border-top:4px solid #c29a75;padding:clamp(38px,5vw,77px) 0 clamp(41px,5vw,76px)}
.site .dga-back{display:inline-block;color:#ebdfd1!important;font:700 12px/1.4 Arial,sans-serif;text-decoration:none!important;margin:0 0 28px}
.site .dga-eyebrow{display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#d5a780}
.site .dga-hero h1{font:500 clamp(35px,5.25vw,65px)/1.085 Georgia,serif;letter-spacing:-.026em;color:#fff;max-width:990px;margin:12px 0 17px}
.site .dga-hero p{font:400 clamp(15px,1.75vw,19px)/1.57 Arial,sans-serif;color:#d8e4e9;margin:0;max-width:830px}
.site .dga-hero .dga-meta{font:750 11px/1.6 Arial,sans-serif;color:#e6b894;margin-top:20px}
.site .dga-shell{padding-top:26px;padding-bottom:35px}
.site .dga-judgment{display:grid;grid-template-columns:minmax(0,1.37fr) minmax(230px,.73fr);gap:29px;border:1px solid #dedbd4;border-left:5px solid #ae7e60;background:#fffefa;padding:clamp(22px,3.4vw,36px)}
.site .dga-judgment .dga-eyebrow,.site .dga-body-title .dga-eyebrow{color:#8c5a3b}
.site .dga-judgment h2{font:500 clamp(27px,3.6vw,39px)/1.16 Georgia,serif;color:#1a3649;margin:9px 0 14px;max-width:700px}
.site .dga-judgment p{font:400 14px/1.67 Arial,sans-serif;color:#47606c;margin:0;max-width:745px}
.site .dga-move{border-left:1px solid #d5d9d5;padding-left:25px;align-self:center}
.site .dga-move strong{display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.12em;color:#935f3c;text-transform:uppercase;margin-bottom:10px}
.site .dga-move p{font-weight:600;color:#264252}
.site .dga-stage{margin:23px 0 14px;background:#153248;border:1px solid #496579;border-top:4px solid #cea381;padding:clamp(20px,3vw,34px);color:#fff}
.site .dga-stage-top{display:flex;justify-content:space-between;gap:20px;align-items:start}
.site .dga-stage-top h2{font:500 clamp(26px,3.2vw,38px)/1.2 Georgia,serif;color:#fff;margin:7px 0 9px}
.site .dga-stage-top p{font:400 13px/1.66 Arial,sans-serif;color:#c5d5de;margin:0 0 21px;max-width:790px}
.site .dga-stage-ref{font:500 44px/1 Georgia,serif;color:#c69b79}
.site .dga-streams{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.site .dga-stream{background:#203f53;border:1px solid #617d8c;padding:21px 22px;min-width:0}
.site .dga-stream--ai{background:#2c3d50;border-color:#807b78}
.site .dga-stream .dga-small{display:block;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.13em;color:#badbe0;text-transform:uppercase}
.site .dga-stream--ai .dga-small{color:#f1c2a1}
.site .dga-stream h3{font:500 clamp(22px,2.5vw,30px)/1.2 Georgia,serif;color:#fff;margin:10px 0 8px}
.site .dga-stream p{font:400 13px/1.6 Arial,sans-serif;color:#e0e9eb;margin:0}
.site .dga-evidence{border-top:1px solid #657989;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin-top:16px;padding-top:14px}
.site .dga-evidence div{min-width:0}
.site .dga-evidence b{display:block;font:850 10px/1.4 Arial,sans-serif;letter-spacing:.1em;color:#d9b494;margin-bottom:7px}
.site .dga-evidence span{display:block;font:400 12px/1.6 Arial,sans-serif;color:#d4e1e6}
.site .dga-merge{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px;margin:15px 0}
.site .dga-merge div{height:1px;background:#7f9ca9}
.site .dga-merge span{font:800 10px/1.5 Arial,sans-serif;letter-spacing:.15em;color:#dec09f;text-transform:uppercase}
.site .dga-gate{background:#f2e4d3;color:#203d4c;border-left:5px solid #ca9872;padding:22px 25px;display:grid;grid-template-columns:minmax(0,1fr) minmax(210px,.58fr);align-items:center;gap:20px}
.site .dga-gate h3{font:500 clamp(25px,2.8vw,33px)/1.2 Georgia,serif;color:#193749;margin:5px 0 8px}
.site .dga-gate p{font:400 13px/1.65 Arial,sans-serif;color:#445969;margin:0}
.site .dga-gate b{display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.12em;color:#825336}
.site .dga-gate strong{font:800 14px/1.55 Arial,sans-serif;color:#263f51}
.site .dga-visual-note{font:400 11px/1.6 Arial,sans-serif;color:#becfd8;margin:16px 0 0}
.site .dga-failure{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin:14px 0 23px}
.site .dga-fail-card{border:1px solid #d9d9d2;background:#fffdf9;padding:18px 19px;border-top:3px solid #8da9a4}
.site .dga-fail-card:nth-child(2){border-top-color:#be9a73}.site .dga-fail-card:nth-child(3){border-top-color:#8a96a3}
.site .dga-fail-card b{display:block;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.1em;color:#976742}
.site .dga-fail-card h3{font:500 21px/1.23 Georgia,serif;color:#233f50;margin:7px 0}
.site .dga-fail-card p{font:400 12px/1.6 Arial,sans-serif;color:#526671;margin:0}
.site .dga-article{border:1px solid #e0ddd7;background:#fffefa;padding:clamp(22px,4.2vw,52px);margin-bottom:23px}
.site .dga-body-title{padding-bottom:20px;margin-bottom:23px;border-bottom:1px solid #d6dcd7}
.site .dga-body-title h2{font:500 clamp(28px,3.4vw,39px)/1.17 Georgia,serif;color:#1c3d50;margin:9px 0}
.site .dga-body-title p{font:400 13px/1.6 Arial,sans-serif;color:#5a6d78;margin:0}
.site .dga-article .article-body{max-width:790px;margin:0 auto;font:400 15px/1.8 Arial,sans-serif;color:#354f5c}
.site .dga-article .article-body p{margin:0 0 17px}
.site .dga-article .article-body h2{font:500 clamp(25px,3vw,32px)/1.22 Georgia,serif;color:#16394e;margin:37px 0 13px}
.site .dga-article .article-body h3{font:500 21px/1.3 Georgia,serif;color:#254657;margin:24px 0 9px}
.site .dga-article .article-body strong{color:#1b3b50}
.site .dga-article .article-body li{padding-left:5px;margin:0 0 10px}
.site .dga-article .article-body li::marker{color:#a67656}
.site .dga-article .article-body a{color:#875c3d;text-decoration:underline;text-underline-offset:3px;overflow-wrap:anywhere}
.site .dga-share{padding:5px 0 24px}
@media(max-width:850px){
 .site .dga-judgment,.site .dga-gate{grid-template-columns:1fr}
 .site .dga-move{border-left:0;border-top:1px solid #d5d9d5;padding:17px 0 0}
}
@media(max-width:650px){
 .site .dga-hero{padding:32px 0 39px}.site .dga-shell{padding-top:16px}
 .site .dga-streams,.site .dga-failure{grid-template-columns:1fr}
 .site .dga-stream{padding:17px 18px}
 .site .dga-evidence{grid-template-columns:1fr}
 .site .dga-stage{padding:20px 16px}.site .dga-stage-ref{display:none}
 .site .dga-gate{padding:19px 17px}
 .site .dga-article{padding:24px 17px}.site .dga-article .article-body{font-size:14px}
 .site .dga-merge span{white-space:normal;text-align:center}
}
</style>"""


def dual_governance_briefing_article(
    article, tags: str, source: str, share_footer: str,
    cms_css: str, briefings_css: str, contact_html: str,
    infographic_html: str = "",
) -> str:
    """A self-contained editorial issue with original evidence-handoff visual."""

    stage = (
        '<section class="dga-stage" aria-label="Data and AI governance evidence streams converge at a business decision gate" '
        'data-analytics-section="briefing-governance-handoff">'
        '<div class="dga-stage-top"><div>'
        '<span class="dga-eyebrow">The executive operating boundary</span>'
        '<h2>Two evidence streams. One approval.</h2>'
        '<p>Each function has something distinct to prove. The business owner should not authorise the AI-enabled workflow until both are credible for the intended purpose.</p>'
        '</div><span class="dga-stage-ref" aria-hidden="true">02/01</span></div>'
        '<div class="dga-streams">'
        '<section class="dga-stream"><span class="dga-small">01 / Information fitness</span>'
        '<h3>Data governance</h3>'
        '<p>Can this information be understood, accessed and relied upon for this business purpose?</p>'
        '<div class="dga-evidence">'
        '<div><b>ACCOUNTABLE</b><span>Data owner and process stewards</span></div>'
        '<div><b>SHOW THE EVIDENCE</b><span>Definitions · sources · quality · provenance · permitted access</span></div>'
        '</div></section>'
        '<section class="dga-stream dga-stream--ai"><span class="dga-small">02 / Operating assurance</span>'
        '<h3>AI governance</h3>'
        '<p>Is the system fit to recommend or act, under the permissions and consequences of this use?</p>'
        '<div class="dga-evidence">'
        '<div><b>ACCOUNTABLE</b><span>AI business owner and system operator</span></div>'
        '<div><b>SHOW THE EVIDENCE</b><span>Use classification · evaluation · oversight · action limits · monitoring</span></div>'
        '</div></section></div>'
        '<div class="dga-merge"><div aria-hidden="true"></div><span>Joint decision boundary</span><div aria-hidden="true"></div></div>'
        '<div class="dga-gate"><div><b>RELEASE GATE / BUSINESS SPONSOR</b>'
        '<h3>Should this workflow be allowed to operate?</h3>'
        '<p>One decision record. Distinct approvals. Explicit restrictions, failure ownership and a next review trigger.</p>'
        '</div><strong>Proceed · Restrict · Test · Stop</strong></div>'
        '<p class="dga-visual-note">Original executive operating model by Jair Ribeiro. Decision model, not a legal classification or a claim that both functions share identical regulatory duties.</p>'
        '</section>'
    )
    counterexamples = (
        '<section class="dga-failure" aria-label="Three management failure patterns" '
        'data-analytics-section="briefing-boundary-failures">'
        '<div class="dga-fail-card"><b>INFORMATION FAILURE</b><h3>Wrong source</h3>'
        '<p>An assistant accurately repeats an outdated rule. Repair the source and how it is kept current.</p></div>'
        '<div class="dga-fail-card"><b>AI BEHAVIOR FAILURE</b><h3>Wrong interpretation</h3>'
        '<p>The approved rule is current, but the assistant mishandles an exception. Fix evaluation and review.</p></div>'
        '<div class="dga-fail-card"><b>SHARED CONTROL FAILURE</b><h3>Wrong permission</h3>'
        '<p>The information may be read, but the AI has more authority to act or disclose than intended. Restrict the workflow.</p></div>'
        '</section>'
    )
    return (
        THINKING_CSS + cms_css + briefings_css + DUAL_GOV_CSS + nav("thinking")
        + '<main class="briefing-reader dga-reader">'
        '<section class="dga-hero" data-analytics-section="briefing-reader-introduction"><div class="container">'
        '<a href="?page=briefings" target="_self" class="dga-back">← All Executive AI Briefings</a>'
        '<span class="dga-eyebrow">Executive AI Briefing / Governance decision rights</span>'
        f'<h1>{escape(article.title)}</h1>'
        f'<p>{escape(article.subtitle or article.excerpt)}</p>'
        f'<p class="dga-meta">Jair Ribeiro · {escape(article.published_label if article.published_at else "Draft preview")} · {escape(str(article.read_minutes))} min read</p>'
        '</div></section>'
        '<section class="section paper"><div class="container dga-shell">'
        '<section class="dga-judgment" data-analytics-section="briefing-reader-summary">'
        '<div><span class="dga-eyebrow">The executive judgment</span>'
        '<h2>Do not merge two different responsibilities—or build two approval empires.</h2>'
        '<p>Give data ownership and AI oversight distinct evidence requirements, then bring them together in one accountable business release decision. Neither the data catalogue nor the model score is the approval.</p></div>'
        '<aside class="dga-move"><strong>Next management move</strong>'
        '<p>Choose one AI-enabled workflow. Request its data-fitness proof, its AI behavior and permission proof, and the named sponsor who will decide to proceed, restrict, test or stop.</p></aside></section>'
        + (infographic_html or stage) + counterexamples
        + '<article class="dga-article" data-analytics-section="briefing-reader-full-article">'
        '<div class="dga-body-title"><span class="dga-eyebrow">The complete perspective</span>'
        '<h2>Where the responsibilities meet—and where they do not.</h2>'
        '<p>Decision authority, real-world failure modes, evidence, ownership and a field-informed operating example.</p></div>'
        f'<div class="article-body">{article.content_html}{tags}{source}</div></article>'
        '<div class="dga-share">' + share_footer + '</div>'
        '</div></section>' + contact_html + '</main>' + footer()
    )
