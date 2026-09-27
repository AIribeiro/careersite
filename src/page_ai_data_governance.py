from __future__ import annotations

from site_assets import CV_URI
from site_components import nav, footer, CV_DOWNLOAD_NAME


DFM_GOVERNANCE_URL = "https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/"


def ai_data_governance() -> str:
    cv = (
        f'<a class="btn ghost" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" '
        f'data-hq-event="cv_download_governance">Download CV ↓</a>'
        if CV_URI
        else ""
    )

    return f'''{nav("ai-data-governance")}<main>
<section class="pagehero"><div class="container">
<p class="eyebrow">AI &amp; Data Governance · Executive leadership</p>
<h1>I build governance that lets enterprises scale AI with clearer accountability.</h1>
<p>My work connects business ownership, data responsibility, lifecycle decisions, risk, evidence and adoption — so governance supports enterprise AI rather than becoming a separate control structure around it.</p>
<div class="actions"><a class="btn primary" href="#governance-evidence" data-hq-event="governance_hero_evidence">See the evidence →</a><a class="btn ghost" href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_dfm">Read my governance article ↗</a>{cv}</div>
</div></section>

<section class="section white" id="governance-evidence"><div class="container">
<div class="head"><div><p class="eyebrow">Leadership evidence</p><h2>Governance experience grounded in enterprise operating work.</h2></div><p>The perspective on this page comes from building structures around AI and Data, working across business and technology environments, and studying how Responsible AI can move from principles into enterprise practice.</p></div>
<div class="grid3">
<article class="card"><span class="org">MSX International · AI &amp; Data CoE</span><h3>Portfolio, lifecycle and scale-readiness.</h3><p>I built portfolio and lifecycle structure for an emerging AI &amp; Data capability, including decision points, ownership, scale-readiness criteria, data-governance foundations and a 2026–2027 maturity roadmap.</p><div class="proof">Portfolio visibility · lifecycle stages · decision rights · stewardship foundations</div></article>
<article class="card"><span class="org">Volvo Group / Volvo Trucks</span><h3>Governance connected to real enterprise use.</h3><p>Across AI roles, I worked between business, Digital &amp; IT and specialist functions while AI initiatives moved across warranty, sales, aftermarket, legal, compliance and sustainability contexts.</p><div class="proof">Cross-functional AI · adoption · business ownership · enterprise constraints</div></article>
<article class="card"><span class="org">MSc dissertation research · Artificial Intelligence</span><h3>Responsible AI as an enterprise capability.</h3><p><em>Responsible AI Adoption in Global Enterprises: Balancing Innovation, Governance, and Trust</em> examines how large organizations can turn Responsible AI principles into operating practice across strategic, operational, technical, human and regulatory governance.</p><div class="proof"><strong>Selinus University of Science and Literature</strong><br>Risk-based governance · lifecycle controls · accountability · trust · human oversight</div></article>
</div></div></section>

<section class="section soft"><div class="container">
<div class="head"><div><p class="eyebrow">What I can own</p><h2>The governance mandate I can take responsibility for.</h2></div><p>This is where the work becomes operational: turning policy intent into decision mechanisms, ownership and evidence that business, Data, Technology and Risk teams can use.</p></div>
<div class="grid3">
<article class="card"><span class="org">Operating model</span><h3>Enterprise governance structure.</h3><p>Define roles, decision rights, federated governance patterns, CoE responsibilities and escalation so accountability is explicit without centralizing every decision.</p></article>
<article class="card"><span class="org">Portfolio &amp; lifecycle</span><h3>From intake to scale decision.</h3><p>Establish use-case intake, prioritization, risk classification, stage criteria, evidence requirements and clear scale, stop or change decisions.</p></article>
<article class="card"><span class="org">Responsible AI</span><h3>Controls proportionate to consequence.</h3><p>Translate human oversight, transparency, accountability, fairness and risk principles into practical expectations for different classes of AI use.</p></article>
<article class="card"><span class="org">Data governance for AI</span><h3>Trusted data responsibilities.</h3><p>Connect AI decisions with ownership, stewardship, quality, business definitions, lineage, access and the conditions under which data may be used.</p></article>
<article class="card"><span class="org">Executive governance</span><h3>Visibility for leadership decisions.</h3><p>Create portfolio visibility, escalation paths, risk exposure and evidence that let senior leaders decide where AI can move faster and where stronger assurance is needed.</p></article>
<article class="card"><span class="org">Adoption &amp; capability</span><h3>Governance people can actually use.</h3><p>Build role clarity, AI literacy and responsible-use patterns close enough to real workflows that governance becomes part of everyday operating behavior.</p></article>
</div></div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">The executive definition</p><h2>Know what AI may do, who owns the consequence, and what evidence supports the decision.</h2></div><p>That is the practical core. Governance should help leaders answer the difficult questions before an issue forces the organization to answer them under pressure.</p></div>
<div class="principles">
<article class="principle"><span>01 · Boundaries</span><h3>What is the system allowed to do?</h3><p>Define the business context, level of autonomy, actions that are out of scope and where human judgment remains explicit.</p></article>
<article class="principle"><span>02 · Accountability</span><h3>Who owns the outcome?</h3><p>Separate business accountability, technical ownership, data responsibility and independent risk or assurance roles. Shared work should not mean anonymous responsibility.</p></article>
<article class="principle"><span>03 · Evidence</span><h3>What must be true before use expands?</h3><p>Set proportionate evidence for data quality, performance, security, fairness, privacy, human oversight and operational readiness based on the consequence of the use case.</p></article>
<article class="principle"><span>04 · Traceability</span><h3>Can we reconstruct what happened?</h3><p>Keep enough lineage, decision records, versioning and monitoring to explain which data, system behavior and human decisions shaped an outcome.</p></article>
</div></div></section>

<section class="section navy"><div class="container">
<div class="head"><div><p class="eyebrow">Decision rights</p><h2>Good governance makes the owner of each decision visible.</h2></div><p>Cross-functional work does not remove accountability. A practical operating model distinguishes who owns business consequence, data, technical readiness, risk acceptance, scale decisions and ongoing operation.</p></div>
<div class="grid3">
<article class="card"><span class="org">Business purpose</span><h3>Business owner</h3><p>Owns the problem being solved, expected value, workflow consequence and accountability for the business outcome.</p></article>
<article class="card"><span class="org">Data use</span><h3>Data owner / steward</h3><p>Owns meaning, quality expectations, access, permitted use and the conditions under which the data can support the use case.</p></article>
<article class="card"><span class="org">Technical readiness</span><h3>Product / technology owner</h3><p>Owns system behavior, security, integration, operational readiness and the technical evidence behind release.</p></article>
<article class="card"><span class="org">Risk acceptance</span><h3>Appropriate risk authority</h3><p>Owns acceptance or escalation of residual exposure according to consequence, regulation and enterprise risk policy.</p></article>
<article class="card"><span class="org">Scale decision</span><h3>Portfolio / governance authority</h3><p>Decides whether the available evidence justifies broader deployment, further work, constrained use or stopping the initiative.</p></article>
<article class="card"><span class="org">Operational monitoring</span><h3>Named operating owner</h3><p>Owns thresholds, incidents, material-change triggers and the decision to reassess the system after deployment.</p></article>
</div>
<p class="flowcopy">The exact titles vary by organization. The important point is that responsibility does not disappear between functions.</p>
</div></section>

<section class="section paper"><div class="container">
<div class="head"><div><p class="eyebrow">What good looks like</p><h2>A small number of mechanisms, used consistently.</h2></div><p>Good governance becomes visible in daily decisions. Teams know where data comes from, which definitions are authoritative, who can approve a change, what should be logged and when an exception needs escalation.</p></div>
<div class="grid3">
<article class="card"><span class="org">Data foundation</span><h3>Trusted inputs, not mystery data.</h3><p>Approved sources, ownership, quality expectations, lineage and access rules should be clear enough that a team can defend the data used by an AI capability.</p><div class="proof">Ownership · quality · lineage · access · retention</div></article>
<article class="card"><span class="org">Decision ownership</span><h3>A named owner for the business consequence.</h3><p>The person accountable for the outcome should be identifiable even when technology, data and risk responsibilities sit with different specialists.</p><div class="proof">Decision rights · accountable owner · escalation</div></article>
<article class="card"><span class="org">Control by consequence</span><h3>More consequence means stronger proof.</h3><p>A low-impact productivity assistant and an AI-supported customer or employee decision should not carry the same control burden. Governance should be proportionate to exposure.</p><div class="proof">Risk tier · evidence · human oversight · release criteria</div></article>
<article class="card"><span class="org">Traceability</span><h3>Enough history to explain an outcome.</h3><p>Versioning, decision records, source references and logs should support review without turning every interaction into bureaucracy.</p><div class="proof">Version · source · decision record · audit trail</div></article>
<article class="card"><span class="org">Monitoring</span><h3>Govern after launch, not only before it.</h3><p>Performance, drift, exceptions, user behavior and incident signals need owners and thresholds. Approval is a point in time; governance is a lifecycle.</p><div class="proof">Monitoring · thresholds · incidents · review cadence</div></article>
<article class="card"><span class="org">Change control</span><h3>Know when the original approval no longer applies.</h3><p>A new model, new data source, wider user group or different business purpose can materially change the risk. The governance model should make those changes visible.</p><div class="proof">Material change · re-assessment · release decision</div></article>
</div></div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">Questions I bring into an AI investment or scale decision</p><h2>The conversation I want before a leadership team says “go”.</h2></div><p>These questions are deliberately plain. If they cannot be answered without specialist jargon, the governance model is probably not yet usable by the people expected to own the decision.</p></div>
<div class="prooflist">
<div class="proofitem"><strong>Purpose:</strong> What decision, recommendation or workflow is this AI changing, and what happens if it is wrong?</div>
<div class="proofitem"><strong>Data:</strong> Which sources does it depend on, who owns them, and do we know their quality, meaning and permitted use?</div>
<div class="proofitem"><strong>Accountability:</strong> Who owns the business outcome, who owns the technical behavior, and who can stop or restrict use?</div>
<div class="proofitem"><strong>Boundaries:</strong> Which actions are outside the system's authority, and where is human judgment mandatory?</div>
<div class="proofitem"><strong>Evidence:</strong> What proof is required before release or broader scale, and who accepts the remaining risk?</div>
<div class="proofitem"><strong>Traceability:</strong> Could we reconstruct why a material output occurred using the information we retain?</div>
<div class="proofitem"><strong>Monitoring:</strong> Which signals would tell us that performance, data, usage or risk has changed enough to intervene?</div>
</div></div></section>

<section class="section soft"><div class="container">
<div class="head"><div><p class="eyebrow">AI governance + data governance</p><h2>Two disciplines, one operating conversation.</h2></div><p>AI risk is often discussed as if it begins with the model. In enterprises, many failures start earlier with data ownership, semantics, access, quality or lineage. Treating AI and data governance separately can simply move the same ambiguity downstream.</p></div>
<div class="twocol">
<div><p class="eyebrow">Data governance establishes</p><h2>Whether the foundation can be trusted.</h2><div class="chips" style="margin-top:24px"><span>Data ownership</span><span>Stewardship</span><span>Quality rules</span><span>Business definitions</span><span>Lineage</span><span>Access</span><span>Privacy</span><span>Retention</span></div><p class="muted">The question is not only whether data exists. It is whether the enterprise knows what it means, who is responsible for it and under which conditions it may be used.</p></div>
<div><p class="eyebrow">AI governance establishes</p><h2>Whether the use and consequence are justified.</h2><div class="chips" style="margin-top:24px"><span>Use-case ownership</span><span>Risk classification</span><span>Human oversight</span><span>System evidence</span><span>Transparency</span><span>Monitoring</span><span>Incident response</span><span>Change control</span></div><p class="muted">The shared layer is accountability: a defensible link between the business purpose, the data, the system behavior, the decision owner and the evidence used to permit continued use.</p></div>
</div></div></section>

<section class="section navy"><div class="container">
<div class="head"><div><p class="eyebrow">From policy to operating system</p><h2>The governance model I prefer is lifecycle-based.</h2></div><p>Policies set intent. Operating governance turns that intent into repeatable decisions with explicit owners, proportionate evidence and a path for exceptions.</p></div>
<div class="flow">
<div class="step"><span>01</span><strong>Frame the business purpose and consequence</strong></div>
<div class="step"><span>02</span><strong>Classify risk and data sensitivity</strong></div>
<div class="step"><span>03</span><strong>Assign business, technical and data owners</strong></div>
<div class="step"><span>04</span><strong>Define evidence and controls for the stage</strong></div>
<div class="step"><span>05</span><strong>Make an explicit release or scale decision</strong></div>
<div class="step"><span>06</span><strong>Monitor, learn and re-assess material change</strong></div>
</div>
<p class="flowcopy">The central governance function should set the pattern, challenge where consequence warrants it and make escalation possible. It should not become the place where every ordinary decision goes to wait.</p>
</div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">Why it matters</p><h2>Most governance failures show warning signs before they become incidents.</h2></div><p>The warning signs are usually operational: unclear ownership, weak data lineage, undocumented exceptions, missing monitoring or a use case that changed faster than the control model around it.</p></div>
<div class="flow" style="border-color:var(--line)">
<div class="step" style="border-color:var(--line)"><span>01</span><strong>A useful AI capability is introduced</strong></div>
<div class="step" style="border-color:var(--line)"><span>02</span><strong>Use expands into a real decision or workflow</strong></div>
<div class="step" style="border-color:var(--line)"><span>03</span><strong>Data, behavior or context changes</strong></div>
<div class="step" style="border-color:var(--line)"><span>04</span><strong>An output creates an unexpected consequence</strong></div>
<div class="step" style="border-color:var(--line)"><span>05</span><strong>Ownership or evidence is hard to reconstruct</strong></div>
<div class="step" style="border-color:var(--line)"><span>06</span><strong>Leadership discovers the control gap late</strong></div>
</div>
<p class="muted" style="max-width:850px;margin-top:26px">The point of governance is not to predict every failure. It is to make the organization capable of seeing, owning and responding to the risks that matter before they become someone else's surprise.</p>
</div></section>

<section class="section paper"><div class="container">
<div class="head"><div><p class="eyebrow">Research &amp; external perspective</p><h2>Responsible AI as an operating capability, not a compliance sidecar.</h2></div><p>My MSc dissertation research and public writing reinforce the same operating view: enterprise AI governance is strongest when business value, accountability, evidence, human oversight and trust are designed together.</p></div>
<div class="grid3">
<article class="card"><span class="org">Strategic governance</span><h3>Direction, sponsorship and accountability.</h3><p>Executive direction, enterprise priorities and decision rights establish who owns the use of AI and where governance authority sits.</p></article>
<article class="card"><span class="org">Operational + technical governance</span><h3>Controls embedded in the lifecycle.</h3><p>Risk classification, documentation, data responsibilities, validation, monitoring and auditability need to live inside delivery rather than arrive after it.</p></article>
<article class="card"><span class="org">Human + regulatory governance</span><h3>Trust, oversight and defensibility.</h3><p>AI literacy, human accountability, adoption, regulatory obligations and enterprise risk have to work together if governance is expected to survive real operating pressure.</p></article>
</div>
<div class="actions"><a class="btn dark" href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_evidence">Read: AI Governance Is Not About Control. It Is About Scale. ↗</a><a class="btn dark" href="?page=thinking" target="_self" data-hq-event="governance_thinking">Selected thinking →</a></div>
</div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">The board view</p><h2>The signal is not “we have an AI policy.” The signal is that the enterprise can answer for its AI.</h2></div><p>For an executive team, I reduce governance health to four observable capabilities. They are simple to state and difficult to fake.</p></div>
<div class="metrics">
<div class="metric"><strong>Know</strong><p>We know where material AI is being used and for which business purpose.</p></div>
<div class="metric"><strong>Own</strong><p>We know who is accountable for the business consequence, data and technical behavior.</p></div>
<div class="metric"><strong>Explain</strong><p>We can reconstruct the evidence, rules and decisions behind a material outcome.</p></div>
<div class="metric"><strong>Respond</strong><p>We know what triggers intervention, who can act and when a use case must be reassessed.</p></div>
</div>
<div class="actions"><a class="btn dark" href="?page=governance" target="_self" data-hq-event="governance_role_lens">See the governance role lens →</a><a class="btn dark" href="?page=impact" target="_self" data-hq-event="governance_impact_final">Leadership impact →</a></div>
</div></section>

<section class="cta"><div class="container ctain"><div><h2>Building or strengthening enterprise AI governance?</h2><p>I am particularly relevant where an organization needs to connect AI strategy, Responsible AI, data governance, portfolio decisions and operating ownership without creating another layer of bureaucracy.</p></div><a class="btn ghost" href="?page=contact" target="_self" data-hq-event="contact_governance_final">Discuss an AI &amp; Data governance leadership mandate →</a></div></section>
</main>{footer()}'''
