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


def landing() -> str:
    primary = article_by_key(CURRENT_PRIMARY)
    secondary = article_by_key(CURRENT_SECONDARY)
    return f'''{THINKING_CSS}{nav("thinking")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Articles &amp; Perspectives</p><h1>My thinking on AI, data and business value.</h1><p>Through these articles, I share how I approach the decisions that shape enterprise AI and data: where to focus, how to govern responsibly, what drives adoption, and how to turn strategy into measurable results.</p><p>I write to explore ideas, challenge assumptions, and share the reasoning, trade-offs, and practical experience behind my perspectives on AI and data leadership.</p></div></section>
<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Selected writing</p><h2>Explore the articles.</h2></div><p>Explore practical perspectives on AI priorities, accountability, adoption, governance and business value.</p></div>{_recent_cards()}{_upcoming_preview()}</div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Further reading</p><h2>Longer perspectives behind the decisions.</h2></div><p>Longer pieces on strategy, value, operating models, governance, data readiness and adoption. They give more context to the shorter, current material above.</p></div>{thought_grid(THOUGHTS,"articles")}<div class="actions"><a class="btn dark" href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_thinking">More writing on Medium ↗</a><a class="btn dark" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_thinking">LinkedIn ↗</a></div></div></section>
<section class="section white"><div class="container editorial-split"><div><p class="eyebrow">Approach</p><h2>Each piece starts from a concrete operating decision.</h2><p>The focus is on the situation, the trade-off, what changes the answer, and what the next decision requires.</p><div class="grid3" style="margin-top:24px"><article class="card"><span class="org">Situation first</span><h3>Start with what is actually happening</h3><p>A pilot has no clear owner, governance arrives too late, a strong use case has weak business pull, or adoption looks good in a dashboard while the work itself has not changed. The operating consequence is usually more useful than the abstract theme.</p></article><article class="card"><span class="org">Trade-off</span><h3>Make the trade-off visible</h3><p>Most enterprise choices are not solved by a universal best practice. The useful questions are what changes the answer, who carries the consequence and where a compromise is worth making.</p></article><article class="card"><span class="org">Practical use</span><h3>End with a decision, not a slogan</h3><p>A useful piece should help someone frame the problem better, challenge an assumption or make the next decision with more confidence.</p></article></div></div><div class="editorial-photo portrait"><img src="{THINKING_PANEL_URI}" alt="Jair Ribeiro listening during an industry panel discussion" loading="lazy" decoding="async"></div></div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Research &amp; speaking</p><h2>Related work beyond the articles.</h2></div><p>Selected research, conference participation and publications are documented separately.</p></div><div class="actions"><a class="btn dark" href="?page=presence" target="_self">Speaking &amp; publications →</a></div></div></section>{journey_next("thinking")}</main>{footer()}'''
