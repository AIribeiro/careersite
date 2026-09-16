from __future__ import annotations

import html
from site_assets import WORKSHOP_URI
from site_components import nav, footer, opportunity
from site_artifacts import leadership_frameworks


def case(org: str, role: str, date: str, title: str, intro: str, boxes: list[tuple[str, str]]) -> str:
    box_html = "".join(f'<div class="box"><span>{html.escape(k)}</span><p>{html.escape(v)}</p></div>' for k, v in boxes)
    return f'<article class="case"><div class="casemeta"><div class="org">{html.escape(org)}</div><strong>{html.escape(role)}</strong><span>{html.escape(date)}</span></div><div><h2>{html.escape(title)}</h2><p>{html.escape(intro)}</p><div class="caseboxes">{box_html}</div></div></article>'


def impact() -> str:
    cases = [
        case(
            "MSX International",
            "AI & Data Center of Excellence Director",
            "Dec 2025 – Jun 2026 · Gothenburg",
            "Building the foundations for an enterprise AI & Data capability.",
            "The six-month mandate was not about claiming a company-wide transformation. It was about putting clearer foundations under an emerging AI and Data capability while portfolio management, data governance, adoption and business engagement were still maturing together.",
            [
                ("Situation", "AI opportunities existed across business areas, but visibility, prioritization, ownership and scale-readiness were inconsistent. Data governance also needed a practical starting point."),
                ("My responsibility", "I was responsible for shaping the CoE foundations: portfolio structure, lifecycle stages, governance logic, maturity assessment, data-stewardship concepts and a stabilization roadmap."),
                ("Trade-off", "The question was how much structure the organization could use productively at that stage. Too little would preserve ambiguity; too much would create bureaucracy before the operating habits existed."),
                ("What I chose / influenced", "I favored a small number of connected decision mechanisms: clearer portfolio visibility, risk-aware criteria, lifecycle ownership, stewardship and evidence for scale-readiness rather than a heavy central control model."),
                ("What changed", "The work established clearer foundations for portfolio prioritization, lifecycle ownership, data stewardship and responsible scale. It also made the remaining organizational dependencies more explicit."),
            ],
        ),
        case(
            "Volvo Group / Volvo Trucks",
            "AI leadership roles across Volvo Group and Volvo Trucks",
            "Jun 2018 – Dec 2025 · Poland / Sweden",
            "Connecting AI opportunity, adoption and enterprise reality across two Volvo AI roles.",
            "Across my Volvo AI roles, the recurring challenge was not a shortage of ideas. It was helping different business areas connect real workflows, data conditions, Digital & IT constraints, governance and the people expected to use the capability.",
            [
                ("Situation", "AI opportunities ranged from enterprise-wide use-case work and practitioner communities to commercial operations such as warranty, sales and aftermarket, each with different stakeholders and readiness."),
                ("My responsibility", "I shaped and supported use cases, portfolio discussions, business translation, literacy and adoption activity, working across business owners, Digital & IT, analytics specialists and enterprise communities."),
                ("Trade-off", "Visible activity can be mistaken for progress. More PoCs and more training can increase momentum without creating ownership, changed workflows or a credible path into enterprise delivery."),
                ("What I chose / influenced", "I treated adoption as both a portfolio and capability problem: connect use cases to real work, involve business and technical partners early, and make literacy practical enough to improve the quality of demand and everyday use."),
                ("What changed", "Across these roles, I shaped and supported 100+ AI initiatives, PoCs and projects. At Volvo Trucks, adoption activity reached 1,000+ employees while the work increasingly connected AI opportunity with workflow, governance and delivery reality."),
            ],
        ),
        case(
            "Kimberly-Clark",
            "AI Strategist – EMEA",
            "Jul 2021 – Sep 2022 · EMEA",
            "Making AI opportunities comparable without losing the business context.",
            "Value discovery across EMEA meant working with functions that had different problems, data realities and readiness levels. A solution-first approach risked producing technically interesting ideas with weak business ownership; an overly standardized approach risked ignoring the differences that made each opportunity viable or not.",
            [
                ("Situation", "Manufacturing, supply chain, logistics, sales and marketing teams were exploring different AI and data-science opportunities with different value cases and levels of readiness."),
                ("My responsibility", "I led value discovery and realization work across EMEA, helping business leaders and data-science teams frame the problem, expected value, feasibility and delivery considerations in a form both sides could work with."),
                ("Trade-off", "The tension was consistency versus context: create enough structure to compare opportunities, but not so much that the method replaced the business reality behind each one."),
                ("What I chose / influenced", "I started from the business problem and value hypothesis before moving to the technical solution, using value-engineering thinking to make assumptions and delivery implications visible early."),
                ("What changed", "The work created a clearer bridge between business priorities and data-science possibilities, improving the quality of opportunity framing and making cross-functional discussions more concrete."),
            ],
        ),
    ]

    practice = f'''<section class="section white"><div class="container speak"><img src="{WORKSHOP_URI}" alt="Jair Ribeiro presenting to an enterprise audience" loading="lazy" decoding="async"><div><p class="eyebrow">Leadership in practice</p><h2>Much of the work happens across boundaries rather than through hierarchy.</h2><p>Much of my work has involved leading across organizational boundaries rather than through hierarchy — bringing business owners, Digital &amp; IT, architects, analytics specialists, governance teams and practitioners into the same decision.</p><p>That work includes executive stakeholder communication, translating between technical and business perspectives, facilitating difficult trade-offs and building enough shared understanding for ownership to become explicit. The aim is not agreement for its own sake. It is a better decision and a clearer next step.</p></div></div></section>'''

    technical = '''<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Why the technical foundation matters</p><h2>Technical fluency supports better leadership judgment.</h2></div><p>My earlier work across IBM, HPE and Volvo covered cloud, infrastructure, enterprise systems, Watson solution design, consulting and client-facing technology delivery. That background helps me engage engineers, architects and data specialists, understand the consequences of architecture and data choices, and challenge trade-offs around scalability, security, cost, governance and operational readiness. Specialist depth should remain with the specialists responsible for those decisions.</p></div><div class="grid3"><article class="card"><span class="org">Systems thinking</span><h3>Architecture changes the answer</h3><p>A use case that works in isolation may fail once integration, security, data access, supportability and scale enter the picture. My technical foundation helps surface those constraints before they become late delivery surprises.</p></article><article class="card"><span class="org">Specialist dialogue</span><h3>Make technical disagreement useful</h3><p>I can work through trade-offs with engineers, architects and data specialists while keeping specialist ownership where it belongs. The point is to make consequences visible enough for the right owner to decide.</p></article><article class="card"><span class="org">Business translation</span><h3>Technology still has to fit the business reality</h3><p>Client-facing solution design taught me to connect technical possibility with cost, operating reality, stakeholder expectations and the problem the organization is actually trying to solve.</p></article></div></div></section>'''

    return f'''{nav("impact")}<main><section class="pagehero"><div class="container"><p class="eyebrow">Leadership impact</p><h1>Leadership evidence through situations, choices and trade-offs.</h1><p>The cases below focus on what I entered, what was difficult, what I was responsible for, the trade-off that had to be managed, what I chose or influenced and what changed. They are intended to show the judgment behind the CV bullet point.</p></div></section>{practice}<section class="section paper"><div class="container">{"".join(cases)}</div></section>{leadership_frameworks()}<section class="section navy"><div class="container"><div class="head"><div><p class="eyebrow">Recurring trade-offs</p><h2>The tensions repeat. The balance changes with context.</h2></div><p>These are recurring enterprise decisions rather than universal rules. I try to make the tension explicit, identify what evidence matters and decide what level of structure the organization can use productively at that point.</p></div><div class="flow"><div class="step"><span>01</span><strong>Speed ↔ governance</strong></div><div class="step"><span>02</span><strong>Experiment ↔ scale</strong></div><div class="step"><span>03</span><strong>Central ↔ federated</strong></div><div class="step"><span>04</span><strong>Ambition ↔ data maturity</strong></div><div class="step"><span>05</span><strong>Sophistication ↔ adoption</strong></div><div class="step"><span>06</span><strong>Volume ↔ investment focus</strong></div></div><p class="flowcopy">Early experimentation may need speed; broader use needs stronger evidence and ownership. Central capability can accelerate learning; distributed ownership is usually required for adoption. The useful leadership question is when the balance has to move.</p></div></section>{technical}{opportunity()}</main>{footer()}'''
