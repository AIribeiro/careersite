from __future__ import annotations

import html

from site_assets import THINKING_PANEL_URI, PANEL_DIALOGUE_URI, LINKEDIN, MEDIUM
from site_components import nav, footer, opportunity, THOUGHTS, thought_grid
from thinking_articles import article_by_key, article_relative_url
from thinking_core import THINKING_CSS


CURRENT_PRIMARY = "stop_ai_use_case"
CURRENT_SECONDARY = "roi_diagnosed_too_late"

RECENT = [
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
        '<h3>Questions I’m working through next.</h3></div>'
        '<p>The next topics are driven by what I’m seeing in enterprise AI and data right now, especially where new capability creates a harder operating decision.</p></div>'
        '<div class="upcoming-grid">' + ''.join(items) + '</div></section>'
    )


def landing() -> str:
    primary = article_by_key(CURRENT_PRIMARY)
    secondary = article_by_key(CURRENT_SECONDARY)
    return f'''{THINKING_CSS}{nav("thinking")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Thinking</p><h1>Notes on enterprise AI decisions, operating models, adoption and value.</h1><p>These pieces start from recurring enterprise situations and focus on the decision: where to invest, what to stop, how to assign ownership, and how to connect adoption with value.</p></div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Current questions</p><h2>Current notes on AI portfolio, governance, adoption and value.</h2></div><p>Questions that recur when new technology has to become a practical choice about value, ownership, adoption or execution.</p></div>
<div class="thinking-now"><article class="featured-thinking"><div class="kicker">{html.escape(primary.kind_topic)}</div><h2>{html.escape(primary.title)}</h2><p>AI portfolios need explicit exit criteria. A technically credible use case can still be the wrong place for the next unit of investment — and continuing by default is not portfolio discipline.</p><a class="read-live" href="{html.escape(article_relative_url(primary), quote=True)}" target="_self" data-hq-event="thinking_current_stop_open">Read the field note →</a><div class="meta">{html.escape(primary.published_label)} · {html.escape(primary.topic)} · {primary.read_minutes} min</div></article>
<article class="decision-note"><div class="kicker">{html.escape(secondary.kind_topic)}</div><h3>{html.escape(secondary.title)}</h3><p>If value only becomes a serious question after deployment, the portfolio has already missed the most useful moment to shape it.</p><a class="read-live" style="margin-top:18px;font-size:11px;font-weight:850;text-decoration:none" href="{html.escape(article_relative_url(secondary), quote=True)}" target="_self" data-hq-event="thinking_current_roi_open">Read note →</a><div class="meta">{html.escape(secondary.published_label)} · {html.escape(secondary.topic)} · {secondary.read_minutes} min</div></article></div>
<div class="format-strip"><div class="format-card"><span>Point of view</span><strong>Where I take a position</strong><p>Clear arguments on enterprise AI and data choices where leaders have to make a trade-off.</p></div><div class="format-card"><span>Field notes</span><strong>Patterns from real enterprise work</strong><p>What recurring situations have taught me about ownership, adoption, data and execution.</p></div><div class="format-card"><span>Decision notes</span><strong>The call I would make</strong><p>Short answers to a specific leadership decision, with the reasoning behind them.</p></div><div class="format-card"><span>Frameworks</span><strong>Tools for better decisions</strong><p>Simple models I use to structure portfolio, operating-model, adoption and value questions.</p></div></div>
<div class="themebar"><span>AI Strategy</span><span>Operating Models</span><span>AI Governance</span><span>Adoption</span><span>Portfolio &amp; Value</span><span>Data &amp; Analytics Leadership</span></div></div></section>
<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">More leadership questions</p><h2>The operating problems behind AI ambition.</h2></div><p>Earlier pieces stay here because the same questions keep returning: scaling, accountability, portfolio choices, adoption, data and value.</p></div>{_recent_cards()}{_upcoming_preview()}</div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Leading in the AI Enterprise</p><h2>Deeper essays behind the decisions.</h2></div><p>Longer pieces on strategy, value, operating models, governance, data readiness and adoption. They give more context to the shorter, current material above.</p></div>{thought_grid(THOUGHTS,"articles")}<div class="actions"><a class="btn dark" href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_thinking">More writing on Medium ↗</a><a class="btn dark" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_thinking">LinkedIn ↗</a></div></div></section>
<section class="section white"><div class="container editorial-split"><div><p class="eyebrow">Approach</p><h2>Each piece starts from a concrete operating decision.</h2><p>The focus is on the situation, the trade-off, what changes the answer, and what the next decision requires.</p><div class="grid3" style="margin-top:24px"><article class="card"><span class="org">Situation first</span><h3>Start with what is actually happening</h3><p>A pilot has no clear owner, governance arrives too late, a strong use case has weak business pull, or adoption looks good in a dashboard while the work itself has not changed. The operating consequence is usually more useful than the abstract theme.</p></article><article class="card"><span class="org">Trade-off</span><h3>Make the trade-off visible</h3><p>Most enterprise choices are not solved by a universal best practice. The useful questions are what changes the answer, who carries the consequence and where a compromise is worth making.</p></article><article class="card"><span class="org">Practical use</span><h3>End with a decision, not a slogan</h3><p>A useful piece should help someone frame the problem better, challenge an assumption or make the next decision with more confidence.</p></article></div></div><div class="editorial-photo portrait"><img src="{THINKING_PANEL_URI}" alt="Jair Ribeiro listening during an industry panel discussion" loading="lazy" decoding="async"></div></div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Research &amp; speaking</p><h2>Related work beyond the articles.</h2></div><p>Selected research, conference participation and publications are documented separately.</p></div><div class="actions"><a class="btn dark" href="?page=presence" target="_self">Speaking &amp; publications →</a></div></div></section></main>{footer()}'''
