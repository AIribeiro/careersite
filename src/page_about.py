from __future__ import annotations

from site_assets import CV_URI, ABOUT_BW_URI
from site_components import nav, footer, opportunity, CV_DOWNLOAD_NAME


def about() -> str:
    cv = f'<a class="btn dark" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_about">Download full CV ↓</a>' if CV_URI else ""
    return f'''{nav("about")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">About</p><h1>A career that moved from enterprise technology foundations into business-facing AI, Data and Analytics leadership.</h1><p>20+ years in enterprise technology, including 8+ years in AI, data and analytics leadership. The recurring work has been helping organizations connect ambition with the conditions required to make it useful: priorities, responsibility, data, governance, everyday use and value.</p></div></section>

<section class="section soft"><div class="container leadership-identity"><div class="identity-copy"><p class="eyebrow">Leadership identity</p><h2>I lead where business, AI and technology meet.</h2><p>AI is not a standalone technical discipline in my work. I connect strategic intent with the data, technology, governance and operating conditions required to make it useful at enterprise scale.</p><p>That means moving from opportunity to adoption, from experimentation to repeatable capability, and from AI activity to measurable business value.</p><div class="chips identity-chips"><span>Business &amp; strategic leadership</span><span>AI &amp; Data leadership</span><span>Technology &amp; architecture</span></div></div><figure class="leadership-visual"><svg viewBox="0 0 1200 1100" role="img" aria-labelledby="leadership-title leadership-desc" xmlns="http://www.w3.org/2000/svg">
<title id="leadership-title">Jair Ribeiro — enterprise AI and data leadership model</title>
<desc id="leadership-desc">Business and strategic leadership, AI and data leadership, and technology and architecture overlap in an enterprise AI and data leader focused on responsible adoption and business value.</desc>
<defs>
  <linearGradient id="circleA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#083e79"/><stop offset="1" stop-color="#0b69c7"/></linearGradient>
  <linearGradient id="circleB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#067be1"/><stop offset="1" stop-color="#2da7ff"/></linearGradient>
  <linearGradient id="circleC" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#074480"/><stop offset="1" stop-color="#0d6dc4"/></linearGradient>
  <style>
    .brand{{font:700 20px Arial,sans-serif;letter-spacing:7px;fill:#0b2c59}}
    .micro{{font:600 13px Arial,sans-serif;letter-spacing:3px;fill:#506781}}
    .title{{font:700 48px Arial,sans-serif;fill:#071d43}}
    .accent{{fill:#1689f4}}
    .sub{{font:400 20px Arial,sans-serif;fill:#30465f}}
    .circle-title{{font:700 25px Arial,sans-serif;fill:white}}
    .circle-copy{{font:400 17px Arial,sans-serif;fill:#eaf6ff}}
    .circle-tag{{font:600 15px Arial,sans-serif;letter-spacing:.6px;fill:white}}
    .center-title{{font:700 34px Arial,sans-serif;fill:#071d43}}
    .center-copy{{font:700 12px Arial,sans-serif;letter-spacing:1.2px;fill:#263a53}}
    .side-kicker{{font:700 13px Arial,sans-serif;letter-spacing:3px;fill:#405777}}
    .side-head{{font:700 25px Arial,sans-serif;fill:#071d43}}
    .side-copy{{font:400 16px Arial,sans-serif;fill:#334760}}
    .side-label{{font:700 16px Arial,sans-serif;fill:#071d43}}
    .tagline{{font:700 22px Arial,sans-serif;letter-spacing:2px;fill:#071d43}}
  </style>
</defs>

<rect width="1200" height="1100" fill="#fbfdff"/>
<line x1="55" y1="36" x2="55" y2="90" stroke="#1689f4" stroke-width="4"/>
<text x="82" y="52" class="brand">JAIR RIBEIRO</text>
<text x="82" y="78" class="micro">AI | DATA | PEOPLE | IMPACT</text>

<text x="55" y="145" class="title">Where business, AI and people</text>
<text x="55" y="198" class="title">create <tspan class="accent">real impact</tspan></text>
<text x="55" y="235" class="sub">Strategy. Technology. People. Responsible AI that works in the enterprise.</text>

<!-- Venn -->
<circle cx="300" cy="500" r="238" fill="url(#circleA)" opacity=".96"/>
<circle cx="565" cy="500" r="238" fill="url(#circleB)" opacity=".92"/>
<circle cx="432" cy="710" r="238" fill="url(#circleC)" opacity=".95"/>

<!-- intersection highlights -->
<path d="M432 339c64 41 106 104 106 176 0 77-48 146-122 184-74-38-122-107-122-184 0-72 42-135 106-176a233 233 0 0 1 32 0z" fill="#78c8ff" opacity=".55"/>
<path d="M414 568c67-23 142-15 199 31-7 90-63 163-143 195-68-21-122-74-146-142 19-37 50-66 90-84z" fill="#42a8ff" opacity=".45"/>
<path d="M449 568c-67-23-142-15-199 31 7 90 63 163 143 195 68-21 122-74 146-142-19-37-50-66-90-84z" fill="#42a8ff" opacity=".37"/>

<!-- business -->
<text x="178" y="418" class="circle-title">Business &amp; strategic</text>
<text x="215" y="450" class="circle-title">leadership</text>
<text x="145" y="486" class="circle-copy">Strategy execution, value creation,</text>
<text x="150" y="512" class="circle-copy">stakeholder leadership and change.</text>
<line x1="170" y1="545" x2="230" y2="545" stroke="#d8efff" stroke-width="2"/>
<text x="145" y="578" class="circle-tag">STRATEGY</text>
<text x="145" y="604" class="circle-tag">TRANSFORMATION</text>
<text x="145" y="630" class="circle-tag">STAKEHOLDER LEADERSHIP</text>
<text x="145" y="656" class="circle-tag">VALUE &amp; ROI</text>

<!-- ai -->
<text x="548" y="430" class="circle-title">AI &amp; Data leadership</text>
<text x="535" y="470" class="circle-copy">From strategy to adoption, with</text>
<text x="532" y="496" class="circle-copy">responsibility and scale in mind.</text>
<line x1="575" y1="530" x2="635" y2="530" stroke="#e9f7ff" stroke-width="2"/>
<text x="552" y="563" class="circle-tag">AI STRATEGY</text>
<text x="552" y="589" class="circle-tag">GENERATIVE AI / LLM</text>
<text x="552" y="615" class="circle-tag">AI GOVERNANCE</text>
<text x="552" y="641" class="circle-tag">RESPONSIBLE AI</text>
<text x="552" y="667" class="circle-tag">ADOPTION &amp; SCALE</text>

<!-- technology -->
<text x="365" y="770" class="circle-title">Technology &amp; architecture</text>
<text x="300" y="807" class="circle-copy">Data, platforms and enterprise technology</text>
<text x="320" y="833" class="circle-copy">as foundations for scalable solutions.</text>
<line x1="400" y1="858" x2="460" y2="858" stroke="#e9f7ff" stroke-width="2"/>
<text x="340" y="888" class="circle-tag">DATA MANAGEMENT</text>
<text x="340" y="914" class="circle-tag">ANALYTICS &amp; INSIGHTS</text>
<text x="340" y="940" class="circle-tag">ENTERPRISE ARCHITECTURE</text>
<text x="340" y="966" class="circle-tag">SECURITY · PLATFORMS · CLOUD</text>

<!-- center -->
<ellipse cx="432" cy="606" rx="112" ry="126" fill="#dff2ff" opacity=".92"/>
<text x="381" y="578" class="center-title">AI &amp; Data</text>
<text x="389" y="616" class="center-title">Leader</text>
<line x1="400" y1="636" x2="465" y2="636" stroke="#1689f4" stroke-width="2"/>
<text x="406" y="661" class="center-copy">PEOPLE</text>
<text x="411" y="681" class="center-copy">TRUST</text>
<text x="411" y="701" class="center-copy">VALUE</text>

<!-- side panel -->
<line x1="825" y1="275" x2="825" y2="955" stroke="#c9d9e8" stroke-width="2"/>
<text x="860" y="320" class="side-kicker">MY PURPOSE</text>
<text x="860" y="358" class="side-head">Turn AI potential into</text>
<text x="860" y="388" class="side-head">responsible business value.</text>
<text x="860" y="420" class="side-copy">For people, operations and society.</text>

<text x="860" y="488" class="side-kicker">WHAT I BRING</text>

<circle cx="885" cy="535" r="20" fill="none" stroke="#1689f4" stroke-width="3"/>
<path d="M875 535l7 8 14-18" fill="none" stroke="#071d43" stroke-width="3" stroke-linecap="round"/>
<text x="925" y="530" class="side-label">Strategy to execution</text>
<text x="925" y="554" class="side-copy">From ambition to measurable outcomes.</text>

<circle cx="885" cy="615" r="20" fill="none" stroke="#1689f4" stroke-width="3"/>
<path d="M872 620c8-17 22-17 30 0M879 602a8 8 0 1 0 12 0" fill="none" stroke="#071d43" stroke-width="2.5"/>
<text x="925" y="610" class="side-label">People-centred leadership</text>
<text x="925" y="634" class="side-copy">Capability, literacy and adoption.</text>

<circle cx="885" cy="695" r="20" fill="none" stroke="#1689f4" stroke-width="3"/>
<path d="M885 680l13 6v10c0 10-7 16-13 20-6-4-13-10-13-20v-10z" fill="none" stroke="#071d43" stroke-width="2.5"/>
<text x="925" y="690" class="side-label">Responsible AI</text>
<text x="925" y="714" class="side-copy">Trust, governance and control by design.</text>

<circle cx="885" cy="775" r="20" fill="none" stroke="#1689f4" stroke-width="3"/>
<path d="M868 775h34M885 758v34M873 763c8 8 8 16 0 24M897 763c-8 8-8 16 0 24" fill="none" stroke="#071d43" stroke-width="2"/>
<text x="925" y="770" class="side-label">Global, cross-functional work</text>
<text x="925" y="794" class="side-copy">Business, data, technology and governance.</text>

<text x="860" y="865" class="side-kicker">THE OUTCOME</text>
<text x="860" y="904" class="side-head">More capable organizations.</text>
<text x="860" y="934" class="side-head">More empowered people.</text>
<line x1="860" y1="958" x2="965" y2="958" stroke="#1689f4" stroke-width="4"/>

<!-- bottom -->
<line x1="55" y1="1010" x2="1145" y2="1010" stroke="#d5e1ec"/>
<text x="55" y="1052" class="tagline">AI CAN DO A LOT. <tspan class="accent">PEOPLE MAKE IT MATTER.</tspan></text>
<text x="930" y="1052" class="micro">JAIR RIBEIRO</text>
</svg></figure></div></section>

<section class="section white"><div class="container editorial-split"><div><p class="eyebrow">Professional arc</p><h2>The technology changed. The leadership questions became clearer.</h2><p class="muted">My early career was grounded in enterprise systems, infrastructure, cloud, consulting and client-facing technology work. That period taught me something I still rely on: a technical choice always carries operating, cost, risk and stakeholder consequences once it leaves the lab.</p><p class="muted">From 2017 onward, AI moved closer to the center of my work. IBM Watson solution design led into business-facing AI roles at Volvo Group, then EMEA AI strategy at Kimberly-Clark, AI and analytics adoption at Volvo Trucks, and most recently the foundations of an AI &amp; Data Center of Excellence at MSX International.</p><p class="muted">What kept repeating was not a specific model or platform. It was the gap between technical possibility and enterprise use. I have seen promising initiatives slow down because the problem was poorly framed, responsibility was implicit, data was not trusted, governance arrived too late, or the people expected to use the capability were never brought into the decision.</p><p class="muted">That is why my leadership perspective is increasingly about the system around AI. I am interested in how organizations make better choices about where to focus, what has to be true before scaling, where each decision belongs and how technical possibility connects to everyday work.</p></div><div class="editorial-photo portrait"><img src="{ABOUT_BW_URI}" alt="Jair Ribeiro portrait" loading="lazy" decoding="async"></div></div><div class="container"><div class="timeline"><div class="trow"><b>2004–2017</b><div><strong>Enterprise technology foundations</strong><span>Infrastructure, enterprise systems, consulting, cloud and client-facing technology work across Italy, Brazil and Poland.</span></div></div><div class="trow"><b>2017–2021</b><div><strong>From technology delivery to AI business translation</strong><span>IBM Watson solution design followed by Volvo Group AI CoE work spanning 100+ AI initiatives, PoCs and projects across regions, with business requirements, product management and stakeholder work at the center.</span></div></div><div class="trow"><b>2021–2025</b><div><strong>AI strategy, adoption and analytics leadership</strong><span>EMEA AI value discovery at Kimberly-Clark, reporting directly to the CDAO, followed by Volvo Trucks adoption work where AI solutions and agents were introduced across warranty, sales and aftermarket workflows.</span></div></div><div class="trow"><b>2025–2026</b><div><strong>Building the structures around AI &amp; Data</strong><span>CoE portfolio and lifecycle governance, a 2026–2027 maturity roadmap, data-governance foundations and scale-readiness criteria that gave AI initiatives a clearer path beyond isolated PoCs at MSX International.</span></div></div></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">How I lead</p><h2>Collaborative in understanding. Clear when decisions need to be made.</h2></div><p>Business, technology, governance and users often look at the same AI initiative through different lenses: opportunity, dependencies, risk and disruption to the work. Much of my role has been making those perspectives visible early enough for the organization to decide with fewer hidden assumptions.</p></div><div class="principles"><div class="principle"><span>01</span><h3>Make complexity understandable</h3><p>I separate what is known, what is assumed and what still needs to be proven. That gives teams enough structure to decide without turning uncertainty into bureaucracy.</p></div><div class="principle"><span>02</span><h3>Work across boundaries</h3><p>Most AI problems sit between business, data, technology, governance and people. I make the dependencies visible and translate the consequences of one discipline’s choices for the others.</p></div><div class="principle"><span>03</span><h3>Make disagreement useful</h3><p>I surface disagreement early, explain the trade-off and make a recommendation without pretending uncertainty has disappeared. Useful challenge is more valuable than artificial certainty.</p></div><div class="principle"><span>04</span><h3>Build capability, not dependency</h3><p>I prefer reusable patterns, clear decision rights and stronger internal judgment over a central team that has to approve or deliver everything. Scale improves when the organization learns to act for itself.</p></div></div></div></section>

<section class="section navy"><div class="container"><div class="head"><div><p class="eyebrow">Enterprise AI perspective</p><h2>AI scales as a system, not as a model.</h2></div><p>That view comes from seeing the same pattern across different organizations: technically promising work becomes useful only when priorities, responsibility, data, governance and adoption line up well enough for people to act on it.</p></div><p class="flowcopy">For me, this is less a framework than a way of reading the organization around the technology: where the real constraint sits, which decision is still implicit, and what has to change before the next step is credible.</p></div></section>

<section class="section white"><div class="container twocol"><div><p class="eyebrow">Technical &amp; enterprise fluency</p><h2>Technical judgment in service of leadership decisions.</h2><p class="muted">My technical background helps me engage engineers, architects and data specialists, understand the consequences of architecture and data choices, and challenge trade-offs around scalability, security, cost, governance and operational readiness. Specialist depth should remain with the specialists responsible for those decisions.</p><p class="muted">The value I add is knowing which technical questions matter for the business decision, where a technical constraint changes the answer, and when specialist depth should lead.</p></div><div><div class="chips"><span>Enterprise AI architecture</span><span>GenAI</span><span>Agentic AI</span><span>Analytics</span><span>Data platforms</span><span>Data quality</span><span>Stewardship</span><span>Cloud</span><span>MLOps principles</span><span>Security</span><span>AI risk</span><span>Governance</span><span>Scalability</span><span>Vendor evaluation</span><span>Cost / accuracy trade-offs</span><span>Operational readiness</span></div><div class="grid3" style="margin-top:24px"><article class="card"><span class="org">Architecture</span><h3>Can this survive the enterprise?</h3><p>I look beyond model quality to integration, scalability, security, maintainability and the cost of turning a promising prototype into something the organization can operate.</p></article><article class="card"><span class="org">Data &amp; trust</span><h3>Is the foundation credible?</h3><p>Data access, quality, semantics, stewardship and lineage shape both technical performance and organizational trust. Weak foundations usually reappear later as adoption or governance problems.</p></article><article class="card"><span class="org">Risk &amp; economics</span><h3>Is the trade-off justified?</h3><p>Accuracy, autonomy, cost, control and user value move together. The useful question is what level of capability is justified for this decision, user and risk.</p></article></div></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Credentials &amp; perspective</p><h2>Formal study matters when it sharpens practical judgment.</h2></div><p>My academic work complements rather than replaces operating experience. The focus has been on how AI can be adopted responsibly inside real organizations, where governance, trust, incentives and business pressure exist at the same time.</p></div><div class="grid3"><div class="card"><span class="org">Education</span><h3>MSc, Artificial Intelligence</h3><p>Research focused on Responsible AI adoption in global enterprises and the tension between innovation, governance and trust.</p></div><div class="card"><span class="org">Research lens</span><h3>Responsible adoption, not compliance-only governance</h3><p>I am interested in governance as part of how the organization works: how responsibility, proof, risk and escalation can increase trust and decision quality without disconnecting control from the work.</p></div><div class="card"><span class="org">Recognition</span><h3>Thinkers360 Top 50</h3><p>Global Thought Leaders &amp; Influencers on Emerging Technology, 2023.</p></div></div><div class="actions"><a class="btn dark" href="?page=certifications" target="_self" data-hq-event="about_certifications">Explore credentials &amp; certifications →</a><a class="btn dark" href="?page=presence" target="_self">Selected speaking &amp; publications →</a></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Languages &amp; working context</p><h2>International experience, with Sweden as the professional base.</h2></div><p>Based in Gothenburg, with experience across Sweden, Poland, Italy and Brazil and work in global organizations. That background has made me comfortable adapting how I communicate and lead without changing the standard of reasoning or accountability behind the decision.</p></div><div class="chips"><span>Portuguese — native/bilingual</span><span>Italian — native/bilingual</span><span>English — full professional</span><span>Spanish — professional</span><span>Polish — limited working</span><span>Swedish — elementary</span></div><div class="actions">{cv}</div></div></section>
{opportunity()}</main>{footer()}'''
