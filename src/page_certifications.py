from __future__ import annotations

import html

from site_components import nav, footer, opportunity
from site_media import (
    eitca_eu_banner,
    openai_ai_leadership,
    databricks_genai_fundamentals_badge,
    microsoft_leadership_innovation_diploma,
    credly_cognitive_practitioner,
    credly_ai_agents_rag_langchain,
    credly_genai_product_managers,
    credly_genai_foundation_models,
    credly_data_privacy,
    credly_design_thinking_cocreator,
    credly_azure_ai,
    credly_azure_data,
)

LINKEDIN_CERTIFICATIONS = "https://www.linkedin.com/in/jairribeiro/details/certifications/"
OPENAI_AI_LEADERSHIP_URL = (
    "https://oaiacademy.credential.net/855a1e37-b0d2-4e7d-aed6-ae9a839c6de0?"
    "key=9532428a326b32d3b088f47b34479eac"
    "60493830b1f3ce502097c2a10e237c2c"
)

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
        "signal": "Explainability & trust",
        "title": "Explainable AI (XAI)",
        "issuer": "Duke University",
        "date": "May 2025",
        "credential": "Y6M3FVJWGQ9R",
        "verify_url": "https://www.coursera.org/account/accomplishments/records/Y6M3FVJWGQ9R",
        "program_url": "",
        "copy": "Adds formal grounding in explainability, transparency and evidence—important when AI decisions need to be understood, challenged and governed.",
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
        "signal": "Executive AI leadership",
        "title": "Generative AI for Leaders",
        "issuer": "Vanderbilt University",
        "date": "May 2025",
        "credential": "EDHXM2H7DJP5",
        "verify_url": "https://www.coursera.org/account/accomplishments/records/EDHXM2H7DJP5",
        "program_url": "",
        "copy": "Focuses on leadership choices around generative AI, helping connect emerging capabilities with business priorities, organizational readiness and responsible adoption.",
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
        "signal": "AI product judgment",
        "title": "Generative AI for Product Managers",
        "issuer": "SkillUp EdTech",
        "date": "May 2025",
        "credential": "G2UB5ZRCAEBU",
        "verify_url": "https://www.coursera.org/account/accomplishments/records/G2UB5ZRCAEBU",
        "program_url": "",
        "copy": "Strengthens product-level judgment around where generative AI creates value, how use cases are framed and how AI capabilities translate into usable products and services.",
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
        "signal": "Leadership highlight · Enterprise AI",
        "title": "Microsoft AI Transformation Leader Professional Certificate",
        "issuer": "Microsoft",
        "date": "Oct 2026",
        "credential": "49J7ASIMWWFA",
        "verify_url": "https://www.coursera.org/account/accomplishments/professional-cert/49J7ASIMWWFA",
        "alternate_verify_url": "https://www.coursera.org/account/accomplishments/specialization/49J7ASIMWWFA",
        "program_url": "https://www.coursera.org/professional-certificates/microsoft-ai-transformation-leader",
        "copy": "Executive-level preparation for leading enterprise AI transformation across strategy, investment decisions, governance, adoption, Microsoft AI orchestration and measurable business value.",
        "featured": True,
    },
]

CREDLY_PROFILE = "https://www.credly.com/users/jair-pinto-ribeiro/"
ACCREDIBLE_WALLET = "https://www.credential.net/profile/jairribeiro188506/wallet"

CREDLY_BADGES = [
    {
        "signal": "AI continuity",
        "title": "Cognitive Practitioner",
        "issuer": "IBM",
        "date": "Sep 2017",
        "image": credly_cognitive_practitioner,
        "url": "https://www.credly.com/badges/72167c2a-2db9-4c64-a3a8-b574b5236126/public_url",
        "copy": "Evidence of applied AI capability from the IBM Watson and cognitive-computing era, adding continuity between earlier enterprise AI work and today’s generative and agentic AI landscape.",
    },
    {
        "signal": "RAG & orchestration",
        "title": "AI Agents Using RAG and LangChain",
        "issuer": "Coursera · authorized by IBM",
        "date": "Jun 2025",
        "image": credly_ai_agents_rag_langchain,
        "url": "https://www.credly.com/badges/064f7390-5871-43c5-9886-99e7ec3faf24/public_url",
        "copy": "Working context around RAG, retrieval, LangChain and agent workflows for stronger architecture and delivery conversations.",
    },
    {
        "signal": "AI product & value",
        "title": "Generative AI for Product Managers Specialization",
        "issuer": "Coursera · authorized by IBM",
        "date": "Jun 2025",
        "image": credly_genai_product_managers,
        "url": "https://www.credly.com/badges/942f3f3d-bdb2-4efa-8076-3a05f9f7ffd2/public_url",
        "copy": "Connects generative AI with product concepts, roadmaps and lifecycle decisions, linking capability with usable business value.",
    },
    {
        "signal": "Foundation models",
        "title": "Generative AI: Foundation Models and Platforms",
        "issuer": "Coursera · authorized by IBM",
        "date": "Jun 2025",
        "image": credly_genai_foundation_models,
        "url": "https://www.credly.com/badges/b352e372-743f-409a-93ff-b9b5c9d470ff/public_url",
        "copy": "Model- and platform-level context for decisions involving foundation models, pretrained capabilities and enterprise GenAI platforms.",
    },
    {
        "signal": "Privacy & trust",
        "title": "Data Privacy Fundamentals",
        "issuer": "IBM",
        "date": "Dec 2017",
        "image": credly_data_privacy,
        "url": "https://www.credly.com/badges/795e1e65-e8af-44c8-9ed6-2f285e81e7e8/public_url",
        "copy": "An established privacy and ethics foundation behind later Responsible AI work, including the implications of collecting, using and sharing data.",
    },
    {
        "signal": "Human-centered adoption",
        "title": "Enterprise Design Thinking Co-Creator",
        "issuer": "IBM",
        "date": "Nov 2017",
        "image": credly_design_thinking_cocreator,
        "url": "https://www.credly.com/badges/0c166467-7348-42e0-a377-a00f46f0998c/public_url",
        "copy": "Supports co-creation, facilitation and user-centered problem framing—useful when new AI capability must translate into adopted ways of working.",
    },
    {
        "signal": "Cloud AI",
        "title": "Microsoft Certified: Azure AI Fundamentals",
        "issuer": "Microsoft",
        "date": "Jun 2021",
        "image": credly_azure_ai,
        "url": "https://www.credly.com/badges/7d987d1e-e06f-4248-91a4-9544c8549c11/public_url",
        "copy": "Verified foundational knowledge of AI, machine learning and related Azure services for cloud-platform discussions.",
    },
    {
        "signal": "Cloud data",
        "title": "Microsoft Certified: Azure Data Fundamentals",
        "issuer": "Microsoft",
        "date": "Jul 2021",
        "image": credly_azure_data,
        "url": "https://www.credly.com/badges/7b796e8b-50a1-4602-abde-73f9b5752ac8/public_url",
        "copy": "Verified grounding in core data concepts and Azure data services, complementing broader data-platform and analytics leadership.",
    },
]

ACCREDIBLE_BADGES = [
    {
        "signal": "GenAI platform fluency",
        "title": "Academy Accreditation - Generative AI Fundamentals",
        "issuer": "Databricks Academy",
        "date": "Apr 2025",
        "image": databricks_genai_fundamentals_badge,
        "url": "https://www.credential.net/debbdbb9-df3f-46d8-a218-4f5f73288dae",
        "verify_label": "Verify on Accredible ↗",
        "copy": "Adds Databricks-specific grounding in generative AI concepts, complementing broader foundation-model knowledge with platform context relevant to enterprise data and AI decisions.",
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
            "Microsoft AI Transformation Leader Professional Certificate · Microsoft · 2026",
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


def _leadership_credential(item: dict[str, str]) -> str:
    return (
        '<article class="leadership-cert-highlight">'
        '<div class="leadership-cert-main">'
        f'<span class="leadership-cert-kicker">{html.escape(item["signal"])}</span>'
        f'<h3>{html.escape(item["title"])}</h3>'
        f'<div class="leadership-cert-issuer">{html.escape(item["issuer"])} · 5-course Professional Certificate · {html.escape(item["date"])}</div>'
        '<p class="leadership-cert-lead">This credential is particularly aligned with my leadership profile because it concentrates on the decisions I work with in enterprise AI: shaping transformation strategy, evaluating investments and solutions, establishing governance and accountability, orchestrating AI platforms, and moving from pilots toward scalable adoption and measurable business value.</p>'
        '<div class="actions">'
        f'<a class="btn ghost" href="{html.escape(item["verify_url"], quote=True)}" target="_blank" rel="noopener">Verify Professional Certificate ↗</a>'
        f'<a class="btn ghost" href="{html.escape(item["alternate_verify_url"], quote=True)}" target="_blank" rel="noopener">View Specialization Diploma ↗</a>'
        f'<a class="btn ghost" href="{html.escape(item["program_url"], quote=True)}" target="_blank" rel="noopener">Programme scope ↗</a>'
        '</div>'
        f'<p class="leadership-cert-meta">Professional Certificate + Specialization diploma · Credential {html.escape(item["credential"])} · Microsoft · Coursera</p>'
        '</div>'
        '<div class="leadership-cert-side">'
        f'<a class="leadership-cert-diploma" href="{html.escape(item["alternate_verify_url"], quote=True)}" target="_blank" rel="noopener">'
        f'<img src="{microsoft_leadership_innovation_diploma}" alt="Microsoft Leadership and Innovation Specialization diploma" loading="lazy" decoding="async">'
        '<span><strong>Microsoft Leadership and Innovation</strong>Specialization · 4 courses · Oct 2026</span>'
        '</a>'
        '<div class="leadership-cert-facts">'
        '<div><strong>Strategy</strong><span>Enterprise AI transformation roadmap</span></div>'
        '<div><strong>Value</strong><span>Investment, TCO &amp; measurable outcomes</span></div>'
        '<div><strong>Governance</strong><span>Responsible AI, risk &amp; accountability</span></div>'
        '<div><strong>Orchestration</strong><span>Copilot, Azure AI &amp; agentic workflows</span></div>'
        '</div>'
        '</div>'
        '</article>'
    )


def _credly_badge(item: dict[str, str]) -> str:
    verify_label = item.get("verify_label", "Verify on Credly ↗")
    return (
        '<article class="credly-card">'
        f'<a class="credly-art" href="{html.escape(item["url"], quote=True)}" target="_blank" rel="noopener">'
        f'<img src="{item["image"]}" alt="{html.escape(item["title"])} digital badge" loading="lazy" decoding="async"></a>'
        f'<span class="credly-signal">{html.escape(item["signal"])}</span>'
        f'<h3>{html.escape(item["title"])}</h3>'
        f'<div class="credly-meta"><strong>{html.escape(item["issuer"])}</strong><span>{html.escape(item["date"])}</span></div>'
        f'<p>{html.escape(item["copy"])}</p>'
        f'<a class="credly-verify" href="{html.escape(item["url"], quote=True)}" target="_blank" rel="noopener">{html.escape(verify_label)}</a>'
        '</article>'
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
    leadership_credential = next(item for item in FLAGSHIP if item.get("featured"))
    flagship = "".join(_credential_card(item) for item in FLAGSHIP if not item.get("featured"))
    digital_badges = "".join(_credly_badge(item) for item in [*ACCREDIBLE_BADGES, *CREDLY_BADGES])
    pathways = "".join(_pathway(title, copy, items) for title, copy, items in PATHWAYS)
    eitca = "".join(f"<li>{html.escape(item)}</li>" for item in EITCA_COMPONENTS)
    timeline = "".join(
        f'<div class="trow"><b>{html.escape(years)}</b><div><strong>{html.escape(title)}</strong>'
        f'<span>{html.escape(copy)}</span></div></div>'
        for years, title, copy in FOUNDATION_TIMELINE
    )

    return f'''{nav("certifications")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">About · Credentials</p><h1>Selected AI, data and leadership credentials.</h1><p>Formal learning across AI strategy, governance, adoption, agentic AI, data platforms and technical foundations, with direct links for verification.</p><div class="actions"><a class="btn ghost" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications">View full LinkedIn credential record ↗</a></div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Coverage</p><h2>What the credential record covers.</h2></div><p>The selected record spans strategy and value, Responsible AI, adoption and operating models, and technical and data foundations.</p></div><div class="grid3 cert-signal-grid"><article class="card"><span class="org">01 · Strategy &amp; value</span><h3>From AI ambition to business priorities</h3><p>Executive AI study covers use-case selection, feasibility, investment choices, business value and the decisions needed to move from experimentation to scale.</p></article><article class="card"><span class="org">02 · Governance &amp; trust</span><h3>Responsible AI as an operating discipline</h3><p>Responsible AI, explainability and ethics credentials add depth in accountability, policy, risk, transparency and responsible deployment.</p></article><article class="card"><span class="org">03 · Adoption &amp; operating model</span><h3>AI embedded into how work gets done</h3><p>Leadership and agentic-AI learning supports capability building, human–AI collaboration, organizational adoption and the operating choices required for sustainable use.</p></article><article class="card"><span class="org">04 · Technical &amp; data fluency</span><h3>Architecture-level judgment without engineering positioning</h3><p>EITCA/AI, Databricks, Microsoft and agent-building credentials provide context for discussions on data, cloud, models, platforms, dependencies and technical trade-offs.</p></article></div></div></section>

<section class="section navy eitca-feature"><div class="container"><div class="eitca-banner"><img src="{eitca_eu_banner}" alt="European Union flags outside a modern institutional building" loading="lazy" decoding="async"></div><div class="eitca-top"><div><p class="eyebrow">Featured technical foundation</p><h2>EITCA/AI Artificial Intelligence Academy</h2><p class="eitca-lead">A <strong>24 ECTS</strong> European AI certification programme spanning <strong>12 component certifications</strong> across machine learning, deep learning, Python, cloud platforms and applied AI technologies.</p></div><div class="eitca-facts"><div><strong>24 ECTS</strong><span>Structured AI curriculum</span></div><div><strong>12</strong><span>Component certifications</span></div><div><strong>2025</strong><span>Credential awarded</span></div></div></div><div class="eitca-body"><div><h3>Scope and relevance</h3><p>EITCA/AI adds structured technical breadth across machine learning, deep learning, Python and cloud platforms. That background is useful when discussing model and data dependencies, architecture assumptions, platform choices, governance, scalability and cost with specialist teams.</p><p class="eitca-secondary">The credential supports business-facing work by providing technical context for decisions on platforms, delivery approaches, Responsible AI and adoption without positioning the role as specialist engineering.</p><div class="eitca-value-grid"><div><strong>Technical breadth</strong><span>AI, machine learning, deep learning, Python and cloud foundations.</span></div><div><strong>Decision quality</strong><span>Context for architecture, data, model and platform trade-offs.</span></div><div><strong>Leadership bridge</strong><span>Connects strategy, governance and adoption with technical delivery.</span></div></div><div class="actions"><a class="btn ghost" href="https://www.eitci.org/val.php?id=EITCA/AI/SLJ25004525&t=j5xq3TMD6GcHgrj9" target="_blank" rel="noopener">Verify credential ↗</a><a class="btn ghost" href="https://eitca.org/eitca-ai-artificial-intelligence-academy/" target="_blank" rel="noopener">Programme scope ↗</a></div><div class="eitca-meta-row">{EU_ROUND_EMBLEM}<div><span class="eitca-meta-label">European credential context</span><p class="eitca-id">Credential ID · EITCA/AI/SLJ25004525 · EITCA Academy</p></div></div></div><details class="cert-archive"><summary>View 12 component certifications</summary><ul>{eitca}</ul></details></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Recent credentials</p><h2>Current credentials across enterprise AI and leadership priorities.</h2></div><p>Ten selected credentials complement the featured EITCA/AI programme. The Microsoft AI Transformation Leader Professional Certificate is highlighted because its scope is particularly close to my enterprise AI leadership work across strategy, governance, investment, adoption and business value.</p></div>{_leadership_credential(leadership_credential)}<div class="cert-grid">{flagship}</div></div></section>



<section class="section credly-section"><div class="container"><div class="head"><div><p class="eyebrow">Verified digital badges</p><h2>Specific capability evidence, independently verifiable.</h2></div><div><p>I use these badges as supporting evidence beneath my broader AI &amp; Data leadership work. The OpenAI Academy AI Leadership badge is highlighted because its scope closely matches how I work across enterprise AI strategy, governance, roadmap and adoption.</p></div></div>

<article class="openai-badge-highlight"><div class="openai-badge-art"><a href="{OPENAI_AI_LEADERSHIP_URL}" target="_blank" rel="noopener" data-hq-event="openai_ai_leadership_badge"><img src="{openai_ai_leadership}" alt="OpenAI Academy AI Leadership artwork" loading="lazy" decoding="async"></a></div><div class="openai-badge-copy"><span class="openai-badge-kicker">Highlighted badge · OpenAI Academy</span><h3>AI Leadership</h3><p class="openai-badge-lead">This badge is especially aligned with how I lead enterprise AI: connecting initiatives to business priorities, establishing ownership and governance, shaping a roadmap, and planning for adoption. It reinforces the operating discipline behind my work—turning AI strategy into accountable decisions, coordinated execution and measurable business value.</p><div class="openai-badge-facts"><div><strong>Strategy</strong><span>Business priorities</span></div><div><strong>Governance</strong><span>Ownership &amp; accountability</span></div><div><strong>Roadmap</strong><span>From initiative to action</span></div><div><strong>Adoption</strong><span>Organizational execution</span></div></div><div class="actions"><a class="btn ghost" href="{OPENAI_AI_LEADERSHIP_URL}" target="_blank" rel="noopener" data-hq-event="openai_ai_leadership_verify">Verify issued badge ↗</a></div><p class="openai-badge-meta">OpenAI Academy badge · course completion and passing assessment · issued via Accredible</p></div></article>

<div class="credly-subhead"><div><span class="credly-subtitle">Additional selected badges</span><p>Curated across Credly and Accredible: agentic AI, GenAI product and platform judgment, privacy, human-centered adoption, and cloud/data foundations.</p></div><div class="actions"><a class="btn dark" href="{CREDLY_PROFILE}" target="_blank" rel="noopener" data-hq-event="credly_profile">Credly profile ↗</a><a class="btn dark" href="{ACCREDIBLE_WALLET}" target="_blank" rel="noopener" data-hq-event="accredible_wallet">Accredible wallet ↗</a></div></div><div class="credly-grid">{digital_badges}</div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Earlier and specialist credentials</p><h2>Broader learning across AI, data and leadership.</h2></div><p>Earlier and specialist credentials provide context behind the headline selections, spanning enterprise AI leadership, Responsible AI, data and cloud foundations, product thinking and analytics.</p></div><div class="cert-path-grid">{pathways}</div></div></section>

<section class="section soft"><div class="container twocol"><div><p class="eyebrow">Earlier learning</p><h2>A record that predates the current AI cycle.</h2><p class="muted">The sequence reflects a long progression from enterprise technology and data foundations through IBM Watson, AI ethics and cloud, to generative and agentic AI.</p><div class="actions"><a class="btn dark" href="?page=about" target="_self">Back to About →</a><a class="btn dark" href="{LINKEDIN_CERTIFICATIONS}" target="_blank" rel="noopener" data-hq-event="linkedin_certifications_bottom">Full credential record ↗</a></div></div><div class="timeline">{timeline}</div></div></section>

</main>{footer()}'''
