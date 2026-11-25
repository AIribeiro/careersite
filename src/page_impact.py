"""Public AI leadership: selected operating evidence before career breadth.

Employer-neutral cases show substantive contributions, delivered results and realistic
scope. Employment history and role dates come from approved public career facts.
"""
from __future__ import annotations

from portfolio_operating_evidence import impact_evidence
from site_components import nav, footer
from about_next_navigation import portfolio_next_navigation
from career_facts import (
    MSX_PUBLIC_DATES, MSX_ROADMAP, VOLVO_AI_INITIATIVES,
    VOLVO_CURRENT_DATES, VOLVO_SENIOR_AI_DATES, KIMBERLY_DATES,
)

CLAES_LINKEDIN = "https://se.linkedin.com/in/claes-sandros-1a795512"
ANNA_LINKEDIN = "https://se.linkedin.com/in/annaborjesson"


def impact() -> str:
    return f'''{nav("impact")}<main>
<section class="pagehero"><div class="container">
<p class="eyebrow">AI Leadership</p>
<h1>What I led, built and changed.</h1>
<p>My work spans AI strategy, product development, portfolio decisions, governance and adoption. I lead across business, IT and engineering, translating priorities into requirements, testing solutions, developing people and establishing accountable ways of working. The cases below show how that work took shape.</p>
<div class="actions"><a class="btn primary" href="#operating-evidence" target="_self" data-hq-event="impact_hero_cases">Selected cases →</a><a class="btn ghost" href="?page=ai-data-governance" target="_self" data-hq-event="impact_hero_governance">Governance approach →</a></div>
</div></section>

{impact_evidence()}

<section class="section white" id="career-experience"><div class="container">
<div class="head"><div><p class="eyebrow">Experience by mandate</p><h2>Where the work took place.</h2></div><p>Selected mandates and contributions across enterprise AI, Data and Analytics. My CV carries the complete career chronology.</p></div>
<div class="grid3">
<article class="card"><span class="org">MSX International · {MSX_PUBLIC_DATES.replace(' - ', ' – ')}</span><h3>AI &amp; Data CoE Director</h3><p>I led the enterprise AI &amp; Data CoE foundation across functions and Value Streams, consolidating 80+ opportunities and owning the assessment, design, development, requirements and implementation work for dozens of leadership-sponsored opportunities. I introduced decision criteria, lifecycle checkpoints, RACI materials, a seven-pillar assessment and a {MSX_ROADMAP.replace('-', '–')} maturity roadmap. Common governance and AI literacy and Champions foundations supported investment decisions and distributed delivery ownership.</p></article>
<article class="card"><span class="org">Volvo Group / Volvo Trucks · {VOLVO_CURRENT_DATES.replace(' - ', ' – ')}</span><h3>Data Analytics and AI Leader</h3><p>Led business-facing AI and analytics work across warranty, sales and aftermarket, including Copilot and agent initiatives, requirements and testing for several GenAI prototypes, stakeholder engagement and adoption planning with Digital &amp; IT. This provided strong exposure to connected-vehicle operations. I also owned technical and business-side responsibilities for Power BI Premium capacity serving more than 4,000 users.</p></article>
<article class="card"><span class="org">Kimberly-Clark · {KIMBERLY_DATES.replace(' - ', ' – ')}</span><h3>AI Strategist · EMEA</h3><p>Reported to the Chief Data &amp; Analytics Officer, helping manufacturing, supply-chain and commercial teams evaluate AI value, feasibility and readiness across functions.</p></article>
<article class="card"><span class="org">Volvo Group · {VOLVO_SENIOR_AI_DATES.replace(' - ', ' – ')}</span><h3>Senior AI Business Expert</h3><p>Led business requirements, product work and cross-functional coordination in an AI &amp; ML CoE, and drove practical AI adoption across international teams. I delivered 100+ practical AI learning sessions at Volvo, communicating with executives, engineers and international teams. Across both Volvo AI roles, I shaped and supported {VOLVO_AI_INITIATIVES} AI initiatives, proofs of concept and projects at different stages of maturity.</p></article>
</div>
<p class="muted" style="margin-top:20px;max-width:1050px;line-height:1.7"><strong>Technical foundation — and where it still matters.</strong> My career began in hands-on systems administration and senior IT engineering, followed by enterprise infrastructure and cloud services at HPE and IBM. My AI experience began with IBM Watson in Poland in 2016. I have worked with Azure, AWS and Databricks and engage directly with developers and IT teams on requirements, architecture, testing, delivery trade-offs, data dependencies, feasibility, quality and cost. I have also led GenAI prototype work, including testing multilingual customer-interview analysis and what it would take to operate the solution beyond a demonstration. <a href="?page=about" target="_self">Career background →</a></p>
</div></section>

<section class="section soft" id="leadership-references" data-analytics-section="impact-leadership-references"><div class="container">
<div class="head"><div><p class="eyebrow">Leadership references</p><h2>Comments from people I worked with.</h2></div><p>Published professional recommendations from senior colleagues.</p></div>
<div class="principles">
<article class="principle"><span>Direct manager · Volvo Trucks</span><h3>Claes Sandros</h3><p><strong>Acting Head of Data and Vice President Data, Analytics &amp; AI, Volvo Trucks</strong></p><p style="font:500 18px/1.5 Georgia,serif;color:var(--ink);margin-top:20px">“What truly impressed me was his ability to combine deep analytical knowledge with strategic thinking and a collaborative mindset.”</p><div class="proof"><a href="{CLAES_LINKEDIN}" target="_blank" rel="noopener" data-hq-event="reference_claes_impact">LinkedIn profile ↗</a></div></article>
<article class="principle"><span>Senior cross-functional colleague · Volvo Group</span><h3>Anna Börjesson Sandberg</h3><p><strong>VP, Digital Transformation, Volvo Group Trucks Technology</strong></p><p style="font:500 18px/1.5 Georgia,serif;color:var(--ink);margin-top:20px">“Jair continuously wanted to move towards the future of Data and AI and could always explain the purpose and next possible steps.”</p><div class="proof"><a href="{ANNA_LINKEDIN}" target="_blank" rel="noopener" data-hq-event="reference_anna_impact">LinkedIn profile ↗</a></div></article>
</div>
</div></section>
{portfolio_next_navigation("impact")}
</main>{footer()}'''
