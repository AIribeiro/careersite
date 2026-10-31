from __future__ import annotations

import html

from site_assets import THINKING_PANEL_URI, PANEL_DIALOGUE_URI, LINKEDIN, MEDIUM
from site_components import nav, footer, journey_next, opportunity, THOUGHTS, thought_grid
from thinking_articles import article_by_key, article_relative_url
from thinking_core import THINKING_CSS


CURRENT_PRIMARY = "stop_ai_use_case"
CURRENT_SECONDARY = "roi_diagnosed_too_late"

RECENT = [
    ("stop_ai_use_case", "When a technically promising AI use case should be stopped rather than scaled by default.", "thinking_recent_stop_open"),
    ("roi_diagnosed_too_late", "Why the business value question belongs at the start of an AI initiative, not after deployment.", "thinking_recent_roi_open"),
    ("coe_not_ai_department", "Why the center should build distributed capability rather than become the permanent owner of AI work.", "thinking_recent_coe_open"),
    ("strategy_to_value_framework", "A five-link management model connecting AI ambition to investment, responsible scale, changed work and outcomes.", "thinking_recent_strategy_value_open"),
    ("investable_portfolio", "Why an inventory of ideas becomes strategic only when leaders choose, sequence and stop.", "thinking_recent_portfolio_open"),
    ("adoption_metric", "Licenses and active users show reach, not whether real work has changed.", "thinking_recent_adoption_metric_open"),
    ("pilot_to_scale", "Why technical success does not yet prove ownership, adoption or operating readiness.", "thinking_recent_pilot_scale_open"),
    ("governance_accountability", "Controls can be tiered. Human accountability for consequential use cannot be implicit.", "thinking_recent_governance_open"),
]

UPCOMING = [
    ("Point of view · AI Governance", "AI Governance That Helps Teams Move Faster", "How proportionate guardrails can reduce uncertainty and speed responsible decisions."),
    ("Point of view · AI Adoption", "What AI Adoption Looks Like Beyond License Usage", "What changes when adoption is measured through workflows, decisions and behavior rather than access."),
    ("Point of view · AI Strategy", "Why AI Strategy Without an Operating Model Usually Fails", "Why ambition stalls when ownership, decision rights and execution mechanisms stay implicit."),
    ("Field note · Strategy & Delivery", "The Missing Owner Between AI Strategy and Delivery", "A look at the accountability gap between enterprise intent and day-to-day execution."),
    ("Point of view · Operating Capability", "What Changes When AI Moves From Experiment to Operating Capability", "The organizational shift from proving possibility to running AI as part of normal operations."),
    ("Point of view · AI Value", "AI ROI Is Often an Operating Problem Before It Is a Technology Problem", "Why value leakage often begins in workflow design, ownership and adoption before model performance becomes the issue."),
]


def _recent_cards() -> str:
    cards = []
    for key, desc, event in RECENT:
        article = article_by_key(key)
        cards.append(
            f'<a class="recent-card" href="{html.escape(article_relative_url(article), quote=True)}" target="_self" data-hq-event="{html.escape(event)}">'
            f'<span class="kicker">{html.escape(article.kind_topic)}</span><h3>{html.escape(article.title)}</h3><p>{html.escape(desc)}</p><span class="read">Read →</span></a>'
        )
    return '<div class="recent-grid">' + ''.join(cards) + '</div>'


def _upcoming_preview() -> str:
    items = []
    for label, title, desc in UPCOMING:
        items.append(
            f'<article class="upcoming-item"><span class="kicker">{html.escape(label)}</span>'
            f'<strong>{html.escape(title)}</strong><p>{html.escape(desc)}</p></article>'
        )
    return (
        '<section class="upcoming-wrap"><div class="upcoming-head"><div><p class="eyebrow">On my radar</p>'
        '<h3>Topics for upcoming articles.</h3></div>'
        '<p>The next topics focus on enterprise AI and data situations where new capability creates a harder operating decision.</p></div>'
        '<div class="upcoming-grid">' + ''.join(items) + '</div></section>'
    )



SPEAKING_CSS = r'''<style>
.speaking-feature{background:#111d2d;color:#f1f3f4;padding:70px 0 68px}
.speaking-feature .eyebrow{color:#dfaa82}
.speaking-intro{display:grid;grid-template-columns:minmax(0,1.16fr) minmax(290px,.84fr);gap:42px;align-items:end;margin-bottom:32px}
.speaking-intro h2{margin:14px 0 0;font:500 clamp(35px,4.2vw,58px)/1.08 Georgia,serif;letter-spacing:-.027em;color:#fff}
.speaking-intro>p{margin:0 0 3px;max-width:470px;color:#c1cbd8;font-size:16px;line-height:1.75}
.speaking-layout{display:grid;grid-template-columns:minmax(0,.94fr) minmax(0,1.06fr);gap:18px;align-items:stretch}
.speaking-photo{min-width:0;min-height:456px;position:relative;margin:0;overflow:hidden;border:1px solid rgba(255,255,255,.17);background:#182a42}
.speaking-photo img{display:block;width:100%;height:100%;position:absolute;inset:0;object-fit:cover;object-position:center}
.speaking-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(8,17,30,.96),rgba(8,17,30,.02) 63%)}
.speaking-photo figcaption{position:absolute;bottom:0;left:0;right:0;z-index:1;padding:29px 28px;display:flex;flex-direction:column;gap:8px}
.speaking-photo figcaption span,.speaking-record .record-meta{font:800 10px/1.4 Inter,Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#e6ae85}
.speaking-photo figcaption strong{font:500 clamp(23px,2.35vw,35px)/1.16 Georgia,serif;color:#fff}
.speaking-photo figcaption small{font:400 13px/1.5 Inter,Arial,sans-serif;color:#d1dae3}
.speaking-records{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.speaking-record{min-width:0;min-height:219px;padding:23px 21px;display:flex;flex-direction:column;gap:11px;background:#1d2c40;border:1px solid rgba(255,255,255,.14);text-decoration:none!important;transition:border-color .15s ease,background .15s ease}
.speaking-record:hover,.speaking-record:focus-visible{border-color:#e3ae86;background:#253751}
.speaking-record strong{font:500 clamp(19px,2vw,26px)/1.16 Georgia,serif;color:#fff}
.speaking-record .record-detail{font:400 13px/1.55 Inter,Arial,sans-serif;color:#c2ced9}
.speaking-record .record-link{margin-top:auto;padding-top:9px;font:750 11px/1.4 Inter,Arial,sans-serif;color:#f0c4a5}
.speaking-bottom{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:22px;margin-top:24px}
.speaking-bottom p{margin:0;font:400 13px/1.6 Inter,Arial,sans-serif;color:#acb9c7}
.speaking-about-link{display:inline-flex;align-items:center;gap:17px;padding:14px 20px;border:1px solid #d5a17e;color:#fff!important;text-decoration:none!important;font:750 12px/1.4 Inter,Arial,sans-serif}
.speaking-about-link:hover,.speaking-about-link:focus-visible{background:#d5a17e;color:#101c2b!important}
@media(max-width:1050px){.speaking-intro{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(18px,3.5vw,32px);align-items:center}.speaking-intro>p{max-width:none;width:100%}.speaking-layout{grid-template-columns:1fr}.speaking-photo{min-height:390px}.speaking-records{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.speaking-feature{padding:46px 0}.speaking-intro{grid-template-columns:minmax(0,1fr);gap:16px}.speaking-intro>p{max-width:none}.speaking-intro h2{font-size:36px}.speaking-intro>p{font-size:15px}.speaking-photo{min-height:285px}.speaking-photo figcaption{padding:20px}.speaking-records{grid-template-columns:1fr}.speaking-record{min-height:0;padding:22px}.speaking-bottom{align-items:stretch}.speaking-about-link{justify-content:space-between;width:100%;box-sizing:border-box}}
@media(prefers-reduced-motion:reduce){.speaking-record{transition:none}}
</style>'''



THINKING_APPROACH_CSS = r'''<style>
/* Four equal-size tiles: a consistent 2x2 grid on iPad and desktop. */
.thinking-approach-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  grid-auto-rows:minmax(305px,1fr);
  gap:20px;
  align-items:stretch;
}
.thinking-approach-grid>.thinking-approach-tile{
  box-sizing:border-box;
  width:100%;
  height:100%;
  min-width:0;
  min-height:0;
  margin:0;
}
.thinking-approach-grid>.card{
  padding:clamp(22px,2.8vw,34px);
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.thinking-approach-grid>.card h3{
  margin:20px 0 12px;
  font-size:clamp(22px,2.5vw,30px);
  line-height:1.2;
}
.thinking-approach-grid>.card p{
  margin:0;
  font-size:clamp(13px,1.3vw,15px);
  line-height:1.65;
}
.thinking-approach-photo{
  position:relative;
  overflow:hidden;
  border:1px solid var(--line);
  background:#111b2c;
}
.thinking-approach-photo img{
  display:block;
  position:absolute;
  inset:0;
  width:100%;
  height:100%;
  max-width:none;
  object-fit:cover;
  object-position:center 28%;
}
@media (min-width:701px) and (max-width:900px){
  .thinking-approach-grid{gap:16px;grid-auto-rows:minmax(315px,1fr)}
  .thinking-approach-grid>.card{padding:22px}
  .thinking-approach-grid>.card h3{font-size:24px}
  .thinking-approach-grid>.card p{font-size:13px}
}
@media (max-width:700px){
  .thinking-approach-grid{grid-template-columns:minmax(0,1fr);grid-auto-rows:auto;gap:16px}
  .thinking-approach-grid>.card{min-height:0;padding:25px}
  .thinking-approach-photo{height:auto!important;min-height:320px!important}
}
</style>'''


def landing() -> str:
    primary = article_by_key(CURRENT_PRIMARY)
    secondary = article_by_key(CURRENT_SECONDARY)
    return f'''{THINKING_CSS}{SPEAKING_CSS}{THINKING_APPROACH_CSS}{nav("thinking")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Thinking · Articles &amp; Knowledge Sharing</p><h1>What I’ve learned about AI—and what I’m still questioning.</h1><p>My articles draw on the decisions and trade-offs I’ve faced in enterprise AI and Data leadership: what to prioritize, how to govern responsibly, what makes adoption real, and how to judge business value.</p><p>I share these perspectives to make practical experience useful to others, challenge my own assumptions and keep learning through conversation.</p></div></section>
<section class="section paper" data-analytics-section="thinking-executive-briefings"><div class="container">
<div class="head"><div><p class="eyebrow">Executive AI Briefings</p><h2>AI, explained through business decisions.</h2></div><p>A distinct series of concise executive explanations, informed by enterprise leadership experience and organized around the next decision—not technology terminology alone.</p></div>
<div class="actions"><a class="btn dark" href="?page=briefings" target="_self" data-hq-event="thinking_briefings_open">Explore Executive AI Briefings →</a></div>
</div></section>
<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Selected writing</p><h2>Explore the articles.</h2></div><p>Explore practical perspectives on AI priorities, accountability, adoption, governance and business value.</p></div>{_recent_cards()}{_upcoming_preview()}</div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Further reading</p><h2>Longer perspectives behind the decisions.</h2></div><p>Longer pieces on strategy, value, operating models, governance, data readiness and adoption. They give more context to the shorter, current material above.</p></div>{thought_grid(THOUGHTS,"articles")}<div class="actions"><a class="btn dark" href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_thinking">More writing on Medium ↗</a><a class="btn dark" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_thinking">LinkedIn ↗</a></div></div></section>
<section class="section white thinking-approach" data-analytics-section="thinking-approach"><div class="container">
<div class="head"><div><p class="eyebrow">Approach</p><h2>Each piece starts from a concrete operating decision.</h2></div><p>The focus is on the situation, the trade-off, what changes the answer, and what the next decision requires.</p></div>
<div class="thinking-approach-grid">
<article class="card thinking-approach-tile"><span class="org">Situation first</span><h3>Start with what is actually happening</h3><p>A pilot has no clear owner, governance arrives too late, a strong use case has weak business pull, or adoption looks good in a dashboard while the work itself has not changed. The operating consequence is usually more useful than the abstract theme.</p></article>
<article class="card thinking-approach-tile"><span class="org">Trade-off</span><h3>Make the trade-off visible</h3><p>Most enterprise choices are not solved by a universal best practice. The useful questions are what changes the answer, who carries the consequence and where a compromise is worth making.</p></article>
<article class="card thinking-approach-tile"><span class="org">Practical use</span><h3>End with a decision, not a slogan</h3><p>A useful piece should help someone frame the problem better, challenge an assumption or make the next decision with more confidence.</p></article>
<figure class="thinking-approach-photo thinking-approach-tile"><img src="{THINKING_PANEL_URI}" alt="Jair Ribeiro sharing perspectives at an AI industry discussion" loading="lazy" decoding="async"></figure>
</div></div></section>
<section class="section speaking-feature" data-analytics-section="speaking-publications-feature" aria-labelledby="speaking-heading">
<div class="container">
<div class="speaking-intro"><div><p class="eyebrow">Speaking &amp; publications</p><h2 id="speaking-heading">Ideas tested beyond the page.</h2></div><p>I also take these conversations into conferences, panels and external publications. The themes remain close to my work: business adoption, AI governance, accountability and what it takes to scale.</p></div>
<div class="speaking-layout">
<figure class="speaking-photo"><img src="{PANEL_DIALOGUE_URI}" alt="Jair Ribeiro taking part in the Financial Times Future of AI Summit panel" loading="lazy" decoding="async"><figcaption><span>On stage · 2023</span><strong>Financial Times Future of AI Summit</strong><small>Discussing how AI becomes part of business operations.</small></figcaption></figure>
<div class="speaking-records">
<a class="speaking-record" href="https://www.smau.it/stockholm/schedule/driving-transformation-through-ai-and-digitalisation" target="_blank" rel="noopener noreferrer" data-hq-event="thinking_speaking_smau">
<span class="record-meta">2026 · Panel</span><strong>SMAU Stockholm</strong><span class="record-detail">AI and digitalisation in business ecosystems, with leaders from industry and academia.</span><span class="record-link">Official event record ↗</span></a>
<a class="speaking-record" href="https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/" target="_blank" rel="noopener noreferrer" data-hq-event="thinking_speaking_digitalfirst">
<span class="record-meta">2026 · Publication</span><strong>Digital First Magazine</strong><span class="record-detail">Why AI governance needs to support accountable, repeatable use—not simply control.</span><span class="record-link">Read the publication ↗</span></a>
<a class="speaking-record" href="https://eco-cdn.iqpc.com/eco/files/event_content/chief-ai-officcer-exchange-europe-event-agenda-2024SUq6T8hBKVXfnBqCHm3LLUYAgsH9fL5OPo5cKlEK.pdf" target="_blank" rel="noopener noreferrer" data-hq-event="thinking_speaking_caio">
<span class="record-meta">2024 · Keynote</span><strong>Chief AI Officer Exchange Europe</strong><span class="record-detail">Getting the business on board through AI literacy, storytelling and adoption.</span><span class="record-link">Official agenda ↗</span></a>
<a class="speaking-record" href="https://www.edreamsodigeo.com/press-releases/2023/11/edreams-odigeo-shares-insights-on-infusing-ai-into-business-operations-at-the-financial-times-future-of-ai-summit/" target="_blank" rel="noopener noreferrer" data-hq-event="thinking_speaking_ft">
<span class="record-meta">2023 · Panel</span><strong>Financial Times Future of AI Summit</strong><span class="record-detail">A discussion about bringing AI beyond specialist teams and into business operations.</span><span class="record-link">Event coverage ↗</span></a>
</div></div>
<div class="speaking-bottom"><p>A selected record of external contributions, rather than a complete events archive.</p><a class="speaking-about-link" href="?page=about#speaking-publications" target="_self" data-hq-event="thinking_speaking_about">Explore the full speaking &amp; publication record <span aria-hidden="true">→</span></a></div>
</div></section>{journey_next("thinking")}</main>{footer()}'''
