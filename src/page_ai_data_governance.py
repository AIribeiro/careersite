from __future__ import annotations

from site_assets import CV_URI
from site_components import nav, footer, opportunity, CV_DOWNLOAD_NAME


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
<p class="eyebrow">AI &amp; Data Governance · Executive perspective</p>
<h1>Governance that helps AI move with accountability.</h1>
<p>AI governance should not be a committee, a policy document or a final approval gate. It should make ownership, boundaries, evidence, data responsibility and escalation clear enough for an enterprise to use AI with confidence.</p>
<div class="actions"><a class="btn primary" href="?page=impact" target="_self" data-hq-event="impact_governance_hero">See leadership evidence →</a><a class="btn ghost" href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_dfm">Read my governance article ↗</a>{cv}</div>
</div></section>

<section class="section white"><div class="container">
<div class="head"><div><p class="eyebrow">The executive definition</p><h2>Know what AI may do, who owns the consequence, and what evidence supports the decision.</h2></div><p>That is the practical core. Governance should help leaders answer the difficult questions before an issue forces the organization to answer them under pressure.</p></div>
<div class="principles">
<article class="principle"><span>01 · Boundaries</span><h3>What is the system allowed to do?</h3><p>Define the business context, level of autonomy, actions that are out of scope and where human judgment remains explicit.</p></article>
<article class="principle"><span>02 · Accountability</span><h3>Who owns the outcome?</h3><p>Separate business accountability, technical ownership, data responsibility and independent risk or assurance roles. Shared work should not mean anonymous responsibility.</p></article>
<article class="principle"><span>03 · Evidence</span><h3>What must be true before use expands?</h3><p>Set proportionate evidence for data quality, performance, security, fairness, privacy, human oversight and operational readiness based on the consequence of the use case.</p></article>
<article class="principle"><span>04 · Traceability</span><h3>Can we reconstruct what happened?</h3><p>Keep enough lineage, decision records, versioning and monitoring to explain which data, system behavior and human decisions shaped an outcome.</p></article>
</div></div></section>

<section class="section navy"><div class="container">
<div class="head"><div><p class="eyebrow">Why it matters</p><h2>Most governance failures show warning signs before they become incidents.</h2></div><p>The warning signs are usually operational: unclear ownership, weak data lineage, undocumented exceptions, missing monitoring or a use case that changed faster than the control model around it.</p></div>
<div class="flow">
<div class="step"><span>01</span><strong>A useful AI capability is introduced</strong></div>
<div class="step"><span>02</span><strong>Use expands into a real decision or workflow</strong></div>
<div class="step"><span>03</span><strong>Data, behavior or context changes</strong></div>
<div class="step"><span>04</span><strong>An output creates an unexpected consequence</strong></div>
<div class="step"><span>05</span><strong>Ownership or evidence is hard to reconstruct</strong></div>
<div class="step"><span>06</span><strong>Leadership discovers the control gap late</strong></div>
</div>
<p class="flowcopy">The point of governance is not to predict every failure. It is to make the organization capable of seeing, owning and responding to the risks that matter before they become someone else's surprise.</p>
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
<div class="head"><div><p class="eyebrow">Questions I use</p><h2>The conversation I want before a leadership team says “go”.</h2></div><p>These questions are deliberately plain. If they cannot be answered without specialist jargon, the governance model is probably not yet usable by the people expected to own the decision.</p></div>
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
<div class="head"><div><p class="eyebrow">Evidence behind the perspective</p><h2>This view comes from operating work, not only governance theory.</h2></div><p>My governance perspective has been shaped by AI portfolio work, enterprise adoption, data-governance foundations, operating-model design and formal research into responsible AI adoption.</p></div>
<div class="grid3">
<article class="card"><span class="org">MSX International · AI &amp; Data CoE</span><h3>Lifecycle, ownership and scale-readiness.</h3><p>I built portfolio and lifecycle structure for an emerging AI &amp; Data capability, including decision points, ownership, scale-readiness criteria and data-governance foundations within a 2026–2027 maturity roadmap.</p><div class="proof">Portfolio visibility · lifecycle stages · decision rights · stewardship foundations</div></article>
<article class="card"><span class="org">Volvo Group / Volvo Trucks</span><h3>Governance connected to real enterprise use.</h3><p>Across AI roles, I worked between business, Digital &amp; IT and specialist functions while AI initiatives moved across warranty, sales, aftermarket, legal, compliance and sustainability contexts. That reinforced the need to connect responsible use with the workflow and the people accountable for it.</p><div class="proof">Cross-functional AI · adoption · business ownership · enterprise constraints</div></article>
<article class="card"><span class="org">Research &amp; external perspective</span><h3>Responsible adoption as an enterprise capability.</h3><p>My MSc dissertation research in Artificial Intelligence, <em>Responsible AI Adoption in Global Enterprises: Balancing Innovation, Governance, and Trust</em>, examines how large organizations can turn Responsible AI principles into operating practice. The work connects risk-based governance, lifecycle controls, accountability, traceability, human oversight, AI literacy and trust with the business conditions required to scale AI.</p><div class="proof"><strong>MSc dissertation research · Artificial Intelligence · Selinus University of Science and Literature</strong><br><a href="{DFM_GOVERNANCE_URL}" target="_blank" rel="noopener" data-hq-event="article_governance_evidence">Digital First Magazine · “AI Governance Is Not About Control. It Is About Scale.” ↗</a></div></article>
</div></div></section>

<section class="section paper"><div class="container">
<div class="head"><div><p class="eyebrow">The board view</p><h2>The signal is not “we have an AI policy.” The signal is that the enterprise can answer for its AI.</h2></div><p>For an executive team, I would reduce governance health to four observable capabilities. They are simple to state and difficult to fake.</p></div>
<div class="metrics">
<div class="metric"><strong>Know</strong><p>We know where material AI is being used and for which business purpose.</p></div>
<div class="metric"><strong>Own</strong><p>We know who is accountable for the business consequence, data and technical behavior.</p></div>
<div class="metric"><strong>Explain</strong><p>We can reconstruct the evidence, rules and decisions behind a material outcome.</p></div>
<div class="metric"><strong>Respond</strong><p>We know what triggers intervention, who can act and when a use case must be reassessed.</p></div>
</div>
<div class="actions"><a class="btn dark" href="?page=governance" target="_self" data-hq-event="governance_role_lens">See the governance role lens →</a><a class="btn dark" href="?page=thinking" target="_self" data-hq-event="governance_thinking">Read selected thinking →</a></div>
</div></section>

{opportunity()}</main>{footer()}'''
