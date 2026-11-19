"""Concise, employer-neutral operating evidence shared by Home and AI Leadership.

Claims distinguish a working prototype, delivered foundations, and measured adoption.
Do not introduce unverified savings, production deployments, or investment decisions.
"""
from __future__ import annotations


def home_evidence() -> str:
    return '''<section class="section white" id="leadership-in-practice" data-analytics-section="home-operating-evidence"><div class="container">
<div class="head"><div><p class="eyebrow">Leadership in practice</p><h2>What I helped build, test and put in place.</h2></div><p>Four examples from enterprise AI work, with the outcomes and limits made clear.</p></div>
<article class="card" style="margin-bottom:16px"><span class="org">Featured · Generative AI product development</span><h3>Customer Interview Analyzer</h3><p>I led a working GenAI prototype to transcribe, translate and summarize lengthy customer interviews and surface feedback for product teams. It proved technical feasibility, but was not scaled: the organization was not yet ready to operate it.</p><p><a href="?page=impact#customer-interview-analyzer" target="_self" data-hq-event="home_evidence_customer_interviews">Read the case →</a></p></article>
<div class="grid3 evidence-cards-grid"><article class="card"><span class="org">Portfolio decisions</span><h3>80+ AI opportunities</h3><p>Consolidated an AI inventory and developed prioritization, lifecycle and ownership criteria for investment discussions.</p></article>
<article class="card"><span class="org">Workforce enablement</span><h3>Practical AI learning</h3><p>Delivered AI learning sessions and structured prompt-engineering education; training was not counted as measured adoption.</p></article>
<article class="card"><span class="org">Governance foundations</span><h3>Ownership and readiness</h3><p>Developed CoE governance, decision-rights and scale-readiness materials—not a claim of a fully scaled operating model.</p></article></div>
<div class="actions"><a class="btn dark" href="?page=impact" target="_self" data-hq-event="home_evidence_cases">Explore leadership evidence →</a><a class="btn text" href="?page=ai-data-governance" target="_self" data-hq-event="home_evidence_governance">Governance approach →</a></div>
</div></section>'''


def impact_evidence() -> str:
    """Render four employer-neutral cases with optional, bounded operating detail.

    The deep dives clarify how work was approached. Reconstructed decisions
    must be explicitly identified as illustrative, not past employer outcomes.
    Browser-native <details> works without extra scripts, sign-in or reruns.
    """
    return '''<section class="section paper" id="operating-evidence" data-analytics-section="leadership-operating-evidence"><div class="container">
<div class="head" style="display:block;max-width:940px;margin-bottom:32px"><p class="eyebrow">Selected work</p><h2>What I led and what changed.</h2><p style="margin:17px 0 0;max-width:890px">These are selected examples, not an exhaustive record of my work. They show where my leadership helped move AI and Data work forward—by testing new approaches, making investment options easier to compare or establishing operating controls. Each case explains my contribution, what changed and where the outcome had limits. Employer details are omitted where the operating lesson matters more than the name.</p>
<div class="evidence-context-links" role="navigation" aria-label="Find operating evidence by mandate"><span>Evidence by mandate</span><a href="#customer-interview-analyzer" data-hq-event="impact_evidence_nav_product">AI product delivery</a><a href="#ai-portfolio-decisions" data-hq-event="impact_evidence_nav_portfolio">Portfolio decisions</a><a href="#operational-governance" data-hq-event="impact_evidence_nav_operations">Operating accountability</a></div></div>
<article class="card evidence-featured-case" id="customer-interview-analyzer" style="margin-bottom:18px"><span class="org">01 · GenAI product development · Global industrial enterprise</span><h3>Turning customer interviews into product insight.</h3>
<p><strong>Problem.</strong> Product teams ran hundreds of customer interviews, sometimes lasting two hours, with comparable time needed to review each recording manually.</p>
<p><strong>My role.</strong> I led development of a working GenAI prototype with business and technical colleagues. It transcribed and translated interviews, summarized conversations and extracted structured feedback for product owners. We tested multilingual processing and assessed quality, cost and what enterprise use would require.</p>
<p><strong>Result.</strong> The prototype demonstrated technical feasibility. It was not rolled out at scale because organizational readiness had not caught up. The experience sharpened my approach to ownership, adoption and operating conditions before deployment.</p>
<details class="evidence-deep-dive" data-evidence-case="customer-interview-analyzer"><summary data-hq-event="impact_case_analyzer_toggle">How the prototype was evaluated</summary><div class="evidence-deep-dive-body">
<p><strong>Workflow.</strong> Recorded interview → transcription and translation → generated summary and themes → structured feedback for product owners to review. Human review remained necessary; generated text was not treated as a verified customer finding on its own.</p>
<p><strong>My responsibility.</strong> Connecting the product-team problem with technical development and testing, including the usefulness of outputs, multilingual handling and the conditions for continuing beyond a prototype. Specialist engineering work remained with the technical colleagues involved.</p>
<p><strong>Decision and constraint.</strong> Technical feasibility alone was insufficient for a wider rollout. Ownership, review, integration into product-team routines and ongoing support also needed to be workable. This is a decision lesson, not a claim of an approved production release.</p>
<p class="evidence-boundary"><strong>Evidence boundary.</strong> No production deployment, audited processing-time reduction, quantified accuracy or realized financial benefit is claimed.</p>
</div></details></article>
<div class="grid3 evidence-cards-grid">
<article class="card" id="ai-portfolio-decisions"><span class="org">02 · AI portfolio management</span><h3>Making investment choices comparable.</h3><p>Consolidated an inventory of 80+ AI opportunities and developed Keep / Kill / Scale criteria, lifecycle stages and ownership materials. The delivered outcome was a common decision foundation, not a claimed count of cancelled or scaled projects.</p>
<details class="evidence-deep-dive" data-evidence-case="ai-portfolio-decisions"><summary data-hq-event="impact_case_portfolio_toggle">How decisions were structured</summary><div class="evidence-deep-dive-body">
<p><strong>Mechanism.</strong> Compare opportunities using expected business value, feasibility, data readiness, risk, potential reuse, required resources and accountable owners. Bring those differences into the same leadership discussion.</p>
<p><strong>My responsibility.</strong> Portfolio consolidation and assessment criteria; investment authorization and operational results remained the responsibility of their respective decision owners.</p>
<p class="evidence-illustration"><strong>Illustrative decision logic—not an actual disclosed employer decision:</strong> A use case with attractive value but no clear data owner or receiving team should be paused for prerequisite work rather than presented as ready to scale.</p>
<p class="evidence-boundary"><strong>Evidence boundary.</strong> No specific approval, cancellation, portfolio savings or production result is attributed to the framework.</p>
</div></details></article>
<article class="card" id="ai-adoption-learning"><span class="org">03 · AI literacy and adoption</span><h3>Teaching AI through everyday work.</h3><p>Delivered 100+ AI learning sessions across enterprise roles and developed practical prompt-engineering materials. The program connected AI capabilities and limitations to business tasks; session volume is not presented as proof of productivity gains.</p>
<details class="evidence-deep-dive" data-evidence-case="ai-adoption-learning"><summary data-hq-event="impact_case_learning_toggle">What delivery demonstrated</summary><div class="evidence-deep-dive-body">
<p><strong>Mechanism.</strong> Practical examples, shared vocabulary and exercises linked AI capabilities and limitations to everyday work rather than treating tool access as adoption.</p>
<p><strong>Measured activity.</strong> The documented scale is the education delivered; business-process changes would require a separate baseline and follow-up measurement.</p>
<p class="evidence-boundary"><strong>Evidence boundary.</strong> Training reach is not equated with sustained usage, adoption, cost savings or organizational productivity.</p>
</div></details></article>
<article class="card" id="operational-governance"><span class="org">04 · Operational data-platform governance</span><h3>Managing shared analytics capacity in practice.</h3><p>Worked on Power BI Premium capacity governance, including workspace-request reviews, capacity monitoring and coordination with central Digital &amp; IT specialists. This was recurring operational accountability—not a claim of AI model governance or quantified savings.</p>
<details class="evidence-deep-dive" data-evidence-case="operational-governance"><summary data-hq-event="impact_case_operations_toggle">What the operating controls involved</summary><div class="evidence-deep-dive-body">
<p><strong>Operating mechanism.</strong> Review a workspace's business purpose, capacity implications and support ownership; monitor shared use; coordinate decisions or escalations with the technical specialists responsible for the platform.</p>
<p><strong>My responsibility.</strong> Governance and stakeholder coordination around shared analytical resources, rather than claiming direct ownership of every engineering operation or the entire underlying platform.</p>
<p class="evidence-illustration"><strong>Illustrative request assessment—not an actual disclosed employer event:</strong> A new workspace request should be checked against its use, available headroom and the team responsible for ongoing support before approval.</p>
<p class="evidence-boundary"><strong>Evidence boundary.</strong> This is an anonymized data-platform operations example; no particular capacity incident, financial result or employer-sensitive configuration is disclosed.</p>
</div></details></article>
</div>
<p class="muted" style="margin-top:18px">Selected employer-neutral examples. Real delivered work is distinguished from clearly marked illustrative decision logic. Prototypes, operating foundations and recurring responsibilities are not described as equivalent to enterprise-wide production adoption or measured return.</p>
</div></section>'''
