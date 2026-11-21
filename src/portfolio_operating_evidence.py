"""Concise, employer-neutral operating evidence shared by Home and AI Leadership.

Lead with what was delivered and what changed. Describe scope with precision, without
turning every example into a list of things not claimed. Never invent ROI or rollout.
"""
from __future__ import annotations


def home_evidence() -> str:
    """Four equal, compact Home case links to the corresponding Impact anchors."""
    return '''<section class="section white" id="leadership-in-practice" data-analytics-section="home-operating-evidence"><div class="container">
<div class="head"><div><p class="eyebrow">Leadership in practice</p><h2>What I delivered across AI and Data.</h2></div><p>Four examples of practical leadership: building a working prototype, structuring investment choices, developing people and managing shared analytics resources.</p></div>
<div class="home-evidence-grid">
<article class="card"><a class="home-evidence-card-link" href="?page=impact#customer-interview-analyzer" target="_self" data-hq-event="home_evidence_customer_interviews"><span class="org">01 · GenAI product development</span><h3>Customer Interview Analyzer</h3><p>Led a working multilingual GenAI prototype that turned recorded interviews into structured themes and feedback for product-owner review.</p><span class="home-evidence-card-cta">Read example →</span></a></article>
<article class="card"><a class="home-evidence-card-link" href="?page=impact#ai-portfolio-decisions" target="_self" data-hq-event="home_evidence_portfolio"><span class="org">02 · Portfolio decisions</span><h3>80+ AI opportunities</h3><p>Brought 80+ AI opportunities into one portfolio view and developed investment criteria, lifecycle stages and ownership guidance.</p><span class="home-evidence-card-cta">Read example →</span></a></article>
<article class="card"><a class="home-evidence-card-link" href="?page=impact#ai-adoption-learning" target="_self" data-hq-event="home_evidence_learning"><span class="org">03 · Workforce enablement</span><h3>Practical AI learning</h3><p>Delivered 100+ practical AI learning sessions and reusable prompt-engineering guidance tied to everyday business work.</p><span class="home-evidence-card-cta">Read example →</span></a></article>
<article class="card"><a class="home-evidence-card-link" href="?page=impact#operational-governance" target="_self" data-hq-event="home_evidence_operations"><span class="org">04 · Operating accountability</span><h3>Analytics capacity governance</h3><p>Helped govern shared Power BI capacity through workspace reviews, usage monitoring and coordination with Digital &amp; IT.</p><span class="home-evidence-card-cta">Read example →</span></a></article>
</div></div></section>'''


def impact_evidence() -> str:
    """Render four employer-neutral cases with optional, bounded operating detail.

    The deep dives clarify how work was approached. Reconstructed decisions
    must be explicitly identified as illustrative, not past employer outcomes.
    Browser-native <details> works without extra scripts, sign-in or reruns.
    """
    return '''<section class="section paper" id="operating-evidence" data-analytics-section="leadership-operating-evidence"><div class="container">
<div class="head" style="display:block;max-width:940px;margin-bottom:32px"><p class="eyebrow">Selected work</p><h2>What I led and what changed.</h2><p style="margin:17px 0 0;max-width:890px">These four cases show how I turn AI and Data priorities into concrete work: a tested product concept, a portfolio of investment options, practical AI learning and controls for shared analytics. Each explains the problem, my contribution and what the work delivered. Some employer details are intentionally kept confidential.</p>
<div class="evidence-context-links" role="navigation" aria-label="Find operating evidence by mandate"><span>Evidence by mandate</span><a href="#customer-interview-analyzer" data-hq-event="impact_evidence_nav_product">AI product delivery</a><a href="#ai-portfolio-decisions" data-hq-event="impact_evidence_nav_portfolio">Portfolio decisions</a><a href="#operational-governance" data-hq-event="impact_evidence_nav_operations">Operating accountability</a></div></div>
<article class="card evidence-featured-case" id="customer-interview-analyzer" style="margin-bottom:18px"><span class="org">01 · GenAI product development · Global industrial enterprise</span><h3>Turning customer interviews into product insight.</h3>
<p><strong>Problem.</strong> Product teams ran hundreds of customer interviews, sometimes lasting two hours, with comparable time needed to review each recording manually.</p>
<p><strong>My contribution.</strong> I led development of a working GenAI prototype with business and technical colleagues, connecting product-team needs to the solution and its evaluation. It transcribed and translated interviews, generated summaries and organized customer feedback. We tested multilingual performance, output quality, cost and practical requirements for enterprise use.</p>
<p><strong>What we delivered.</strong> A working multilingual prototype and a validated end-to-end workflow from recordings to structured feedback for product owners to review. The tests established technical feasibility and exposed the ownership, review and support needed for wider use. The organization did not proceed to a production rollout at that stage.</p>
<details class="evidence-deep-dive" data-evidence-case="customer-interview-analyzer"><summary data-hq-event="impact_case_analyzer_toggle">How the prototype was evaluated</summary><div class="evidence-deep-dive-body">
<p><strong>Workflow.</strong> Recorded interview → transcription and translation → generated summary and themes → structured feedback for product owners to review. Human review remained necessary; generated text was not treated as a verified customer finding on its own.</p>
<p><strong>My leadership role.</strong> I connected the product-team problem to development and testing, set the focus on useful outputs and multilingual handling, and examined what would be required to move beyond a prototype. Technical specialists handled the engineering work.</p>
<p><strong>What the work clarified.</strong> A viable technology still needs a product owner, a review process and a place in daily team routines. These were the practical conditions identified before considering wider rollout; the outcome was a tested prototype rather than an operational service.</p>
</div></details></article>
<div class="grid3 evidence-cards-grid">
<article class="card" id="ai-portfolio-decisions"><span class="org">02 · AI portfolio management</span><h3>Making investment choices comparable.</h3><p>I consolidated 80+ AI opportunities into a portfolio view and developed Keep / Kill / Scale criteria, lifecycle stages and ownership guidance. The result was a common basis for leadership to compare value, feasibility and readiness—and discuss where to invest, test or pause.</p>
<details class="evidence-deep-dive" data-evidence-case="ai-portfolio-decisions"><summary data-hq-event="impact_case_portfolio_toggle">How decisions were structured</summary><div class="evidence-deep-dive-body">
<p><strong>Decision structure.</strong> I brought expected business value, feasibility, data readiness, risk, reuse potential, required resources and accountable owners into a consistent comparison. That made the trade-offs visible in one leadership discussion.</p>
<p><strong>My leadership role.</strong> I owned portfolio consolidation and the assessment approach, giving decision owners a structured way to evaluate competing AI opportunities. Funding and execution decisions remained with the relevant business owners.</p>
<p class="evidence-illustration"><strong>Illustrative decision example:</strong> An attractive use case without a data owner or a team ready to receive it should complete that groundwork before being considered for scale.</p>
</div></details></article>
<article class="card" id="ai-adoption-learning"><span class="org">03 · AI literacy and adoption</span><h3>Teaching AI through everyday work.</h3><p>I delivered 100+ AI learning sessions across enterprise roles and developed practical prompt-engineering materials. The sessions helped make AI understandable and usable in the context of real business tasks, with an emphasis on sound judgment as well as capability.</p>
<details class="evidence-deep-dive" data-evidence-case="ai-adoption-learning"><summary data-hq-event="impact_case_learning_toggle">What delivery demonstrated</summary><div class="evidence-deep-dive-body">
<p><strong>Mechanism.</strong> Practical examples, shared vocabulary and exercises linked AI capabilities and limitations to everyday work rather than treating tool access as adoption.</p>
<p><strong>What changed.</strong> People received a shared vocabulary, practical exercises and clearer ways to assess where AI could assist their work. Delivery was tracked through the learning sessions; longer-term behavior change would require separate measurement.</p>
</div></details></article>
<article class="card" id="operational-governance"><span class="org">04 · Operational data-platform governance</span><h3>Managing shared analytics capacity in practice.</h3><p>I helped manage shared Power BI Premium capacity through recurring workspace-request reviews, capacity monitoring and coordination with central Digital &amp; IT specialists. The work brought business purpose, resource demand and support responsibility into day-to-day platform decisions.</p>
<details class="evidence-deep-dive" data-evidence-case="operational-governance"><summary data-hq-event="impact_case_operations_toggle">What the operating controls involved</summary><div class="evidence-deep-dive-body">
<p><strong>Operating mechanism.</strong> Review a workspace's business purpose, capacity implications and support ownership; monitor shared use; coordinate decisions or escalations with the technical specialists responsible for the platform.</p>
<p><strong>My leadership role.</strong> I coordinated governance decisions and stakeholders around shared analytical resources, working with technical specialists accountable for platform engineering and operations.</p>
<p class="evidence-illustration"><strong>Illustrative request example:</strong> Before approving a new workspace, check its purpose, available headroom and who will support it over time.</p>
</div></details></article>
</div>
<section class="additional-usecases" id="additional-ai-data-usecases" aria-labelledby="additional-usecases-title" data-analytics-section="additional-ai-data-usecases">
<header class="additional-usecases-intro">
<p class="eyebrow">A broader body of work</p>
<h2 id="additional-usecases-title">The list goes well beyond four examples.</h2>
<p>Across the years, the AI and analytics use cases I have worked with have been both numerous and diverse. Some I led directly; others I helped shape through business requirements, portfolio decisions, technical collaboration or adoption planning. These are more of the areas I have contributed to across industries and at different stages of maturity.</p>
</header>
<div class="additional-usecases-grid">
<div class="additional-usecases-group">
<h3>Automotive, service &amp; aftermarket</h3>
<ul>
<li>Warranty-claim trends and recurring-failure analysis</li>
<li>Service and repair process analytics</li>
<li>Dealer and service-network performance reporting</li>
<li>Aftermarket parts demand and availability analysis</li>
<li>Customer and fleet service insights</li>
<li>Sales and commercial opportunity analytics</li>
</ul>
</div>
<div class="additional-usecases-group">
<h3>Manufacturing &amp; supply chain</h3>
<ul>
<li>Manufacturing quality and process-performance analytics</li>
<li>Demand forecasting and supply planning</li>
<li>Sales and operations planning (S&amp;OP) scenarios</li>
<li>Inventory and replenishment analytics</li>
<li>Logistics performance and delivery reliability</li>
<li>Supply-chain risks and exception monitoring</li>
</ul>
</div>
<div class="additional-usecases-group">
<h3>Enterprise AI &amp; knowledge</h3>
<ul>
<li>Enterprise knowledge search and retrieval assistants</li>
<li>Copilot use cases for commercial and support teams</li>
<li>AI-assisted document analysis and summarization</li>
<li>Multilingual business-content processing</li>
<li>AI support for repetitive business workflows</li>
<li>Agent-based process support and autonomy assessments</li>
</ul>
</div>
<div class="additional-usecases-group">
<h3>Data, insight &amp; decisions</h3>
<ul>
<li>Customer segmentation and marketing-performance analytics</li>
<li>Executive KPI and business-performance dashboards</li>
<li>Self-service analytics for business teams</li>
<li>Data-quality assessment for operational reporting</li>
<li>Workforce data ownership and stewardship</li>
<li>AI-assisted insight discovery from enterprise data</li>
</ul>
</div>
</div>
</section>
</div></section>'''
