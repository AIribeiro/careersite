from __future__ import annotations

import html

from site_assets import THINKING_PANEL_URI, PANEL_DIALOGUE_URI, LINKEDIN, MEDIUM
from site_components import nav, footer, opportunity, THOUGHTS, thought_grid
from thinking_core import THINKING_CSS


RECENT = [
    ("Point of view · AI Operating Model", "The AI CoE Should Not Become the Company’s AI Department", "Why the center should build distributed capability rather than become the permanent owner of AI work.", "coe-not-ai-department", "thinking_recent_coe_open"),
    ("Framework · Enterprise AI", "Strategy → Portfolio → Governance → Adoption → Value", "A five-link management model connecting AI ambition to investment, responsible scale, changed work and outcomes.", "strategy-to-value", "thinking_recent_strategy_value_open"),
    ("Field note · Portfolio & Value", "From AI Use-Case List to Investable Portfolio", "Why an inventory of ideas becomes strategic only when leaders choose, sequence and stop.", "investable-portfolio", "thinking_recent_portfolio_open"),
    ("Decision note · AI Adoption", "One AI adoption metric I don’t trust.", "Licenses and active users show reach, not whether real work has changed.", "adoption-metric", "thinking_recent_adoption_metric_open"),
    ("Point of view · Enterprise AI", "Why Enterprise AI Often Stalls Between Pilot and Scale", "Why technical success does not yet prove ownership, adoption or operating readiness.", "pilot-to-scale", "thinking_recent_pilot_scale_open"),
    ("Decision note · AI Governance", "The AI governance gate I would never remove.", "Controls can be tiered. Human accountability for consequential use cannot be implicit.", "governance-accountability", "thinking_recent_governance_open"),
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
    for label, title, desc, slug, event in RECENT:
        cards.append(
            f'<a class="recent-card" href="?page=thinking&amp;article={html.escape(slug)}" target="_self" data-hq-event="{html.escape(event)}">'
            f'<span class="kicker">{html.escape(label)}</span><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><span class="read">Read →</span></a>'
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
        '<section class="upcoming-wrap"><div class="upcoming-head"><div><p class="eyebrow">Coming next</p>'
        '<h3>Questions I’m working through next.</h3></div>'
        '<p>A short preview of the editorial agenda ahead — the operating questions I plan to explore as this body of work develops.</p></div>'
        '<div class="upcoming-grid">' + ''.join(items) + '</div></section>'
    )


def landing() -> str:
    return f'''{THINKING_CSS}{nav("thinking")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Thinking</p><h1>Current thinking on the decisions behind enterprise AI.</h1><p>I use this page as a working record of the operating questions I keep encountering: what deserves investment, what is ready to scale, where governance helps or gets in the way, how ownership should work and what turns AI activity into durable business capability.</p></div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">What I’m thinking about now</p><h2>Fresh arguments, short notes and practical frameworks.</h2></div><p>New material appears here first. The purpose is not publishing volume; it is to make the judgment behind enterprise AI and Data leadership visible while the questions are still current.</p></div>
<div class="thinking-now"><article class="featured-thinking"><div class="kicker">Field note · Portfolio &amp; Value</div><h2>When an AI Use Case Should Be Stopped</h2><p>AI portfolios need explicit exit criteria. A technically credible use case can still be the wrong place for the next unit of investment — and continuing by default is not portfolio discipline.</p><a class="read-live" href="?page=thinking&amp;article=stop-ai-use-case" target="_self" data-hq-event="thinking_week4_stop_open">Read the field note →</a><div class="meta">17 Sep 2026 · Portfolio &amp; Value · 5 min</div></article>
<article class="decision-note"><div class="kicker">Decision note · AI Value</div><h3>AI ROI is often diagnosed too late.</h3><p>If value only becomes a serious question after deployment, the portfolio has already missed the most useful moment to shape it.</p><a class="read-live" style="margin-top:18px;font-size:11px;font-weight:850;text-decoration:none" href="?page=thinking&amp;article=roi-diagnosed-too-late" target="_self" data-hq-event="thinking_week4_roi_open">Read note →</a><div class="meta">17 Sep 2026 · AI Value · 1 min</div></article></div>
{_upcoming_preview()}
<div class="format-strip"><div class="format-card"><span>Point of view</span><strong>A position worth defending</strong><p>Longer arguments on enterprise AI decisions, trade-offs and operating choices.</p></div><div class="format-card"><span>Field notes</span><strong>What practice teaches</strong><p>Observations shaped by recurring patterns in enterprise work.</p></div><div class="format-card"><span>Decision notes</span><strong>One judgment, briefly</strong><p>Short positions on a specific leadership or governance decision.</p></div><div class="format-card"><span>Frameworks</span><strong>Reusable ways to think</strong><p>Simple models for portfolio, operating-model, adoption and value questions.</p></div></div>
<div class="themebar"><span>AI Strategy</span><span>Operating Models</span><span>AI Governance</span><span>Adoption</span><span>Portfolio &amp; Value</span><span>Data &amp; Analytics Leadership</span></div></div></section>
<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Recent thinking</p><h2>Earlier topics remain part of the working record.</h2></div><p>Current material moves to the top without disappearing when the next argument is published.</p></div>{_recent_cards()}</div></section>
<section class="section paper"><div class="container"><div class="head"><div><p class="eyebrow">Leading in the AI Enterprise</p><h2>Selected essays from the longer series.</h2></div><p>The archive provides deeper context around strategy, value, operating models, governance, data readiness and adoption. The newer material above is where the page stays current.</p></div>{thought_grid(THOUGHTS,"articles")}<div class="actions"><a class="btn dark" href="{MEDIUM}" target="_blank" rel="noopener" data-hq-event="medium_thinking">More writing on Medium ↗</a><a class="btn dark" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_thinking">LinkedIn ↗</a></div></div></section>
<section class="section white"><div class="container editorial-split"><div><p class="eyebrow">How I use writing</p><h2>A point of view is useful only when it improves a decision.</h2><p>I write selectively, usually when a recurring operating question is worth working through. The strongest pieces start from tensions I have seen in enterprise work and force me to take a position I would be willing to defend with a leadership team.</p><div class="grid3" style="margin-top:24px"><article class="card"><span class="org">Experience first</span><h3>Start from a real operating tension</h3><p>Governance versus speed, experimentation versus scale, centralized expertise versus business responsibility, or technical possibility versus adoption. These tensions produce better thinking than trend summaries.</p></article><article class="card"><span class="org">Judgment</span><h3>State the trade-off clearly</h3><p>Most enterprise decisions are not solved by a universal best practice. I try to explain what changes the answer, what information matters and which compromise I would choose in a given context.</p></article><article class="card"><span class="org">Practical use</span><h3>Leave the reader with a better question</h3><p>The useful test is whether a piece helps someone frame a problem or decision more clearly, challenge an assumption or make the next choice with more precision.</p></article></div></div><div class="editorial-photo portrait"><img src="{THINKING_PANEL_URI}" alt="Jair Ribeiro listening during an industry panel discussion" loading="lazy" decoding="async"></div></div></section>
<section class="section paper"><div class="container speak"><img src="{PANEL_DIALOGUE_URI}" alt="Jair Ribeiro contributing to a conference panel discussion" loading="lazy" decoding="async"><div><p class="eyebrow">External context</p><h2>Writing, speaking and research extend the operating perspective.</h2><p>The same questions appear in practice, research and executive conversations. Writing and speaking give me another way to test whether an argument remains useful outside the context in which it was formed.</p><div class="prooflist"><div class="proofitem"><strong>Thinkers360</strong> — Top 50 Global Thought Leaders &amp; Influencers on Emerging Technology (2023).</div><div class="proofitem"><strong>Generative AI Summit 2023, London</strong> — keynote on scaling AI adoption across the enterprise.</div><div class="proofitem"><strong>Research focus</strong> — MSc work on Responsible AI adoption in global enterprises.</div></div></div></div></section>{opportunity()}</main>{footer()}'''
