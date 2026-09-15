from __future__ import annotations

import html
from site_assets import WORKSHOP_URI
from site_components import nav, footer, opportunity


def case(org: str, role: str, date: str, title: str, intro: str, boxes: list[tuple[str,str]]) -> str:
    box_html = "".join(f'<div class="box"><span>{html.escape(k)}</span><p>{html.escape(v)}</p></div>' for k,v in boxes)
    return f'<article class="case"><div class="casemeta"><div class="org">{html.escape(org)}</div><strong>{html.escape(role)}</strong><span>{html.escape(date)}</span></div><div><h2>{html.escape(title)}</h2><p>{html.escape(intro)}</p><div class="caseboxes">{box_html}</div></div></article>'


def impact() -> str:
    cases = [
        case(
            "MSX International",
            "AI & Data Center of Excellence Director",
            "Dec 2025 – Jun 2026 · Gothenburg",
            "Building decision discipline around an emerging AI & Data CoE.",
            "I joined a mandate where AI activity, data governance, adoption and business engagement all needed more structure at the same time. The leadership challenge was to introduce enough operating discipline to improve decisions without creating a governance layer the organization was not yet ready to absorb.",
            [
                ("Inherited problem","AI opportunities existed across business areas, but visibility, prioritization, ownership and scale-readiness were inconsistent. Data governance also needed a practical starting point."),
                ("What I owned","I owned the design of the CoE foundations: portfolio structure, lifecycle stages, governance logic, maturity assessment, data-stewardship concepts and the stabilization roadmap."),
                ("Decision / trade-off","The choice was not whether governance was needed, but how much structure to introduce before delivery maturity could absorb it. Too little would preserve ambiguity; too much would create bureaucracy before the operating habits existed."),
                ("What I chose","I favored a small number of connected decision mechanisms: clearer portfolio visibility, risk-aware criteria, lifecycle ownership, stewardship and evidence for scale-readiness rather than a heavy central control model."),
                ("What changed","The organization gained clearer portfolio visibility and prioritization, more explicit lifecycle discipline, and stronger foundations for data ownership, quality and responsible scale."),
            ],
        ),
        case(
            "Volvo Group / Volvo Trucks",
            "Data Analytics & AI Leader",
            "Aug 2022 – Dec 2025 · Gothenburg",
            "Turning broad AI interest into practical adoption across commercial operations.",
            "In a global industrial organization, the easy outcome is activity: more ideas, more pilots and more training. The harder outcome is a portfolio that connects business problems, enterprise technology, governance and the people who have to change how they work.",
            [
                ("Inherited problem","Warranty, sales and aftermarket teams had real opportunities for AI, but each use case sat inside different workflows, data conditions, stakeholders and enterprise constraints."),
                ("What I owned","I led AI and analytics adoption across those commercial areas, managed a portfolio of 100+ ideas and PoCs, and designed practical AI literacy and adoption activity reaching 1,000+ employees."),
                ("Decision / trade-off","The risk was equating volume with progress. More PoCs and more training could increase visible activity without creating adoption, ownership or a credible path into enterprise delivery."),
                ("What I chose","I treated adoption as both a portfolio and capability problem: connect use cases to real workflows, involve business and technical partners early, and make literacy practical enough to improve the quality of demand and everyday use."),
                ("What changed","The work created a more connected way to move between business need, AI opportunity, responsible use and delivery reality while increasing practical AI capability across a large employee population."),
            ],
        ),
        case(
            "Kimberly-Clark",
            "AI Strategist – EMEA",
            "Jul 2021 – Sep 2022 · EMEA",
            "Making AI opportunities comparable without losing the business context.",
            "Value discovery across EMEA meant working with functions that had different problems, data realities and readiness levels. A solution-first approach would have produced technically interesting ideas with weak business ownership; an overly standardized approach would have ignored the differences that made each use case viable or not.",
            [
                ("Inherited problem","Manufacturing, supply chain, logistics, sales and marketing teams were exploring different AI and data-science opportunities with different value cases and levels of readiness."),
                ("What I owned","I led value discovery and realization work across EMEA, helping business leaders and data-science teams frame the problem, expected value, feasibility and delivery considerations in a form both sides could work with."),
                ("Decision / trade-off","The tension was consistency versus context: create enough structure to compare opportunities, but not so much that the method replaced the business reality behind each one."),
                ("What I chose","I started from the business problem and value hypothesis before moving to the technical solution, using value-engineering thinking to make assumptions and delivery implications visible early."),
                ("What changed","The work created a clearer bridge between business priorities and data-science possibilities, improving the quality of opportunity framing and making cross-functional discussions more concrete."),
            ],
        ),
    ]

    practice = f'''<section class="section white"><div class="container speak"><img src="{WORKSHOP_URI}" alt="Jair Ribeiro in a cross-functional business discussion" loading="lazy" decoding="async"><div><p class="eyebrow">Leadership in practice</p><h2>Enterprise AI moves through conversation before it moves through technology.</h2><p>Much of the leadership work happens before a formal decision: getting business owners, technical specialists and governance stakeholders to describe the same problem in compatible language. That is where assumptions surface, ownership becomes visible and a promising idea either earns a credible next step or stops consuming attention.</p><p>The purpose of those conversations is not alignment for its own sake. It is better decision quality — enough shared understanding to make trade-offs explicit, assign ownership and move with confidence.</p></div></div></section>'''

    technical = '''<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Why the technical foundation matters</p><h2>Leadership decisions are better when the underlying constraints are understood.</h2></div><p>My earlier work across IBM, HPE and Volvo covered cloud, infrastructure, enterprise systems, Watson solution design, consulting and client-facing technology delivery. I do not use that background to claim current engineering depth; I use it to ask better questions and understand the consequences of technical choices.</p></div><div class="grid3"><article class="card"><span class="org">Systems thinking</span><h3>Architecture changes the answer</h3><p>A use case that works in isolation may fail once integration, security, data access, supportability and scale enter the picture. My technical foundation helps me surface those constraints before they become late delivery surprises.</p></article><article class="card"><span class="org">Specialist dialogue</span><h3>Challenge without pretending expertise</h3><p>I can engage engineers, architects and data specialists on trade-offs while keeping specialist ownership where it belongs. That creates better decisions than either deferring every technical question or overruling expert depth.</p></article><article class="card"><span class="org">Business translation</span><h3>Technology has to survive the business case</h3><p>Client-facing solution design taught me to connect technical possibility with cost, operating reality, stakeholder expectations and the problem the customer is actually trying to solve.</p></article></div></div></section>'''

    return f'''{nav("impact")}<main><section class="pagehero"><div class="container"><p class="eyebrow">Leadership impact</p><h1>Leadership evidence through decisions, not project lists.</h1><p>The cases below focus on the problem I inherited, what I personally owned, the trade-off that had to be managed, the choice I made or shaped, and what changed. That is a more useful test of senior leadership than a catalogue of initiatives.</p></div></section>{practice}<section class="section paper"><div class="container">{"".join(cases)}</div></section><section class="section navy"><div class="container"><div class="head"><div><p class="eyebrow">Recurring trade-offs</p><h2>The tensions repeat. The right answer depends on context.</h2></div><p>These are not abstract preferences. They are the decisions that determine whether AI work remains isolated or becomes part of how the enterprise operates. My approach is to make the tension explicit, identify what evidence matters and decide what level of structure the organization can use productively.</p></div><div class="flow"><div class="step"><span>01</span><strong>Speed ↔ governance</strong></div><div class="step"><span>02</span><strong>Experiment ↔ scale</strong></div><div class="step"><span>03</span><strong>Central ↔ federated</strong></div><div class="step"><span>04</span><strong>Ambition ↔ data maturity</strong></div><div class="step"><span>05</span><strong>Sophistication ↔ adoption</strong></div><div class="step"><span>06</span><strong>Volume ↔ investment focus</strong></div></div><p class="flowcopy">The point is not to choose one side permanently. Early experimentation may need speed; scale needs stronger evidence and ownership. Central capability can accelerate learning; distributed ownership is usually required for adoption. Senior leadership is knowing when the balance has to move.</p></div></section>{technical}{opportunity()}</main>{footer()}'''
