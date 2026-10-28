from __future__ import annotations

from site_assets import AI_PANEL_URI, CV_URI, HERO_URI, LINKEDIN, WORKSHOP_URI
from site_components import nav, footer, CV_DOWNLOAD_NAME
from page_home_featured import home_featured_article
from career_facts import PROFILE_TECH_YEARS, VOLVO_AI_INITIATIVES, VOLVO_WORKFLOW_SCOPE, MSX_PUBLIC_DATES, VOLVO_CURRENT_DATES, VOLVO_SENIOR_AI_DATES, KIMBERLY_DATES


CLAES_LINKEDIN = "https://se.linkedin.com/in/claes-sandros-1a795512"
ANNA_LINKEDIN = "https://se.linkedin.com/in/annaborjesson"
KUMARA_LINKEDIN = "https://in.linkedin.com/in/kumara-datta"
JIM_LINKEDIN = "https://www.linkedin.com/in/james-edwards-7233b8152"


def home() -> str:
    return f'''{nav("home")}<main>
<section class="hero"><div class="container heroin"><div><p class="eyebrow">Enterprise AI · Data · Analytics</p><h1>Jair Ribeiro<span>Enterprise AI &amp; Data Leader</span></h1><p class="deck">My career has moved from enterprise technology into AI, Data and Analytics leadership. I’ve led cross-functional work on strategy, portfolio priorities, governance and adoption—helping teams bring AI into everyday operations and build the foundations for responsible scale.</p><p class="context">Based in Gothenburg, Sweden · International enterprise experience</p><div class="actions"><a class="btn primary" href="?page=impact" target="_self" data-hq-event="impact_home">Explore my AI leadership →</a><a class="btn text" href="?page=ai-data-governance" target="_self" data-hq-event="governance_home">AI &amp; Data Governance →</a><a class="btn text" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_home">Download CV ↓</a></div></div><div class="portrait"><img src="{HERO_URI}" alt="Jair Ribeiro contributing to an executive AI panel" loading="eager" fetchpriority="high" decoding="async"><div class="note"><span>Operating perspective</span><strong>AI becomes useful when priorities, ownership and adoption are clear enough to support better business decisions.</strong></div></div></div></section>



<section class="home-credential-strip" data-analytics-section="home-latest-credential">
  <div class="container home-credential-inner">
    <div class="home-credential-text">
      <span class="home-credential-tag">Latest achievement · October 2026</span>
      <strong>Strengthen Your Business Savvy</strong>
      <span>Harvard Business Review · Four-course specialization on Coursera</span>
    </div>
    <a href="?page=certifications" target="_self" data-hq-event="home_hbr_certifications">
      Explore my credentials <span aria-hidden="true">→</span>
    </a>
  </div>
</section>

<section class="section paper journey-section" data-analytics-section="home-choose-your-path"><div class="container">
<div class="journey-intro"><p class="eyebrow">Explore further</p><h2>If you’d like to know a little more</h2><p>I’ve shared examples of what I’ve led, the choices behind the work, and questions I keep exploring about AI and Data.</p></div>
<div class="journey-grid">
<a class="journey-card" href="?page=impact" target="_self" data-hq-event="journey_home_impact"><span class="journey-step">01 · Experience &amp; impact</span><h3>What I’ve led</h3><p>Explore leadership responsibilities, decisions and practical contributions across international enterprise settings.</p><span class="journey-link">Explore my experience →</span></a>
<a class="journey-card" href="?page=ai-data-governance" target="_self" data-hq-event="journey_home_governance"><span class="journey-step">02 · Governance &amp; adoption</span><h3>How I make AI work</h3><p>See my approach to ownership, governance and adoption — the operating choices behind responsible enterprise use.</p><span class="journey-link">Explore governance →</span></a>
<a class="journey-card" href="?page=thinking" target="_self" data-hq-event="journey_home_thinking"><span class="journey-step">03 · Articles &amp; perspectives</span><h3>How I think</h3><p>Read my perspectives on the trade-offs, risks and leadership decisions facing enterprise AI and Data teams.</p><span class="journey-link">Read my articles →</span></a>
</div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Leadership focus</p><h2>Enterprise AI and Data leadership, from strategic priorities to operating capability.</h2></div><p>The common thread is moving from ambition to clearer choices, ownership and adoption — with enough structure to scale without adding unnecessary complexity.</p></div><div class="grid3 home-focus-grid"><article class="card"><span class="org">Enterprise AI strategy &amp; scaling</span><h3>Focus the portfolio on business value.</h3><p>Connect business priorities with AI opportunities, investment choices, ownership and the operating model needed to move from isolated pilots into sustained use — including Microsoft 365 Copilot and agent initiatives where they fit the work.</p></article><article class="card"><span class="org">Data &amp; Analytics leadership</span><h3>Strengthen the foundations behind decisions.</h3><p>Bring data strategy, analytics, governance and business ownership together so information and AI can support decisions at enterprise scale.</p></article><article class="card"><span class="org">Governance &amp; operating model</span><h3>Make accountability practical.</h3><p>Clarify decision rights, lifecycle responsibilities and proportionate controls so teams can move at the right pace with clearer accountability.</p></article><figure class="home-photo home-photo--dialogue"><img src="{AI_PANEL_URI}" alt="Jair Ribeiro in a professional discussion" loading="lazy" decoding="async"><figcaption>Leadership in practice · Dialogue and shared decisions</figcaption></figure></div><div class="prooflist" style="margin-top:30px"><div class="proofitem"><strong>{PROFILE_TECH_YEARS} years</strong> — enterprise technology experience across infrastructure, cloud, consulting, Data &amp; Analytics and AI.</div><div class="proofitem"><strong>{VOLVO_AI_INITIATIVES} AI initiatives, PoCs and projects</strong> — business-requirement, product and stakeholder work across a broad Volvo AI portfolio; at Volvo Trucks, this included Microsoft 365 Copilot and agent initiatives plus AI solutions introduced across {VOLVO_WORKFLOW_SCOPE}.</div><div class="proofitem"><strong>CoE foundations and decision clarity</strong> — at MSX International, an AI opportunity inventory, portfolio decision criteria, lifecycle and RACI materials, a seven-pillar maturity baseline and 2026–2027 roadmap, and initial stewardship work created a concrete starting point for the CoE.</div></div><div class="actions"><a class="btn dark" href="?page=impact" target="_self" data-hq-event="impact_focus_home">View selected experience →</a><a class="btn dark" href="?page=ai-data-governance" target="_self" data-hq-event="governance_focus_home">Governance evidence →</a><a class="btn dark" href="?page=certifications" target="_self" data-hq-event="credentials_focus_home">Credentials &amp; verification →</a></div><p class="muted" style="margin:20px 0 0"><strong>Adoption in practice:</strong> GenAI, Copilot and agent work is treated as workflow and operating change — what changes in ownership, decisions and day-to-day use, not AI activity as an end in itself.</p></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">References</p><h2>Comments from people I worked with.</h2></div><p>Two examples from a direct manager and a senior cross-functional colleague.</p></div><div class="principles"><article class="principle"><span>Direct manager · Volvo Trucks</span><h3>Claes Sandros</h3><p><strong>Acting Head of Data and Vice President Data, Analytics &amp; AI, Volvo Trucks</strong></p><p style="font:500 18px/1.5 Georgia,serif;color:var(--ink);margin-top:20px">“What truly impressed me was his ability to combine deep analytical knowledge with strategic thinking and a collaborative mindset.”</p><div class="proof"><a href="{CLAES_LINKEDIN}" target="_blank" rel="noopener" data-hq-event="reference_claes_home">LinkedIn profile ↗</a></div></article><article class="principle"><span>Senior cross-functional colleague · Volvo Group</span><h3>Anna Börjesson Sandberg</h3><p><strong>VP, Digital Transformation, Volvo Group Trucks Technology</strong></p><p style="font:500 18px/1.5 Georgia,serif;color:var(--ink);margin-top:20px">“Jair continuously wanted to move towards the future of Data and AI and could always explain the purpose and next possible steps.”</p><div class="proof"><a href="{ANNA_LINKEDIN}" target="_blank" rel="noopener" data-hq-event="reference_anna_home">LinkedIn profile ↗</a></div></article></div></div></section>

{home_featured_article()}

<section class="cta"><div class="container ctain"><div><h2>For enterprise AI and Data mandates.</h2><p>Experience across strategy, adoption, operating models, governance and Data &amp; Analytics in international enterprise environments.</p></div><div class="actions"><a class="btn ghost" href="?page=contact" target="_self" data-hq-event="contact_home_final">Contact →</a><a class="btn ghost" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_home_final">LinkedIn ↗</a></div></div></section>
</main>{footer()}'''
