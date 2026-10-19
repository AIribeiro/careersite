from __future__ import annotations

import html
from site_assets import WORKSHOP_URI
from site_components import nav, footer, opportunity, journey_next
from site_artifacts import leadership_frameworks
from career_facts import KIMBERLY_SCOPE, KIMBERLY_TITLE, MSX_PUBLIC_DATES, MSX_ROADMAP, VOLVO_AI_INITIATIVES, VOLVO_AI_LEARNING_SESSIONS, VOLVO_CURRENT_DATES, VOLVO_SENIOR_AI_DATES, VOLVO_WORKFLOW_SCOPE


def case(org: str, role: str, date: str, scope: str, title: str, intro: str, boxes: list[tuple[str, str]]) -> str:
    box_html = "".join(f'<div class="box"><span>{html.escape(k)}</span><p>{html.escape(v)}</p></div>' for k, v in boxes)
    return f'<article class="case"><div class="casemeta"><div class="org">{html.escape(org)}</div><strong>{html.escape(role)}</strong><span>{html.escape(date)}</span><div class="proof" style="margin-top:16px">{html.escape(scope)}</div></div><div><h2>{html.escape(title)}</h2><p>{html.escape(intro)}</p><div class="caseboxes">{box_html}</div></div></article>'


def impact() -> str:
    cases = [
        case(
            "MSX International",
            "AI & Data Center of Excellence Director",
            f"{MSX_PUBLIC_DATES.replace(' - ', ' – ')} · Göteborg, Sweden",
            "Enterprise CoE mandate across strategy, operations, technology and business leaders · AI portfolio · governance · data foundations · adoption",
            "Building the foundations for an enterprise AI & Data capability.",
            "The mandate was to put clearer foundations under an emerging AI & Data capability while portfolio management, data governance, adoption and business engagement were still maturing together.",
            [
                ("Situation", "AI opportunities existed across business areas, but visibility, prioritization, decision rights and readiness criteria were inconsistent. Data governance also needed a practical starting point."),
                ("My responsibility", "I led the AI and data excellence agenda across the organization, shaping the CoE foundations: portfolio structure, lifecycle stages, governance mechanisms, maturity assessment, data stewardship, adoption connections and the capability model needed to mature the function."),
                ("Trade-off", "The question was how much structure the organization could use productively at that stage. Too little would preserve ambiguity; too much would create bureaucracy before the operating habits existed."),
                ("Decision / contribution", f"I favored a small number of connected decision mechanisms: clearer portfolio visibility, practical lifecycle discipline, risk-aware criteria, stewardship and the proof needed before broader use. I also connected the maturity assessment to a pragmatic {MSX_ROADMAP.replace('-', '–')} roadmap rather than treating maturity as a score in isolation."),
                ("What changed", f"The CoE became a more defined business-facing capability: a visible AI opportunity portfolio, clearer lifecycle stages and responsibilities, a {MSX_ROADMAP.replace('-', '–')} maturity roadmap, initial data-ownership and stewardship foundations, and explicit capability gaps that informed the creation of new roles."),
            ],
        ),
        case(
            "Volvo Group / Volvo Trucks",
            "Data Analytics and AI Leader",
            f"{VOLVO_CURRENT_DATES.replace(' - ', ' – ')} · Göteborg, Sweden",
            f"Commercial operations · {VOLVO_WORKFLOW_SCOPE} · Microsoft 365 Copilot and agent initiatives · cross-functional adoption",
            "Bringing enterprise AI into commercial workflows with responsible use.",
            "Within Volvo Trucks commercial operations, the challenge was connecting AI opportunities to actual workflows, accountable business teams, technical feasibility and adoption, rather than measuring progress in experiments alone.",
            [
                ("Situation", f"Warranty, sales and aftermarket teams had distinct processes, information needs and stakeholder dependencies; additional use cases touched legal, compliance and sustainability."),
                ("My responsibility", "I led business-facing AI adoption, use-case and stakeholder work across commercial operations, including Microsoft 365 Copilot and agent initiatives and work with Digital & IT and business owners."),
                ("Trade-off", "Fast demonstrations and broad awareness could build interest, but operational use required clearer ownership, human review, appropriate controls and practical changes in day-to-day work."),
                ("Decision / contribution", "I connected use-case choices and literacy with the workflows where AI would be used, engaging cross-functional stakeholders and keeping human oversight part of the approach."),
                ("What changed", f"AI solutions and agents were introduced into {VOLVO_WORKFLOW_SCOPE} workflows. Practical AI learning activity reached thousands of employees globally; no unverified productivity or financial outcomes are claimed."),
            ],
        ),
        case(
            "Kimberly-Clark",
            KIMBERLY_TITLE.replace(" - ", " – "),
            "Jul 2021 – Sep 2022 · EMEA",
            f"EMEA role · reporting directly to the Chief Data & Analytics Officer · {KIMBERLY_SCOPE}",
            "Making AI opportunities comparable without losing the business context.",
            "Value discovery across EMEA meant working with functions that had different problems, data realities and readiness levels. A solution-first approach risked producing technically interesting ideas with weak business responsibility; an overly standardized approach risked ignoring the differences that made each opportunity viable or not.",
            [
                ("Situation", "Manufacturing, supply chain, logistics, sales and marketing teams were exploring different AI and data-science opportunities with different value cases and levels of readiness."),
                ("My responsibility", "In a global role reporting directly to the CDAO, I led value discovery and realization work across EMEA, helping business leaders and data-science teams frame the problem, expected value, feasibility and delivery considerations in a form both sides could work with."),
                ("Trade-off", "The tension was consistency versus context: create enough structure to compare opportunities, but not so much that the method replaced the business reality behind each one."),
                ("Decision / contribution", "I started from the business problem and value hypothesis before moving to the technical solution, using value-engineering thinking to make assumptions and delivery implications visible early."),
                ("What changed", "The work gave business and data-science teams a more consistent basis for comparing opportunities, exposing assumptions earlier and deciding which ideas were ready for deeper investment."),
            ],
        ),
        case(
            "Volvo Group",
            "Senior Artificial Intelligence Business Expert",
            f"{VOLVO_SENIOR_AI_DATES.replace(' - ', ' – ')} · Wroclaw, Poland",
            "AI & ML Center of Excellence · business requirements · product and stakeholder management · practitioner communities",
            "Building the business-facing practices around an emerging enterprise AI capability.",
            "In the earlier Volvo chapter, the work focused on shaping AI opportunities across functions and regions while strengthening the business and practitioner capabilities needed to collaborate with specialists.",
            [
                ("Situation", "Business units were exploring AI and ML applications with different levels of technical maturity, problem definition and stakeholder understanding."),
                ("My responsibility", "I led business-requirement, product and stakeholder activities across a broad set of AI initiatives and supported enterprise AI & ML CoE capability building."),
                ("Trade-off", "The organization needed enough shared language and discipline to select useful work without turning education or PoC activity into a proxy for business results."),
                ("Decision / contribution", f"I helped translate business demand into tractable AI initiatives and delivered {VOLVO_AI_LEARNING_SESSIONS} AI learning sessions. Across this and my later Volvo chapter, my combined portfolio work covered {VOLVO_AI_INITIATIVES} AI initiatives, PoCs and projects."),
                ("What changed", "Enterprise practitioners had more opportunities to build AI literacy and engage with an organized AI community; business and technical teams had a clearer basis for discussing use cases and requirements."),
            ],
        ),
    ]

    foundation = '''<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Foundation · IBM</p><h2>Where the business-translation thread started.</h2></div><p><strong>Cloud and AI Project Manager | IBM Watson Solution Designer · Jul 2017 – Jun 2018 · Wroclaw, Poland</strong></p></div><p style="max-width:860px">Watson solution design and client-facing cloud and AI work put me directly at the boundary between technical possibility and client need. The recurring lesson was to start with the user and business problem, make assumptions visible and only then connect them to feasible technical choices.</p><div class="grid3" style="margin-top:28px"><article class="card"><span class="org">Problem framing</span><h3>Keep platform capability from defining the problem</h3><p>Client conversations were stronger when the decision, process or user need came before a demonstration of what the technology could do.</p></article><article class="card"><span class="org">Design thinking</span><h3>Make context and assumptions explicit</h3><p>IBM Design Thinking and solution-design practices helped connect user context, business need and technical feasibility before solution positioning moved too far.</p></article><article class="card"><span class="org">Career thread</span><h3>A foundation for the work that followed</h3><p>That translation discipline became the starting point for later work in value discovery, enterprise adoption, portfolio decisions and the structures around AI &amp; Data.</p></article></div></div></section>'''

    practice = f'''<section class="section white"><div class="container speak"><img src="{WORKSHOP_URI}" alt="Jair Ribeiro presenting to an enterprise audience" loading="lazy" decoding="async"><div><p class="eyebrow">Working across functions</p><h2>Much of the work happens across boundaries rather than through hierarchy.</h2><p>Much of my work has involved leading across organizational boundaries rather than through hierarchy — bringing business owners, Digital & IT, architects, analytics specialists, governance teams and practitioners into the same decision.</p><p>That work includes executive stakeholder communication, translating between technical and business perspectives, facilitating difficult trade-offs and building enough shared understanding for responsibility to become explicit. The aim is not agreement for its own sake. It is a better decision and a clearer next step.</p></div></div></section>'''

    technical = '''<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Why the technical foundation matters</p><h2>Technical fluency supports better leadership judgment.</h2></div><p>My earlier work across IBM, HPE and Volvo covered cloud, infrastructure, enterprise systems, Watson solution design, consulting and client-facing technology delivery. That background helps me engage engineers, architects and data specialists, understand the consequences of architecture and data choices, and challenge trade-offs around scalability, security, cost, governance and operational readiness. Specialist depth should remain with the specialists responsible for those decisions.</p></div><div class="grid3"><article class="card"><span class="org">Systems thinking</span><h3>Architecture changes the answer</h3><p>A use case that works in isolation may fail once integration, security, data access, supportability and scale enter the picture. My technical foundation helps surface those constraints before they become late delivery surprises.</p></article><article class="card"><span class="org">Specialist dialogue</span><h3>Make technical disagreement useful</h3><p>I can work through trade-offs with engineers, architects and data specialists while keeping specialist accountability where it belongs. The point is to make consequences visible enough for the right person to decide.</p></article><article class="card"><span class="org">Business translation</span><h3>Technology still has to fit the business reality</h3><p>Client-facing solution design taught me to connect technical possibility with cost, operating reality, stakeholder expectations and the problem the organization is actually trying to solve.</p></article></div></div></section>'''

    return f'''{nav("impact")}<main><section class="pagehero"><div class="container"><p class="eyebrow">Selected experience</p><h1>What changed, what I was accountable for, and the trade-offs behind it.</h1><p>Across these roles, the work moved from business translation and value discovery into enterprise adoption, portfolio choices, governance and AI &amp; Data operating structures.</p></div></section>{practice}<section class="section paper"><div class="container">{"".join(cases)}</div></section>{foundation}{leadership_frameworks()}<section class="section navy"><div class="container"><div class="head"><div><p class="eyebrow">Recurring trade-offs</p><h2>The tensions repeat. The balance changes with context.</h2></div><p>These are recurring enterprise decisions rather than universal rules. I try to make the tension explicit, identify what needs to be demonstrated and decide what level of structure the organization can use productively at that point.</p></div><div class="flow"><div class="step"><span>01</span><strong>Speed ↔ governance</strong></div><div class="step"><span>02</span><strong>Experiment ↔ scale</strong></div><div class="step"><span>03</span><strong>Central ↔ federated</strong></div><div class="step"><span>04</span><strong>Ambition ↔ data maturity</strong></div><div class="step"><span>05</span><strong>Sophistication ↔ adoption</strong></div><div class="step"><span>06</span><strong>Volume ↔ investment focus</strong></div></div><p class="flowcopy">Early experimentation may need speed; broader use needs stronger proof and clearer responsibility. Central capability can accelerate learning; distributed accountability is usually required for adoption. The useful leadership question is when the balance has to move.</p></div></section>{technical}{journey_next("impact")}{opportunity()}</main>{footer()}'''
