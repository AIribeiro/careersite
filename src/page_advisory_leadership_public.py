"""Public Executive AI Leadership Workshop, using the Investment Decision Advisor design.

No account data or private assessments are accessed by the public renderer.
The CTA enters the existing verified Advisory account, rather than enrolling
a visitor in a new system or requesting individual pro-bono approval.
"""
from __future__ import annotations

from page_advisory_investment import SERVICE_CSS as INVESTMENT_SERVICE_CSS
from page_advisory_scorecard import SCORECARD_CSS
from page_public_services import SERVICES_CSS
from site_components import nav, footer


LEADERSHIP_SERVICE_CSS = """
<style>
.site .leadership-product .sc-hero{
 background:linear-gradient(118deg,#0c2034 0%,#182e42 75%,#233f54 100%)
}
.site .leadership-product .leadership-evidence{
 border-left:3px solid #e5b58f;background:#233e55;max-width:750px;
 padding:21px 25px;margin:27px 0;color:#fff
}
.site .leadership-product .leadership-evidence strong{
 display:block;font:500 clamp(22px,2.8vw,29px)/1.25 Georgia,serif;color:#fff
}
.site .leadership-product .leadership-evidence p{
 margin:9px 0 0;font-size:14px;color:#d2dfe7
}
.site .leadership-product .leadership-proofline{
 display:flex;gap:9px;flex-wrap:wrap;margin-top:24px
}
.site .leadership-product .leadership-proofline span{
 border:1px solid #668094;padding:9px 12px;font:750 11px/1.4 Arial,sans-serif;
 color:#e6ebee;letter-spacing:.01em
}
.site .leadership-product .leadership-stages{
 display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:28px 0
}
.site .leadership-product .leadership-stages article{
 background:#fff;border:1px solid #dedbd5;padding:26px;min-width:0
}
.site .leadership-product .leadership-stages small{
 display:block;color:#a36d49;font:800 10px/1.6 Arial,sans-serif;letter-spacing:.11em
}
.site .leadership-product .leadership-stages h3{margin:13px 0 10px}
.site .leadership-product .leadership-stages p{font-size:14px;line-height:1.7;margin:0}
.site .leadership-product .leadership-dimensions{
 display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 26px;
 margin:25px 0 7px
}
.site .leadership-product .leadership-dimensions div{
 display:flex;gap:15px;align-items:baseline;border-bottom:1px solid #dedbd5;
 padding:16px 5px;min-width:0
}
.site .leadership-product .leadership-dimensions span{font:750 11px Arial,sans-serif;color:#ad7754}
.site .leadership-product .leadership-dimensions strong{font:600 15px/1.45 Arial,sans-serif;color:#1b3044}
.site .leadership-product .leadership-output-sample{
 background:#fff;border:1px solid #d7d4cd;border-top:4px solid #b87d58;
 padding:29px 32px;margin:27px 0;color:#253b4b
}
.site .leadership-product .leadership-output-sample small{
 color:#986b50;font:800 10px/1.6 Arial,sans-serif;letter-spacing:.1em
}
.site .leadership-product .leadership-output-sample h3{
 font:500 clamp(25px,3vw,35px)/1.2 Georgia,serif;color:#173149;margin:10px 0 12px
}
.site .leadership-product .leadership-output-sample p{
 font-size:14px;line-height:1.73;color:#4d5f6d
}
.site .leadership-product .leadership-output-sample ol{
 margin:16px 0 0;padding-left:22px;color:#263c51
}
.site .leadership-product .leadership-output-sample li{padding:5px 0;font-size:14px}
.site .leadership-product .leadership-trust{
 display:grid;grid-template-columns:minmax(0,1.15fr) minmax(240px,.8fr);
 gap:34px;align-items:start;margin-top:30px
}
.site .leadership-product .leadership-trust article{
 background:#fff;border:1px solid #dedbd5;padding:27px 29px
}
.site .leadership-product .leadership-trust article h3{margin:0 0 14px}
.site .leadership-product .leadership-trust article p{margin:10px 0;line-height:1.75}
.site .leadership-product .leadership-trust ul{padding-left:19px;margin:10px 0}
.site .leadership-product .leadership-trust li{
 color:#4b5d70;font-size:14px;line-height:1.7;margin:9px 0
}
.site .leadership-product .leadership-auth{
 background:#fff;border:1px solid #dcd8d0;padding:28px 30px;margin:26px 0 0
}
.site .leadership-product .leadership-auth h3{margin:0 0 11px}
.site .leadership-product .leadership-auth p{margin:8px 0;max-width:760px}
.site .leadership-product a:focus-visible{outline:3px solid #b87950;outline-offset:3px}
@media(max-width:850px),(max-device-width:850px){
 .site .leadership-product .leadership-trust{grid-template-columns:1fr}
}
@media(max-width:760px),(max-device-width:760px){
 .site .leadership-product .leadership-stages{grid-template-columns:1fr}
 .site .leadership-product .leadership-dimensions{grid-template-columns:1fr}
 .site .leadership-product .leadership-output-sample{padding:22px 19px}
 .site .leadership-product .leadership-auth{padding:23px 19px}
 .site .leadership-product .leadership-trust article{padding:22px 19px}
 .site .leadership-product .leadership-evidence{padding:19px 20px}
}
</style>
"""


def advisory_leadership() -> str:
    """A credible public explanation before the first account form."""
    return f'''{SERVICES_CSS}{SCORECARD_CSS}{INVESTMENT_SERVICE_CSS}{LEADERSHIP_SERVICE_CSS}{nav("advisory")}
<main class="scorecard-page investment-product leadership-product">
<section class="sc-hero" aria-labelledby="leadership-title" data-analytics-section="leadership-workshop-hero">
 <div class="container">
  <span class="sc-kicker">Executive AI Advisory / Free leadership assessment</span>
  <h1 id="leadership-title">Executive AI Leadership Workshop.</h1>
  <p class="sc-lead">Are your leaders prepared to own the decisions behind AI adoption?</p>
  <p>A structured self-service workshop for individual executives and leadership teams. Examine the leadership conditions that turn AI ambition into accountable choices, changed work and measurable business outcomes—then agree what needs to happen next.</p>
  <div class="leadership-evidence">
   <span class="investment-eyebrow">THE EXECUTIVE OUTPUT</span>
   <strong>A leadership decision agenda, not another maturity badge.</strong>
   <p>See seven leadership dimensions, the gaps in reported evidence, two relevant executive dilemmas, three recommended actions and a downloadable decision record.</p>
  </div>
  <div class="sc-actions">
   <a class="sc-btn" href="?page=advisory-access&amp;view=workshop" target="_self" data-hq-event="leadership_start_register">Register free · Start workshop</a>
   <a class="sc-btn alt" href="?page=advisory-access&amp;view=workshop&amp;signin=1" target="_self" data-hq-event="leadership_start_signin">Already registered? Sign in</a>
  </div>
  <div class="leadership-proofline" aria-label="Service conditions">
   <span>21 guided questions</span><span>Individual or invited team</span>
   <span>Private saved history</span><span>Executive PDF</span><span>No payment</span>
  </div>
 </div>
</section>

<section class="sc-wrap" id="leadership-value" data-analytics-section="leadership-workshop-value">
 <span class="sc-kicker">The leadership question</span>
 <h2>AI capability does not automatically create leadership readiness.</h2>
 <p>An organization may have promising AI pilots, an approved strategy and a governance framework while still struggling to decide what to prioritize, who owns the outcome, how work must change and what evidence should justify further investment.</p>
 <p>This workshop makes those conditions explicit. It is intended to support a practical management conversation—not to measure technology proficiency or declare an organization compliant.</p>
 <div class="leadership-stages">
  <article><small>01 / ASSESS</small><h3>Test leadership conditions.</h3><p>Answer 21 structured questions based on what is actually established today. Seven dimensions help locate ownership, adoption, governance and decision gaps.</p></article>
  <article><small>02 / CHALLENGE</small><h3>Discuss realistic dilemmas.</h3><p>Choose how leadership would respond to two scenarios selected from investment trade-offs, employee concerns, governance authority and adoption.</p></article>
  <article><small>03 / DECIDE</small><h3>Record what should change.</h3><p>Review the findings, select accountable functions, agree a review horizon and download a concise executive decision brief.</p></article>
 </div>
 <div class="sc-boundary"><p><strong>What makes the assessment different?</strong> Its logic is explicit. Critical failures in business ownership or essential AI control conditions can override a favorable average. Missing answers are disclosed as missing evidence, not treated as a low score. Recommendations are derived from selections—not invented outcomes.</p></div>
</section>

<section class="sc-wrap" id="leadership-scope" data-analytics-section="leadership-workshop-dimensions">
 <span class="sc-kicker">What leadership will examine</span>
 <h2>Seven dimensions. One shared view of the decisions that matter.</h2>
 <p>Each dimension contains three questions. Participants select the closest demonstrated condition; unanswered items remain visible as evidence gaps.</p>
 <div class="leadership-dimensions" role="list">
  <div role="listitem"><span>01</span><strong>Strategy and investment priorities</strong></div>
  <div role="listitem"><span>02</span><strong>Governance and risk authority</strong></div>
  <div role="listitem"><span>03</span><strong>Leadership accountability</strong></div>
  <div role="listitem"><span>04</span><strong>Data ownership and readiness</strong></div>
  <div role="listitem"><span>05</span><strong>Adoption, people and changed work</strong></div>
  <div role="listitem"><span>06</span><strong>Operational readiness</strong></div>
  <div role="listitem"><span>07</span><strong>Realized business value</strong></div>
 </div>
 <p class="sc-micro">The scoring weights and thresholds are disclosed methodology choices, not a validated industry ranking. The result reflects self-reported practice and is not an independent organizational audit.</p>
</section>

<section class="sc-wrap sc-dark" style="max-width:none" id="leadership-deliverables" data-analytics-section="leadership-workshop-outputs">
 <div style="max-width:1100px;margin:auto">
  <span class="sc-kicker">What you receive</span>
  <h2>An outcome executives can use in the next leadership meeting.</h2>
  <div class="sc-grid-2">
   <article class="sc-card"><span class="sc-num">Readiness</span><h3>Leadership assessment</h3><p>A seven-dimension profile, clearly identified evidence gaps, and critical conditions requiring attention.</p></article>
   <article class="sc-card"><span class="sc-num">Discussion</span><h3>Executive dilemmas</h3><p>Two contextual scenarios, selected responses, overlooked assumptions and trade-offs to challenge.</p></article>
   <article class="sc-card"><span class="sc-num">Accountability</span><h3>Three leadership actions</h3><p>Specific actions, suggested accountable roles, the evidence to examine and the next review conditions.</p></article>
   <article class="sc-card"><span class="sc-num">Record</span><h3>Private decision brief</h3><p>A downloadable two-page PDF, a saved assessment and an editable decision history in your account.</p></article>
  </div>
 </div>
</section>

<section class="sc-wrap" id="leadership-report-example" data-analytics-section="leadership-workshop-example">
 <span class="sc-kicker">Illustrative outcome / Fictional example</span>
 <h2>What a decision-ready result looks like.</h2>
 <p>This is an example of the report structure. It is not a real company's assessment and makes no claim about your organization.</p>
 <div class="leadership-output-sample">
  <small>EXECUTIVE LEADERSHIP DECISION BRIEF / EXAMPLE ONLY</small>
  <h3>Targeted leadership changes required.</h3>
  <p>A fictional assessment indicates that operational AI capabilities are better established than business ownership and workforce adoption. The recommended response is to address those leadership conditions before widening deployment.</p>
  <ol>
   <li><strong>Confirm business ownership:</strong> name the executive accountable for the changed process and business result.</li>
   <li><strong>Revisit the workflow:</strong> test operational roles, employee concerns and measures of sustained use.</li>
   <li><strong>Set a review gate:</strong> establish the evidence needed before a further rollout decision.</li>
  </ol>
  <p class="sc-micro">The real report uses your selected answers, not this example. Suggested ownership becomes an agreed responsibility only when leadership confirms it.</p>
 </div>
</section>

<section class="sc-wrap" id="leadership-trust" data-analytics-section="leadership-workshop-trust">
 <span class="sc-kicker">The basis for the advice</span>
 <h2>Practical enterprise experience. Transparent limits.</h2>
 <div class="leadership-trust">
  <article>
   <h3>Why this perspective?</h3>
   <p>The method draws on Jair Ribeiro's experience working with enterprise AI and data leadership, AI portfolios, governance, business ownership, Lean and organizational adoption. It asks the questions that often determine whether promising AI investments become useful operating changes.</p>
   <p>Rather than presenting a proprietary, externally certified maturity benchmark, the service exposes its questions, evidence assumptions and rules. Leaders can challenge the findings and retain authority over the final decision.</p>
   <p><a href="?page=impact" target="_self">Review leadership experience</a> · <a href="?page=thinking" target="_self">Read executive perspectives</a></p>
  </article>
  <article>
   <h3>Privacy and decision boundaries</h3>
   <ul>
    <li>Free account. No payment details or automatic editorial subscription.</li>
    <li>Use non-confidential context and guided selections; do not submit client-sensitive material.</li>
    <li>Individual assessments are private in the verified Advisory account.</li>
    <li>Team participants must explicitly choose to share answers with the organizer. Small-group comparisons are not anonymous.</li>
    <li>No AI deployment, legal-compliance or investment approval is issued.</li>
   </ul>
   <p><a href="?page=privacy" target="_self">Read the Privacy &amp; Data notice</a></p>
  </article>
 </div>
</section>

<section class="sc-wrap" id="leadership-access" data-analytics-section="leadership-workshop-access">
 <span class="sc-kicker">Access and next step</span>
 <h2>Make a leadership decision with the evidence in front of you.</h2>
 <p>Start as an individual executive or create a team workshop and invite colleagues. Participants answer separately; shared findings only use the answers members choose to disclose. You can save progress, return to the workspace and download the executive record after completing the questions and discussion exercises.</p>
 <div class="leadership-auth">
  <h3>One free Executive Advisory account.</h3>
  <p>Registration requires email verification and account access. No individual approval is needed for the self-service workshop. Optional personal pro-bono discussions are requested separately and selected individually.</p>
  <div class="sc-actions">
   <a class="sc-btn" href="?page=advisory-access&amp;view=workshop" target="_self" data-hq-event="leadership_footer_register">Register free · Start workshop</a>
   <a class="sc-btn light" href="?page=advisory-access&amp;view=workshop&amp;signin=1" target="_self" data-hq-event="leadership_footer_signin">Sign in to my workshop</a>
  </div>
  <p class="sc-micro">Already have a verified Advisory account? Sign in; you do not need to register again.</p>
 </div>
 <p class="sc-note" style="margin-top:20px">Self-service guidance only. The assessment is based on the answers supplied, not independently verified evidence. Review important organizational and legal decisions with the responsible specialists.</p>
</section>
</main>{footer()}'''
