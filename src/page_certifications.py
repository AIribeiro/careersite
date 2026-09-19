from __future__ import annotations

import html

from site_components import nav, footer, opportunity
from site_media import eitca_eu_banner

LINKEDIN_CERTIFICATIONS = "https://www.linkedin.com/in/jairribeiro/details/certifications/"

EU_ROUND_EMBLEM = """<svg class="eu-round-emblem" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
<circle cx="32" cy="32" r="31" fill="#003399"/>
<g fill="#ffcc00" font-size="8" font-family="Arial, sans-serif" text-anchor="middle" dominant-baseline="middle">
<text x="32" y="9">★</text><text x="43.5" y="12">★</text><text x="52" y="20">★</text><text x="55" y="32">★</text>
<text x="52" y="44">★</text><text x="43.5" y="52">★</text><text x="32" y="55">★</text><text x="20.5" y="52">★</text>
<text x="12" y="44">★</text><text x="9" y="32">★</text><text x="12" y="20">★</text><text x="20.5" y="12">★</text>
</g></svg>"""

FLAGSHIP = [
    {
        "signal": "AI strategy",
        "title": "Generative AI for Executives and Business Leaders Specialization",
        "issuer": "IBM",
        "date": "Oct 2025",
        "credential": "X5XFLRL8YQ9K",
        "verify_url": "https://www.coursera.org/account/accomplishments/specialization/X5XFLRL8YQ9K",
        "program_url": "https://www.coursera.org/specializations/generative-ai-for-executives-and-business-leaders",
        "copy": "Connects GenAI use cases with business strategy, governance, compliance, feasibility and value at executive level.",
    },
    {
        "signal": "Responsible AI",
        "title": "Responsible Generative AI",
        "issuer": "University of Michigan",
        "date": "May 2025",
        "credential": "G7A2NUZLL0YJ",
        "verify_url": "https://www.coursera.org/account/accomplishments/specialization/G7A2NUZLL0YJ",
        "program_url": "https://www.coursera.org/specializations/responsible-generative-ai",
        "copy": "Covers responsible development, assessment, adoption and governance of generative AI, including policy, regulation, trust and organizational accountability.",
    },
    {
        "signal": "AI leadership & adoption",
        "title": "AI for Organizational Leaders",
        "issuer": "Microsoft + LinkedIn",
        "date": "Mar 2025",
        "credential": "",
        "verify_url": "https://www.linkedin.com/learning/certificates/94a24a7c132173b60320b2283bd9ac8a3aa66e4218af40c4d2bb2d4ad4df3e43",
        "program_url": "https://www.linkedin.com/learning/paths/ai-for-organizational-leaders-by-microsoft-and-linkedin",
        "copy": "Reinforces the leadership choices behind AI adoption: business strategy, Responsible AI, organization-wide capability and long-term value.",
    },
    {
        "signal": "Agentic AI leadership",
        "title": "Agentic AI and AI Agents: A Primer for Leaders",
        "issuer": "Vanderbilt University",
        "date": "May 2025",
        "credential": "YAMOO2UIDDPN",
        "verify_url": "https://www.coursera.org/account/accomplishments/records/YAMOO2UIDDPN",
        "program_url": "https://www.coursera.org/learn/agentic-ai",
        "copy": "Builds leadership-level understanding of how AI agents work and where agentic patterns can support decisions, automation and human-in-the-loop workflows.",
    },
    {
        "signal": "Current technical fluency",
        "title": "Fundamentals of Building AI Agents",
        "issuer": "IBM",
        "date": "May 2026",
        "credential": "VXKY3NPDNMW6",
        "verify_url": "https://www.coursera.org/account/accomplishments/records/VXKY3NPDNMW6",
        "program_url": "https://www.coursera.org/learn/fundamentals-of-building-ai-agents",
        "copy": "Adds practical fluency in agent reasoning and task execution, supporting informed discussion of agent architectures and delivery choices.",
    },
    {
        "signal": "Data platforms",
        "title": "Azure Databricks Platform Architect · Academy Accreditation",
        "issuer": "Databricks",
        "date": "Apr 2025",
        "credential": "141535340",
        "verify_url": "https://credentials.databricks.com/d1419d4d-9224-4749-81f7-948aee58d4c5",
        "program_url": "",
        "copy": "Strengthens architecture-level understanding of enterprise data platforms, including platform administration, networking, security and cloud integrations.",
    },
]

EITCA_COMPONENTS = [
    "Google Vision API",
    "Google Cloud Machine Learning",
    "TensorFlow Fundamentals",
    "Machine Learning with Python",
    "Deep Learning with TensorFlow",
    "Deep Learning with Python, TensorFlow and Keras",
    "Deep Learning with Python and PyTorch",
    "Advanced Deep Learning",
    "Advanced Reinforcement Learning",
    "Google Cloud Platform",
    "Python Programming Fundamentals",
    "TensorFlow Quantum Machine Learning",
]

PATHWAYS = [
    (
        "Enterprise AI leadership",
        "Strategy, adoption and organizational judgment.",
        [
            "Generative AI for Executives & Business Leaders · IBM · 2025",
            "AI for Organizational Leaders · Microsoft + LinkedIn · 2025",
            "Generative AI for Leaders · Vanderbilt University · 2025",
            "GenAI for Executives & Business Leaders: An Introduction · IBM · 2024",
            "AI For Everyone · DeepLearning.AI · 2019",
        ],
    ),
    (
        "Responsible AI & trust",
        "Governance, explainability and ethics as operating questions.",
        [
            "Responsible Generative AI · University of Michigan · 2025",
            "Explainable AI (XAI) · Duke University · 2025",
            "Data Science Ethics · University of Michigan · 2020",
            "Ethics in AI and Big Data · The Linux Foundation · 2020",
        ],
    ),
    (
        "Technical & platform fluency",
        "Technical depth for stronger architecture and engineering conversations.",
        [
            "EITCA/AI Artificial Intelligence Academy · 24 ECTS · 12 component certifications · 2025",
            "Azure Databricks Platform Architect · Databricks · 2025",
            "Fundamentals of Building AI Agents · IBM · 2026",
            "Microsoft Certified: Azure AI Fundamentals · 2021",
            "Microsoft Certified: Azure Data Fundamentals · 2021",
            "Introduction to Machine Learning · Duke University · 2021",
        ],
    ),
    (
        "Product, data & execution",
        "Product judgment, data management and translating AI into usable capability.",
        [
            "Data Integration, Data Storage, & Data Migration · SkillUp · 2026",
            "Generative AI for Product Managers · IBM / SkillUp · 2025",
            "IBM Product Management pathway · 4-course sequence · 2025",
            "Executive Data Science Specialization · Johns Hopkins University · 2020",
            "IBM Design Thinking Co-Creator · IBM · 2017",
        ],
    ),
]

FOUNDATION_TIMELINE = [
    (
        "2024–2026",
        "Agentic and generative AI",
        "AI agents, GenAI strategy, Responsible GenAI, product applications and data-management refreshers keep the learning record close to current enterprise AI practice.",
    ),
    (
        "2020–2023",
        "Governance, data and cloud",
        "AI ethics, executive data science, Azure AI/Data/Cloud fundamentals, predictive analytics and digital leadership strengthened the bridge between technology choices and enterprise accountability.",
    ),
    (
        "2017–2019",
        "AI delivery foundations",
        "IBM Watson, data platforms, chatbots, design thinking, machine-learning project structure and business-facing AI study supported the move from enterprise technology into AI roles.",
    ),
    (
        "2016",
        "Leadership foundation",
        "International Leadership and Organizational Behavior at Università Bocconi added formal study of leadership and organizational behavior to an already international technology career.",
    ),
]


def _credential_card(item: dict[str, str]) -> str:
    program_link = (
        f'<a href="{html.escape(item["program_url"], quote=True)}" target="_blank" rel="noopener">Program scope ↗</a>'
        if item.get("program_url")
        else ""
    )
    details = (
        f'<details class="cert-details"><summary>Credential ID</summary>'
        f'<span>{html.escape(item["credential"])}</span></details>'
        if item.get("credential")
        else ""
    )
    return (
        '<article class="cert-card">'
        '<div class="cert-card-head">'
        f'<span class="cert-kicker">{html.escape(item["signal"])}</span>'
        f'<span class="cert-date">{html.escape(item["date"])}</span>'
        "</div>"
        f'<h3>{html.escape(item["title"])}</h3>'
        f'<div class="cert-issuer">{html.escape(item["issuer"])}</div>'
        f'<p>{html.escape(item["copy"])}</p>'
        '<div class="cert-links">'
        f'<a class="cert-verify" href="{html.escape(item["verify_url"], quote=True)}" target="_blank" rel="noopener">Verify credential ↗</a>'
        f'{program_link}'
        "</div>"
        f'{details}'
        "</article>"
    )


def _pathway(title: str, copy: str, items: list[str]) -> str:
    rows = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return (
        '<article class="cert-path">'
        f'<h3>{html.escape(title)}</h3><p>{html.escape(copy)}</p>'
        f'<ul>{rows}</ul>'
        "</article>"
    )


def certifications() -> str:
    flagship = "".join(_credential_card(item) for item in FLAGSHIP)
    pathways = "".join(_pathway(title, copy, items) for title, copy, items in PATHWAYS)
    eitca = "".join(f"<li>{html.escape(item)}</li>" for item in EITCA_COMPONENTS)
    timeline = "".join(
        f'<div class="trow"><b>{html.escape(years)}</b><div><strong>{html.escape(title)}</strong>'
        f'<span>{html.escape(copy)}</span></div></div>'
        for years, title, copy in FOUNDATION_TIMELINE
    )

    return f'''{nav("certifications")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">About · Credentials</p><h1>Credentials supporting enterprise AI &amp; Data leadership.</h1><p>Operating experience is the primary evidence. Formal learning adds verifiable depth across AI strategy, governance, adoption, agentic AI, data platforms and technical foundations.</p><div class="actions"><a class="btn ghost" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications">View full LinkedIn credential record ↗</a></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Leadership relevance</p><h2>Where the credential record adds depth.</h2></div><p>The emphasis is on capabilities that increasingly sit together in enterprise AI leadership: strategic prioritization, measurable value, responsible governance, organizational adoption and enough technical fluency to make informed decisions.</p></div><div class="grid3 cert-signal-grid"><article class="card"><span class="org">01 · Strategy &amp; value</span><h3>From AI ambition to business priorities</h3><p>Executive AI study covers use-case selection, feasibility, investment choices, business value and the decisions needed to move from experimentation to scale.</p></article><article class="card"><span class="org">02 · Governance &amp; trust</span><h3>Responsible AI as an operating discipline</h3><p>Responsible AI, explainability and ethics credentials add depth in accountability, policy, risk, transparency and responsible deployment.</p></article><article class="card"><span class="org">03 · Adoption &amp; operating model</span><h3>AI embedded into how work gets done</h3><p>Leadership and agentic-AI learning supports capability building, human–AI collaboration, organizational adoption and the operating choices required for sustainable use.</p></article><article class="card"><span class="org">04 · Technical &amp; data fluency</span><h3>Architecture-level judgment without engineering positioning</h3><p>EITCA/AI, Databricks, Microsoft and agent-building credentials provide context for discussions on data, cloud, models, platforms, dependencies and technical trade-offs.</p></article></div></div></section>

<section class="section navy eitca-feature"><div class="container"><div class="eitca-banner"><img src="{eitca_eu_banner}" alt="European Union flags outside a modern institutional building" loading="lazy" decoding="async"></div><div class="eitca-top"><div><p class="eyebrow">Featured technical foundation</p><h2>EITCA/AI Artificial Intelligence Academy</h2><p class="eitca-lead">A <strong>24 ECTS</strong> European AI certification programme spanning <strong>12 component certifications</strong> across machine learning, deep learning, Python, cloud platforms and applied AI technologies.</p></div><div class="eitca-facts"><div><strong>24 ECTS</strong><span>Structured AI curriculum</span></div><div><strong>12</strong><span>Component certifications</span></div><div><strong>2025</strong><span>Credential awarded</span></div></div></div><div class="eitca-body"><div><h3>What the credential adds</h3><p>The programme adds structured technical breadth to a business-facing AI leadership profile. Its value is not in positioning for specialist engineering work, but in strengthening the technical judgment needed to lead AI portfolios: understanding model and data dependencies, testing architecture assumptions, engaging product and engineering teams at the right level, and recognizing where delivery choices create implications for governance, risk, scalability and cost.</p><p class="eitca-secondary">For senior AI &amp; Data leadership, that breadth supports a practical bridge between executive priorities and technical execution—connecting strategy with credible decisions on platforms, delivery approaches, Responsible AI and organizational adoption.</p><div class="eitca-value-grid"><div><strong>Technical breadth</strong><span>AI, machine learning, deep learning, Python and cloud foundations.</span></div><div><strong>Decision quality</strong><span>Context for architecture, data, model and platform trade-offs.</span></div><div><strong>Leadership bridge</strong><span>Connects strategy, governance and adoption with technical delivery.</span></div></div><div class="actions"><a class="btn ghost" href="https://www.eitci.org/val.php?id=EITCA/AI/SLJ25004525&t=j5xq3TMD6GcHgrj9" target="_blank" rel="noopener">Verify credential ↗</a><a class="btn ghost" href="https://eitca.org/eitca-ai-artificial-intelligence-academy/" target="_blank" rel="noopener">Programme scope ↗</a></div><div class="eitca-meta-row">{EU_ROUND_EMBLEM}<div><span class="eitca-meta-label">European credential context</span><p class="eitca-id">Credential ID · EITCA/AI/SLJ25004525 · EITCA Academy</p></div></div></div><details class="cert-archive"><summary>View 12 component certifications</summary><ul>{eitca}</ul></details></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Current and role-relevant credentials</p><h2>Focused evidence across today’s enterprise AI priorities.</h2></div><p>Six credentials complement the featured EITCA/AI programme with direct relevance to AI strategy, Responsible AI, organizational adoption, agentic systems and data-platform decisions. Each can be verified directly.</p></div><div class="cert-grid">{flagship}</div></div></section>



<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Supporting depth</p><h2>Broader learning across AI, data and leadership.</h2></div><p>Earlier and specialist credentials provide context behind the headline selections, spanning enterprise AI leadership, Responsible AI, data and cloud foundations, product thinking and analytics.</p></div><div class="cert-path-grid">{pathways}</div></div></section>

<section class="section soft"><div class="container twocol"><div><p class="eyebrow">Continuity</p><h2>A record that predates the current AI cycle.</h2><p class="muted">The sequence reflects a long progression from enterprise technology and data foundations through IBM Watson, AI ethics and cloud, to generative and agentic AI.</p><div class="actions"><a class="btn dark" href="?page=about" target="_self">Back to About →</a><a class="btn dark" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications_bottom">Full credential record ↗</a></div></div><div class="timeline">{timeline}</div></div></section>

{opportunity()}</main>{footer()}'''
