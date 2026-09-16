from __future__ import annotations

import html

from site_assets import CV_URI, AI_PANEL_URI, HERO_URI, PANEL_DIALOGUE_URI
from site_components import nav, footer, opportunity


CLAES_LINKEDIN = "https://se.linkedin.com/in/claes-sandros-1a795512"
KUMARA_LINKEDIN = "https://in.linkedin.com/in/kumara-datta"
JIM_LINKEDIN = "https://www.linkedin.com/in/james-edwards-7233b8152"


def role_lens(
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
            f'<span class="org">Independent recommendation</span><h3>{html.escape(person)}</h3>'
            f'{role_html}'
            f'<p style="font:500 20px/1.45 Georgia,serif;color:var(--ink);margin-top:22px">“{html.escape(quote)}”</p>'
            f'<div class="proof"><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener" '
            f'data-hq-event="reference_{html.escape(person.lower().replace(" ", "_"))}_lens">LinkedIn profile ↗</a></div>'
            '</div></section>'
        )

    cv = (
        f'<a class="btn dark" href="{CV_URI}" download="Jair_Ribeiro_Master_CV_2026.pdf" '
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
        f'{nav("")}<main><section class="pagehero"><div class="container">'
        f'<p class="eyebrow">{html.escape(kicker)}</p><h1>{html.escape(title)}</h1>'
        f'<p>{html.escape(deck)}</p></div></section>'
        f'<section class="section paper"><div class="container lensgrid">'
        f'<aside class="lensaside"><p class="eyebrow">Jair Ribeiro</p>'
        f'<h2>Enterprise AI &amp; Data Leader</h2>{photo}'
        f'<p class="muted">Strategy, operating models, governance, adoption and business value — '
        f'with technical fluency grounded in enterprise technology.</p>'
        f'<p class="muted">{html.escape(perspective)}</p><div class="actions">'
        f'<a class="btn dark" href="?page=impact" target="_self" data-hq-event="impact_lens">'
        f'Leadership impact</a>{cv}</div></aside><div>{"".join(body)}</div></div></section>'
        f'{opportunity()}</main>{footer()}'
    )


def enterprise() -> str:
    return role_lens(
        "Role lens · Data & AI Leadership",
        "Data and AI leadership that turns strategy into operating capability.",
        "For Head / Director mandates spanning AI, data and analytics where the organization needs clearer priorities, ownership, data trust, governance and a practical path from experimentation to scale.",
        "My strongest fit is where one leader has to connect business direction with the data and AI capabilities underneath it, while remaining clear about where specialist technical ownership belongs.",
        [
            (
                "What I bring",
                "A business-facing data and AI leadership profile",
                "Experience spanning enterprise AI strategy, data and analytics, portfolio management, governance, adoption, operating models and architecture-aware decision-making. The value is in connecting these disciplines so they support one set of business choices rather than competing agendas.",
                [
                    "100+ AI initiatives and PoCs shaped across global contexts",
                    "AI literacy and adoption activity reaching 1,000+ employees",
                    "CoE and portfolio foundations connecting business, data, governance and technology",
                ],
            ),
            (
                "Operating capability",
                "From scattered activity to clearer ownership",
                "I focus on the structures that make AI repeatable: roles, decision rights, lifecycle stages, portfolio logic, data ownership and escalation paths. The aim is enough structure to improve decisions without making a central function the bottleneck for every decision.",
                [
                    "AI & Data CoE foundations at MSX International",
                    "Lifecycle stages, ownership and scale-readiness criteria",
                    "Data stewardship, quality and trusted-data foundations",
                ],
            ),
            (
                "Leadership style",
                "Technically credible without pretending to be the deepest specialist",
                "I can challenge architecture, scalability, cost, governance and adoption trade-offs while giving specialists room to own specialist decisions. That balance matters in leadership teams where business urgency and technical constraints are both real.",
                [
                    "Enterprise technology and cloud foundations",
                    "IBM Watson solution-design background",
                    "Cross-functional leadership across business, Digital & IT, analytics and governance",
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
        "Role lens · AI Transformation & Adoption",
        "Moving AI from experimentation into adopted enterprise capability.",
        "For mandates where the organization already has AI activity but needs clearer priorities, stronger adoption, governance and a practical path to scale. The work is less about launching another pilot and more about changing the system around the pilots.",
        "I tend to be most useful after initial enthusiasm has produced a long list of use cases. At that point, the leadership problem becomes prioritization, ownership, readiness, capability and the discipline to stop or reshape work that is not ready to scale.",
        [
            (
                "Transformation focus",
                "The hard part starts after the pilot",
                "My work centers on the organizational mechanisms that make AI usable at scale: prioritization, adoption, literacy, governance, data readiness and operating-model choices. A technically successful pilot is evidence of possibility, not yet evidence of an enterprise capability.",
                [
                    "1,000+ employees reached through AI literacy and adoption",
                    "1,500+ practitioners engaged through enterprise AI communities",
                    "Business use cases across warranty, sales, aftermarket, manufacturing, supply chain, logistics and marketing",
                ],
            ),
            (
                "Adoption",
                "Training is not adoption",
                "Capability building has to connect to real workflows, decisions, ownership and confidence. Literacy improves the quality of demand and use, but adoption only becomes visible when behavior and operating routines change.",
                [
                    "Practical GenAI literacy and responsible-use programs",
                    "Cross-functional use-case discovery and business translation",
                    "Connecting AI adoption with governance and data foundations",
                ],
            ),
            (
                "Scale",
                "Governance should help good work move faster",
                "I prefer governance mechanisms that clarify ownership, evidence and risk so teams know how to move. The useful question is not how many approvals exist, but whether the organization can distinguish low-risk experimentation from work that needs stronger evidence before it reaches customers, employees or critical processes.",
                [
                    "Lifecycle stage-gates and scale-readiness criteria",
                    "Risk-aware portfolio choices",
                    "Responsible AI positioned as an enabler of trusted adoption",
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
        "Role lens · AI Governance & Operating Model",
        "Governance and operating models that make ownership, evidence and scale clearer.",
        "For leadership mandates where AI needs stronger decision rights, lifecycle discipline, portfolio governance and responsible-AI mechanisms without creating a control layer that slows useful work.",
        "I treat governance as part of the operating system around AI. The objective is not more gates. It is to make clear who owns each decision, what evidence is required, when risk needs escalation and what must be true before broader use is justified.",
        [
            (
                "Operating model",
                "Make ownership visible before adding process",
                "AI programs become hard to scale when business ownership, technical ownership, data accountability and risk decisions are implicit. I start by making those responsibilities visible, then design the minimum structure needed to support repeatable decisions.",
                [
                    "Roles and decision rights across business, data, technology and governance",
                    "Lifecycle ownership from discovery through scale-readiness",
                    "CoE patterns designed to enable rather than centralize every decision",
                ],
            ),
            (
                "Governance",
                "Evidence and escalation instead of compliance theatre",
                "Good governance tells teams what they need to prove and where a decision belongs. It should distinguish experimentation from higher-risk use, expose unresolved assumptions and create a credible route for escalation when the consequences justify it.",
                [
                    "Responsible AI and risk-aware lifecycle mechanisms",
                    "Stage criteria and evidence requirements",
                    "Clearer escalation paths for higher-risk or higher-scale use",
                ],
            ),
            (
                "Data and trust",
                "Many governance problems begin as ownership problems",
                "Data quality, semantics, stewardship, access and lineage shape both technical performance and organizational trust. Treating them as separate from AI governance usually moves the same problem downstream.",
                [
                    "Data governance foundations connected to AI portfolio decisions",
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
        "Role lens · Business-Driven AI & Consulting",
        "Executive AI conversations grounded in what happens after the strategy deck.",
        "For consulting and advisory leadership where clients need a credible bridge between business priorities, technology choices, governance, adoption and delivery reality. My perspective is shaped by having worked on the operating side of that change as well as in client-facing technology roles.",
        "The differentiator I bring to advisory work is practical consequence. Recommendations have to survive data quality, architecture, governance, competing priorities and the people who will actually use the capability after the consulting team leaves.",
        [
            (
                "Advisory value",
                "Lived enterprise experience on the client side of AI change",
                "Experience from the operating side of global organizations — where recommendations have to survive architecture constraints, data realities, governance, adoption and competing priorities. That changes the questions I ask before recommending a target state.",
                [
                    "AI value discovery across EMEA business units",
                    "Enterprise portfolio and operating-model work",
                    "Executive and cross-functional communication across business and technology",
                ],
            ),
            (
                "Commercial relevance",
                "Shape the problem before shaping the solution",
                "My background includes consulting, client-facing technology work, IBM Watson solution design and supporting the development and sale of cognitive solutions. I am strongest in advisory selling built around a real business problem rather than a pre-packaged AI proposition.",
                [
                    "Business problem and value discovery",
                    "Solution and proposition shaping",
                    "Executive workshops and stakeholder dialogue",
                ],
            ),
            (
                "Differentiator",
                "Strategy connected to operating reality",
                "The strongest advisory work is not a recommendation that stops at the presentation. It creates decisions, ownership and a realistic path into execution, while making assumptions and dependencies visible enough for the client to act on them.",
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
            "",
            "He’s incredibly good at bringing people along on the journey and explaining the benefits of what AI can bring to an organization.",
            JIM_LINKEDIN,
        ),
    )
