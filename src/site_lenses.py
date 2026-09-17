from __future__ import annotations

import html

from site_assets import CV_URI, AI_PANEL_URI, HERO_URI, PANEL_DIALOGUE_URI
from site_components import nav, footer, opportunity, CV_DOWNLOAD_NAME


CLAES_LINKEDIN = "https://se.linkedin.com/in/claes-sandros-1a795512"
KUMARA_LINKEDIN = "https://in.linkedin.com/in/kumara-datta"
JIM_LINKEDIN = "https://www.linkedin.com/in/james-edwards-7233b8152"


def role_lens(
    page: str,
    kicker: str,
    title: str,
    deck: str,
    perspective: str,
    sections: list[tuple[str, str, str, list[str]]],
    image_uri: str,
    image_alt: str,
    reference: tuple[str, str, str, str] | None = None,
) -> str:
    body = []
    for k, h, p, bullets in sections:
        bullet_html = "".join(f'<div>{html.escape(x)}</div>' for x in bullets)
        body.append(
            f'<section class="lenssection"><p class="eyebrow">{html.escape(k)}</p>'
            f'<h3>{html.escape(h)}</h3><p>{html.escape(p)}</p>'
            f'<div class="bullets">{bullet_html}</div></section>'
        )

    if reference:
        person, role, quote, url = reference
        role_html = f'<p><strong>{html.escape(role)}</strong></p>' if role else ""
        body.append(
            '<section class="lenssection"><p class="eyebrow">External perspective</p>'
            '<div class="card">'
            f'<span class="org">Recommendation context</span><h3>{html.escape(person)}</h3>'
            f'{role_html}'
            f'<p style="font:500 18px/1.5 Georgia,serif;color:var(--ink);margin-top:20px">“{html.escape(quote)}”</p>'
            f'<div class="proof"><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener" '
            f'data-hq-event="reference_{html.escape(person.lower().replace(" ", "_"))}_lens">LinkedIn profile ↗</a></div>'
            '</div></section>'
        )

    cv = (
        f'<a class="btn dark" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" '
        f'data-hq-event="cv_download_lens">Download CV</a>'
        if CV_URI
        else ""
    )
    photo = (
        f'<div class="lensphoto"><img src="{image_uri}" alt="{html.escape(image_alt)}" '
        f'loading="lazy" decoding="async"></div>'
        if image_uri
        else ""
    )
    return (
        f'{nav(page)}<main><section class="pagehero"><div class="container">'
        f'<p class="eyebrow">{html.escape(kicker)}</p><h1>{html.escape(title)}</h1>'
        f'<p>{html.escape(deck)}</p></div></section>'
        f'<section class="section paper"><div class="container lensgrid">'
        f'<aside class="lensaside"><p class="eyebrow">Jair Ribeiro</p>'
        f'<h2>Enterprise AI &amp; Data Leader</h2>{photo}'
        f'<p class="muted">I bring enterprise AI, Data &amp; Analytics experience across strategy, portfolio choices, governance, adoption and operating-model decisions, with the technical fluency to connect business priorities with delivery reality.</p>'
        f'<p class="muted">{html.escape(perspective)}</p><div class="actions">'
        f'<a class="btn dark" href="?page=impact" target="_self" data-hq-event="impact_lens">'
        f'Leadership impact</a>{cv}</div></aside><div>{"".join(body)}</div></div></section>'
        f'{opportunity()}</main>{footer()}'
    )


def enterprise() -> str:
    return role_lens(
        "enterprise",
        "Role lens · Enterprise AI & Data Leadership",
        "Connecting AI and Data strategy with the operating capability underneath it.",
        "This lens is most relevant when a leadership mandate spans priorities, portfolio choices, Data & Analytics, operating models, governance and enterprise adoption rather than one isolated technical domain.",
        "My strongest contribution in this context is connecting disciplines that often sit in different parts of the organization while keeping specialist ownership explicit.",
        [
            (
                "Selected evidence",
                "A business-facing AI and Data leadership profile",
                "The experience spans AI strategy, analytics, portfolio decisions, governance, adoption, operating models and architecture-aware decision-making. I have worked across global industrial and consumer environments where those disciplines had to support the same business choices.",
                [
                    "Across my Volvo AI roles, I shaped and supported 100+ AI initiatives, PoCs and projects.",
                    "At MSX International, I built foundations for an emerging AI & Data CoE covering portfolio, governance, data ownership and scale-readiness.",
                    "At Kimberly-Clark, I led EMEA AI value discovery across functions with different levels of readiness.",
                ],
            ),
            (
                "Operating capability",
                "Make ownership clearer before adding more process",
                "I focus on the structures that help AI become repeatable: roles, decision rights, lifecycle stages, portfolio logic, data ownership and escalation. The aim is enough structure to improve decisions without making a central function the bottleneck for every decision.",
                [
                    "Portfolio visibility and prioritization",
                    "Lifecycle ownership and scale-readiness evidence",
                    "Data stewardship, quality and trusted-data foundations",
                ],
            ),
            (
                "Leadership style",
                "Work comfortably between business priorities and technical reality",
                "My technical background helps me engage engineers, architects and data specialists and understand where architecture, security, cost or data choices change the business answer. Specialist depth remains with the specialists responsible for those decisions.",
                [
                    "Cross-functional work across business, Digital & IT, analytics and governance",
                    "Executive stakeholder communication and business translation",
                    "Technical judgment rather than technical demonstration",
                ],
            ),
        ],
        AI_PANEL_URI,
        "Jair Ribeiro discussing AI with senior industry peers",
        (
            "Claes Sandros",
            "Acting Head of Data and Vice President Data, Analytics & AI, Volvo Trucks · Direct manager",
            "What truly impressed me was his ability to combine deep analytical knowledge with strategic thinking and a collaborative mindset.",
            CLAES_LINKEDIN,
        ),
    )


def transformation() -> str:
    return role_lens(
        "transformation",
        "Role lens · AI Transformation & Adoption",
        "Moving AI from experimentation toward practical organizational use.",
        "This lens is relevant when an organization already has AI activity but needs clearer priorities, stronger adoption, capability building and a more credible path from promising work to repeatable use.",
        "I tend to be most useful once initial enthusiasm has created enough activity to expose the real operating questions: what deserves investment, who owns the outcome, what evidence is missing and what has to change in the workflow.",
        [
            (
                "Transformation focus",
                "The hard part usually begins after possibility has been proven",
                "A technically successful pilot is useful evidence, but it does not yet show that the organization can operate, govern or adopt the capability. My work has often been about connecting those missing conditions around the technology.",
                [
                    "AI literacy and adoption activity reaching 1,000+ employees",
                    "Enterprise communities engaging 1,500+ practitioners",
                    "Use-case work across commercial operations and other global business functions",
                ],
            ),
            (
                "Adoption",
                "Training matters, but behavior is the real test",
                "Capability building works best when it is close to real workflows and decisions. Literacy can improve the quality of demand and confidence, while adoption becomes visible only when people change how work is done and ownership is clear enough to sustain it.",
                [
                    "Practical GenAI literacy and responsible-use activity",
                    "Cross-functional use-case discovery and business translation",
                    "Business, Digital & IT and specialist collaboration around real workflows",
                ],
            ),
            (
                "Scale",
                "Responsible adoption needs evidence, not only enthusiasm",
                "I prefer governance that helps teams understand what has to be true next: which risks matter, who owns them, what evidence is required and when broader use should wait. That is different from treating governance as a separate compliance exercise.",
                [
                    "Lifecycle and scale-readiness criteria",
                    "Risk-aware portfolio choices",
                    "Governance connected to adoption and operating ownership",
                ],
            ),
        ],
        HERO_URI,
        "Jair Ribeiro speaking during an executive AI panel",
        (
            "Kumara Datta",
            "AI Strategy & Adoption / Product Owner – GenAI Hub, Volvo · AI colleague",
            "Jair has a rare ability to translate complex AI and data concepts into clear, actionable insights that resonate with both technical and business stakeholders.",
            KUMARA_LINKEDIN,
        ),
    )


def governance() -> str:
    return role_lens(
        "governance",
        "Role lens · AI Governance & Operating Model",
        "Creating clearer ownership, evidence and decision rights around AI.",
        "This lens is relevant where AI needs stronger lifecycle discipline, portfolio governance, data accountability and Responsible AI mechanisms without turning governance into a control layer disconnected from delivery.",
        "I treat governance as part of the operating system around AI. The purpose is to make clear who owns each decision, what evidence is required, when risk needs escalation and what must be true before broader use is justified.",
        [
            (
                "Operating model",
                "Make ownership visible before adding process",
                "AI becomes difficult to scale when business ownership, technical ownership, data accountability and risk decisions remain implicit. I start by making those responsibilities visible, then add the minimum structure needed for repeatable decisions.",
                [
                    "Roles and decision rights across business, data, technology and governance",
                    "Lifecycle ownership from discovery through scale-readiness",
                    "CoE patterns intended to enable rather than centralize every decision",
                ],
            ),
            (
                "Governance",
                "Responsible adoption, not compliance-only governance",
                "Useful governance tells teams what they need to prove and where a decision belongs. It distinguishes experimentation from higher-consequence use, exposes unresolved assumptions and creates a credible route for escalation when the consequences justify it.",
                [
                    "Responsible AI and risk-aware lifecycle mechanisms",
                    "Stage criteria and evidence requirements",
                    "Clearer escalation for higher-risk or higher-scale use",
                ],
            ),
            (
                "Data and trust",
                "Many governance problems begin as ownership problems",
                "Data quality, semantics, stewardship, access and lineage shape both technical performance and organizational trust. Treating them as separate from AI governance often moves the same problem downstream.",
                [
                    "Data-governance foundations connected to AI portfolio decisions",
                    "Stewardship and trusted-data responsibilities",
                    "Architecture, security, cost and control considered alongside adoption",
                ],
            ),
        ],
        PANEL_DIALOGUE_URI,
        "Jair Ribeiro in an industry panel dialogue",
    )


def consulting() -> str:
    return role_lens(
        "consulting",
        "Role lens · Business-Driven AI & Consulting",
        "Advisory work grounded in what has to happen after the recommendation.",
        "This is a secondary but genuine part of my profile: client-facing technology, problem framing, value discovery and executive dialogue, informed by having also worked on the operating side of enterprise AI change.",
        "The perspective I bring to consulting is practical consequence. Recommendations have to survive data quality, architecture, governance, competing priorities and the people who will use the capability after the presentation is over.",
        [
            (
                "Client perspective",
                "Start from the problem and the organization that has to act on it",
                "Experience from the operating side of global organizations changes the questions I ask in advisory work. I want to understand the business problem, readiness, ownership and dependencies before describing a target state.",
                [
                    "AI value discovery across EMEA business units",
                    "Enterprise portfolio and operating-model work",
                    "Executive and cross-functional communication across business and technology",
                ],
            ),
            (
                "Problem framing",
                "Shape the question before shaping the solution",
                "My background includes consulting, client-facing technology work and IBM Watson solution design. The most useful part of that experience is learning to clarify the problem, expose assumptions and connect technical possibilities to what the client is actually trying to change.",
                [
                    "Business problem and value discovery",
                    "Solution and proposition shaping",
                    "Workshops and stakeholder dialogue",
                ],
            ),
            (
                "Practical consequence",
                "A recommendation is useful when the client can act on it",
                "The strongest advisory work leaves clearer decisions, ownership and a realistic path into execution. It should also make the unresolved assumptions visible enough for the client to know what needs to be learned next.",
                [
                    "Portfolio prioritization and decision mechanisms",
                    "Governance and data-readiness implications",
                    "Adoption and internal capability building",
                ],
            ),
        ],
        PANEL_DIALOGUE_URI,
        "Jair Ribeiro in an industry panel dialogue",
        (
            "Jim Edwards",
            "Leadership colleague · transformation / consulting perspective",
            "He’s incredibly good at bringing people along on the journey and explaining the benefits of what AI can bring to an organization.",
            JIM_LINKEDIN,
        ),
    )
