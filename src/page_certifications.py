from __future__ import annotations

import html

from site_components import nav, footer, opportunity

LINKEDIN_CERTIFICATIONS = "https://www.linkedin.com/in/jairribeiro/details/certifications/"

FLAGSHIP = [
    {
        "signal": "Agentic AI",
        "title": "Fundamentals of Building AI Agents",
        "issuer": "IBM",
        "date": "May 2026",
        "credential": "VXKY3NPDNMW6",
        "copy": "Strengthens my perspective on how AI agents can be applied within enterprise workflows, with attention to orchestration, autonomy and control.",
        "skills": ("AI agents", "Agentic AI", "Applied AI"),
    },
    {
        "signal": "AI strategy",
        "title": "Generative AI for Executives and Business Leaders Specialization",
        "issuer": "IBM",
        "date": "Oct 2025",
        "credential": "X5XFLRL8YQ9K",
        "copy": "Connects generative AI use cases with strategy, governance and organizational planning at executive level.",
        "skills": ("AI strategy", "GenAI", "Governance"),
    },
    {
        "signal": "Responsible AI",
        "title": "Responsible Generative AI",
        "issuer": "University of Michigan",
        "date": "May 2025",
        "credential": "G7A2NUZLL0YJ",
        "copy": "Deepens the governance perspective on risk, trust and accountability in the use of generative AI.",
        "skills": ("Responsible AI", "Generative AI", "Trust"),
    },
    {
        "signal": "Explainability",
        "title": "Explainable AI (XAI)",
        "issuer": "Duke University",
        "date": "May 2025",
        "credential": "Y6M3FVJWGQ9R",
        "copy": "Adds technical grounding in explainability and the role of evidence, transparency and trust in AI adoption.",
        "skills": ("XAI", "Responsible AI", "Machine learning"),
    },
    {
        "signal": "AI leadership",
        "title": "AI for Organizational Leaders",
        "issuer": "Microsoft + LinkedIn",
        "date": "Mar 2025",
        "credential": "",
        "copy": "Focuses on the leadership choices involved in organizational AI adoption, Responsible AI and enterprise-scale use.",
        "skills": ("AI leadership", "Responsible AI", "Business adoption"),
    },
    {
        "signal": "Technical foundation",
        "title": "EITCA/AI Artificial Intelligence Academy",
        "issuer": "EITCA Academy · European certification programme",
        "date": "Mar 2025",
        "credential": "EITCA/AI/SLJ25004525",
        "copy": "Provides structured technical breadth across AI, machine learning, deep learning, Python and cloud, supporting stronger leadership judgment in technical environments.",
        "skills": ("24 ECTS", "12 components", "AI / ML / Cloud"),
    },
    {
        "signal": "Data platforms",
        "title": "Azure Databricks Platform Architect · Academy Accreditation",
        "issuer": "Databricks",
        "date": "Apr 2025",
        "credential": "141535340",
        "copy": "Adds architecture-level understanding of enterprise data platforms and the trade-offs involved in scale, data design and platform choices.",
        "skills": ("Databricks", "Azure", "Platform architecture"),
        "validity": "Valid through Apr 2027",
    },
    {
        "signal": "Agentic AI leadership",
        "title": "Agentic AI and AI Agents: A Primer for Leaders",
        "issuer": "Vanderbilt University",
        "date": "May 2025",
        "credential": "YAMOO2UIDDPN",
        "copy": "Builds leadership understanding of agentic patterns, where autonomous and semi-autonomous systems create value and new governance questions.",
        "skills": ("AI agents", "Leadership", "GenAI"),
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
        "Credentials that sharpen strategy, adoption and organizational judgment.",
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
        "Governance, explainability and ethics as operating questions rather than compliance-only topics.",
        [
            "Responsible Generative AI · University of Michigan · 2025",
            "Explainable AI (XAI) · Duke University · 2025",
            "Data Science Ethics · University of Michigan · 2020",
            "Ethics in AI and Big Data (LFS112x) · The Linux Foundation · 2020",
        ],
    ),
    (
        "Technical & platform fluency",
        "Enough depth to engage specialists and understand what architecture, data and model choices imply for the enterprise.",
        [
            "EITCA/AI Artificial Intelligence Academy · 24 ECTS · 2025",
            "Azure Databricks Platform Architect · Databricks · 2025–2027",
            "Microsoft Certified: Azure AI Fundamentals · 2021",
            "Microsoft Certified: Azure Data Fundamentals · 2021",
            "Microsoft Certified: Azure Fundamentals · 2021",
            "Introduction to Machine Learning · Duke University · 2021",
        ],
    ),
    (
        "Product, data & execution",
        "Formal learning that supports prioritization, product ownership, data management and translating AI into usable capability.",
        [
            "Data Integration, Data Storage, & Data Migration · SkillUp · 2026",
            "Generative AI for Product Managers · SkillUp EdTech · 2025",
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
        "AI agents, GenAI strategy, Responsible GenAI, product applications and data-management refreshers keep the learning record close to the capabilities organizations are deploying now.",
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


def _credential_card(item: dict[str, object]) -> str:
    detail_bits = []
    if item.get("credential"):
        detail_bits.append(
            f'<span>Credential ID · {html.escape(str(item["credential"]))}</span>'
        )
    if item.get("validity"):
        detail_bits.append(
            f'<span>{html.escape(str(item["validity"]))}</span>'
        )
    details = (
        '<details class="cert-details"><summary>Credential details</summary>'
        + "".join(detail_bits)
        + "</details>"
        if detail_bits
        else ""
    )
    return (
        '<article class="cert-card">'
        '<div class="cert-card-head">'
        f'<span class="cert-kicker">{html.escape(str(item["signal"]))}</span>'
        f'<span class="cert-date">{html.escape(str(item["date"]))}</span>'
        "</div>"
        f'<h3>{html.escape(str(item["title"]))}</h3>'
        f'<div class="cert-issuer">{html.escape(str(item["issuer"]))}</div>'
        f'<p>{html.escape(str(item["copy"]))}</p>'
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
<section class="pagehero"><div class="container"><p class="eyebrow">About · Credentials</p><h1>Formal learning that strengthens enterprise AI leadership judgment.</h1><p>The strongest signal is the combination: operating experience across AI, Data and Analytics, reinforced by current study in agentic AI, Responsible AI, GenAI strategy, data platforms and technical foundations.</p><div class="actions"><a class="btn ghost" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications">View full LinkedIn credential record ↗</a></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">What the record supports</p><h2>Four dimensions that matter in senior AI &amp; Data roles.</h2></div><p>The page is intentionally curated. Recent, role-relevant credentials come first; deeper technical modules sit underneath the leadership story rather than competing with it.</p></div><div class="grid3 cert-signal-grid"><article class="card"><span class="org">01 · Leadership</span><h3>AI strategy and organizational adoption</h3><p>Executive and leadership programmes from IBM, Microsoft and Vanderbilt reinforce the work of translating AI capability into priorities, operating choices and adoption.</p></article><article class="card"><span class="org">02 · Governance</span><h3>Responsible, explainable AI</h3><p>University of Michigan, Duke and Linux Foundation study supports a practical view of accountability, explainability, trust and responsible scale.</p></article><article class="card"><span class="org">03 · Technical fluency</span><h3>AI, ML, cloud and platform architecture</h3><p>The EITCA/AI programme, Databricks accreditation and Microsoft fundamentals provide enough technical depth to engage specialists and challenge enterprise trade-offs credibly.</p></article><article class="card"><span class="org">04 · Execution</span><h3>Product, data and value delivery</h3><p>Product-management, data-integration, executive data-science and design-thinking study strengthens the path from use-case framing to an operable business capability.</p></article></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Selected credentials</p><h2>A focused record of continuing professional development.</h2></div><p>Selected for their relevance to enterprise AI strategy, Responsible AI, adoption, operating models, data, and the technical judgment required to lead AI and Data at enterprise scale.</p></div><div class="cert-grid">{flagship}</div></div></section>

<section class="section navy"><div class="container twocol"><div><p class="eyebrow">Depth behind the leadership profile</p><h2>EITCA/AI · 24 ECTS across 12 component certifications.</h2><p class="flowcopy">The programme provides a structured technical foundation across machine learning, deep learning, Python, Google Cloud and related AI technologies. I use that depth to ask better questions of technical teams, understand dependencies and make stronger leadership decisions—not to replace specialist engineering ownership.</p></div><div><details class="cert-archive" open><summary>See the 12 component certifications</summary><ul>{eitca}</ul></details></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Credential pathways</p><h2>A learning record built around the problems I actually lead.</h2></div><p>Grouped this way, the record is easier to read than a chronological badge list. It shows where formal learning reinforces the professional work.</p></div><div class="cert-path-grid">{pathways}</div></div></section>

<section class="section soft"><div class="container twocol"><div><p class="eyebrow">Continuity</p><h2>Not a recent pivot into AI.</h2><p class="muted">The credential history tracks the same professional progression visible in the career: enterprise technology foundations, IBM Watson and data work, AI business translation, cloud and ethics, then GenAI, agentic AI and enterprise Responsible AI.</p><div class="actions"><a class="btn dark" href="?page=about" target="_self">Back to About →</a><a class="btn dark" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications_bottom">Full credential record ↗</a></div></div><div class="timeline">{timeline}</div></div></section>

{opportunity()}</main>{footer()}'''
