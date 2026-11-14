"""Public, evidence-led service page for the individually approved AI Scorecard.

This describes the method and its pro-bono access criteria. The public page
never renders a client's portfolio, private data, or entitlement details.
"""
from __future__ import annotations

from page_public_services import SERVICES_CSS
from site_components import nav, footer


SCORECARD_CSS = """
<style>
.site .scorecard-page{color:#172b40;background:#f7f5f0;overflow-wrap:break-word}
.site .scorecard-page *{box-sizing:border-box}
.site .scorecard-page .container{max-width:1180px}
.site .sc-hero{background:#0e2237;color:#f9f7f3;padding:clamp(55px,8vw,100px) 0}
.site .sc-kicker{display:block;color:#c99070;text-transform:uppercase;font:800 11px/1.5 Arial,sans-serif;letter-spacing:.14em}
.site .sc-hero .sc-kicker,.site .sc-dark .sc-kicker{color:#e5b58f}
.site .sc-hero h1{font:500 clamp(40px,6vw,76px)/1.09 Georgia,serif;max-width:900px;letter-spacing:-.035em;margin:20px 0 24px;color:#f9f7f3}
.site .sc-hero p{font:17px/1.7 Arial,sans-serif;max-width:810px;color:#cbd7e3;margin:0 0 16px}
.site .sc-hero .sc-lead{font-size:clamp(19px,2.1vw,23px);line-height:1.58;color:#f4eee8}
.site .sc-actions{display:flex;gap:13px;flex-wrap:wrap;margin-top:30px;align-items:center}
.site .sc-btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 21px;border:1px solid #e1ac87;text-decoration:none!important;background:#dba77e;color:#142438!important;font:700 13px/1.4 Arial,sans-serif;text-align:center}
.site .sc-btn.alt{background:transparent;color:#f7f7f5!important;border-color:#96a8b8}
.site .sc-btn.light{background:transparent;color:#24394c!important;border-color:#a8b4bc}
.site .sc-btn:focus-visible{outline:2px solid #de966d;outline-offset:4px}
.site .sc-wrap{width:100%;max-width:1120px;margin:0 auto;padding:72px 28px;min-width:0}
.site .sc-wrap h2{font:500 clamp(31px,4vw,51px)/1.17 Georgia,serif;margin:10px 0 22px;color:#172e46;letter-spacing:-.018em}
.site .sc-wrap h3{font:500 24px/1.26 Georgia,serif;margin:0 0 13px;color:#18304a}
.site .sc-wrap p,.site .sc-wrap li{font:15px/1.77 Arial,sans-serif;color:#4b5d70}
.site .sc-wrap>p{max-width:900px}
.site .sc-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:30px}
.site .sc-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:24px}
.site .sc-card{padding:28px 27px;background:#fff;border:1px solid #e2ddd5;min-width:0}
.site .sc-card h3{margin-top:12px}
.site .sc-card p{margin:0}
.site .sc-num{font:800 11px/1.5 Arial,sans-serif;color:#ac704b;letter-spacing:.1em;text-transform:uppercase}
.site .sc-rule{height:1px;background:#d8d5ce;border:0;margin:34px 0}
.site .sc-narrative{max-width:860px}
.site .sc-narrative strong{color:#172f49}
.site .sc-boundary{border-left:4px solid #c58c64;background:#fff9ef;padding:23px 28px;margin-top:28px}
.site .sc-boundary p{margin:0}
.site .sc-dark{background:#182a3d;color:#f8f7f3}
.site .sc-dark h2,.site .sc-dark h3{color:#fff}
.site .sc-dark p,.site .sc-dark li{color:#ccd7e0}
.site .sc-dark .sc-card{background:#233a50;border-color:#496074}
.site .sc-dark .sc-card h3{color:#f9f7f3}
.site .sc-dark .sc-card p{color:#d4dfe7}
.site .sc-dark .sc-num{color:#e5b58f}
.site .sc-list{padding-left:23px;max-width:900px}
.site .sc-list li{padding-left:5px;margin:0 0 17px}
.site .sc-list li strong{color:#213b53}
.site .sc-micro{font:12px/1.7 Arial,sans-serif!important;color:#6a7785!important}
.site .sc-table-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #dcd9d1;background:#fff;margin:25px 0 12px}
.site .sc-example-table{width:100%;border-collapse:collapse;table-layout:fixed;min-width:650px}
.site .sc-example-table th{background:#e8edf0;color:#183148;text-align:left;font:700 12px/1.4 Arial,sans-serif;letter-spacing:.02em;padding:15px 16px}
.site .sc-example-table td{padding:16px;border-top:1px solid #e0e4e5;vertical-align:top;font:14px/1.55 Arial,sans-serif;color:#4b5d70}
.site .sc-example-table td:first-child{font-weight:700;color:#203a50}
.site .sc-example-table th:nth-child(1){width:29%}
.site .sc-example-table th:nth-child(2){width:36%}
.site .sc-example-table th:nth-child(3){width:35%}
.site .sc-note{font:12px/1.65 Arial,sans-serif!important;color:#6b7885!important}
.site .sc-pullquote{border-left:3px solid #d7a27d;padding:7px 0 7px 25px;margin:28px 0 10px;font:italic 500 clamp(21px,2.6vw,29px)/1.5 Georgia,serif;color:#213a50;max-width:900px}
.site .sc-dark .sc-pullquote{color:#f0e6dc}
.site .sc-process{counter-reset:step;list-style:none;padding:0;max-width:860px;margin:30px 0 0}
.site .sc-process li{counter-increment:step;position:relative;padding:0 0 26px 66px;border-left:1px solid #d7d8d8;margin-left:17px}
.site .sc-process li:last-child{border-left:0}
.site .sc-process li:before{content:counter(step,decimal-leading-zero);position:absolute;left:-18px;top:0;width:37px;height:37px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#233d54;color:#fff;font:700 12px Arial,sans-serif}
.site .sc-process li strong{display:block;color:#1b344c;margin-bottom:5px}
.site .sc-process li p{margin:0}
.site .sc-final-actions{display:flex;flex-wrap:wrap;align-items:center;gap:13px;margin-top:25px}
.site .sc-final-actions .sc-btn{flex:0 1 auto}
@media(max-width:980px){
 .site .sc-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
 .site .sc-wrap{padding:60px 28px}
 .site .sc-hero h1{font-size:clamp(40px,6.4vw,61px)}
}
@media(max-width:760px){
 .site .scorecard-page{max-width:100%;overflow-x:clip}
 .site .scorecard-page .container{width:calc(100% - 36px);max-width:100%;margin:0 auto}
 .site .sc-grid,.site .sc-grid-2{grid-template-columns:minmax(0,1fr)}
 .site .sc-wrap{padding:49px 20px;max-width:100%}
 .site .sc-hero{padding:62px 0}
 .site .sc-hero h1{font-size:clamp(36px,8.8vw,49px);letter-spacing:-.03em}
 .site .sc-hero p{font-size:16px}
 .site .sc-actions,.site .sc-final-actions{flex-direction:column;align-items:stretch}
 .site .sc-actions .sc-btn,.site .sc-final-actions .sc-btn{width:100%;min-width:0;white-space:normal}
 .site .sc-card{padding:24px}
 .site .sc-wrap h2{font-size:clamp(30px,7.9vw,42px)}
 .site .sc-boundary{padding:20px 22px}
 .site .sc-example-table{min-width:650px}
}
</style>
"""


def advisory_scorecard() -> str:
    """Public explanation of the on-demand, individually approved Scorecard."""
    return f"""{SERVICES_CSS}{SCORECARD_CSS}{nav('advisory')}
<main class="scorecard-page">
<section class="sc-hero"><div class="container">
 <div class="sc-kicker">Executive Advisory / On-demand decision service / Selective pro-bono access</div>
 <h1>AI Portfolio Prioritization Scorecard.</h1>
 <p class="sc-lead">Which AI initiatives should your organization fund, test, pause or stop—and what evidence supports that decision?</p>
 <p>The Scorecard is a structured working environment for reviewing competing AI opportunities against business value, delivery capacity, operational readiness and control requirements. Its purpose is to help leadership make explicit choices, not simply produce a ranked list.</p>
 <div class="sc-actions">
  <a class="sc-btn" href="?page=advisory-access&amp;view=scorecard" target="_self" data-hq-event="scorecard_apply">Request access through Advisory →</a>
  <a class="sc-btn alt" href="#sc-how-it-works" data-hq-event="scorecard_method">How the service works</a>
 </div>
 <p style="margin-top:20px;font-size:13px">Free for clients individually approved within a selected pro-bono Advisory engagement. Registration alone does not provide access.</p>
</div></section>

<section class="sc-wrap" aria-labelledby="sc-problem">
 <span class="sc-kicker">The executive problem</span>
 <h2 id="sc-problem">A growing pipeline of ideas is not an investment strategy.</h2>
 <p>It is relatively easy to generate AI use cases. It is harder to compare them fairly when they draw on the same specialists, data, budget and leadership attention. A useful idea can be the wrong priority; a technically promising pilot may lack an accountable process owner; and a high-value use case may require controls that are not yet in place.</p>
 <p>In a portfolio review, the questions are practical: <strong>What is the business outcome? What would we do without AI? What evidence supports the benefit? Which work or investment must be displaced? Who owns the result after launch?</strong></p>
 <div class="sc-grid">
  <article class="sc-card"><span class="sc-num">01 / Compare consistently</span><h3>Make trade-offs visible</h3><p>Use the same decision criteria across proposals instead of relying on presentation quality, enthusiasm or who sponsors an initiative.</p></article>
  <article class="sc-card"><span class="sc-num">02 / Test constraints</span><h3>Consider the whole portfolio</h3><p>Review specialist capacity, one-time investment, ongoing costs and competing priorities before promising delivery dates or returns.</p></article>
  <article class="sc-card"><span class="sc-num">03 / Document judgment</span><h3>Make decisions accountable</h3><p>Record which initiatives advance, what must be proved first, which controls remain open, and who owns the next decision.</p></article>
 </div>
</section>

<section class="sc-dark"><div class="sc-wrap" aria-labelledby="sc-credibility">
 <span class="sc-kicker">The experience behind the method</span>
 <h2 id="sc-credibility">Built from the realities of enterprise AI, not from a generic scoring template.</h2>
 <p>Over years working across enterprise AI, data and business operations, I have been involved in reviewing competing AI initiatives, defining governance and ownership, assessing opportunities for operational AI, and helping teams move from experimentation toward changes in real work.</p>
 <p>I have seen how easily portfolios become collections of promising pilots without a common basis for deciding what deserves attention. Funding is only one constraint. Data quality, process readiness, sponsorship, delivery capacity and the willingness to change established ways of working often determine whether an initiative creates value.</p>
 <div class="sc-pullquote">My starting point is not “Where can we apply AI?” It is “Which business decision or process needs to change, and why is AI the right intervention?”</div>
 <p>The Scorecard brings those considerations into one repeatable discussion. It draws on my work with enterprise AI portfolios, governance arrangements, adoption and operating models. It is an independent advisory resource, not a claim that one scoring model can replace executive judgment.</p>
 <p style="margin-top:25px"><a class="sc-btn alt" href="?page=about" target="_self">Explore my professional background →</a></p>
</div></section>

<section class="sc-wrap" aria-labelledby="sc-example">
 <span class="sc-kicker">Illustrative example</span>
 <h2 id="sc-example">Four promising AI opportunities. One constrained investment decision.</h2>
 <p>Consider a service organization facing these competing proposals. All four may have merit, but there is not enough capacity to progress every initiative simultaneously.</p>
 <div class="sc-table-wrap" role="region" aria-label="Illustrative AI portfolio comparison" tabindex="0">
  <table class="sc-example-table">
   <thead><tr><th>AI opportunity</th><th>Question leadership must answer</th><th>Possible next action</th></tr></thead>
   <tbody>
    <tr><td>Service knowledge assistant</td><td>Can teams trust the retrieved guidance, and who owns its accuracy?</td><td>Test with approved content, a business owner and a measurable service baseline.</td></tr>
    <tr><td>Warranty claim triage</td><td>Are the proposed savings credible, and is human escalation defined?</td><td>Hold broader rollout until the control and evidence gaps are closed.</td></tr>
    <tr><td>Demand forecasting</td><td>Does better forecasting justify scarce data and planning capacity?</td><td>Compare expected benefit against a conventional process improvement and the cost of displaced work.</td></tr>
    <tr><td>Management reporting assistant</td><td>Is the problem primarily repetitive reporting, data quality or unclear ownership?</td><td>Establish a baseline; improve the process first where AI adds little incremental value.</td></tr>
   </tbody>
  </table>
 </div>
 <p class="sc-note">Fictional examples for explanation only. These actions are hypotheses for further examination, not conclusions from actual scored portfolios.</p>
 <div class="sc-boundary"><p><strong>What changes after this review?</strong> Instead of four proposals competing through separate business cases, leadership can identify the evidence needed, make the capacity trade-offs explicit and record which decisions can be made now versus which must wait.</p></div>
</section>

<section class="sc-wrap" aria-labelledby="sc-criteria" style="padding-top:10px">
 <span class="sc-kicker">The assessment method</span>
 <h2 id="sc-criteria">Seven dimensions. A consistent basis for challenge.</h2>
 <p>Initiatives are evaluated against evidence-based 1–5 anchors. The default weights can be changed for the organization, but control gates and approvals remain independent of the numerical result.</p>
 <div class="sc-grid-2">
  <article class="sc-card"><span class="sc-num">01 / Strategic fit</span><h3>Business priority</h3><p>Does this initiative serve a named business objective, with a sponsor and measurable operational outcome?</p></article>
  <article class="sc-card"><span class="sc-num">02 / Business value</span><h3>Defensible benefit</h3><p>Is there a baseline, a credible estimate of incremental value and an owner accountable for realizing it?</p></article>
  <article class="sc-card"><span class="sc-num">03 / Feasibility</span><h3>Delivery and operations</h3><p>Are technical dependencies, processes, vendors and ongoing operating needs sufficiently understood?</p></article>
  <article class="sc-card"><span class="sc-num">04 / Capacity</span><h3>Opportunity cost</h3><p>Are critical people and funds available, and what must be delayed or stopped to release them?</p></article>
  <article class="sc-card"><span class="sc-num">05 / Data readiness</span><h3>Data that can be trusted</h3><p>Are ownership, accessibility, provenance and quality established for the intended use?</p></article>
  <article class="sc-card"><span class="sc-num">06 / Adoption</span><h3>Ownership and changed work</h3><p>Who owns the process after deployment, and how will the organization demonstrate meaningful adoption?</p></article>
  <article class="sc-card"><span class="sc-num">07 / Risk and controls</span><h3>Conditions for proceeding</h3><p>Are required safeguards, human oversight, escalation and specialist reviews defined and evidenced?</p></article>
  <article class="sc-card"><span class="sc-num">Beyond the score</span><h3>Executive discretion</h3><p>High scores cannot override unresolved legal, security, privacy or operating controls. The final decision always belongs to accountable leaders.</p></article>
 </div>
</section>

<section class="sc-dark"><div class="sc-wrap" aria-labelledby="sc-workspace">
 <span class="sc-kicker">What approved clients receive</span>
 <h2 id="sc-workspace">A private, editable portfolio decision workspace.</h2>
 <p>Approved Advisory clients receive individual access to a working service. It is designed to support a real portfolio discussion and preserve the reasoning behind decisions—not to generate an automatic verdict.</p>
 <div class="sc-grid">
  <article class="sc-card"><span class="sc-num">Portfolio scorecard</span><h3>Compare up to 30 initiatives</h3><p>Record opportunity descriptions, sponsors, business owners, scores, evidence confidence and control gates.</p></article>
  <article class="sc-card"><span class="sc-num">Capacity and value</span><h3>Examine realistic options</h3><p>Model proposed selections against FTE-months, available budget, estimated costs and indicative benefits.</p></article>
  <article class="sc-card"><span class="sc-num">Decision record</span><h3>Keep an audit trail of judgment</h3><p>Document the rationale, alternatives, conditions, accountability and next review for each proposal.</p></article>
 </div>
 <p style="margin-top:27px">The workspace also includes adjustable scoring weights, example scenarios and a CSV summary export. Client work is saved privately within the approved Advisory account; only the authorized client and advisor can access that workspace through its permissions.</p>
 <p>The workspace starts empty. It is intended for high-level, non-confidential information. Detailed company data, personal records or protected material require a separately agreed handling arrangement.</p>
 <p>At a few natural points—after an assessment, decision guidance or summary export—clients can optionally rate clarity and usefulness in one short step. Comments are optional, and feedback never delays the decision or download. I use it to improve the service and identify where more explanation may be needed.</p>
</div></section>

<section class="sc-wrap" id="sc-how-it-works" aria-labelledby="sc-process-title">
 <span class="sc-kicker">How an engagement works</span>
 <h2 id="sc-process-title">From a specific business challenge to a recorded decision.</h2>
 <ol class="sc-process">
  <li><strong>Describe the decision.</strong><p>Register for a free Advisory account and explain the portfolio problem, responsible sponsor, decision timing and the outcome you need. You can request Scorecard access directly from the account.</p></li>
  <li><strong>Individual assessment.</strong><p>I review requests for strategic relevance, a clearly defined challenge, executive sponsorship, readiness to act, potential impact and available time. Not every request is accepted.</p></li>
  <li><strong>Agree the scope and activate access.</strong><p>For a selected pro-bono engagement, we agree the question and boundaries. I then enable the private Scorecard individually. An account or an access request alone does not grant permission.</p></li>
  <li><strong>Review options and record next steps.</strong><p>The client assesses initiatives in the workspace, examines constraints and unresolved controls, and records the leadership decision and its next evidence requirements. Any direct advisory discussion is limited to the agreed scope.</p></li>
 </ol>
 <div class="sc-boundary"><p><strong>Service boundaries.</strong> The Scorecard is a management decision aid, not a legal or regulatory certification, an independently audited financial forecast or permission to deploy an AI system. It does not replace privacy, security or specialist risk reviews.</p></div>
 <div class="sc-final-actions">
  <a class="sc-btn" href="?page=advisory-access&amp;view=scorecard" target="_self" data-hq-event="scorecard_request_footer">Open Advisory account · Request access →</a>
  <a class="sc-btn light" href="?page=advisory" target="_self">Return to Executive Advisory →</a>
 </div>
</section>
</main>{footer()}"""
