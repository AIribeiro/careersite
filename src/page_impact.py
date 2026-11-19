"""Public AI leadership: selected operating evidence before career breadth.

Employer-neutral cases describe bounded contributions. Employment history remains
explicit; role dates come from the approved public career facts.
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
<h1>What I led, built and learned.</h1>
<p>My work spans AI product development, portfolio decisions, governance and adoption. These examples show the contribution and the outcome—including where enterprise rollout did not follow.</p>
<div class="actions"><a class="btn primary" href="#operating-evidence" target="_self" data-hq-event="impact_hero_cases">Selected cases →</a><a class="btn ghost" href="?page=ai-data-governance" target="_self" data-hq-event="impact_hero_governance">Governance approach →</a></div>
</div></section>

{impact_evidence()}

<section class="section white" id="career-experience"><div class="container">
<div class="head"><div><p class="eyebrow">Experience by mandate</p><h2>Where the work took place.</h2></div><p>The full career chronology is available in my CV. These are selected responsibilities, not claims that every initiative was deployed.</p></div>
<div class="grid3">
<article class="card"><span class="org">MSX International · {MSX_PUBLIC_DATES.replace(' - ', ' – ')}</span><h3>AI &amp; Data CoE Director</h3><p>Led an emerging CoE mandate: an 80+ opportunity inventory, decision criteria, lifecycle and RACI materials, a seven-pillar assessment and a {MSX_ROADMAP.replace('-', '–')} maturity roadmap. These were delivered foundations, not a fully scaled CoE.</p></article>
<article class="card"><span class="org">Volvo Group / Volvo Trucks · {VOLVO_CURRENT_DATES.replace(' - ', ' – ')}</span><h3>Data Analytics and AI Leader</h3><p>Led business-facing AI and analytics work across warranty, sales and aftermarket, including Copilot and agent initiatives, product prototypes, stakeholder engagement and adoption planning with Digital &amp; IT.</p></article>
<article class="card"><span class="org">Kimberly-Clark · {KIMBERLY_DATES.replace(' - ', ' – ')}</span><h3>AI Strategist · EMEA</h3><p>Reported to the Chief Data &amp; Analytics Officer, helping manufacturing, supply-chain and commercial teams evaluate AI value, feasibility and readiness across functions.</p></article>
<article class="card"><span class="org">Volvo Group · {VOLVO_SENIOR_AI_DATES.replace(' - ', ' – ')}</span><h3>Senior AI Business Expert</h3><p>Led business-requirement, product and stakeholder work in an AI &amp; ML CoE and delivered 100+ AI learning sessions. Across both Volvo AI roles, portfolio involvement covered {VOLVO_AI_INITIATIVES} AI initiatives, PoCs and projects—not production deployments.</p></article>
</div>
<p class="muted" style="margin-top:20px;max-width:1050px;line-height:1.7"><strong>Technical foundation — and where it still matters.</strong> My career began in hands-on systems administration and senior IT engineering, followed by enterprise infrastructure, cloud services and IBM Watson solution design. That experience helps me engage directly with technical teams on architecture choices, data dependencies, feasibility, quality and cost—not just discuss AI strategy. I have also led GenAI prototype work, including testing multilingual customer-interview analysis and what it would take to operate the solution beyond a demonstration. <a href="?page=about" target="_self">Career background →</a></p>
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
