"""Public advisory offering and privacy notice.

These two first-party pages are deliberately separate from reader authentication
and the privileged owner/CMS account. No email is sent by these page renderers.
"""
from __future__ import annotations

from site_assets import ADVISORY_EMAIL, EMAIL, PRIVACY_EMAIL, READERS_EMAIL
from site_media import IMAGE_DIR
from site_components import footer, nav
import streamlit as st


SERVICES_CSS = """
<style>
.site .advisory-page,.site .privacy-page{color:#142032;background:#f6f3ed}
.site .advisory-page *, .site .privacy-page *{box-sizing:border-box}
.site .service-eyebrow{margin:0 0 19px;color:#b96b40;font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}
.site .service-lede{font-size:clamp(18px,2vw,22px);line-height:1.62;max-width:760px;color:#c5ced9}
.site .advisory-hero{background:#0c1728;color:#f9f6f0;padding:104px 0 90px;overflow:hidden}
.site .advisory-hero-grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(275px,.68fr);gap:72px;align-items:center}
.site .advisory-hero h1{font:500 clamp(48px,6.6vw,82px)/1.03 Georgia,serif;letter-spacing:-.045em;max-width:900px;margin:0 0 27px}
.site .advisory-actions{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-top:34px}
.site .advisory-button{display:inline-flex;align-items:center;justify-content:center;min-height:51px;padding:15px 23px;background:#d69b75;color:#142032!important;text-decoration:none!important;font-size:13px;font-weight:850;letter-spacing:.01em;border:1px solid #d69b75;transition:background .15s ease}
.site .advisory-button:hover{background:#edbb9c}
.site .advisory-button--outline{background:transparent;color:#f3eee8!important;border-color:#7e8b9b}
.site .advisory-button--outline:hover{background:#263850}
.site .advisory-aside{border:1px solid #586777;padding:38px 33px;background:linear-gradient(155deg,#1b2e46,#101c2f);position:relative}
.site .advisory-aside:before{content:"";display:block;width:52px;height:3px;background:#d69b75;margin-bottom:40px}
.site .advisory-aside small{display:block;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#d4b39d;font-weight:800}
.site .advisory-aside blockquote{font:500 clamp(25px,2.7vw,36px)/1.23 Georgia,serif;letter-spacing:-.02em;margin:24px 0 26px}
.site .advisory-aside p{font-size:13px;line-height:1.75;color:#bdc8d5;margin:0}
.site .service-section{padding:85px 0}
.site .service-section--white{background:#fffefa}
.site .service-section--ink{background:#102039;color:#f6f4ee}
.site .service-section-header{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.75fr);gap:60px;align-items:end;margin-bottom:36px}
.site .service-section h2{font:500 clamp(37px,4.6vw,61px)/1.08 Georgia,serif;letter-spacing:-.025em;margin:0}
.site .service-section-header>p,.site .service-intro{line-height:1.78;color:#546276;font-size:16px;margin:0}
.site .service-section--ink .service-section-header>p,.site .service-section--ink .service-intro{color:#c4cfdb}
.site .service-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.site .service-card{background:#f6f3ed;border:1px solid #e0d9ce;padding:32px 35px;min-height:230px}
.site .service-card span{display:block;font-size:10px;letter-spacing:.17em;text-transform:uppercase;color:#b46439;font-weight:850}
.site .service-card h3{font:500 29px/1.16 Georgia,serif;margin:24px 0 13px;letter-spacing:-.015em}
.site .service-card p{line-height:1.75;font-size:14px;color:#526174;margin:0}
.site .service-formats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.site .service-format{border-top:2px solid #ca8a5d;padding:25px 26px;background:#1c2e46;min-height:252px}
.site .service-format small{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#d6a682;font-weight:800}
.site .service-format h3{font:500 27px/1.22 Georgia,serif;margin:26px 0 13px}
.site .service-format p{font-size:14px;line-height:1.76;color:#c0ccd9;margin:0}
.site .service-steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid #ded8cd;border-bottom:1px solid #ded8cd;margin-top:36px}
.site .service-step{padding:29px 25px 29px 0}
.site .service-step+.service-step{border-left:1px solid #ded8cd;padding-left:25px}
.site .service-step span{font:500 32px Georgia,serif;color:#b86c43}
.site .service-step h3{font-size:16px;line-height:1.3;margin:22px 0 10px}
.site .service-step p{font-size:13px;line-height:1.75;color:#526174;margin:0}
.site .service-contact{background:#f1e7da;border-top:1px solid #dccbb8;padding:66px 0}
.site .service-contact-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(270px,.65fr);gap:55px;align-items:center}
.site .service-contact h2{font:500 clamp(37px,4.6vw,58px)/1.09 Georgia,serif;letter-spacing:-.02em;margin:0 0 15px}
.site .service-contact p{line-height:1.73;font-size:15px;max-width:680px;color:#536073}
.site .service-contact .service-mail{font-size:17px;font-weight:750;overflow-wrap:anywhere;color:#18304d}
.site .service-note{font-size:12px!important;color:#6b6d6b!important;line-height:1.6!important}
.site .privacy-hero{background:#0e1c31;color:#f9f6ef;padding:90px 0 75px}
.site .privacy-hero h1{margin:0 0 18px;font:500 clamp(47px,6vw,76px)/1.06 Georgia,serif;letter-spacing:-.035em}
.site .privacy-hero p:not(.service-eyebrow){max-width:790px;color:#c7d1df;font-size:19px;line-height:1.65}
.site .privacy-effective{color:#e0b294!important;font-size:12px!important;letter-spacing:.04em}
.site .privacy-body{display:grid;grid-template-columns:250px minmax(0,780px);gap:70px;align-items:start;padding:75px 0 95px}
.site .privacy-toc{position:sticky;top:105px;padding:20px 23px;background:#eee8df;border:1px solid #ddd5c8}
.site .privacy-toc strong{display:block;font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:16px}
.site .privacy-toc a{display:block;margin:12px 0;color:#2d4563!important;text-decoration:none!important;font-size:13px;line-height:1.4}
.site .privacy-content section{padding:0 0 34px;margin:0 0 37px;border-bottom:1px solid #dcd5cb;scroll-margin-top:110px}
.site .privacy-content h2{font:500 31px/1.2 Georgia,serif;letter-spacing:-.015em;margin:0 0 17px}
.site .privacy-content p,.site .privacy-content li{font-size:15px;line-height:1.82;color:#45566b}
.site .privacy-content ul{padding-left:22px}
.site .privacy-content li{margin-bottom:9px}
.site .privacy-content a{color:#214d77!important;text-underline-offset:3px}
.site .privacy-contact{display:flex;align-items:flex-start;flex-direction:column;gap:5px;border-left:3px solid #b96b40;padding:16px 20px;background:#f0e9df}
.site .privacy-contact a{font-weight:800;overflow-wrap:anywhere}
@media(max-width:850px){
.site .advisory-hero-grid,.site .service-section-header,.site .service-contact-layout{grid-template-columns:1fr;gap:29px}
.site .service-formats{grid-template-columns:1fr}
.site .service-steps{grid-template-columns:repeat(2,minmax(0,1fr))}
.site .service-step:nth-child(3){border-left:0;padding-left:0}
.site .privacy-body{grid-template-columns:1fr;gap:26px}
.site .privacy-toc{position:static}
}
@media(max-width:620px){
.site .advisory-hero{padding:62px 0}
.site .advisory-hero h1{font-size:clamp(42px,11vw,60px)}
.site .advisory-aside{padding:26px}
.site .service-section{padding:58px 0}
.site .service-grid,.site .service-steps{grid-template-columns:1fr}
.site .service-step,.site .service-step+.service-step{border-left:0;border-bottom:1px solid #ddd5cb;padding:24px 0}
.site .service-card{padding:26px;min-height:0}
.site .service-contact{padding:50px 0}
.site .privacy-hero{padding:62px 0 50px}
.site .privacy-body{padding:48px 0}
}

.site .advisory-hero{padding:86px 0 76px}
.site .advisory-hero-grid{grid-template-columns:minmax(0,1.26fr) minmax(280px,.72fr);gap:62px}
.site .advisory-hero h1{font-size:clamp(45px,6vw,75px);line-height:1.08}
.site .advisory-proofline{display:flex;flex-wrap:wrap;gap:10px;margin-top:34px}
.site .advisory-proofline span{border:1px solid #5d7184;padding:9px 13px;font-size:11px;font-weight:700;color:#e2e9f2}
.site .service-section--ink .service-eyebrow{color:#e4ad84}
.site .service-intro a{color:#a35a31!important;text-underline-offset:3px}
.site .advisory-personal{display:grid;grid-template-columns:minmax(250px,.77fr) minmax(0,1.15fr);gap:70px;align-items:center}
.site .advisory-portrait{margin:0;position:relative}
.site .advisory-portrait img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#d5d0c8;filter:saturate(.85)}
.site .advisory-portrait figcaption{font-size:12px;line-height:1.5;color:#687381;margin-top:14px}
.site .advisory-personal h2{font:500 clamp(36px,4.4vw,58px)/1.1 Georgia,serif;letter-spacing:-.025em;margin:0 0 22px}
.site .advisory-personal p:not(.service-eyebrow){line-height:1.82;color:#49586b;font-size:15px;margin:0 0 17px}
.site .advisory-personal .advisory-signoff{color:#173047!important;font-weight:800;font-size:13px!important;letter-spacing:.02em;margin-top:24px!important}
.site .advisory-results{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;margin-top:22px}
.site .advisory-result{padding:26px;border:1px solid #d7d1c8;background:#fffefa}
.site .advisory-result strong{display:block;font:500 22px/1.22 Georgia,serif;color:#1a2d43;margin-bottom:12px}
.site .advisory-result p{font-size:13px;color:#536175;line-height:1.72;margin:0}
.site .advisory-access{padding:66px 0;background:#102039;color:#f6f4ef;border-top:1px solid #26394e}
.site .advisory-access-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(250px,.8fr);gap:60px;align-items:center}
.site .advisory-access h2{font:500 clamp(36px,4vw,56px)/1.13 Georgia,serif;margin:0 0 19px}
.site .advisory-access p{color:#c4d0dc;font-size:15px;line-height:1.76}
.site .advisory-access .advisory-access-inclusion{border-left:3px solid #db9b70;padding-left:20px}
.site .advisory-access .advisory-access-inclusion strong{display:block;color:#ffe2cb;font:500 24px/1.3 Georgia,serif;margin-bottom:12px}
.site .advisory-small-link{display:inline-block;font-size:13px;font-weight:750;text-decoration:underline!important;color:#f8eee7!important;text-underline-offset:4px;margin-top:16px}

.site .advisory-access .service-eyebrow{color:#e9b58e}
.site .advisory-access .advisory-actions{margin-top:27px}
.site .advisory-access .advisory-access-inclusion{padding-top:7px}
.site .advisory-access-direct{margin-top:27px;padding-top:24px;border-top:1px solid rgba(255,255,255,.2);scroll-margin-top:100px}
.site .advisory-access-direct span{display:block;font-size:13px;font-weight:800;color:#faf5f0;letter-spacing:.01em}
.site .advisory-access-direct p{margin:9px 0 12px;color:#c4d0dc;font-size:13px;line-height:1.67}
.site .advisory-access-direct a{color:#f0b98f!important;font-size:13px;font-weight:800;text-decoration:underline!important;text-underline-offset:4px;overflow-wrap:anywhere}
.site .advisory-access-direct a:focus-visible{outline:3px solid #e9b48b;outline-offset:4px}

.site .service-method-note{margin:25px 0 0;font-size:13px;line-height:1.75;color:#627185}
.site .advisory-button:focus-visible,.site .advisory-small-link:focus-visible{outline:3px solid #e9b48b;outline-offset:4px}
@media(max-width:850px){
.site .advisory-personal,.site .advisory-access-grid{grid-template-columns:1fr;gap:30px}
.site .advisory-results{grid-template-columns:1fr}
.site .advisory-personal .advisory-portrait{max-width:520px}
}
@media(max-width:620px){
.site .advisory-hero{padding:60px 0}
.site .advisory-proofline{gap:7px}
.site .advisory-proofline span{padding:8px 10px}
.site .advisory-access{padding:53px 0}
}

/* Minimal additions: original premium layout and desktop typography are intact.
   Only ensure the original intended mobile grid wins over its desktop override. */
@media(max-width:850px){
.site .advisory-hero-grid{grid-template-columns:minmax(0,1fr);gap:29px}
.site .advisory-hero-grid>*{min-width:0}
}
@media(max-width:620px){
.site .advisory-hero h1{font-size:clamp(42px,11vw,60px)}
}
/* A quiet editorial reference beneath the three established engagement formats. */
.site .advisory-tool-reference{
 display:flex;align-items:center;justify-content:space-between;
 flex-wrap:wrap;gap:17px 28px;margin-top:23px;padding:22px 25px;
 background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.17)
}
.site .advisory-tool-reference>div{flex:1 1 360px;min-width:0}
.site .advisory-tool-reference small{
 display:block;color:#e0ab86;font:800 10px/1.4 Arial,sans-serif;
 text-transform:uppercase;letter-spacing:.13em
}
.site .advisory-tool-reference strong{
 display:block;margin-top:9px;color:#f8f5ef;
 font:500 22px/1.2 Georgia,serif
}
.site .advisory-tool-reference p{
 max-width:780px;margin:9px 0 0;color:#c2ceda;
 font:13px/1.65 Arial,sans-serif
}
.site .advisory-tool-reference>a{
 flex:0 0 auto;color:#f0b994!important;
 font:800 12px/1.4 Arial,sans-serif;
 text-decoration:none!important;border-bottom:1px solid #bb8662;
 padding:9px 0
}
.site .advisory-tool-reference>a:focus-visible{outline:2px solid #e9b48b;outline-offset:4px}
@media(max-width:620px){
.site .advisory-tool-reference{padding:19px 20px;margin-top:17px;gap:9px}
.site .advisory-tool-reference strong{font-size:20px}
.site .advisory-tool-reference>a{min-height:40px;display:inline-flex;align-items:center}
}

</style>
"""


def advisory() -> str:
    """Executive-grade advisory value, method, fit and distinct access."""
    member_signed_in = st.session_state.get("advisory_member") is True
    invitation = ("Continue your advisory conversation." if member_signed_in
                  else "Submit a decision for pro-bono review.")
    cta = ("Open my advisory space →" if member_signed_in
           else "Register free to submit a request →")
    invitation_text = (
        "Your private conversation, requests and next steps are available in your "
        "Advisory account. The Premium Reader library remains included."
        if member_signed_in
        else "Register free to describe the AI or data decision you are facing. "
        "I review requests individually and may offer a focused pro-bono discussion "
        "where a senior external perspective could help. There is no charge, "
        "but availability is limited and registration does not guarantee a session."
    )

    # A repository-backed, optimized WebP; committed as plain base64 text so
    # it can be delivered reliably through the managed code connection.
    try:
        encoded_photo = (IMAGE_DIR / "advisory-portrait.webp.b64").read_text(encoding="ascii").strip()
        photo = "data:image/webp;base64," + encoded_photo if encoded_photo.startswith("UklGR") else ""
    except OSError:
        photo = ""
    portrait = (
        f'<img src="{photo}" alt="Jair Ribeiro in a relaxed professional portrait beside a stack of books" '
        'loading="lazy" decoding="async" width="540" height="540">'
        if photo else ""
    )
    return f'''{SERVICES_CSS}{nav("advisory")}
<main class="advisory-page">
<section class="advisory-hero" aria-labelledby="advisory-title">
 <div class="container advisory-hero-grid">
  <div>
   <p class="service-eyebrow">Selective pro-bono executive advisory / AI &amp; Data</p>
   <h1 id="advisory-title">Better AI decisions. Clearer ownership. Measurable business value.</h1>
   <p class="service-lede">For leaders facing decisions on AI investment, governance, adoption or operating ownership. I consider a limited number of focused pro-bono discussions to examine options, trade-offs and a practical next step.</p>
   <div class="advisory-actions">
    <a class="advisory-button" href="#advisory-focus" data-hq-event="advisory_explore_value">See where I can help →</a>
    <a class="advisory-button advisory-button--outline" href="#advisory-contact" data-hq-event="advisory_email_primary">Discuss a decision →</a>
   </div>
   <div class="advisory-proofline" aria-label="Advisory disciplines"><span>Portfolio judgement</span><span>AI &amp; data governance</span><span>Operating model</span><span>Adoption &amp; value</span></div>
  </div>
  <aside class="advisory-aside" aria-label="Advisory principle">
   <small>Executive judgement</small>
   <blockquote>What should the business decide, own and measure differently?</blockquote>
   <p>The technology matters. The business case, decision rights and evidence for change determine whether it earns a place in operations.</p>
  </aside>
 </div>
</section>

<section class="service-section service-section--white" id="advisory-focus" data-analytics-section="advisory-focus">
 <div class="container">
  <p class="service-eyebrow">Where I contribute</p>
  <div class="service-section-header"><h2>The decisions between AI ambition and business results.</h2>
   <p>I work at the intersection of strategy, governance, data, Lean and the way people actually work. The aim is not to produce more AI activity; it is to improve the quality of the decisions that determine value.</p>
  </div>
  <div class="service-grid">
   <article class="service-card"><span>01 / Investment judgement</span><h3>Which AI bets deserve capital?</h3><p>Challenge the portfolio against value, feasibility, reuse, cost and risk. Identify what to stop, test further, consolidate or prepare to scale—before another pilot becomes a permanent commitment.</p></article>
   <article class="service-card"><span>02 / Operating accountability</span><h3>Who owns the result?</h3><p>Set useful decision rights, business ownership and CoE responsibilities. Clarify how priorities are approved, how exceptions move, and where accountability sits after delivery.</p></article>
   <article class="service-card"><span>03 / Adoption and business change</span><h3>What will change in the work?</h3><p>Connect AI to process design, people, confidence and incentives. Measure changed workflows, decision quality and operational outcomes—not just licences, attendance or tool launches.</p></article>
   <article class="service-card"><span>04 / Trustworthy scale</span><h3>What conditions make scale credible?</h3><p>Examine data ownership and quality, AI controls, lifecycle evidence, stewardship and regulation. Make governance proportional to the business risk, without losing the ability to act.</p></article>
  </div>
 </div>
</section>

<section class="service-section" id="advisory-outcomes" data-analytics-section="advisory-outcomes">
 <div class="container">
  <p class="service-eyebrow">What the business should gain</p>
  <div class="service-section-header"><h2>Clarity you can take into the next decision.</h2>
   <p>Where a request is selected, the value should be a clearer decision: options, ownership and an evidence-based next step that can be used in a leadership discussion. Scope depends on the question and available information.</p>
  </div>
  <div class="advisory-results">
   <article class="advisory-result"><strong>A defensible decision</strong><p>Options, trade-offs, assumptions and a recommendation that makes the cost of action—and inaction—visible.</p></article>
   <article class="advisory-result"><strong>Named accountability</strong><p>Decision owners, milestones, governance boundaries and the dependencies that must be resolved.</p></article>
   <article class="advisory-result"><strong>A way to test value</strong><p>Business measures, evidence thresholds and a practical next step for stop, adapt, prove or scale.</p></article>
  </div>
 </div>
</section>

<section class="service-section service-section--ink" id="advisory-engagements" data-analytics-section="advisory-engagements">
 <div class="container">
  <p class="service-eyebrow">Ways of working</p>
  <div class="service-section-header"><h2>The right level of involvement for the decision.</h2>
   <p>I consider short decision reviews and defined working discussions on a selective, pro-bono basis. Fit, available time and the question to be examined determine what is possible.</p>
  </div>
  <div class="service-formats">
   <article class="service-format"><small>01 / Independent assessment</small><h3>Decision review</h3><p>Challenge a strategy, AI business case, investment portfolio or governance proposal. Typical result: a concise assessment of options, assumptions, risks and the recommended next decision.</p></article>
   <article class="service-format"><small>02 / Leadership working engagement</small><h3>Executive working sessions</h3><p>Work with sponsors and accountable leaders to define priorities, decision rights, operating measures and a practical route forward. Typical result: a decision record and agreed actions.</p></article>
   <article class="service-format"><small>03 / Selective follow-up</small><h3>Next-step review</h3><p>Where useful, revisit the decision record, remaining evidence gaps and named owners after an initial discussion. Follow-up is limited to the agreed question, not ongoing consulting support.</p></article>
  </div>
  <div class="advisory-tool-reference" data-analytics-section="advisory-scorecard">
   <div>
    <small>First on-demand advisory resource · Individual approval</small>
    <strong>AI Portfolio Prioritization Scorecard</strong>
    <p>Compare AI initiatives against value, capacity, readiness and control conditions. The private workspace is free for clients individually approved within a pro-bono Advisory engagement. Registration alone does not provide access.</p>
   </div>
   <a href="?page=advisory-scorecard" target="_self" data-hq-event="advisory_scorecard_service">Explore the service →</a>
  </div>
  <div class="advisory-tool-reference" data-analytics-section="advisory-rollout">
   <div>
    <small>Executive AI Decision Advisor · Individual approval</small>
    <strong>Enterprise AI Rollout Readiness Advisor</strong>
    <p>A focused, one-session assessment of business value, operational readiness, governance, adoption and scaling capability. Receive a clear executive verdict, its reasoning and three priority actions. Free for individually approved Advisory clients.</p>
   </div>
   <a href="?page=advisory-rollout" target="_self" data-hq-event="advisory_rollout_service">Explore the service →</a>
  </div>
 </div>
</section>

<section class="service-section service-section--white" id="advisory-method" data-analytics-section="advisory-method">
 <div class="container">
  <p class="service-eyebrow">The method</p>
  <div class="service-section-header"><h2>From executive question to an owned next move.</h2>
   <p>The method is deliberately simple. It draws on enterprise portfolio management, Lean, evidence-based prioritisation, risk controls and experience of the organisational realities behind AI adoption.</p>
  </div>
  <div class="service-steps">
   <div class="service-step"><span>01</span><h3>Frame the decision</h3><p>Business outcome, sponsor, affected process, constraints and the cost of doing nothing.</p></div>
   <div class="service-step"><span>02</span><h3>Examine the evidence</h3><p>Current state, value case, data readiness, process friction, risk, stakeholders and missing facts.</p></div>
   <div class="service-step"><span>03</span><h3>Challenge the options</h3><p>What to stop, rework, test or scale; consequences, ownership and proportional controls.</p></div>
   <div class="service-step"><span>04</span><h3>Agree action and proof</h3><p>Decision record, named owners, next milestone and measures for checking whether it worked.</p></div>
  </div>
  <p class="service-method-note">I assess each request for relevance and available time. If selected, we agree the question, information boundaries and a focused next step. Pro-bono discussions are free of charge; registration alone does not confirm an engagement.</p>
 </div>
</section>

<section class="service-section" id="advisory-perspective" data-analytics-section="advisory-credibility">
 <div class="container advisory-personal">
  <figure class="advisory-portrait">{portrait}<figcaption>Jair Ribeiro · Enterprise AI &amp; Data leadership</figcaption></figure>
  <div>
   <p class="service-eyebrow">The person behind the advice</p>
   <h2>Experience from inside the decisions, not outside the business.</h2>
   <p>I have worked across enterprise AI, analytics and data leadership, often in the uncomfortable space between an attractive idea and the realities of funding, governance, ownership and adoption.</p>
   <p>I have built portfolio views to help leaders prioritise, challenged whether pilots were ready to scale, shaped governance and stewardship, and worked with business teams to make new capabilities useful in day-to-day operations.</p>
   <p>That experience shapes my approach: listen to the people accountable for the result, examine what the evidence supports, and make the next decision clearer. I don't offer a substitute for engineering delivery or legal advice.</p>
   <p class="advisory-signoff">Jair Ribeiro / Independent executive perspective</p>
   <p><a href="?page=impact" target="_self">Explore my leadership experience →</a> &nbsp; <a href="?page=thinking" target="_self">Read my perspectives →</a></p>
  </div>
 </div>
</section>

<section class="advisory-access" id="advisory-membership" data-analytics-section="advisory-membership">
 <div class="container advisory-access-grid">
  <div>
   <p class="service-eyebrow">Your next step</p>
   <h2>{invitation}</h2>
   <p>{invitation_text}</p>
   <div class="advisory-actions">
    <a class="advisory-button" href="?page=advisory-access" target="_self" data-hq-event="advisory_access_register">{cta}</a>
   </div>
   <a class="advisory-small-link" href="?page=advisory-access&amp;signin=1" target="_self" data-hq-event="advisory_access_signin">Already have an account? Sign in</a>
  </div>
  <aside class="advisory-access-inclusion" aria-label="Included access and direct contact">
   <strong>The Executive AI Reader Library is also free.</strong>
   <p>Register separately or use your verified account to read complete briefings, current articles and Weekly AI, with available infographic downloads. No advisory request is needed.</p>
   <div class="advisory-access-direct" id="advisory-contact" data-analytics-section="advisory-inquiry">
    <span>Prefer a direct introduction?</span>
    <p>Tell me what decision you are facing, who owns it and when it matters. No confidential details are needed.</p>
    <a href="mailto:{ADVISORY_EMAIL}?subject=Executive%20advisory%20discussion" data-hq-event="advisory_email_final">Email {ADVISORY_EMAIL} →</a>
   </div>
  </aside>
 </div>
</section>
</main>{footer()}'''

def privacy() -> str:
    """Public privacy notice for portfolio visitors and registered readers."""
    return f'''{SERVICES_CSS}{nav("privacy")}
<main class="privacy-page">
<section class="privacy-hero"><div class="container">
 <p class="service-eyebrow">Transparency / Reader trust</p>
 <h1>Privacy &amp; data.</h1>
 <p>What information this portfolio handles, why it is used, and how to make a request. Access to the Premium Reader library does not require agreeing to marketing messages.</p>
 <p class="privacy-effective">Last updated: 14 November 2026</p>
</div></section>
<div class="container privacy-body">
 <nav class="privacy-toc" aria-label="Privacy notice sections">
  <strong>In this notice</strong>
  <a href="#privacy-controller">Who is responsible</a>
  <a href="#privacy-collection">Information collected</a>
  <a href="#privacy-purpose">Purposes and legal grounds</a>
  <a href="#privacy-providers">Providers and transfers</a>
  <a href="#privacy-storage">Storage and retention</a>
  <a href="#privacy-rights">Your rights</a>
  <a href="#privacy-contact">Contact</a>
 </nav>
 <div class="privacy-content">
  <section id="privacy-controller"><h2>Who is responsible</h2>
   <p>This professional portfolio, its Premium Reader service and its separate Advisory registration are operated by Jair Ribeiro, based in Gothenburg, Sweden. For requests about personal information processed through this site, contact <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
  </section>
  <section id="privacy-collection"><h2>What information may be collected</h2>
   <ul>
    <li><strong>Website visits:</strong> page views, on-site interactions, source or campaign attribution, approximate session duration, broad browser or device characteristics and related operational information.</li>
    <li><strong>Premium Reader accounts:</strong> the name and email you provide, verification and account status, optional profile or editorial interests, subscription preference, and records needed to show your reading or PDF-download history.</li>
    <li><strong>Advisory accounts:</strong> your verified professional email, first and last name, role or title, organization and a short description of your business decision or objective. You may also provide your advisory focus and expected decision timeframe. If you submit an advisory request, the service stores your stated business objective, context, requested next step, private conversation, response history, request stage and follow-up dates. Account and engagement status support the dedicated service. Advisory registration also grants Reader library access; Reader registration does not automatically create Advisory access.</li>
    <li><strong>Approved AI Portfolio Scorecard workspaces:</strong> for clients individually approved for this pro-bono Advisory service, the system stores initiative names, business roles, evidence scores, capacity and cost estimates, control conditions, decision records, workspace revisions, and approval and access audit events. The advisor can review workspace information during the engagement. Clients may view only their own active, authorized workspace; registration alone does not provide access. Do not enter confidential business data, personal records or protected information without a separate handling agreement.</li>
    <li><strong>Correspondence:</strong> the email address and information you choose to share when contacting me, including advisory and privacy requests.</li>
    <li><strong>Service security:</strong> technical events and connection details that may be processed by hosting or authentication providers to operate and protect the service.</li>
   </ul>
   <p>No payment details are requested for free Reader Library registration, and reader contact details are not sold. Avoid placing confidential or sensitive personal information in an initial inquiry.</p>
  </section>
  <section id="privacy-purpose"><h2>Why information is used</h2>
   <ul>
    <li><strong>Reader and Advisory account access:</strong> to establish and maintain a requested account, verify identity and deliver access to content you requested. The legal basis is the provision of a requested service and, where applicable, the legitimate interest in keeping your account secure.</li>
    <li><strong>Service measurement:</strong> to understand which pages and publications are useful, how visitors reach them and where the website needs attention. First-party site measurement is carried out for the legitimate interest of maintaining and improving the portfolio, subject to applicable rights.</li>
    <li><strong>Advisory context and correspondence:</strong> to retain the business context you choose to share, review your request, maintain the private response thread, record agreed next steps and manage an actual advisory relationship where one develops. The legal basis is legitimate interest in responding and, when relevant, steps requested before a possible agreement.</li>
    <li><strong>Approved Scorecard workspaces:</strong> to provide the on-demand evaluation tool, record its individual approval, preserve work between sessions, and control or revoke access. These records are associated with the agreed pro-bono Advisory request and handled to provide that requested service and maintain accountable access.</li>
    <li><strong>Optional editorial emails:</strong> based on your separate, optional consent. You can withdraw that choice through your reader preferences or by contacting <a href="mailto:{READERS_EMAIL}">{READERS_EMAIL}</a>.</li>
    <li><strong>Security and legal duties:</strong> where necessary for legitimate security interests or to comply with legal obligations.</li>
   </ul>
   <p>Creating a reader account does not itself subscribe you to editorial messages. Site activity is not used to make decisions with legal or comparably significant effects about you.</p>
  </section>
  <section id="privacy-providers"><h2>Service providers and external destinations</h2>
   <p>The portfolio is hosted through Streamlit, and the Premium Reader and Advisory account services and first-party reporting use Supabase. Authentication and verification messages depend on the configured authentication email service. These providers may handle information needed to operate the relevant function under their own contractual and technical arrangements.</p>
   <p>Links to LinkedIn and other external websites take you to services with their own privacy practices. A branded or masked domain may also involve the domain or forwarding provider. Depending on the provider and configuration, personal data may be processed outside Sweden or the European Economic Area; you can request details of the arrangements relevant to your data through <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
  </section>
  <section id="privacy-storage"><h2>Session data, cookies and retention</h2>
   <p>The first-party portfolio analytics uses browser session storage for short-lived visit and attribution context rather than an analytics cookie intended to identify you across visits. Account access and hosting can use technically necessary cookies, security tokens and server-side records. The site's first-party analytics is not an advertising tracking service.</p>
   <p>Reader, Advisory account, approved Scorecard and reading records are held while needed for the respective services and to support access, correction or deletion requests, subject to applicable legal or security needs. Correspondence is kept as needed to handle the inquiry or any resulting relationship. Measurement and security records are retained according to their operational purpose and applicable service settings; there is not one universal retention period for every record. You can ask about the status or removal of your information.</p>
  </section>
  <section id="privacy-rights"><h2>Your choices and rights</h2>
   <p>Subject to applicable conditions, you may request access, correction, erasure, restriction, portability or object to certain processing. Where processing relies on consent, you may withdraw that consent without affecting earlier lawful processing.</p>
   <p>You may use the reader account area to update your editorial email choice, and the advisory account area to update professional context. To request data access, correction, export or account deletion, email <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>. Identity verification may be needed before releasing or deleting account data.</p>
   <p>You may also lodge a complaint with the Swedish Authority for Privacy Protection (<a href="https://www.imy.se/en/individuals/data-protection/your-rights-as-a-data-subject/" target="_blank" rel="noopener noreferrer">Integritetsskyddsmyndigheten, IMY</a>) or another competent data-protection authority.</p>
  </section>
  <section id="privacy-contact"><h2>Questions or a data request?</h2>
   <div class="privacy-contact"><strong>Privacy and personal-data requests</strong><a href="mailto:{PRIVACY_EMAIL}" data-hq-event="privacy_email">{PRIVACY_EMAIL}</a><span>For reader access questions, use <a href="mailto:{READERS_EMAIL}">{READERS_EMAIL}</a>.</span></div>
   <p>When the service or its data practices change materially, this notice will be updated with a revised date.</p>
  </section>
 </div>
</div>
</main>{footer()}'''
