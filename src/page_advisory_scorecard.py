"""Public landing page for the selectively approved AI Portfolio Decision Kit.

This describes an on-demand pro-bono advisory resource; no portfolio data or
private workspace information is rendered to anonymous visitors.
"""
from __future__ import annotations

from page_public_services import SERVICES_CSS
from site_components import nav, footer


SCORECARD_CSS = """
<style>
.site .scorecard-page{color:#172b40;background:#f7f5f0}
.site .scorecard-page *{box-sizing:border-box}
.site .sc-hero{background:#0e2237;color:#f9f7f3;padding:clamp(55px,8vw,108px) 0}
.site .sc-kicker{color:#dca782;text-transform:uppercase;font:800 11px Arial,sans-serif;letter-spacing:.18em}
.site .sc-hero h1{font:500 clamp(43px,6vw,80px)/1.08 Georgia,serif;max-width:990px;letter-spacing:-.035em;margin:22px 0}
.site .sc-hero p{font:17px/1.75 Arial,sans-serif;max-width:790px;color:#cbd7e3}
.site .sc-hero .sc-actions{display:flex;gap:13px;flex-wrap:wrap;margin-top:32px}
.site .sc-btn{display:inline-flex;align-items:center;justify-content:center;min-height:47px;padding:12px 20px;border:1px solid #e5b28b;text-decoration:none!important;background:#dba77e;color:#142438!important;font:700 13px Arial,sans-serif}
.site .sc-btn.alt{background:transparent;color:#f7f7f5!important;border-color:#7d8c9a}
.site .sc-wrap{max-width:1120px;margin:auto;padding:68px 28px}
.site .sc-wrap h2{font:500 clamp(32px,4vw,52px)/1.16 Georgia,serif;margin:0 0 15px;color:#172e46}
.site .sc-wrap p,.site .sc-wrap li{font:15px/1.8 Arial,sans-serif;color:#4b5d70}
.site .sc-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:28px}
.site .sc-card{padding:29px 27px;background:white;border:1px solid #e1dbd2}
.site .sc-card h3{font:500 24px/1.3 Georgia,serif;margin:10px 0;color:#18304a}
.site .sc-num{font:bold 12px Arial,sans-serif;color:#b26d42;letter-spacing:.12em}
.site .sc-boundary{border-left:4px solid #c58c64;background:#fff9ee;padding:24px 29px;margin-top:32px}
.site .sc-boundary p{margin:0}
.site .sc-dark{background:#182a3d}
.site .sc-dark h2{color:#fff}
.site .sc-dark p{color:#ccd7e0}
.site .sc-list{padding-left:22px}
.site .sc-micro{font:12px/1.7 Arial,sans-serif;color:#6a7785}
@media(max-width:760px){.site .sc-grid{grid-template-columns:1fr}.site .sc-wrap{padding:46px 20px}.site .sc-hero{padding:58px 0}}
</style>
"""


def advisory_scorecard() -> str:
    """Public introduction to a separately approved, private scorecard workspace."""
    return f"""{SERVICES_CSS}{SCORECARD_CSS}{nav('advisory')}
<main class="scorecard-page">
<section class="sc-hero"><div class="container">
 <div class="sc-kicker">Executive Advisory / On-demand working service / Selective pro-bono access</div>
 <h1>AI Portfolio Prioritization Scorecard.</h1>
 <p>A structured way to examine which AI initiatives deserve scarce business attention, delivery capacity and investment—and which should be tested further, held or stopped.</p>
 <p>This is a working decision service, not a general AI maturity quiz. It is offered without charge within selected, approved pro-bono Advisory engagements. Access is granted to each approved client individually.</p>
 <div class="sc-actions">
  <a class="sc-btn" href="?page=advisory-access" target="_self" data-hq-event="scorecard_apply">Submit an advisory request →</a>
  <a class="sc-btn alt" href="?page=advisory-access&amp;signin=1" target="_self" data-hq-event="scorecard_client_signin">Already approved? Open your account →</a>
 </div>
</div></section>
<section class="sc-wrap" aria-labelledby="sc-purpose">
 <span class="sc-kicker">The decision</span>
 <h2 id="sc-purpose">Priorities are choices, not a list of attractive use cases.</h2>
 <p>AI opportunity pipelines often grow faster than available leadership attention, specialist capacity or funding. A high-profile use case can also remain a poor investment when data ownership, operational adoption or safeguards are unresolved. The scorecard makes those trade-offs explicit.</p>
 <div class="sc-grid">
  <article class="sc-card"><span class="sc-num">01 / Compare</span><h3>Common decision criteria</h3><p>Seven evidence-based dimensions: strategic fit, business value, feasibility, capacity and opportunity cost, data readiness, adoption and ownership, and control readiness.</p></article>
  <article class="sc-card"><span class="sc-num">02 / Constrain</span><h3>Capacity before commitments</h3><p>Compare proposed initiatives against available FTE-months, investment limits, recurring cost and indicative annual benefit. See what a proposed portfolio displaces.</p></article>
  <article class="sc-card"><span class="sc-num">03 / Decide</span><h3>Accountable outcomes</h3><p>Document the decision, evidence gaps, control conditions, named owners, next proof and review date. A numeric score never substitutes for executive approval.</p></article>
 </div>
 <div class="sc-boundary"><p><strong>Control conditions override ranking.</strong> A blocked or unreviewed AI use does not become approvable because it scores well elsewhere. Evidence confidence, privacy, security, human oversight and formal authority remain separate checks.</p></div>
</section>
<section class="sc-dark"><div class="sc-wrap">
 <span class="sc-kicker">What approved clients receive</span>
 <h2>A private, editable decision workspace.</h2>
 <p>Within the Advisory account, approved users can maintain a portfolio of up to 30 initiatives, score evidence against explicit 1–5 criteria, revise weights, compare investment and capacity, and record executive decisions. Each client's information is private to that client's account and the advisor.</p>
 <p>The workspace starts empty. It is designed for high-level, non-confidential information. Do not enter personal information, protected data or proprietary client material without a separately agreed data-handling arrangement.</p>
</div></section>
<section class="sc-wrap" aria-labelledby="sc-access">
 <span class="sc-kicker">Individual access / On demand</span>
 <h2 id="sc-access">How access is approved.</h2>
 <ol class="sc-list">
  <li><strong>Register for an Advisory account.</strong> Registration and the initial request are free, but do not grant scorecard access.</li>
  <li><strong>Describe a real executive AI portfolio decision.</strong> Explain the sponsor, timing, affected business outcome and why an independent review would help.</li>
  <li><strong>Individual assessment.</strong> I select requests based on strategic relevance, a defined challenge, executive sponsorship, readiness to act, potential impact and available time.</li>
  <li><strong>Approval and activation.</strong> If a pro-bono engagement is agreed, I enable the scorecard for the approved client. Access can be withdrawn when the engagement ends or if circumstances change.</li>
 </ol>
 <p class="sc-micro">This service is not a guarantee of an engagement, a certified risk assessment or an authorization to fund or deploy AI.</p>
 <div class="sc-hero sc-actions" style="padding:24px;background:transparent">
  <a class="sc-btn" href="?page=advisory-access" target="_self" data-hq-event="scorecard_request_footer">Request individual review →</a>
  <a class="sc-btn alt" style="color:#172e46!important;border-color:#b0a091" href="?page=advisory" target="_self">Return to Executive Advisory →</a>
 </div>
</section>
</main>{footer()}"""
