from __future__ import annotations

"""Decision-first Executive AI Briefings, with original graphical artwork.

Only published Content Studio records are presented as published briefings.
Original article bodies, citations and attribution remain available on demand.
"""

from html import escape

from briefings_visual import PROMO_CSS, briefing_icon, briefing_visual
from site_assets import EMAIL
from site_components import nav, footer, journey_next
from site_cms import fetch_published_articles, article_relative_url

BRIEFING_KIND = "Executive Briefing"
FIRST_SLUG = "ai-capabilities-executive-decisions"

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
.site .briefing-reader-bottom{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:22px 0 8px;padding:23px 27px;background:#1a3144;color:#fff}
.site .briefing-reader-bottom p{margin:0;max-width:700px;color:#d5e0e7;font:400 13px/1.6 Arial,sans-serif}
.site .briefing-reader-bottom a{display:inline-block;flex:0 0 auto;color:#13283a!important;background:#e6bc99;padding:13px 17px;text-decoration:none!important;font:800 12px/1.3 Arial,sans-serif}
@media(max-width:900px){.site .briefings-library-grid{grid-template-columns:minmax(0,1fr)}.site .briefing-reader-summary{grid-template-columns:1fr}.site .briefings-library-card h3{font-size:clamp(26px,4vw,34px)}.site .briefings-art-options{max-width:100%}}
@media(max-width:650px){.site .briefings-library-hero{padding:40px 0}.site .briefings-library-section{padding:29px 0 45px}.site .briefings-library-heading{align-items:start}.site .briefings-library-count{white-space:normal;text-align:right}.site .briefings-library-card-body{padding:22px}.site .briefings-catalog-art{height:160px;padding:19px}.site .briefings-art-numbers{gap:4px}.site .briefings-art-numbers b{height:36px;font-size:13px}.site .briefing-reader-summary,.site .briefing-reader-decision-map{padding:20px}.site .briefing-reader-decision-map .briefings-map{grid-template-columns:minmax(0,1fr)}.site .briefing-full-content{padding:21px}.site .briefing-reader-bottom{flex-direction:column;align-items:start;padding:22px}.site .briefing-reader-bottom a{width:100%;box-sizing:border-box;text-align:center}.site .briefings-library-card-foot{flex-wrap:wrap}}
@media(prefers-reduced-motion:reduce){.site .briefings-library-card{transition:none}}
</style>'''


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
    if slug == FIRST_SLUG:
        return (
            '<div class="briefings-catalog-art" aria-hidden="true">'
            '<span class="briefings-catalog-art-kicker">The capability choice</span>'
            '<div class="briefings-art-options"><span>Predict</span>'
            '<span>Generate</span><span>Act</span></div>'
            '<div class="briefings-art-connector">Business outcome · Permission · Evidence</div></div>'
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
    """Library landing: one independent card and destination per publication."""
    items = published_briefings()
    cards = []
    for index, article in enumerate(items, 1):
        featured = article.slug == FIRST_SLUG
        url = escape(article_relative_url(article), quote=True)
        cards.append(
            f'<a class="briefings-library-card" href="{url}" target="_self" '
            f'data-hq-event="{"briefings_featured_open" if featured else "briefings_article_open"}" '
            f'data-hq-content-slug="{escape(article.slug, quote=True)}" '
            f'aria-label="Read {escape(article.title, quote=True)}">'
            + _briefing_catalog_art(article.slug)
            + '<div class="briefings-library-card-body">'
            f'<div class="briefings-library-card-meta"><span>Briefing {index:02d}</span>'
            '<span>Executive perspective</span></div>'
            f'<h3>{escape(article.title)}</h3>'
            f'<p>{escape(article.subtitle or article.excerpt)}</p>'
            f'<div class="briefings-library-card-foot"><span>{escape(article.published_label)}'
            f' · {article.read_minutes} min read</span><strong>Open briefing →</strong></div>'
            '</div></a>'
        )
    catalogue = (
        '<div class="briefings-library-grid">' + ''.join(cards) + '</div>'
        if cards else
        '<div class="briefings-library-empty"><h3>No published briefings yet.</h3>'
        '<p>The library will show each briefing here after publication. '
        'You can still contact me to discuss a specific executive AI decision.</p></div>'
    )
    return (
        BRIEFINGS_CSS + nav("thinking")
        + '<main><section class="briefings-library-hero" '
        'data-analytics-section="briefings-introduction"><div class="container">'
        '<p class="eyebrow">Thinking / Executive AI Briefings</p>'
        '<h1>Make the next AI decision a better one.</h1>'
        '<p class="briefings-library-deck">Clear, concise leadership perspectives on '
        'where AI belongs, what should be challenged and what evidence deserves investment. '
        'Each briefing stands on its own: a decision, its trade-offs and a practical next move.</p>'
        '<div class="briefings-library-intent">'
        '<span>Business value</span><span>Decision rights</span>'
        '<span>Responsible scale</span></div></div></section>'
        '<section class="section paper briefings-library-section" '
        'data-analytics-section="briefings-library"><div class="container">'
        '<div class="briefings-library-heading"><div>'
        '<span class="briefings-index">The library</span>'
        '<h2>Choose the decision you are facing.</h2></div>'
        f'<p class="briefings-library-count">{len(items)} published briefings</p></div>'
        + catalogue + '</div></section>'
        + contact_block() + '</main>' + footer()
    )


def executive_briefing_article(
    article, read_metadata: str, image: str, tags: str, source: str,
    share_footer: str, cms_css: str,
) -> str:
    """Render an independent article, exposing its principal content directly.

    The CMS remains authoritative for editorial content and source references.
    The seven-question guide has a curated executive structure of its own.
    """
    from thinking_core import THINKING_CSS

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
            '<p>A field-tested way to challenge AI proposals, expose assumptions '
            'and leave the room with a defensible decision, clear ownership and measurable next steps.</p>'
            '</div></section>'
            + seven_questions_body()
            + '<div class="aiq-guide-container aiq-research">'
            '<details class="briefing-reader-detail" data-analytics-section="briefing-reader-depth">'
            '<summary>Background reading, editorial context and source references</summary>'
            f'<div class="article-body briefing-reader-research">{article.content_html}{tags}{source}</div>'
            '</details><div class="briefing-reader-share">' + share_footer + '</div>'
            '</div>' + contact_block() + '</main>' + footer()
        )

    guide = FIRST_DECISION if article.slug == FIRST_SLUG else {
        "call": "Make the business decision explicit.",
        "move": "Name the accountable owner, decide which evidence would change your answer and test the assumption before expanding.",
        "checks": (
            ("The outcome", "What business result needs to improve?", "target"),
            ("The trade-off", "What could go wrong, and who can authorize the decision?", "shield"),
            ("The evidence", "What would justify the next investment?", "chart"),
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
    ) if article.slug == FIRST_SLUG else ''
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
        '<div><span class="briefings-index">The executive judgment</span>'
        f'<h2>{escape(guide["call"])}</h2>'
        '<p>Frame the work before the technology. These questions make the '
        'business outcome, permissions and evaluation criteria explicit.</p>'
        '<div class="briefing-reader-next"><strong>Next move</strong>'
        f'<p>{escape(guide["move"])}</p></div></div>'
        f'<div class="briefing-reader-checks">{checks}</div></section>'
        + decision_map
        + '<article class="briefing-full-content" data-analytics-section="briefing-reader-full-article">'
        '<div class="briefing-full-content-head"><span class="briefings-index">The full briefing</span>'
        '<h2>Reasoning, examples and practical considerations</h2>'
        '<p>The complete published perspective, with the reasoning and operational considerations behind the decision.</p></div>'
        f'<div class="article-body briefing-reader-research">{article.content_html}{tags}{source}</div>'
        '</article>'
        '<div class="briefing-reader-bottom"><p>'
        'Use the framework to challenge one real decision. If the answer depends '
        'on your business context, the next step is a conversation.</p>'
        '<a href="?page=contact" target="_self" '
        'data-hq-event="briefing_reader_contact">Discuss your decision →</a></div>'
        f'<div class="briefing-reader-share">{share_footer}</div>'
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
