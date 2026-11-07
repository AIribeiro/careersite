from __future__ import annotations

"""Decision-first Executive AI Briefings, with original graphical artwork.

Only published Content Studio records are presented as published briefings.
Original article bodies, citations and attribution remain available on demand.
"""

import base64
import re
from html import escape
from functools import lru_cache
from pathlib import Path

from briefings_visual import PROMO_CSS, briefing_icon, briefing_visual
from site_assets import EMAIL
from site_components import nav, footer, journey_next
from site_cms import fetch_published_articles, article_relative_url

BRIEFING_KIND = "Executive Briefing"
FIRST_SLUG = "ai-capabilities-executive-decisions"
GOVERNANCE_SLUG = "ai-governance-explained-to-executives"
AI_ACT_SLUG = "eu-ai-act-what-executives-must-decide"
FUNDING_SLUG = "data-governance-what-deserves-funding"
DUAL_GOV_SLUG = "data-governance-vs-ai-governance-executive-decisions"
SECURITY_SLUG = "secure-enterprise-ai-ten-failures-to-control"
ADOPTION_SLUG = "ai-adoption-four-leadership-responses"

# Capability categories are complementary tools, not a ladder of sophistication.
CAPABILITIES = (
    ("Predict", "Pattern-based estimates", "What forecast changes a business decision?", "chart"),
    ("Interpret", "Signals and context", "Which complex inputs need to be understood?", "search"),
    ("Generate", "Content and language", "Which work requires a draft, not a final decision?", "spark"),
    ("Ground", "Enterprise knowledge", "Which trusted sources must support the answer?", "layers"),
    ("Act", "Permitted actions", "What may the system do without another approval?", "workflow"),
    ("Govern", "Accountable use", "Who owns the outcome, controls and evidence?", "shield"),
)

# This editorial synopsis is specific to the first briefing. Unpublished future
# briefings receive a neutral fallback and never inherit this issue's claims.
FIRST_DECISION = {
    "call": "Start with the decision, not the model.",
    "move": "Select one business process, define the outcome to improve and name the owner before choosing an AI capability.",
    "checks": (
        ("Business outcome", "What will improve in cost, quality, speed or productivity?", "target"),
        ("Permission to act", "Is AI informing, recommending or executing—and who approves?", "shield"),
        ("Evidence of value", "How will changed work and its results be measured?", "chart"),
    ),
}

GOVERNANCE_DECISION = {
    "call": "Govern the business decision, not only the AI model.",
    "move": "Pick one real workflow, name its business owner, verify the data it depends on, define what AI may do and set a review gate before scaling.",
    "checks": (
        ("Trusted information", "Who owns the definitions, quality, access and provenance of the data this use case needs?", "layers"),
        ("Decision rights", "Who approves the use case, its risk, exceptions and any action taken by AI?", "users"),
        ("Operating controls", "Which tests, monitoring, human reviews and stop rules make this system accountable?", "shield"),
    ),
}



ADOPTION_DECISION = {
    "call": "Diagnose the barrier before prescribing the intervention.",
    "move": "Choose one approved workflow, assess task-specific capability and willingness, check operating conditions, and measure work outcomes after differentiated support.",
    "checks": (
        ("Capability", "Can people apply AI safely and judge its output on a real task?", "chart"),
        ("Willingness", "What concern, uncertainty or incentive shapes readiness to try this use case?", "users"),
        ("Work readiness", "Are task fit, data access, permission and manager support in place?", "shield"),
        ("Evidence", "What changed in quality, time, rework and risk beyond tool usage?", "target"),
    ),
}

SECURITY_DECISION = {
    "call": "Grant only the authority the evidence supports.",
    "move": "Select a real workflow. Demonstrate information permissions, permitted actions, failure tests, traceability and an effective stop mechanism before expanding authority.",
    "checks": (
        ("Information trust", "Can untrusted material redirect the AI, expose sensitive data or bypass user access?", "layers"),
        ("Bounded authority", "Which tools, transactions and costs can the AI incur without human approval?", "shield"),
        ("Behavioral assurance", "What evaluation and change evidence shows that answers remain fit for the task?", "chart"),
        ("Operating accountability", "Who can reconstruct, restrict and stop the workflow when something goes wrong?", "users"),
    ),
}

AI_ACT_DECISION = {
    "call": "Classify the use, then decide the controls.",
    "move": "Take one live or proposed AI use case. Record its intended purpose, your role, the relevant legal duties, a named owner and the evidence required before approval.",
    "checks": (
        ("Intended purpose", "What does the system actually do, to whom and in which decision?", "target"),
        ("Legal position", "Is this use prohibited, high-risk, subject to disclosure or subject to other duties?", "shield"),
        ("Accountable evidence", "Who owns the use, vendor controls, records and oversight?", "layers"),
    ),
}

# Original executive governance architecture: seven concurrent control surfaces,
# not a redraw or a maturity sequence borrowed from a reference illustration.
GOVERNANCE_LAYERS = (
    ("01", "Trusted information",
     "Can we rely on the information behind this decision?",
     "Check the sources, shared definitions, quality and who can access them.",
     "Data owner · source list · quality check", "layers", "foundation"),
    ("02", "Business ownership",
     "Who is accountable for the business result?",
     "Name the process owner and system operator, including who handles failures.",
     "Process owner · operator · escalation contact", "users", "foundation"),
    ("03", "Decision authority",
     "Who may approve, change or stop this use?",
     "Set approval rights for launch, exceptions and increases in AI autonomy.",
     "Approval record · change gate · stop authority", "target", "decisions"),
    ("04", "Working rules",
     "What are people and AI allowed to do?",
     "Put access limits, human checks and exception handling into daily work.",
     "Usage rules · access permissions · exception route", "check", "decisions"),
    ("05", "Risk and obligations",
     "What could go wrong, and which legal duties apply?",
     "Assess customer harm, privacy, security and legal exposure for this use case.",
     "Risk assessment · legal check · response owner", "shield", "decisions"),
    ("06", "Testing and monitoring",
     "How do we know it works and stays reliable?",
     "Test representative cases and failures; monitor quality and incidents after release.",
     "Test results · quality thresholds · incident process", "chart", "execution"),
    ("07", "Permission to act",
     "What can AI execute without another approval?",
     "Limit tool access and transactions; log actions and test the stop mechanism.",
     "Action limits · approval triggers · stop test", "workflow", "execution"),
)

GOVERNANCE_RECORD_FIELDS = (
    ("01", "Business outcome", "Target result and today's baseline for cost, quality or speed."),
    ("02", "Accountable owner", "One named business owner, plus the system operator."),
    ("03", "AI authority", "May it read, recommend, prepare or execute? Where is approval required?"),
    ("04", "Risk and controls", "Most consequential failure, access limits, human checks and recovery."),
    ("05", "Evidence of readiness", "Relevant tests, success threshold, monitoring and adoption evidence."),
    ("06", "Decision and next review", "Proceed, hold or stop; approver, deadline and review trigger."),
)

BRIEFINGS_CSS = r'''<style>
.site .briefings-index{font:800 10px/1.45 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#ac663e}
.site .briefings-hero{padding:65px 0 63px}
.site .briefings-hero h1{max-width:940px;font-size:clamp(42px,5.4vw,68px)}
.site .briefings-hero .briefings-deck{max-width:790px;color:#cbd3dd;font-size:17px;line-height:1.6;margin:22px 0 0}
.site .briefings-principles{display:flex;gap:9px;flex-wrap:wrap;margin-top:26px}
.site .briefings-principles span{font:750 11px/1.4 Arial,sans-serif;color:#ecd9ca;border:1px solid rgba(237,190,153,.4);padding:8px 12px}
.site .briefings-overview{padding:50px 0 54px}
.site .briefings-lead{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(300px,.8fr);gap:18px;align-items:stretch}
.site .briefings-feature{min-width:0;background:#13253a;color:#fff;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 18px 40px rgba(14,27,41,.12)}
.site .briefings-feature-art{height:216px;overflow:hidden;border-bottom:1px solid rgba(235,190,149,.22)}
.site .briefings-feature-art .briefing-visual{display:block;width:100%;height:100%;object-fit:cover}
.site .briefings-feature-content{padding:30px 35px 34px;display:flex;flex-direction:column;flex:1}
.site .briefings-feature .briefings-index{color:#e3b58e}
.site .briefings-feature h2{font:500 clamp(28px,3.4vw,39px)/1.11 Georgia,serif;letter-spacing:-.025em;margin:15px 0}
.site .briefings-feature p{font-size:14px;line-height:1.65;color:#c8d3dd;max-width:660px;margin:0 0 20px}
.site .briefings-feature .briefings-read{margin-top:auto;display:inline-flex;align-self:flex-start;align-items:center;min-height:43px;padding:11px 17px;background:#e8bd99;color:#152335!important;text-decoration:none!important;font-size:12px;font-weight:850}
.site .briefings-feature .briefings-read:hover,.site .briefings-feature .briefings-read:focus-visible{background:#fff1e4}
.site .briefings-feature .briefings-date{font-size:11px;color:#aebdcb;margin:16px 0 0}
.site .briefings-method{padding:33px 31px;background:#eae2d7;border:1px solid rgba(17,21,27,.13)}
.site .briefings-method h3{font:500 clamp(26px,3vw,34px)/1.17 Georgia,serif;margin:11px 0 22px}
.site .briefings-method p{font-size:14px;line-height:1.66;color:#525b64;margin:0}
.site .briefings-method-row{display:grid;grid-template-columns:35px 1fr;gap:14px;padding:15px 0;border-top:1px solid #cec3b4;align-items:start}
.site .briefings-method-row .briefing-icon{width:26px;height:26px;color:#98613f}
.site .briefings-method-row strong{display:block;font-size:13px;color:#253346}
.site .briefings-method-row p{font-size:12px;line-height:1.55;margin:5px 0 0}
.site .briefings-method-contact{display:inline-flex;margin-top:22px;text-decoration:none!important;border-bottom:1px solid #a86741;padding-bottom:6px;color:#283342!important;font-size:12px;font-weight:850}
.site .briefings-map-intro{display:flex;align-items:end;justify-content:space-between;gap:28px;margin-bottom:25px}
.site .briefings-map-intro h2{max-width:700px;font:500 clamp(31px,4vw,45px)/1.12 Georgia,serif;margin:9px 0 0}
.site .briefings-map-intro>p{max-width:375px;font-size:14px;line-height:1.65;color:var(--muted);margin:0}
.site .briefings-map{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.site .briefings-capability{min-width:0;display:grid;grid-template-columns:31px 1fr;gap:13px;padding:21px;background:#fffdf8;border:1px solid var(--line);min-height:150px}
.site .briefings-capability .briefing-icon{color:#aa6944;margin-top:4px}
.site .briefings-capability span{font:800 9px/1.5 Arial,sans-serif;letter-spacing:.11em;text-transform:uppercase;color:#aa6944}
.site .briefings-capability h3{font:500 23px/1.15 Georgia,serif;margin:4px 0 8px}
.site .briefings-capability p{font-size:12px;line-height:1.58;color:#58616b;margin:0}
.site .briefings-note{margin:21px 0 0;font-size:12px;line-height:1.65;color:var(--muted);max-width:950px}
.site .briefings-others{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.site .briefings-other{display:flex;flex-direction:column;gap:10px;padding:26px;background:#fffdf8;border:1px solid var(--line);text-decoration:none!important}
.site .briefings-other h3{margin:0;font:500 26px/1.18 Georgia,serif}
.site .briefings-other p{color:var(--muted);font-size:13px;line-height:1.55;margin:0}
.site .briefings-other span{font-size:10px;color:#965633;font-weight:800}
.site .briefings-questions-feature{grid-column:1/-1;position:relative;overflow:hidden;isolation:isolate;min-height:228px;border:1px solid #385367;border-top:3px solid #c58c66;padding:32px 36px;background:linear-gradient(117deg,#101f32,#1a3d50);color:#fff;align-items:flex-start;justify-content:center}
.site .briefings-questions-feature:before{content:"?";position:absolute;z-index:-1;right:9%;top:-25px;font:500 260px/1 Georgia,serif;color:rgba(221,179,144,.17)}
.site .briefings-questions-feature:after{content:"";position:absolute;right:3%;bottom:-50%;width:37%;aspect-ratio:1;border:1px solid rgba(226,185,146,.25);border-radius:50%;box-shadow:0 0 0 28px rgba(226,185,146,.04),0 0 0 60px rgba(226,185,146,.03);pointer-events:none}
.site .briefings-questions-feature span{color:#e7b793}
.site .briefings-questions-feature h3{font:500 clamp(28px,3vw,39px)/1.13 Georgia,serif;color:#fff;max-width:65%;margin:6px 0}
.site .briefings-questions-feature p{max-width:65%;font-size:14px;line-height:1.6;color:#cbd6df}
.site .briefings-questions-feature:hover,.site .briefings-questions-feature:focus-visible{border-color:#d7a47c}
@media(max-width:650px){.site .briefings-questions-feature{min-height:220px;padding:26px}.site .briefings-questions-feature h3,.site .briefings-questions-feature p{max-width:87%}.site .briefings-questions-feature:before{right:-9%;top:0;font-size:210px}}

.site .briefings-conversation{background:#102238;color:#fff;padding:48px 0}
.site .briefings-conversation-inner{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:30px;align-items:center}
.site .briefings-conversation .briefings-index{color:#e6ba98}
.site .briefings-conversation h2{font:500 clamp(31px,3.8vw,45px)/1.14 Georgia,serif;margin:10px 0}
.site .briefings-conversation p{color:#c3d0dc;line-height:1.65;font-size:14px;max-width:780px;margin:0}
.site .briefings-conversation-actions{display:flex;gap:10px;flex-wrap:wrap}
.site .briefings-conversation-actions a{display:inline-flex;align-items:center;min-height:45px;padding:12px 16px;color:#102238!important;background:#e6ba98;text-decoration:none!important;font-size:12px;font-weight:850}
.site .briefings-conversation-actions a:last-child{color:#fff!important;background:transparent;border:1px solid #8ea0b1}
.site .briefings-home-strip{background:#ede3d5;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:30px 0}
.site .briefings-home-inner{display:flex;justify-content:space-between;align-items:center;gap:28px}
.site .briefings-home-inner h2{font:500 25px/1.18 Georgia,serif;margin:6px 0 7px}
.site .briefings-home-inner p{font-size:13px;line-height:1.65;color:#535b64;margin:0}
.site .briefings-home-inner>a{flex:0 0 auto;font-size:12px;font-weight:750;text-decoration:none;border-bottom:1px solid var(--copper);padding:10px 0}
.site .briefing-reader-hero{padding:47px 0 41px;background:#102238;color:#fff}
.site .briefing-reader-hero .briefing-reader-back{display:inline-block;margin:0 0 22px;text-decoration:none!important;color:#ced7df!important;font-size:12px;font-weight:750}
.site .briefing-reader-hero h1{font:500 clamp(37px,5vw,62px)/1.06 Georgia,serif;max-width:940px;margin:12px 0 14px;letter-spacing:-.028em}
.site .briefing-reader-hero p{max-width:850px;color:#c8d2df;font-size:17px;line-height:1.58;margin:0}
.site .briefing-reader-hero .briefings-index{color:#e8bb97}
.site .briefing-reader-body{padding:43px 0 55px}
.site .briefing-reader-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(290px,.85fr);gap:20px}
.site .briefing-reader-intro{background:#fffdf8;border:1px solid var(--line);padding:32px;min-width:0}
.site .briefing-reader-intro h2{font:500 clamp(29px,3.4vw,40px)/1.14 Georgia,serif;margin:11px 0 13px}
.site .briefing-reader-intro>p{font:400 15px/1.7 Arial,sans-serif;color:#48525c;margin:0 0 22px}
.site .briefing-reader-next{margin-top:22px;padding:19px 20px;background:#ece1d4;border-left:3px solid #b76c42}
.site .briefing-reader-next strong{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8a4d30}
.site .briefing-reader-next p{font-size:14px;line-height:1.6;color:#263242;margin:8px 0 0}
.site .briefing-reader-checks{display:grid;gap:0;border-top:1px solid #d7d4ce;margin-top:19px}
.site .briefing-reader-check{display:grid;grid-template-columns:30px 1fr;gap:12px;padding:15px 0;border-bottom:1px solid #dedbd5}
.site .briefing-reader-check .briefing-icon{color:#ad6b43}
.site .briefing-reader-check strong{font-size:13px;color:#203245}
.site .briefing-reader-check p{font-size:12px;line-height:1.55;color:#58636e;margin:4px 0 0}
.site .cms-roi-inline-visual{max-width:950px;margin:28px auto 34px;background:#fffdf9;padding:clamp(10px,1.6vw,20px);border:1px solid #d9dedb;box-shadow:0 13px 35px rgba(17,39,59,.06)}
.site .cms-roi-inline-visual img{display:block;width:100%;height:auto;max-width:100%;aspect-ratio:3/4;background:#fff}
.site .cms-roi-inline-visual figcaption{font:400 13px/1.6 Arial,sans-serif;color:#476071;margin:13px 0}
.site .cms-roi-inline-visual .cms-roi-download{display:inline-flex;justify-content:center;align-items:center;min-height:44px;padding:12px 20px;border:1px solid #8daebc;border-radius:6px;font:800 12px/1.4 Arial,sans-serif;color:#0b3553!important;text-decoration:none!important}
.site .cms-roi-inline-visual .cms-roi-download:hover{background:#e5f4f8}
@media(max-width:700px){.site .cms-roi-inline-visual{padding:9px}.site .cms-roi-inline-visual .cms-roi-download{width:100%}}
.site .briefing-reader-side{display:flex;flex-direction:column;gap:14px;min-width:0}
.site .briefing-reader-cover{height:230px;overflow:hidden;background:#112638}
.site .briefing-reader-cover>.cms-article-image{height:100%;margin:0}
.site .briefing-reader-cover>.cms-article-image img{height:100%;width:100%;max-height:none;object-fit:cover;margin:0;box-shadow:none}
.site .briefing-reader-cover>.cms-fallback-cover{width:100%;height:100%;min-height:0;aspect-ratio:auto;box-shadow:none}
.site .briefing-reader-cover .cms-cover-copy{width:65%;top:10%}
.site .briefing-reader-cover .cms-cover-copy strong{font-size:clamp(18px,2.1vw,29px)}
.site .briefing-reader-cover .cms-briefing-visual{transform:scale(.6);transform-origin:right top;right:1%;top:10%;width:40%}
.site .briefing-reader-cover .cms-cover-copy p{display:none}
.site .briefing-reader-contact{background:#122b40;color:#fff;padding:27px}
.site .briefing-reader-contact .briefing-icon{color:#e7b991}
.site .briefing-reader-contact h3{font:500 26px/1.15 Georgia,serif;margin:15px 0 10px}
.site .briefing-reader-contact p{font-size:13px;line-height:1.6;color:#c7d3dd;margin:0 0 20px}
.site .briefing-reader-contact a{display:inline-flex;padding:12px 16px;min-height:42px;align-items:center;text-decoration:none!important;background:#e7b991;color:#15293a!important;font-size:12px;font-weight:850}
.site .briefing-reader-contact .briefing-contact-secondary{display:block;background:transparent;color:#d6e2eb!important;padding:13px 0 0;font-size:11px;min-height:0}
.site .briefing-reader-detail{margin-top:20px;background:#fffdf8;border:1px solid var(--line)}
.site .briefing-reader-detail summary{cursor:pointer;list-style:auto;padding:22px 25px;color:#21334a;font-size:14px;font-weight:800}
.site .briefing-reader-detail summary:focus-visible{outline:3px solid #b87751;outline-offset:-4px}
.site .briefing-reader-detail .briefing-reader-research{border-top:1px solid var(--line);padding:32px;max-width:100%}
.site .briefing-reader-research.article-body{max-width:none}
.site .briefing-reader-research.article-body p{font-size:14px;line-height:1.68}
.site .briefing-reader-research.article-body h2{font-size:27px;margin:26px 0 12px}
.site .briefing-reader-research .executive-capability-grid{gap:9px}
.site .briefing-reader-research .executive-capability-card{padding:14px}
.site .briefing-reader-share{margin-top:23px;max-width:900px}
@media(max-width:950px){.site .briefings-lead,.site .briefing-reader-grid{grid-template-columns:1fr}.site .briefings-map{grid-template-columns:repeat(2,minmax(0,1fr))}.site .briefings-map-intro,.site .briefings-conversation-inner{display:block}.site .briefings-map-intro>p{margin-top:15px}.site .briefings-conversation-actions{margin-top:24px}.site .briefing-reader-cover{height:230px}}
@media(max-width:650px){.site .briefings-hero{padding:42px 0}.site .briefings-hero .briefings-deck{font-size:15px}.site .briefings-overview{padding:30px 0}.site .briefings-feature-art{height:165px}.site .briefings-feature-content,.site .briefings-method{padding:25px}.site .briefings-map{grid-template-columns:1fr}.site .briefings-capability{min-height:0;padding:17px}.site .briefings-others{grid-template-columns:1fr}.site .briefings-home-inner{display:block}.site .briefings-home-inner>a{display:inline-block;margin-top:10px}.site .briefing-reader-hero{padding:34px 0}.site .briefing-reader-hero p{font-size:14px}.site .briefing-reader-body{padding:24px 0 40px}.site .briefing-reader-intro{padding:23px}.site .briefing-reader-cover{height:190px}.site .briefing-reader-detail .briefing-reader-research{padding:20px}.site .briefings-conversation{padding:35px 0}.site .briefings-conversation-actions{display:grid}.site .briefings-conversation-actions a{justify-content:center}}
@media(prefers-reduced-motion:reduce){.site .briefings-feature .briefings-read{transition:none}}

/* The briefing library is a catalog, never an inline multi-article reader. */
.site .briefing-icon{display:inline-flex;flex:0 0 28px;align-items:center;justify-content:center;box-sizing:border-box;width:28px;height:28px;border:1px solid currentColor;border-radius:7px;font:700 22px/1 Arial,sans-serif;color:#ad7350;background:rgba(184,119,79,.07)}
.site .briefings-library-hero{padding:60px 0 53px;background:#102238;color:#fff}
.site .briefings-library-hero .eyebrow{color:#e4b68f}
.site .briefings-library-hero h1{max-width:950px;margin:14px 0 17px;font:500 clamp(41px,5.7vw,68px)/1.06 Georgia,serif;letter-spacing:-.03em;color:#fff}
.site .briefings-library-hero .briefings-library-deck{max-width:750px;margin:0;color:#d0dbe4;font:400 clamp(15px,1.6vw,18px)/1.65 Arial,sans-serif}
.site .briefings-library-intent{display:flex;flex-wrap:wrap;gap:9px;margin-top:25px}
.site .briefings-library-intent span{padding:8px 11px;border:1px solid rgba(233,189,151,.32);color:#e9c6a9;font:750 10px/1.4 Arial,sans-serif;letter-spacing:.04em}
.site .briefings-library-section{padding:47px 0 66px}
.site .briefings-library-heading{display:flex;align-items:end;justify-content:space-between;gap:22px;margin:0 0 23px}
.site .briefings-library-heading h2{margin:10px 0 0;font:500 clamp(28px,3.5vw,40px)/1.14 Georgia,serif;letter-spacing:-.018em}
.site .briefings-library-count{margin:0 0 5px;font:750 11px/1.4 Arial,sans-serif;color:#67717b;white-space:nowrap}
.site .briefings-library-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;align-items:stretch}
.site .briefings-library-card{display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden;border:1px solid #d5d9d9;background:#fffdf9;color:#152a3b!important;text-decoration:none!important;box-shadow:0 10px 35px rgba(15,34,54,.04);transition:transform .15s,border-color .15s,box-shadow .15s}
.site .briefings-library-card:hover,.site .briefings-library-card:focus-visible{border-color:#b4744e;transform:translateY(-3px);box-shadow:0 18px 44px rgba(15,34,54,.11);outline:0}
.site .briefings-library-card:focus-visible{outline:3px solid #bc835d;outline-offset:3px}
.site .briefings-catalog-art{position:relative;display:flex;flex-direction:column;justify-content:space-between;gap:17px;box-sizing:border-box;width:100%;height:178px;overflow:hidden;padding:22px 26px;color:#fff;background:radial-gradient(ellipse at 78% 80%,#2e5365 0%,#182e42 54%,#102238 100%)}
.site .briefings-catalog-art:after{content:"";position:absolute;z-index:0;inset:13px;border:1px solid rgba(225,185,152,.2);pointer-events:none}
.site .briefings-catalog-art--adoption-svg{padding:0;background:#082c48}
.site .briefings-catalog-art--adoption-svg img{position:absolute;inset:0;z-index:2;display:block;width:100%;height:100%;object-fit:cover;object-position:center top}
.site .briefings-catalog-art--adoption-svg>span{position:absolute;top:28px;left:23px;right:23px;z-index:1;color:#fff;font:800 22px/1.2 Arial,sans-serif}
.site .briefings-catalog-art>span,.site .briefings-catalog-art>div{position:relative;z-index:1}
.site .briefings-catalog-art-kicker{font:800 10px/1.4 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#efc6a3}
.site .briefings-art-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;max-width:460px}
.site .briefings-art-options span{display:grid;place-items:center;min-width:0;min-height:55px;padding:10px 8px;border:1px solid rgba(225,190,157,.52);background:rgba(8,25,41,.55);color:#fff;font:750 clamp(11px,1.45vw,15px)/1.2 Arial,sans-serif}
.site .briefings-art-connector{color:#c6d8e0;font:650 11px/1.45 Arial,sans-serif;letter-spacing:.045em}
.site .briefings-catalog-art--questions{background:radial-gradient(ellipse at 24% 18%,#385668,#122539 74%)}
.site .briefings-art-numbers{display:flex;align-items:center;gap:9px;max-width:470px}
.site .briefings-art-numbers b{display:grid;place-items:center;width:39px;height:44px;flex:1 1 0;border:1px solid rgba(238,194,161,.55);color:#f1c49e;background:#102238;font:750 16px/1 Arial,sans-serif}
.site .briefings-art-label{font:750 11px/1.5 Arial,sans-serif;color:#d5e2e9}
.site .briefings-art-generic{font:500 38px/1.1 Georgia,serif;color:#f4e4d7}
.site .briefings-library-card-body{display:flex;flex:1;flex-direction:column;padding:26px 28px 27px;min-width:0}
.site .briefings-library-card-meta{display:flex;justify-content:space-between;align-items:center;gap:12px;color:#a3623b;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.11em;text-transform:uppercase}
.site .briefings-library-card h3{margin:13px 0 14px;color:#152a3c;font:500 clamp(26px,2.9vw,34px)/1.17 Georgia,serif;letter-spacing:-.015em;overflow-wrap:break-word}
.site .briefings-library-card p{margin:0 0 19px;max-width:600px;color:#526170;font:400 14px/1.65 Arial,sans-serif;overflow-wrap:break-word}
.site .briefings-library-card-foot{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-top:auto;padding-top:15px;border-top:1px solid #e6e1da;color:#586777;font:700 11px/1.45 Arial,sans-serif}
.site .briefings-library-card-foot strong{color:#9e5931;font-size:12px}
.site .briefings-library-empty{padding:34px;border:1px solid #ded8cd;background:#fff}
.site .briefings-library-empty h3{margin:0 0 10px;font:500 27px/1.2 Georgia,serif}
.site .briefings-library-empty p{max-width:720px;color:#526170}
.site .briefing-reader-summary{display:grid;grid-template-columns:minmax(0,.88fr) minmax(0,1.12fr);gap:24px;padding:30px;background:#fffdf8;border:1px solid #dad8d2}
.site .briefing-reader-summary h2{margin:12px 0 12px;font:500 clamp(27px,3.5vw,40px)/1.12 Georgia,serif;color:#1b3445}
.site .briefing-reader-summary p{margin:0;font:400 14px/1.68 Arial,sans-serif;color:#445567}
.site .briefing-reader-summary .briefing-reader-checks{margin:0;border-top:0}
.site .briefing-reader-summary .briefing-reader-check{grid-template-columns:28px minmax(0,1fr);padding:12px 0}
.site .briefing-reader-summary .briefing-reader-check:first-child{padding-top:0}
.site .briefing-reader-summary .briefing-reader-check .briefing-icon{width:26px;height:26px;flex-basis:26px;font-size:19px}
.site .briefing-reader-summary .briefing-reader-check p{margin:5px 0 0;font-size:13px}
.site .briefing-reader-summary .briefing-reader-next{margin-top:20px;padding:16px 18px}
.site .briefing-reader-decision-map{margin:24px 0 0;padding:29px;background:#eef1f0;border:1px solid #d5dfde}
.site .briefing-reader-decision-map h2{font:500 clamp(28px,3.3vw,38px)/1.15 Georgia,serif;margin:8px 0 12px}
.site .briefing-reader-decision-map>p{max-width:820px;font:400 13px/1.62 Arial,sans-serif;color:#52616b}
.site .briefing-reader-decision-map .briefings-map{margin-top:19px}
.site .briefing-reader-decision-map .briefings-capability{grid-template-columns:28px minmax(0,1fr);padding:18px;min-height:135px}
.site .briefing-reader-decision-map .briefings-capability h3{font-size:21px}
.site .briefing-full-content{margin-top:24px;padding:clamp(24px,4vw,42px);background:#fffdf8;border:1px solid #dad8d2}
.site .briefing-full-content-head{margin:0 0 26px;padding-bottom:17px;border-bottom:1px solid #dedbd5}
.site .briefing-full-content-head h2{font:500 clamp(28px,3.3vw,37px)/1.16 Georgia,serif;color:#182d40;margin:9px 0}
.site .briefing-full-content-head p{color:#526170;font:400 13px/1.58 Arial,sans-serif;margin:0}
.site .briefing-full-content .article-body{max-width:820px;margin:0 auto;overflow-wrap:break-word;min-width:0}
.site .briefing-full-content .article-body h2{font:500 clamp(24px,2.8vw,32px)/1.24 Georgia,serif;margin:28px 0 14px}
.site .briefing-full-content .article-body p,.site .briefing-full-content .article-body li{font:400 15px/1.73 Arial,sans-serif;color:#394c5c}
.site .briefing-full-content .article-body img{max-width:100%;height:auto}
@media(max-width:900px){.site .briefings-library-grid{grid-template-columns:minmax(0,1fr)}.site .briefing-reader-summary{grid-template-columns:1fr}.site .briefings-library-card h3{font-size:clamp(26px,4vw,34px)}.site .briefings-art-options{max-width:100%}}
@media(max-width:650px){.site .briefings-library-hero{padding:40px 0}.site .briefings-library-section{padding:29px 0 45px}.site .briefings-library-heading{align-items:start}.site .briefings-library-count{white-space:normal;text-align:right}.site .briefings-library-card-body{padding:22px}.site .briefings-catalog-art{height:160px;padding:19px}.site .briefings-art-numbers{gap:4px}.site .briefings-art-numbers b{height:36px;font-size:13px}.site .briefing-reader-summary,.site .briefing-reader-decision-map{padding:20px}.site .briefing-reader-decision-map .briefings-map{grid-template-columns:minmax(0,1fr)}.site .briefing-full-content{padding:21px}.site .briefings-library-card-foot{flex-wrap:wrap}}
@media(prefers-reduced-motion:reduce){.site .briefings-library-card{transition:none}}
.site .briefings-catalog-art--governance{background:radial-gradient(ellipse at 70% 25%,#33526a,#102238 72%)}
.site .briefings-governance-art{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;max-width:520px}
.site .briefings-governance-art span{border:1px solid rgba(230,187,154,.55);background:#1e3b50;color:#f4e8de;padding:13px 9px;text-align:center;font:750 12px/1.3 Arial,sans-serif}
.site .briefings-governance-art-rule{color:#e4b995!important;font:750 11px/1.4 Arial,sans-serif!important}

/* Independent, text-first executive governance diagram. No borrowed stack artwork. */
.site .gov-seven{margin-top:25px;padding:clamp(20px,3vw,34px);background:#f1f3f1;border:1px solid #cfd9d8}
.site .gov-seven-head{display:flex;justify-content:space-between;align-items:start;gap:25px}
.site .gov-seven-head h2{font:500 clamp(28px,3.8vw,43px)/1.12 Georgia,serif;color:#173046;max-width:750px;margin:10px 0 13px}
.site .gov-seven-head p{font:400 14px/1.67 Arial,sans-serif;color:#4c5f6a;max-width:770px;margin:0}
.site .gov-seven-count{font:700 45px/1 Georgia,serif;color:#a16b48;white-space:nowrap;border-left:1px solid #c5cfcd;padding-left:19px}
.site .gov-seven-thread{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;background:#163247;color:#fff;padding:16px 19px;margin:22px 0 26px}
.site .gov-seven-thread strong{color:#e6ba96;font:750 10px/1.5 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}
.site .gov-seven-thread span{font:600 12px/1.55 Arial,sans-serif;color:#eff5f6}
.site .gov-seven-group{margin-top:21px}
.site .gov-seven-group-head{display:flex;gap:12px;align-items:center;border-bottom:1px solid #cbd5d2;padding:0 0 10px;margin-bottom:8px}
.site .gov-seven-group-head b{font:850 10px/1.5 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#7d563b}
.site .gov-seven-group-head span{font:400 12px/1.5 Arial,sans-serif;color:#63717a}
.site .gov-seven-list{margin:0;padding:0;list-style:none;display:grid;gap:8px}
.site .gov-seven-layer{display:grid;grid-template-columns:49px minmax(155px,.85fr) minmax(180px,1fr) minmax(165px,.95fr);gap:14px;align-items:start;padding:18px 20px;background:#fffdf9;border:1px solid #d8dedc;border-left:4px solid #52788c;min-width:0}
.site .gov-seven-layer--decisions{border-left-color:#b87c52}
.site .gov-seven-layer--execution{border-left-color:#46766d}
.site .gov-seven-number{color:#987054;font:500 29px/1.1 Georgia,serif}
.site .gov-seven-title{display:flex;gap:10px;align-items:start}
.site .gov-seven-title .briefing-icon{flex-shrink:0;width:26px;height:26px;font-size:17px}
.site .gov-seven-title h3{font:500 clamp(18px,1.9vw,23px)/1.2 Georgia,serif;color:#183247;margin:0}
.site .gov-seven-question strong,.site .gov-seven-proof strong{display:block;font:850 10px/1.4 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#986344;margin:0 0 6px}
.site .gov-seven-question p{font:750 13px/1.48 Arial,sans-serif;color:#1d3446;margin:0 0 7px}
.site .gov-seven-question span{display:block;font:400 12px/1.55 Arial,sans-serif;color:#586671}
.site .gov-seven-proof p{font:600 12px/1.6 Arial,sans-serif;color:#415667;margin:0}
.site .gov-seven-example{margin-top:25px;padding:22px 24px;background:#e3e9e8;border:1px solid #cad5d3}
.site .gov-seven-example h3{font:500 25px/1.2 Georgia,serif;color:#1b3546;margin:8px 0}
.site .gov-seven-example>p{font:400 13px/1.65 Arial,sans-serif;color:#425662;margin:0 0 16px;max-width:830px}
.site .gov-seven-modes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.site .gov-seven-mode{padding:15px;background:#fffdf9;border-top:3px solid #c18c66}
.site .gov-seven-mode b{font:500 19px/1.2 Georgia,serif;color:#1e3647;display:block;margin-bottom:6px}
.site .gov-seven-mode p{font:400 12px/1.55 Arial,sans-serif;color:#52636b;margin:0}
.site .gov-seven-actions{display:grid;grid-template-columns:minmax(190px,.75fr) 1fr;gap:23px;margin-top:16px;padding:22px 24px;background:#173247;color:#fff}
.site .gov-seven-actions h3{font:500 26px/1.2 Georgia,serif;color:#fff;margin:5px 0 8px}
.site .gov-seven-actions p{font:400 12px/1.55 Arial,sans-serif;color:#d7e0e6;margin:0}
.site .gov-seven-actions ol{margin:0;padding-left:20px;font:400 13px/1.6 Arial,sans-serif;color:#edf3f5}
.site .gov-seven-actions li+li{margin-top:7px}
.site .gov-seven-note{color:#627079!important;font:400 11px/1.6 Arial,sans-serif!important;margin:13px 0 0!important}
@media(max-width:1050px){.site .gov-seven-layer{grid-template-columns:44px minmax(160px,.9fr) minmax(190px,1.15fr)}.site .gov-seven-proof{grid-column:2 / -1;border-top:1px solid #e2e6e2;padding-top:9px}.site .gov-seven-proof p{margin:0}}
@media(max-width:720px){.site .gov-seven-layer{grid-template-columns:38px minmax(0,1fr);gap:10px 12px;padding:15px}.site .gov-seven-title,.site .gov-seven-question,.site .gov-seven-proof{grid-column:2}.site .gov-seven-question{padding-top:4px}.site .gov-seven-proof{padding-top:9px}.site .gov-seven-modes{grid-template-columns:1fr}.site .gov-seven-actions{grid-template-columns:1fr}.site .gov-seven-head{display:block}.site .gov-seven-count{display:none}.site .gov-seven-group-head{display:block}.site .gov-seven-group-head span{display:block;margin-top:3px}}

/* The governance SVG is injected inline, never requested from /app/static. */
.site .gov-visual{margin:19px 0 0;padding:0;background:#fff;border:1px solid #dae1df}
.site .gov-visual-art{width:100%;min-width:0;overflow:hidden;background:#fff}
.site .gov-visual-art img{display:block;width:100%;height:auto;max-width:100%;object-fit:contain}
.site .gov-visual figcaption{padding:12px 20px;border-top:1px solid #e4e7e5;color:#51616b;font:400 12px/1.55 Arial,sans-serif}
.site .gov-visual figcaption strong{color:#193449}
.site .gov-visual-fallback{padding:24px;background:#f5f8f7;color:#193449}
.site .gov-visual-fallback p{font:600 22px/1.25 Georgia,serif;margin:0 0 15px}
.site .gov-visual-fallback ol{margin:0;padding-left:22px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 30px}
.site .gov-visual-fallback li{font:600 14px/1.5 Arial,sans-serif}
.site .gov-visual-fallback li span{display:block;font-weight:400;color:#55646c}
.site .governance-reader .gov-seven-example{margin-top:17px}
.site .gov-layer-detail .gov-seven{margin:0;border:0;background:#f3f5f2}
.site .gov-layer-detail .gov-seven-head{display:none}
.site .gov-layer-detail .gov-seven-thread{margin:0 0 14px}
.site .gov-layer-detail>.gov-seven{padding:18px}
@media(max-width:650px){.site .gov-visual figcaption{padding:11px 14px}.site .gov-visual-fallback ol{grid-template-columns:1fr}.site .gov-layer-detail .gov-seven{padding:14px}}

/* Executive governance edition: scan first, examine proof when needed. */
.site .gov-judgment{padding:clamp(22px,3.5vw,34px);border-left:4px solid #b9815d;background:#fffdf8;border-top:1px solid #e0dbd4;border-right:1px solid #e0dbd4;border-bottom:1px solid #e0dbd4}
.site .gov-judgment h2{font:500 clamp(27px,3.5vw,38px)/1.16 Georgia,serif;color:#193449;margin:9px 0 11px;max-width:850px}
.site .gov-judgment p{font:400 15px/1.66 Arial,sans-serif;color:#405566;margin:0;max-width:850px}
.site .governance-reader .gov-seven{margin-top:19px}
.site .governance-reader .gov-seven-head p{max-width:800px}
.site .gov-record{margin-top:19px;padding:clamp(20px,3.4vw,33px);background:#fffdf9;border:1px solid #d8d7d1}
.site .gov-record-head h2{font:500 clamp(28px,3.4vw,39px)/1.16 Georgia,serif;color:#1b3549;margin:9px 0 10px}
.site .gov-record-head p{font:400 14px/1.65 Arial,sans-serif;color:#53616a;max-width:830px;margin:0}
.site .gov-record-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:#dbe0dc;border:1px solid #dbe0dc;margin:21px 0 0;padding:0;list-style:none}
.site .gov-record-field{display:grid;grid-template-columns:34px minmax(0,1fr);gap:12px;padding:19px 20px;background:#fffefa;min-width:0}
.site .gov-record-index{font:600 24px/1 Georgia,serif;color:#b0764d}
.site .gov-record-field h3{font:500 21px/1.2 Georgia,serif;color:#193449;margin:0 0 7px}
.site .gov-record-field p{font:400 13px/1.55 Arial,sans-serif;color:#4b5d68;margin:0}
.site .gov-record-gates{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:14px}
.site .gov-record-gates>div{padding:17px;background:#e9efec;border-top:3px solid #6f8c80}
.site .gov-record-gates>div:nth-child(2){background:#f3ece2;border-top-color:#b28a58}
.site .gov-record-gates>div:nth-child(3){background:#f4ebe7;border-top-color:#a47765}
.site .gov-record-gates strong{font:750 13px/1.35 Arial,sans-serif;color:#193448}
.site .gov-record-gates p{font:400 12px/1.55 Arial,sans-serif;color:#425363;margin:5px 0 0}
.site .gov-review{display:grid;grid-template-columns:minmax(210px,.72fr) minmax(0,1.28fr);gap:25px;padding:25px 28px;margin-top:17px;background:#163247;color:#fff}
.site .gov-review h2{font:500 28px/1.18 Georgia,serif;color:#fff;margin:8px 0 10px}
.site .gov-review>div>p{font:400 13px/1.6 Arial,sans-serif;color:#d5e2e7;margin:0}
.site .gov-review ol{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;list-style:none;padding:0;margin:0}
.site .gov-review li{padding:13px 15px;border:1px solid #547082;min-width:0}
.site .gov-review li b{display:block;font:750 10px/1.35 Arial,sans-serif;letter-spacing:.09em;color:#ecc5a2}
.site .gov-review li strong{display:block;font:500 20px/1.24 Georgia,serif;margin:5px 0;color:#fff}
.site .gov-review li span{display:block;font:400 12px/1.55 Arial,sans-serif;color:#d9e3e9}
.site .gov-notes{margin-top:16px}
@media(max-width:850px){.site .gov-review{grid-template-columns:1fr}.site .gov-record-gates{grid-template-columns:1fr}}
@media(max-width:650px){.site .gov-record-grid,.site .gov-review ol{grid-template-columns:1fr}.site .gov-record-field{padding:16px}.site .gov-review{padding:22px}}

/* EU AI Act edition: editorial diagrams, not a reproduction of a third-party infographic. */
.site .briefings-catalog-art--aia{background:radial-gradient(ellipse at 82% 14%,#315669 0%,#102238 76%);border-top:3px solid #c49a74}
.site .aia-art-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;max-width:530px}
.site .aia-art-steps span{min-width:0;padding:12px 10px;border:1px solid rgba(232,192,153,.54);background:rgba(7,27,46,.58);color:#f7f1eb;font:750 13px/1.25 Arial,sans-serif}
.site .aia-art-steps b{display:block;font:850 10px/1.3 Arial,sans-serif;color:#e9bf98;margin-bottom:6px}
.site .aia-art-foot{color:#d4e1e6;font:650 11px/1.45 Arial,sans-serif}
.site .aia-diagram{position:relative;isolation:isolate;overflow:hidden;margin:22px 0 25px;padding:24px 23px;background:radial-gradient(ellipse at 84% 8%,#285063,#122b40 68%);color:#fff;border-top:3px solid #d4a47e}
.site .aia-diagram-caption{display:block;color:#e9c2a3;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;margin-bottom:13px}
.site .aia-diagram h3{font:500 clamp(22px,3vw,30px)/1.23 Georgia,serif;color:#fff;margin:0 0 18px}
.site .aia-path{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
.site .aia-path>div{background:rgba(8,29,45,.72);border:1px solid #557286;padding:16px 11px;min-width:0}
.site .aia-path b{display:block;color:#f0bc93;font:850 10px/1 Arial,sans-serif;letter-spacing:.08em;margin-bottom:10px}
.site .aia-path strong{display:block;color:#fff;font:750 15px/1.25 Arial,sans-serif}
.site .aia-path small{display:block;color:#c7d7de;font:400 11px/1.55 Arial,sans-serif;margin-top:8px}
.site .aia-diagram>p{font:400 11px/1.58 Arial,sans-serif;color:#b8ccd7!important;margin:16px 0 0}
.site .aia-duties{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:18px 0 23px}
.site .aia-duty{padding:19px 21px;border:1px solid #d7deda;background:#f6f7f5;min-width:0}
.site .aia-duty:nth-child(1){border-top:3px solid #9e5e53}
.site .aia-duty:nth-child(2){border-top:3px solid #b3844f}
.site .aia-duty:nth-child(3){border-top:3px solid #638193}
.site .aia-duty:nth-child(4){border-top:3px solid #5f887b}
.site .aia-duty span{display:block;font:850 10px/1.4 Arial,sans-serif;letter-spacing:.09em;color:#926643;text-transform:uppercase}
.site .aia-duty h3{font:500 23px/1.2 Georgia,serif;color:#193449;margin:9px 0 9px}
.site .aia-duty p{font:400 13px/1.6 Arial,sans-serif;color:#455c68;margin:0}
.site .aia-important{background:#f3e8d9;padding:18px 20px;border-left:4px solid #ad7652;margin:18px 0}
.site .aia-important p{margin:0!important;color:#2b3f4e!important}
.site .aia-timeline{display:grid;gap:0;border:1px solid #d5dedb;margin:17px 0 22px}
.site .aia-date{display:grid;grid-template-columns:125px 1fr;gap:16px;padding:12px 16px;border-bottom:1px solid #dbe0dc;background:#f8f8f4}
.site .aia-date:last-child{border-bottom:0}
.site .aia-date b{color:#965a38;font:800 12px/1.5 Arial,sans-serif}
.site .aia-date span{font:400 13px/1.55 Arial,sans-serif;color:#344a59}
.site .aia-record{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:18px 0 22px}
.site .aia-record>div{background:#edf1ed;border:1px solid #d3ded7;padding:15px 17px}
.site .aia-record b{display:block;font:850 10px/1.4 Arial,sans-serif;color:#9b673e;letter-spacing:.11em;margin-bottom:7px}
.site .aia-record strong{display:block;color:#19394a;font:750 14px/1.35 Arial,sans-serif}
.site .aia-record p{margin:6px 0 0!important;font:400 12px/1.58 Arial,sans-serif!important}
@media(max-width:650px){.site .aia-path,.site .aia-duties,.site .aia-record{grid-template-columns:1fr}.site .aia-path>div{padding:11px 14px}.site .aia-date{grid-template-columns:1fr;gap:3px;padding:12px 14px}.site .aia-diagram{padding:19px 16px}.site .aia-art-steps span{font-size:11px;padding:10px 7px}}

/* Editorial cover treatment for the data-governance funding edition. */
.site .briefings-catalog-art--funding{background:radial-gradient(ellipse at 90% 10%,#345c6a,#132e42 73%);border-top:3px solid #c39b75}
.site .dgf-card-diagram{display:flex;align-items:center;gap:5px;max-width:530px}
.site .dgf-card-diagram span{flex:1;padding:12px 4px;text-align:center;background:#244456;border:1px solid #79909b;color:#f8f3ec;font:800 11px/1.35 Arial,sans-serif;letter-spacing:.05em}
.site .dgf-card-diagram b{color:#dfb997;font:600 18px/1 Arial,sans-serif}
@media(max-width:500px){.site .dgf-card-diagram span{font-size:9px;padding:9px 3px}}
/* Unique collection artwork: two evidence streams converging into one gate. */
.site .briefings-catalog-art--dual{background:radial-gradient(ellipse at 83% 10%,#36576a,#142c40 75%);border-top:3px solid #bd906f}
.site .dual-catalog-split{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;max-width:520px}
.site .dual-catalog-split span{padding:13px 11px;text-align:center;color:#f7eee7;font:800 12px/1.42 Arial,sans-serif;letter-spacing:.07em;background:#24485b;border:1px solid #718d9a}
.site .dual-catalog-split span+span{background:#3b4455;border-color:#ac8d77}
.site .dual-catalog-gate{margin:9px auto 0;max-width:325px;padding:8px 12px;background:#e6c1a1;color:#243e4e;font:850 10px/1.3 Arial,sans-serif;text-align:center;letter-spacing:.08em}
@media(max-width:540px){.site .dual-catalog-split span{font-size:11px;padding:10px 6px}}
</style>'''


def governance_decision_map() -> str:
    """Original seven-layer operating map with executive checks and proof points."""
    groups = {
        "foundation": ("Make AI accountable", "Trusted inputs and clear ownership"),
        "decisions": ("Make permissions explicit", "Who may approve, challenge and stop"),
        "execution": ("Keep behaviour controlled", "Proof before release and oversight afterwards"),
    }
    rows = []
    current_group = None
    for number, title, question, move, evidence, icon, group in GOVERNANCE_LAYERS:
        if group != current_group:
            if current_group is not None:
                rows.append("</ol></div>")
            heading, deck = groups[group]
            rows.append(
                '<div class="gov-seven-group">'
                f'<div class="gov-seven-group-head"><b>{escape(heading)}</b>'
                f'<span>{escape(deck)}</span></div>'
                '<ol class="gov-seven-list">'
            )
            current_group = group
        rows.append(
            f'<li class="gov-seven-layer gov-seven-layer--{escape(group)}">'
            f'<span class="gov-seven-number" aria-hidden="true">{escape(number)}</span>'
            '<div class="gov-seven-title">' + briefing_icon(icon)
            + f'<h3>{escape(title)}</h3></div>'
            '<div class="gov-seven-question"><strong>Executive question</strong>'
            f'<p>{escape(question)}</p><span>{escape(move)}</span></div>'
            '<div class="gov-seven-proof"><strong>Ask to see</strong>'
            f'<p>{escape(evidence)}</p></div></li>'
        )
    rows.append("</ol></div>")
    return (
        '<section class="gov-seven" aria-label="Seven operating layers of AI governance" '
        'data-analytics-section="briefings-governance-map">'
        '<div class="gov-seven-head"><div><span class="briefings-index">The operating architecture</span>'
        '<h2>Seven questions to test with your team.</h2>'
        '<p>Use this optional reference to inspect the evidence behind the visual map. '
        'Request only the proof needed for the proposed use and its risk.</p></div>'
        '<span class="gov-seven-count" aria-hidden="true">07</span></div>'
        '<div class="gov-seven-thread"><strong>Across every layer</strong>'
        '<span>Business outcome</span><span>Risk appetite</span>'
        '<span>Real adoption</span><span>Ownership of consequences</span></div>'
        + "".join(rows)
        + '<p class="gov-seven-note">Executive operating model by Jair Ribeiro. '
        'The layers are a practical management view, not a claim that every use case '
        'faces identical legal obligations. Apply relevant requirements based on '
        'context, risk and jurisdiction.</p></section>'
    )


def governance_case_example() -> str:
    """The single worked example: recommend, prepare, or execute within limits."""
    return (
        '<div class="gov-seven-example"><span class="briefings-index">A practical distinction</span>'
        '<h3>One service workflow. Three different levels of AI authority.</h3>'
        '<p>This field-informed illustrative composite follows recurring enterprise service-case patterns. '
        'Imagine an AI assistant helping teams classify and route technical service cases; '
        'the scenario does not represent any identifiable organisation, deployment or measured result. '
        'The control must change as the system gains permission to act.</p>'
        '<div class="gov-seven-modes">'
        '<div class="gov-seven-mode"><b>Recommend</b><p>AI proposes a routing destination with '
        'the relevant case evidence. A person decides and records the outcome.</p></div>'
        '<div class="gov-seven-mode"><b>Prepare</b><p>AI drafts the case assignment and '
        'reason, but cannot submit it until an authorised person approves.</p></div>'
        '<div class="gov-seven-mode"><b>Execute within limits</b><p>AI may route only '
        'clearly defined, low-consequence case categories under approved rules, '
        'with logging, monitoring, manual correction and a stop route.</p></div></div></div>'
    )


@lru_cache(maxsize=1)
def _embedded_governance_svg() -> str:
    """Read the checked-in diagram at render time, without requesting a static URL.

    Streamlit Cloud can return SVG assets with MIME headers that browsers will
    not render as images. Inlining this first-party SVG avoids that dependency.
    """
    asset = Path(__file__).resolve().parent.parent / "static" / (
        "ai-governance-executive-seven-layer-map.svg"
    )
    try:
        svg = asset.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError, UnicodeError):
        return ""
    return svg if svg.startswith("<svg ") and svg.endswith("</svg>") else ""


def governance_visual_map() -> str:
    """Render the checked-in SVG as a self-contained image data URL.

    Streamlit static hosting returns SVG as text/plain with nosniff, while
    st.html may sanitize inline SVG markup. An <img> data URI avoids both
    problems and requires no additional network fetch or JS.
    """
    svg = _embedded_governance_svg()
    if svg:
        image_data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        graphic = (
            '<img src="data:image/svg+xml;base64,' + image_data + '" '
            'loading="eager" decoding="async" '
            'alt="Seven-layer AI governance model. Foundation: information '
            'integrity and accountable ownership. Decisions: authority to '
            'decide, rules in the workflow, risk and obligations. Execution: '
            'system assurance and bounded AI action. Business outcome, risk '
            'appetite and ownership apply across all layers.">'
        )
    else:
        # If the file is not deployed, show content instead of an empty frame.
        layers = "".join(
            '<li><strong>' + escape(title) + '</strong><span>' +
            escape(question) + '</span></li>'
            for _number, title, question, *_rest in GOVERNANCE_LAYERS
        )
        graphic = (
            '<div class="gov-visual-fallback" role="group" '
            'aria-label="Seven layers of AI governance">'
            '<p>The seven layers of AI governance</p><ol>'
            + layers + '</ol></div>'
        )
    return (
        '<figure class="gov-visual" data-analytics-section="briefings-governance-visual">'
        '<div class="gov-visual-art">' + graphic + '</div>'
        '<figcaption><strong>At-a-glance governance map.</strong> '
        'Seven connected layers to govern AI as a business decision, '
        'not only a technical system.</figcaption>'
        '</figure>'
    )


def governance_decision_record() -> str:
    """Compact, reusable management record: one page, six decisions."""
    fields = ''.join(
        '<li class="gov-record-field"><span class="gov-record-index">'
        f'{escape(number)}</span><div><h3>{escape(title)}</h3>'
        f'<p>{escape(detail)}</p></div></li>'
        for number, title, detail in GOVERNANCE_RECORD_FIELDS
    )
    return (
        '<section class="gov-record" data-analytics-section="briefings-governance-decision-record">'
        '<div class="gov-record-head"><span class="briefings-index">The executive decision record</span>'
        '<h2>One page before permission expands.</h2>'
        '<p>Ask the team to complete these six fields for one real workflow. '
        'A blank answer is a decision gap, not a reason to launch another committee.</p></div>'
        f'<ol class="gov-record-grid">{fields}</ol>'
        '<div class="gov-record-gates" aria-label="Governance decision outcomes">'
        '<div><strong>Proceed</strong><p>Owner, value and controls are credible. '
        'Authorize a bounded trial with a review date.</p></div>'
        '<div><strong>Hold</strong><p>A correctable gap remains. '
        'Assign an owner and condition for reconsideration.</p></div>'
        '<div><strong>Stop</strong><p>No accountable owner, unacceptable exposure '
        'or no defensible business case.</p></div></div></section>'
    )


def governance_20_minute_review() -> str:
    """A timed conversation, not a new governance committee."""
    steps = (
        ("0–5 min", "Outcome", "Name the workflow, baseline and business owner."),
        ("5–10 min", "Authority", "Check trusted inputs, permissions and who can stop the AI."),
        ("10–15 min", "Proof", "Examine realistic tests, risks, controls and exceptions."),
        ("15–20 min", "Decision", "Complete the record. Proceed, hold or stop; set the next review."),
    )
    items = ''.join(
        f'<li><b>{escape(time)}</b><strong>{escape(title)}</strong>'
        f'<span>{escape(detail)}</span></li>'
        for time, title, detail in steps
    )
    return (
        '<section class="gov-review" data-analytics-section="briefings-governance-review">'
        '<div><span class="briefings-index">Put it to work</span>'
        '<h2>A 20-minute governance review.</h2>'
        '<p>Start with a live business decision. End with recorded ownership, '
        'permission and the evidence required before the next step.</p></div>'
        f'<ol>{items}</ol></section>'
    )


def _article_infographic(article) -> str:
    """Approved infographic, source-fingerprint checked and fail-closed."""
    from briefing_infographic_store import approved_infographic_for
    return approved_infographic_for(article)


def governance_briefing_article(article, share_footer: str, cms_css: str) -> str:
    """Governance-specific editorial reader with one map and no repeated article."""
    from thinking_core import THINKING_CSS
    if article.slug == "beyond-ai-pilots-operating-decisions-to-scale":
        summary_text = (
            "The proof of a pilot is not the proof of an operating service. Fund scale only when the receiving business team can own the workflow, supervise decisions, measure outcomes and withdraw permission when conditions change."
        )
    return (
        THINKING_CSS + cms_css + BRIEFINGS_CSS + nav("thinking")
        + '<main class="briefing-reader governance-reader">'
        '<section class="briefing-reader-hero" data-analytics-section="briefing-reader-introduction">'
        '<div class="container"><a class="briefing-reader-back" href="?page=briefings" '
        'target="_self">← All Executive AI Briefings</a>'
        '<span class="briefings-index">Executive AI Briefing · Governance</span>'
        f'<h1>{escape(article.title)}</h1>'
        f'<p>{escape(article.subtitle or article.excerpt)}</p></div></section>'
        '<section class="section paper briefing-reader-body"><div class="container">'
        '<section class="gov-judgment" data-analytics-section="briefings-governance-judgment">'
        '<span class="briefings-index">The Leadership Decision</span>'
        '<h2>Govern the business decision, not just the model.</h2>'
        '<p>AI governance decides what the system may do, who owns the result '
        'and what evidence earns permission to proceed. The more consequential '
        'the AI action, the stronger the approval and oversight required.</p></section>'
        + (_article_infographic(article) or governance_visual_map())
        + governance_case_example()
        + governance_decision_record()
        + governance_20_minute_review()
        + '<details class="briefing-reader-detail gov-notes gov-layer-detail" '
        'data-analytics-section="briefings-governance-layer-reference">'
        '<summary>Explore the seven executive questions and evidence to request</summary>'
        + governance_decision_map()
        + '</details>'
        + '<details class="briefing-reader-detail gov-notes" '
        'data-analytics-section="briefings-governance-references">'
        '<summary>Application notes and source references</summary>'
        f'<div class="article-body briefing-reader-research">{article.content_html}</div>'
        '</details>'
        f'<div class="briefing-reader-share">{share_footer}</div>'
        '</div></section>'
        + contact_block()
        + '</main>' + footer()
    )


def published_briefings():
    try:
        return tuple(
            article for article in fetch_published_articles()
            if article.kind.strip().casefold() == BRIEFING_KIND.casefold()
        )
    except (RuntimeError, ValueError, TimeoutError):
        return ()


def home_briefings_strip() -> str:
    return BRIEFINGS_CSS + '''<section class="briefings-home-strip" data-analytics-section="home-executive-briefings">
    <div class="container briefings-home-inner"><div><span class="briefings-index">Executive AI Briefings</span>
    <h2>AI explained through the decisions leaders face.</h2>
    <p>Short operating perspectives on capability, ownership, risk and business value.</p></div>
    <a href="?page=briefings" target="_self" data-hq-event="briefings_home_open">Explore the briefings →</a>
    </div></section>'''


def contact_block() -> str:
    return (
        '<section class="briefings-conversation" data-analytics-section="briefings-contact">'
        '<div class="container briefings-conversation-inner"><div>'
        '<span class="briefings-index">From reading to decision</span>'
        '<h2>Have an AI choice that needs a clearer answer?</h2>'
        '<p>These briefings frame common executive questions. Your context determines the answer. '
        'If you are weighing investment, ownership, adoption or responsible scale, '
        'contact me to discuss the actual business decision.</p></div>'
        '<div class="briefings-conversation-actions">'
        '<a href="?page=contact" target="_self" data-hq-event="briefings_contact_open">Discuss your situation →</a>'
        f'<a href="mailto:{escape(EMAIL, quote=True)}?subject=Executive%20AI%20Briefing" '
        'data-hq-event="briefings_contact_email">Email directly →</a>'
        '</div></div></section>'
    )


def _briefing_catalog_art(slug: str) -> str:
    """Branded, article-specific graphic with no network images or inline SVG."""
    if slug == ADOPTION_SLUG:
        from briefing_adoption_artwork import artwork_data_uri
        thumbnail = artwork_data_uri("thumbnail")
        if thumbnail:
            return (
                '<div class="briefings-catalog-art briefings-catalog-art--adoption-svg" '
                'aria-hidden="true">'
                '<img src="' + thumbnail + '" alt="" '
                'loading="lazy" decoding="async"/></div>'
            )
        # A readable designed fallback beats a blank card if an asset is absent.
        return (
            '<div class="briefings-catalog-art" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">Adoption is not one problem</span>'
            '<div class="briefings-art-options"><span>Develop</span>'
            '<span>Empower</span><span>Engage</span></div>'
            '<div class="briefings-art-connector">Support · Assess work readiness</div>'
            '</div>'
        )
    if slug == FIRST_SLUG:
        return (
            '<div class="briefings-catalog-art" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">The capability choice</span>'
            '<div class="briefings-art-options"><span>Predict</span>'
            '<span>Generate</span><span>Act</span></div>'
            '<div class="briefings-art-connector">Business outcome · Permission · Evidence</div></div>'
        )
    if slug == GOVERNANCE_SLUG:
        return (
            '<div class="briefings-catalog-art briefings-catalog-art--governance" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">The operating governance test</span>'
            '<div class="briefings-governance-art"><span>Trusted inputs</span>'
            '<span>Decision authority</span><span>Bounded action</span></div>'
            '<div class="briefings-governance-art-rule">7 layers · One accountable business outcome</div></div>'
        )
    if slug == AI_ACT_SLUG:
        return (
            '<div class="briefings-catalog-art briefings-catalog-art--aia" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">EU AI ACT / EXECUTIVE DECISION GUIDE</span>'
            '<div class="aia-art-steps"><span><b>01</b> CLASSIFY</span>'
            '<span><b>02</b> ASSIGN</span><span><b>03</b> PROVE</span></div>'
            '<div class="aia-art-foot">The law is in force. Evidence precedes permission.</div></div>'
        )
    if slug == DUAL_GOV_SLUG:
        return (
            '<div class="briefings-catalog-art briefings-catalog-art--dual" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">Two disciplines · One release decision</span>'
            '<div class="dual-catalog-split"><span>DATA<br>FITNESS</span>'
            '<span>AI<br>ASSURANCE</span></div>'
            '<div class="dual-catalog-gate">BUSINESS RELEASE GATE</div>'
            '</div>'
        )
    if slug == FUNDING_SLUG:
        return (
            '<div class="briefings-catalog-art briefings-catalog-art--funding" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">Funding the right control</span>'
            '<div class="dgf-card-diagram"><span>EXPOSURE</span><b>→</b><span>CONTROL</span><b>→</b><span>PROOF</span></div>'
            '<div class="briefings-art-connector">Accountability · Cost · Decision gate</div></div>'
        )
    if slug == "seven-questions-for-better-ai-decisions":
        return (
            '<div class="briefings-catalog-art briefings-catalog-art--questions" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">Seven decision lenses</span>'
            '<div class="briefings-art-numbers">'
            + ''.join(f'<b>{i:02d}</b>' for i in range(1, 8))
            + '</div><div class="briefings-art-label">'
            'Frame the choice · Test the evidence · Make the call</div></div>'
        )
    return (
        '<div class="briefings-catalog-art" aria-hidden="true">'
        '<span class="briefings-catalog-art-kicker">Executive AI briefing</span>'
        '<div class="briefings-art-generic">Decision before technology.</div>'
        '<div class="briefings-art-connector">Business value · Ownership · Measurable work</div></div>'
    )


def executive_briefings() -> str:
    """Uniform, paginated catalog of independently published CMS briefings.

    Each published edition receives the same card treatment, including the
    newest one. Page selection uses a normal link/query parameter so it works
    with Streamlit's sanitized HTML and without JavaScript.
    """
    import streamlit as st
    from urllib.parse import urlencode
    from briefings_landing_premium import PREMIUM_BRIEFINGS_CSS

    items = tuple(sorted(
        published_briefings(),
        key=lambda article: str(
            getattr(article, "published_at", "")
            or getattr(article, "updated_at", "")
            or ""
        ),
        reverse=True,
    ))
    total = len(items)
    page_size = 4 if total >= 4 else 2
    page_count = max(1, (total + page_size - 1) // page_size)
    raw_page = st.query_params.get("briefings_page", "1")
    if isinstance(raw_page, list):
        raw_page = raw_page[0] if raw_page else "1"
    try:
        requested_page = int(str(raw_page))
    except (ValueError, TypeError):
        requested_page = 1
    current_page = min(max(requested_page, 1), page_count)
    start_index = (current_page - 1) * page_size
    visible = items[start_index:start_index + page_size]

    def edition_url(article) -> str:
        return escape(article_relative_url(article), quote=True)

    def edition_meta(article) -> str:
        return (
            f"{escape(article.published_label)}"
            f" · {escape(str(article.read_minutes))} min read"
        )

    def edition_description(article) -> str:
        return escape(article.subtitle or article.excerpt or "")

    def edition_theme(article) -> str:
        themes = {
            AI_ACT_SLUG: "Regulation & responsibility",
            FUNDING_SLUG: "Data governance & investment",
            DUAL_GOV_SLUG: "Data & AI decision rights",
            GOVERNANCE_SLUG: "Governance & ownership",
            FIRST_SLUG: "AI capability decisions",
            "seven-questions-for-better-ai-decisions": "Executive decision-making",
        }
        return escape(themes.get(article.slug, "Executive perspective"))

    cards = []
    for index, article in enumerate(visible, start_index + 1):
        cards.append(
            f'<a class="briefings-library-card" href="{edition_url(article)}" target="_self" '
            'data-hq-event="briefings_article_open" '
            f'data-hq-content-slug="{escape(article.slug, quote=True)}" '
            f'aria-label="Read {escape(article.title, quote=True)}">'
            '<div class="be-card-art">'
            + _briefing_catalog_art(article.slug)
            + '</div>'
            '<div class="be-card-copy">'
            '<div class="be-card-meta">'
            f'<span>Edition {total - index + 1:02d}</span>'
            f'<span>{edition_theme(article)}</span></div>'
            f'<h3>{escape(article.title)}</h3>'
            f'<p>{edition_description(article)}</p>'
            '<div class="be-card-footer">'
            f'<span>{edition_meta(article)}</span>'
            '<strong>Read edition ↗</strong></div>'
            '</div></a>'
        )

    # Keep the existing catalog class and card events for analytics continuity.
    catalog = (
        '<div class="briefings-library-grid">' + ''.join(cards) + '</div>'
        if cards else
        '<div class="be-empty"><strong>The library is being prepared.</strong>'
        'Briefings will appear here when published.</div>'
    )
    count_label = f"{total:02d} PUBLISHED " + (
        "BRIEFING" if total == 1 else "BRIEFINGS"
    )

    def page_url(number: int) -> str:
        # Preserve recognized campaign attribution across library pages.
        params = [("page", "briefings"), ("briefings_page", str(number))]
        for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content",
                    "source", "role"):
            value = st.query_params.get(key, "")
            if isinstance(value, list):
                value = value[0] if value else ""
            if value:
                params.append((key, str(value)[:120]))
        return escape("?" + urlencode(params) + "#briefings-library", quote=True)

    def page_anchor(number: int, text: str, selected: bool = False) -> str:
        current = ' aria-current="page"' if selected else ""
        class_name = "be-page-link is-current" if selected else "be-page-link"
        return (
            f'<a class="{class_name}" href="{page_url(number)}" target="_self"'
            f'{current} data-hq-event="briefings_library_page"'
            f' aria-label="Library page {number}">{escape(text)}</a>'
        )

    pagination = ""
    if page_count > 1:
        previous = (
            page_anchor(current_page - 1, "← Previous")
            if current_page > 1 else
            '<span class="be-page-link is-disabled" aria-disabled="true">← Previous</span>'
        )
        following = (
            page_anchor(current_page + 1, "Next →")
            if current_page < page_count else
            '<span class="be-page-link is-disabled" aria-disabled="true">Next →</span>'
        )
        numbers = "".join(
            page_anchor(number, str(number), selected=number == current_page)
            for number in range(1, page_count + 1)
        )
        pagination = (
            '<nav class="be-pagination" aria-label="Briefing library pagination">'
            f'<span class="be-pagination-status">Page {current_page} of {page_count}</span>'
            '<div class="be-pagination-links">'
            + previous + numbers + following + '</div></nav>'
        )

    return (
        BRIEFINGS_CSS + PREMIUM_BRIEFINGS_CSS + nav("thinking")
        + '<main>'
        '<section class="be-hero" data-analytics-section="briefings-introduction">'
        '<div class="container be-hero-inner">'
        '<div class="be-hero-copy">'
        '<p class="be-eyebrow">Thinking / Executive AI Briefings</p>'
        '<h1>AI changes the options. <em>Leadership makes the call.</em></h1>'
        '<p class="be-hero-deck">'
        'Independent perspectives for leaders making consequential AI choices. '
        'Understand the trade-off, test the evidence and know what to ask next.'
        '</p>'
        '<div class="be-hero-actions">'
        '<a class="be-primary-action" href="#briefings-library" '
        'data-hq-event="briefings_explore_library">Explore the briefings <span aria-hidden="true">↓</span></a>'
        '<a class="be-text-action" href="?page=contact" target="_self" '
        'data-hq-event="briefings_hero_contact">Discuss an AI decision ↗</a>'
        '</div>'
        '<p class="be-hero-attribution">An independent editorial series by '
        '<strong>Jair Ribeiro</strong> · Enterprise AI &amp; Data Leadership</p>'
        '</div>'
        '<div class="be-lens" role="group" aria-label="Four questions to guide an AI decision">'
        '<div class="be-lens-header"><span>The executive decision lens</span>'
        '<span>01 / 04</span></div>'
        '<h2 class="be-lens-title">Before a decision moves forward.</h2>'
        '<ol class="be-lens-steps">'
        '<li><b>01</b><div><strong>What business result matters?</strong>'
        '<p>Start with the work that needs to change.</p></div></li>'
        '<li><b>02</b><div><strong>Who has the authority?</strong>'
        '<p>Name the decision owner and limits.</p></div></li>'
        '<li><b>03</b><div><strong>What evidence is enough?</strong>'
        '<p>Challenge assumptions before committing.</p></div></li>'
        '<li><b>04</b><div><strong>What happens next?</strong>'
        '<p>Proceed, hold or change course with intent.</p></div></li>'
        '</ol>'
        '<div class="be-lens-footer"><span>Business before technology</span>'
        '<span>Jair Ribeiro / Briefings</span></div></div>'
        '</div></section>'
        '<section class="be-bridge" aria-label="How the briefings help">'
        '<div class="container be-bridge-inner">'
        '<div class="be-bridge-label">A short read. A clearer decision.</div>'
        '<div class="be-bridge-item"><b>01 / FRAME</b><span>Define the choice</span></div>'
        '<div class="be-bridge-item"><b>02 / TEST</b><span>Examine the evidence</span></div>'
        '<div class="be-bridge-item"><b>03 / ACT</b><span>Set the next move</span></div>'
        '</div></section>'
        '<section class="be-collection" id="briefings-library" '
        'data-analytics-section="briefings-library">'
        '<div class="container">'
        '<div class="be-section-heading"><div>'
        '<span class="briefings-index">The editor\'s desk</span>'
        '<h2>Decisions worth getting right.</h2></div>'
        '<p>Each issue stands on its own: a real question, '
        'a reasoned perspective and a useful next step.</p></div>'
        + '<div class="be-collection-subheading">'
        '<h2>Explore the library</h2>'
        f'<span>{count_label}</span></div>'
        + catalog
        + pagination
        + '<div class="be-afterword">'
        '<p><strong>Built for executive attention.</strong> '
        'Read the judgment first; go deeper into the rationale, '
        'decision map and cited sources when you need to.</p>'
        '<a href="?page=contact" target="_self" '
        'data-hq-event="briefings_library_contact">Bring your own decision ↗</a>'
        '</div></div></section>'
        + contact_block() + '</main>' + footer()
    )


def executive_briefing_article(
    article, read_metadata: str, image: str, tags: str, source: str,
    share_footer: str, cms_css: str,
) -> str:
    """Render an independent article, exposing its principal content directly.

    The CMS supplies editorial context and source references; the dedicated decision map supplies the primary operating architecture.
    The seven-question guide has a curated executive structure of its own.
    """
    from thinking_core import THINKING_CSS

    if article.slug == GOVERNANCE_SLUG:
        return governance_briefing_article(article, share_footer, cms_css)

    if article.slug == DUAL_GOV_SLUG:
        from data_vs_ai_governance_briefing import dual_governance_briefing_article
        return dual_governance_briefing_article(
            article, tags, source, share_footer, cms_css, BRIEFINGS_CSS, contact_block(),
            infographic_html=_article_infographic(article),
        )

    if article.slug == FUNDING_SLUG:
        from data_governance_funding_briefing import funding_briefing_article
        return funding_briefing_article(
            article, tags, source, share_footer, cms_css, BRIEFINGS_CSS, contact_block(),
            infographic_html=_article_infographic(article),
        )

    # This article is a complete seven-lens executive playbook, not a three-check
    # summary. Give it its own responsive reading surface and keep the original
    # published Content Studio body + references available as supplemental depth.
    if article.slug == "seven-questions-for-better-ai-decisions":
        from seven_questions_guide import SEVEN_QUESTIONS_CSS, seven_questions_body

        return (
            THINKING_CSS + cms_css + BRIEFINGS_CSS + SEVEN_QUESTIONS_CSS
            + nav("thinking")
            + '<main class="briefing-reader aiq-guide-reader">'
            '<section class="briefing-reader-hero" data-analytics-section="briefing-reader-introduction">'
            '<div class="container"><a class="briefing-reader-back" href="?page=briefings" '
            'target="_self">← Executive AI Briefings</a>'
            '<span class="briefings-index">Executive field guide · seven decision lenses</span>'
            f'<h1>{escape(article.title)}</h1>'
            '<p>A field-informed way to challenge AI proposals, expose assumptions '
            'and leave the room with a defensible decision, clear ownership and measurable next steps.</p>'
            '</div></section>'
            + '<section class="section paper"><div class="container">'
            + _article_infographic(article) + '</div></section>'
            + seven_questions_body()
            + '<div class="aiq-guide-container aiq-research">'
            '<details class="briefing-reader-detail" data-analytics-section="briefing-reader-depth">'
            '<summary>Background reading, editorial context and source references</summary>'
            f'<div class="article-body briefing-reader-research">{article.content_html}{tags}{source}</div>'
            '</details><div class="briefing-reader-share">' + share_footer + '</div>'
            '</div>' + contact_block() + '</main>' + footer()
        )

    guide = (FIRST_DECISION if article.slug == FIRST_SLUG else
             ADOPTION_DECISION if article.slug == ADOPTION_SLUG else
             SECURITY_DECISION if article.slug == SECURITY_SLUG else
             AI_ACT_DECISION if article.slug == AI_ACT_SLUG else
             GOVERNANCE_DECISION if article.slug == GOVERNANCE_SLUG else {
        "call": "Make the business decision explicit.",
        "move": "Name the accountable owner, decide which evidence would change your answer and test the assumption before expanding.",
        "checks": (
            ("The outcome", "What business result needs to improve?", "target"),
            ("The trade-off", "What could go wrong, and who can authorize the decision?", "shield"),
            ("The evidence", "What would justify the next investment?", "chart"),
        ),
    })
    if article.slug == "ai-was-approved-who-can-stop-it":
        guide = {
            "call": "Operating permission must include the power to intervene.",
            "move": "Name the accountable owner, test who can pause operations and define when changes trigger a new review.",
            "checks": (
                ("Accountability", "Who remains answerable after the project team leaves?", "target"),
                ("Human authority", "Who may pause or override without waiting for a committee?", "shield"),
                ("Review gate", "Which changed model, data or purpose withdraws the current approval?", "chart"),
            ),
        }
    if article.slug == "beyond-ai-pilots-operating-decisions-to-scale":
        guide = {
            "call": "Scale the operating service, not the demonstration.",
            "move": "Select one proven use case; approve its receiving process owner, redesigned workflow, bounded AI authority, operating controls and outcome measures before expanding.",
            "checks": (
                ("Business outcome", "What changed in cost, quality, speed or service relative to the baseline?", "target"),
                ("Operating ownership", "Who owns the process, exception handling and the service after project handover?", "workflow"),
                ("Authority and evidence", "What can AI do, who can stop it, and what results justify continued use?", "shield"),
            ),
        }
    checks = ''.join(
        '<div class="briefing-reader-check">' + briefing_icon(symbol)
        + f'<div><strong>{escape(title)}</strong><p>{escape(question)}</p></div></div>'
        for title, question, symbol in guide["checks"]
    )
    # Technical capability reference belongs to the actual article, never the
    # briefing-library landing. The six categories overlap: not a ladder.
    capabilities = ''.join(
        '<article class="briefings-capability">' + briefing_icon(icon) + '<div>'
        f'<span>{escape(category)}</span><h3>{escape(name)}</h3>'
        f'<p>{escape(description)}</p></div></article>'
        for category, name, description, icon in CAPABILITIES
    )
    decision_map = (
        '<section class="briefing-reader-decision-map" id="briefings-capability-map" '
        'data-analytics-section="briefings-capability-map">'
        '<span class="briefings-index">Executive decision map</span>'
        '<h2>Which capability does your decision actually need?</h2>'
        '<p>Choose what the work requires before debating models or vendors. '
        'Machine learning, generative AI, retrieval-augmented generation and '
        'agents are complementary approaches—not a ladder of sophistication.</p>'
        f'<div class="briefings-map">{capabilities}</div></section>'
    ) if article.slug == FIRST_SLUG else (governance_decision_map()
                                         if article.slug == GOVERNANCE_SLUG else '')
    # The seven-layer operating architecture stays visible. Detailed rationale
    # remains accessible but does not duplicate its seven proof points on screen.
    # The ROI poster is also in the published CMS body, so older Streamlit
    # deployments can show it without a second infographic-store request.
    # Move that single figure directly below the executive judgment here,
    # rather than displaying two graphics after the new reader deploys.
    roi_inline_visual = ""
    body_html = article.content_html
    if article.slug == "ai-roi-what-executives-must-prove-before-scaling":
        match = re.search(
            r'<figure\s+class="cms-roi-inline-visual"[^>]*>.*?</figure>',
            body_html, flags=re.S,
        )
        if match:
            roi_inline_visual = match.group(0)
            body_html = body_html[:match.start()] + body_html[match.end():]
    full_article = (
        '<details class="briefing-reader-detail" data-analytics-section="briefing-reader-full-article">'
        '<summary>Read the full reasoning, application example and source references</summary>'
        f'<div class="article-body briefing-reader-research">{body_html}{tags}{source}</div>'
        '</details>'
    ) if article.slug == GOVERNANCE_SLUG else (
        '<article class="briefing-full-content" data-analytics-section="briefing-reader-full-article">'
        '<div class="briefing-full-content-head"><span class="briefings-index">The full briefing</span>'
        '<h2>Reasoning, examples and practical considerations</h2>'
        '<p>The complete published perspective, with the reasoning and operational considerations behind the decision.</p></div>'
        f'<div class="article-body briefing-reader-research">{body_html}{tags}{source}</div>'
        '</article>'
    )
    summary_text = (
        "A release decision is conditional. Real accountability needs an owner, an effective stop and override route, an auditable decision trail and a review trigger when circumstances change."
        if article.slug == "ai-was-approved-who-can-stop-it" else
        "Skill and willingness are task-specific starting points, not employee labels. "
        "Test work readiness before choosing coaching, delegated ownership, evidence-led challenge or trust-building support."
        if article.slug == ADOPTION_SLUG else
        "A safe release requires evidence at four boundaries: information trust, authority to act, "
        "behavioral assurance and operational accountability. Controls reduce risk but cannot guarantee it away."
        if article.slug == SECURITY_SLUG else
        "The AI Act does not classify products by their marketing label. Start with purpose, "
        "context, legal role and evidence; apply controls proportionate to the actual duty."
        if article.slug == AI_ACT_SLUG else
        "Make the operating permissions, business outcome and evidence for approval explicit before expanding AI use."
    )
    return (
        THINKING_CSS + cms_css + BRIEFINGS_CSS + nav("thinking")
        + '<main class="briefing-reader">'
        '<section class="briefing-reader-hero" data-analytics-section="briefing-reader-introduction">'
        '<div class="container"><a class="briefing-reader-back" href="?page=briefings" '
        'target="_self">← All Executive AI Briefings</a>'
        '<div class="briefings-index">Executive AI Briefing · Independent edition</div>'
        f'<h1>{escape(article.title)}</h1>'
        f'<p>{escape(article.subtitle or article.excerpt)}</p></div></section>'
        '<section class="section paper briefing-reader-body" data-analytics-section="briefing-reader-summary">'
        '<div class="container"><section class="briefing-reader-summary">'
        '<div><span class="briefings-index">The Leadership Decision</span>'
        f'<h2>{escape(guide["call"])}</h2>'
        f'<p>{escape(summary_text)}</p>'
        '<div class="briefing-reader-next"><strong>Next move</strong>'
        f'<p>{escape(guide["move"])}</p></div></div>'
        f'<div class="briefing-reader-checks">{checks}</div></section>'
        + (roi_inline_visual or _article_infographic(article))
        + decision_map
        + full_article
        + f'<div class="briefing-reader-share">{share_footer}</div>'
        '</div></section>' + contact_block() + '</main>' + footer()
    )


def executive_briefing_page() -> str:
    """Dedicated publication route; never accidentally show an unrelated article."""
    import streamlit as st
    from site_cms import fetch_public_article, render_cms_article

    slug = st.query_params.get("article", "")
    if isinstance(slug, list):
        slug = slug[0] if slug else ""
    slug = str(slug).strip().lower()
    try:
        article = fetch_public_article(slug) if slug else None
    except (RuntimeError, ValueError, TimeoutError):
        article = None
    if article is not None and article.kind.strip().casefold() == BRIEFING_KIND.casefold():
        return render_cms_article(article)
    return (
        BRIEFINGS_CSS + nav("thinking")
        + '<main><section class="briefings-library-hero"><div class="container">'
        '<p class="eyebrow">Executive AI Briefings</p>'
        '<h1>This briefing is not available.</h1>'
        '<p class="briefings-library-deck">It may have been unpublished or the link may have changed.</p>'
        '<p><a class="btn" href="?page=briefings" target="_self">'
        'Return to the briefing library →</a></p>'
        '</div></section></main>' + footer()
    )
