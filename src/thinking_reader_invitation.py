"""Executive-grade invitation to the unified complimentary reader library.

A static, accessible section on the Thinking landing page. Explains the
distinct Article, Briefing and account benefits without confusing the public
archive with registered early access or making a paid-subscription claim.
"""
from __future__ import annotations


READER_INVITATION_CSS = r"""<style>
.site .thinking-reader-invite{background:#f0ece4;padding:clamp(64px,7vw,105px) 0;border-top:1px solid #e1d9cd;border-bottom:1px solid #ddd2c5}
.site .thinking-reader-invite .container{max-width:1180px}
.site .thinking-reader-kicker{display:block;color:#aa6039;font:800 11px/1.5 Arial,sans-serif;text-transform:uppercase;letter-spacing:.15em;margin:0 0 17px}
.site .thinking-reader-intro{display:grid;grid-template-columns:minmax(0,1.24fr) minmax(250px,.76fr);align-items:start;gap:clamp(26px,5.5vw,90px)}
.site .thinking-reader-intro h2{max-width:760px;margin:0;color:#152d40;font:450 clamp(35px,4.15vw,53px)/1.12 Georgia,serif;letter-spacing:-.028em;text-wrap:balance}
.site .thinking-reader-intro>p{margin:8px 0 0;max-width:410px;color:#435565;font:400 clamp(15px,1.4vw,17px)/1.75 Arial,sans-serif}
.site .thinking-reader-benefits{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;margin:42px 0 0;border-top:1px solid #cec4b8;border-bottom:1px solid #cec4b8}
.site .thinking-reader-benefit{box-sizing:border-box;min-width:0;padding:29px clamp(16px,2.7vw,31px) 31px 0}
.site .thinking-reader-benefit+.thinking-reader-benefit{border-left:1px solid #d8cbbf;padding-left:clamp(16px,2.7vw,31px)}
.site .thinking-reader-benefit span{display:block;margin-bottom:18px;color:#a35e3b;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase}
.site .thinking-reader-benefit h3{font:450 clamp(23px,2.25vw,29px)/1.2 Georgia,serif;color:#152d40;margin:0 0 13px;text-wrap:balance}
.site .thinking-reader-benefit p{font:400 14px/1.72 Arial,sans-serif;color:#4a5a65;margin:0}
.site .thinking-reader-actionline{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:20px 32px;margin-top:29px}
.site .thinking-reader-actionline p{max-width:680px;margin:0;color:#4c5b65;font:400 13px/1.65 Arial,sans-serif}
.site .thinking-reader-actions{display:flex;flex-wrap:wrap;align-items:center;gap:11px}
.site .thinking-reader-actions a{box-sizing:border-box;display:inline-flex;min-height:46px;align-items:center;justify-content:center;padding:12px 18px;border:1px solid #17374a;font:750 12px/1.4 Arial,sans-serif;text-decoration:none!important;text-align:center}
.site .thinking-reader-actions a:first-child{background:#15374c;color:#fff!important}
.site .thinking-reader-actions a:first-child:hover{background:#254c61}
.site .thinking-reader-actions a:last-child{color:#15374c!important;background:transparent}
.site .thinking-reader-actions a:last-child:hover{background:#e2dacf}
.site .thinking-reader-steps{margin-top:27px;padding:18px 0 0;background:transparent;border-top:1px solid #cec4b8}
.site .thinking-reader-steps strong{display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#955735;margin-bottom:7px}
.site .thinking-reader-steps p{max-width:880px;margin:0;color:#596570;font:400 12px/1.65 Arial,sans-serif}
@media(max-width:920px){.site .thinking-reader-intro{grid-template-columns:1fr;gap:13px}.site .thinking-reader-intro>p{max-width:810px}.site .thinking-reader-actionline{grid-template-columns:1fr}}
@media(max-width:700px){.site .thinking-reader-invite{padding:50px 0 57px}.site .thinking-reader-benefits{grid-template-columns:1fr;margin-top:30px}.site .thinking-reader-benefit{padding:22px 0!important}.site .thinking-reader-benefit+.thinking-reader-benefit{border-left:0;border-top:1px solid #d8cbbf}.site .thinking-reader-actions{width:100%}.site .thinking-reader-actions a{width:100%}.site .thinking-reader-steps{padding:17px 0 0}}
</style>"""


def reader_invitation() -> str:
    """Visible for every visitor, independent of authentication or CMS latency."""
    return READER_INVITATION_CSS + """<section class="thinking-reader-invite" id="premium-reader-library"
        data-analytics-section="thinking-premium-reader-library" aria-labelledby="thinking-reader-heading">
      <div class="container">
        <span class="thinking-reader-kicker">Premium Reader library · Complimentary access</span>
        <div class="thinking-reader-intro">
          <h2 id="thinking-reader-heading">Go beyond the headline. Examine the decision.</h2>
          <p>A short summary tells you what a piece is about. The full edition
          explores the reasoning: what is at stake, which assumptions to challenge,
          and what leaders need to consider before acting. That is the purpose
          of this library.</p>
        </div>
        <div class="thinking-reader-benefits">
          <article class="thinking-reader-benefit">
            <span>Executive AI Briefings</span>
            <h3>Bring better questions to the table.</h3>
            <p>Examine choices about investment, governance and adoption through
            complete briefings, decision frameworks and original infographics
            where available.</p>
          </article>
          <article class="thinking-reader-benefit">
            <span>Weekly AI</span>
            <h3>See what deserves your attention.</h3>
            <p>A considered selection of AI developments, why they matter for
            business and the original reporting behind them. Listen to the
            narrated edition when available.</p>
          </article>
          <article class="thinking-reader-benefit">
            <span>Leadership articles</span>
            <h3>Understand the thinking behind the position.</h3>
            <p>Go deeper into prioritization, accountability, governance,
            adoption and business value, including the trade-offs and practical
            questions that rarely fit in a summary.</p>
          </article>
        </div>
        <div class="thinking-reader-actionline">
          <p><strong>Premium Reader access is currently complimentary.</strong>
          One account gives you the full reading experience across all three
          formats. Save useful briefings, return to available PDFs and manage
          your profile in My Library. No payment details; editorial emails
          are optional.</p>
          <div class="thinking-reader-actions">
            <a href="?page=readers" target="_self" data-hq-event="thinking_premium_reader_access">Access the reader library</a>
            <a href="?page=briefings" target="_self" data-hq-event="thinking_premium_reader_explore">Browse the briefings</a>
          </div>
        </div>
        <div class="thinking-reader-steps">
          <strong>Access at a glance</strong>
          <p>Explore public summaries before deciding what deserves a closer read.
          Your complimentary Premium Reader account opens complete Executive AI
          Briefings, Premium Articles and the latest Weekly AI edition.
          Open-access editions remain available to everyone.</p>
        </div>
      </div>
    </section>"""
