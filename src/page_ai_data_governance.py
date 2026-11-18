"""Concise executive governance page; keep the approved visual framework intact."""
from __future__ import annotations

from site_assets import CV_URI
from governance_feature import GOVERNANCE_FEATURE
from site_components import nav, footer, CV_DOWNLOAD_NAME
from about_next_navigation import portfolio_next_navigation

DFM_GOVERNANCE_URL = "https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/"


def ai_data_governance() -> str:
    cv = (
        f'<a class="btn ghost" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" '
        f'data-hq-event="cv_download_governance">Download CV ↓</a>'
        if CV_URI else ""
    )
    return f'''{nav("ai-data-governance")}<main>
<section class="pagehero"><div class="container">
<p class="eyebrow">AI &amp; Data Governance · Operating perspective</p>
<h1>AI &amp; Data governance that connects accountability with scale.</h1>
<p>Good governance makes ownership, evidence and escalation part of how AI is delivered and used.</p>
<div class="actions"><a class="btn primary" href="#governance-evidence" data-hq-event="governance_hero_evidence">See the evidence →</a><a class="btn ghost" href="#governance-operating-model" data-hq-event="governance_hero_model">Explore the operating model ↓</a><a class="btn ghost" href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_dfm">Read my governance article ↗</a>{cv}</div>
</div></section>

{GOVERNANCE_FEATURE}

<section class="section white" id="governance-evidence"><div class="container">
<div class="head"><div><p class="eyebrow">Evidence from my work</p><h2>Governance deliverables, not just principles.</h2></div><p>Examples from enterprise AI and Data roles. Outcomes are stated at the stage actually reached.</p></div>
<div class="grid3 evidence-cards-grid">
<article class="card"><span class="org">Portfolio and decision rights</span><h3>Make the next decision explicit.</h3><p>For an emerging AI &amp; Data CoE, I developed lifecycle criteria, Keep / Kill / Scale evaluation, RACI materials and scale-readiness considerations for an 80+ opportunity portfolio. The deliverable was a decision foundation, not a claim that every stage gate was fully operational.</p></article>
<article class="card"><span class="org">Data stewardship foundations</span><h3>Give data responsibility a starting point.</h3><p>I connected a seven-pillar maturity assessment with data ownership and stewardship priorities, producing a 2026–2027 roadmap. Early foundation work is distinct from a completed enterprise-wide data-governance rollout.</p></article>
<article class="card"><span class="org">AI in commercial work</span><h3>Connect controls to real workflows.</h3><p>In business-facing AI initiatives across warranty, sales and aftermarket, I worked with product, Digital &amp; IT, legal and compliance stakeholders on feasibility, human oversight and operating responsibility.</p></article>
</div>
<div class="actions"><a class="btn dark" href="?page=impact#operating-evidence" target="_self" data-hq-event="governance_operating_case">View selected operating cases →</a></div>
</div></section>

<section class="section paper"><div class="container">
<div class="head"><div><p class="eyebrow">Operating decisions</p><h2>Six questions before AI moves forward.</h2></div><p>These are my decision criteria, not a claim that one standard process was deployed everywhere.</p></div>
<div class="prooflist">
<div class="proofitem"><strong>Purpose:</strong> Which business task or decision changes?</div>
<div class="proofitem"><strong>Owner:</strong> Who is accountable for the result and ongoing use?</div>
<div class="proofitem"><strong>Data:</strong> Are the source, quality, permissions and owners clear?</div>
<div class="proofitem"><strong>Evidence:</strong> What must be demonstrated at this stage?</div>
<div class="proofitem"><strong>Human review:</strong> Where does judgment or escalation remain necessary?</div>
<div class="proofitem"><strong>Operation:</strong> Who monitors exceptions and approves material changes?</div>
</div>
</div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">Four observable signals</p><h2>Governance should be visible in everyday decisions.</h2></div></div>
<div class="metrics">
<div class="metric"><strong>Know</strong><p>Where material AI is used and for what purpose.</p></div>
<div class="metric"><strong>Own</strong><p>Who is accountable for business, data and system behavior.</p></div>
<div class="metric"><strong>Explain</strong><p>What evidence supports a material decision.</p></div>
<div class="metric"><strong>Respond</strong><p>Who can intervene and when reassessment is required.</p></div>
</div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Research &amp; published perspective</p><h2>The thinking behind the practice.</h2></div><p>My Responsible AI research and external writing examine how ownership, proportionate controls, human oversight and trust support enterprise use. Research informs the approach; the cases above describe delivered work.</p></div>
<div class="actions"><a class="btn dark" href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_evidence">Read: AI Governance Is Not About Control. It Is About Scale. ↗</a></div>
</div></section>
{portfolio_next_navigation("ai-data-governance")}
</main>{footer()}'''
