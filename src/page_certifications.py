from __future__ import annotations

import html

from site_components import nav, footer, opportunity

LINKEDIN_CERTIFICATIONS = "https://www.linkedin.com/in/jairribeiro/details/certifications/"

FLAGSHIP = [
    {
        "signal": "AI strategy",
        "title": "Generative AI for Executives and Business Leaders Specialization",
        "issuer": "IBM",
        "date": "Oct 2025",
        "credential": "X5XFLRL8YQ9K",
        "verify_url": "https://www.coursera.org/account/accomplishments/specialization/X5XFLRL8YQ9K",
        "program_url": "https://www.coursera.org/specializations/generative-ai-for-executives-and-business-leaders",
        "copy": "Connects GenAI use cases with business strategy, governance, compliance, feasibility and value—directly reinforcing enterprise AI leadership.",
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
        "copy": "Adds practical fluency in agent reasoning and task execution, helping me engage technical teams on agent architectures without positioning as a hands-on engineer.",
    },
    {
        "signal": "Technical foundation",
        "title": "EITCA/AI Artificial Intelligence Academy",
        "issuer": "EITCA Academy · European IT Certification programme",
        "date": "Mar 2025",
        "credential": "EITCA/AI/SLJ25004525",
        "verify_url": "https://www.eitci.org/val.php?id=EITCA/AI/SLJ25004525&t=j5xq3TMD6GcHgrj9",
        "program_url": "https://eitca.org/eitca-ai-artificial-intelligence-academy/",
        "copy": "Provides broad technical grounding across machine learning, deep learning, Python and cloud through 12 constituent certifications and approximately 180 hours of curriculum.",
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
    {
        "signal": "Data & analytics leadership",
        "title": "Executive Data Science Specialization",
        "issuer": "Johns Hopkins University",
        "date": "Feb 2020",
        "credential": "5L6Q5KMVMWQR",
        "verify_url": "https://www.coursera.org/account/accomplishments/specialization/5L6Q5KMVMWQR",
        "program_url": "https://www.coursera.org/specializations/executive-data-science",
        "copy": "Formalizes the leadership side of data science: leading teams, understanding the analytics pipeline, evaluating work and keeping data initiatives focused on outcomes.",
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
            "EITCA/AI Artificial Intelligence Academy · 12 components · ~180 hours · 2025",
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
<section class="pagehero"><div class="container"><p class="eyebrow">About · Credentials</p><h1>Formal learning that sharpens enterprise AI &amp; Data leadership.</h1><p>Operating experience remains the core of the profile. The credential record adds current, verifiable depth across AI strategy, Responsible AI, adoption, agentic AI, data platforms and technical foundations.</p><div class="actions"><a class="btn ghost" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications">View full LinkedIn credential record ↗</a></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">What the record supports</p><h2>Four dimensions of the leadership profile.</h2></div><p>The full record spans 79 unique certifications after duplicate entries are removed. This page foregrounds the evidence that best complements senior enterprise AI and Data leadership.</p></div><div class="grid3 cert-signal-grid"><article class="card"><span class="org">01 · Leadership</span><h3>AI strategy and organizational adoption</h3><p>Executive learning from IBM, Microsoft and Vanderbilt reinforces strategy, adoption, capability building and business-value decisions.</p></article><article class="card"><span class="org">02 · Governance</span><h3>Responsible and explainable AI</h3><p>University of Michigan, Duke and Linux Foundation study adds depth in accountability, explainability, trust, policy and responsible scale.</p></article><article class="card"><span class="org">03 · Technical fluency</span><h3>AI, ML, cloud and platform architecture</h3><p>EITCA/AI, Databricks, Microsoft and current agent-building study support credible architecture and engineering conversations without repositioning the profile as hands-on engineering.</p></article><article class="card"><span class="org">04 · Data &amp; execution</span><h3>Data leadership and value delivery</h3><p>Executive data science, product, data-management and design-thinking study reinforces the path from use-case framing to adoption and measurable business outcomes.</p></article></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Selected credentials</p><h2>A focused record of continuing professional development.</h2></div><p>These eight credentials provide the clearest combined signal across strategy, governance, adoption, agentic AI, data leadership and informed technical judgment. Each includes a direct verification link.</p></div><div class="cert-grid">{flagship}</div></div></section>

<section class="section navy"><div class="container twocol"><div><p class="eyebrow">Depth behind the leadership profile</p><h2>EITCA/AI · 12 component certifications · ~180 hours of curriculum.</h2><p class="flowcopy">The issuer describes the programme as approximately 180 hours across 12 constituent certifications covering machine learning, deep learning, Python, Google Cloud and related AI technologies. I use that depth to ask better questions of technical teams, understand dependencies and make stronger leadership decisions—not to replace specialist engineering ownership.</p><div class="actions"><a class="btn ghost" href="https://eitca.org/eitca-ai-artificial-intelligence-academy/" target="_blank" rel="noopener">View programme scope ↗</a><a class="btn ghost" href="https://www.eitci.org/val.php?id=EITCA/AI/SLJ25004525&t=j5xq3TMD6GcHgrj9" target="_blank" rel="noopener">Verify credential ↗</a></div></div><div><details class="cert-archive" open><summary>See the 12 component certifications</summary><ul>{eitca}</ul></details></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Credential pathways</p><h2>Depth accumulated across the leadership arc.</h2></div><p>Supporting credentials show continuity rather than a recent pivot: enterprise technology foundations, data and analytics leadership, ethics and governance, cloud, product thinking, GenAI and agentic AI.</p></div><div class="cert-path-grid">{pathways}</div></div></section>

<section class="section soft"><div class="container twocol"><div><p class="eyebrow">Continuity</p><h2>Learning that tracks the evolution of the work.</h2><p class="muted">The credential history follows the same progression visible in the career: enterprise technology foundations, IBM Watson and data work, AI business translation, cloud and ethics, then GenAI, agentic AI and enterprise Responsible AI.</p><div class="actions"><a class="btn dark" href="?page=about" target="_self">Back to About →</a><a class="btn dark" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications_bottom">Full credential record ↗</a></div></div><div class="timeline">{timeline}</div></div></section>

{opportunity()}</main>{footer()}'''
