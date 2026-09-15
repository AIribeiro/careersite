from __future__ import annotations

import html

from site_assets import CV_URI
from site_components import nav, footer, opportunity


def role_lens(kicker: str, title: str, deck: str, perspective: str, sections: list[tuple[str,str,str,list[str]]]) -> str:
    body = []
    for k,h,p,bullets in sections:
        bullet_html = "".join(f'<div>{html.escape(x)}</div>' for x in bullets)
        body.append(f'<section class="lenssection"><p class="eyebrow">{html.escape(k)}</p><h3>{html.escape(h)}</h3><p>{html.escape(p)}</p><div class="bullets">{bullet_html}</div></section>')
    cv = f'<a class="btn dark" href="{CV_URI}" download="Jair_Ribeiro_Master_CV_2026.pdf" data-hq-event="cv_download_lens">Download CV</a>' if CV_URI else ""
    return f'''{nav("")}<main><section class="pagehero"><div class="container"><p class="eyebrow">{html.escape(kicker)}</p><h1>{html.escape(title)}</h1><p>{html.escape(deck)}</p></div></section><section class="section paper"><div class="container lensgrid"><aside class="lensaside"><p class="eyebrow">Jair Ribeiro</p><h2>Senior AI &amp; Data Leader</h2><p class="muted">Strategy, operating models, governance, adoption and business value — with technical fluency grounded in enterprise technology.</p><p class="muted">{html.escape(perspective)}</p><div class="actions"><a class="btn dark" href="?page=impact" target="_self" data-hq-event="impact_lens">Leadership impact</a>{cv}</div></aside><div>{"".join(body)}</div></div></section>{opportunity()}</main>{footer()}'''


def enterprise() -> str:
    return role_lens(
        "Role lens · Enterprise AI & Data Leadership",
        "Enterprise AI and Data leadership that connects strategy, governance, adoption and scale.",
        "For Head / Director mandates where the challenge is not only building technical capability, but creating the operating system around it: priorities, ownership, data trust, decision rights and the conditions for scale.",
        "My strongest fit is where the organization needs one leader who can connect business direction with the AI and data capabilities underneath it, while remaining clear about where specialist technical ownership belongs.",
        [
            ("What I bring","A business-facing AI and data leadership profile","Experience spanning enterprise AI strategy, data and analytics, governance, portfolio management, adoption, operating models and architecture-aware decision-making. The value is in connecting these disciplines so they support one set of business choices rather than competing agendas.",["100+ AI initiatives and PoCs shaped across global contexts","AI literacy and adoption activity reaching 1,000+ employees","CoE and portfolio foundations connecting business, data, governance and technology"]),
            ("Operating model","From scattered activity to clearer ownership","I focus on the structures that make AI repeatable: roles, decision rights, lifecycle stages, portfolio logic, data ownership and escalation paths. The aim is enough structure to improve decisions without making a central function the bottleneck for every decision.",["AI / Data CoE foundations at MSX International","Lifecycle stages, ownership and scale-readiness criteria","Data stewardship, quality and trusted-data foundations"]),
            ("Leadership style","Technically credible without pretending to be the deepest specialist","I can challenge architecture, scalability, cost, governance and adoption trade-offs while giving specialists room to own specialist decisions. That balance matters in leadership teams where business urgency and technical constraints are both real.",["Enterprise technology and cloud foundations","IBM Watson solution-design background","Cross-functional leadership across business, Digital & IT, analytics and governance"]),
        ],
    )


def transformation() -> str:
    return role_lens(
        "Role lens · AI Transformation & Capability",
        "Moving AI from experimentation into adopted enterprise capability.",
        "For mandates where the organization already has AI activity but needs clearer priorities, stronger adoption, governance and a practical path to scale. The work is less about launching another pilot and more about changing the system around the pilots.",
        "I tend to be most useful after initial enthusiasm has produced a long list of use cases. At that point, the leadership problem becomes prioritization, ownership, readiness, capability and the discipline to stop or reshape work that is not ready to scale.",
        [
            ("Transformation focus","The hard part starts after the pilot","My work centers on the organizational mechanisms that make AI usable at scale: prioritization, adoption, literacy, governance, data readiness and operating-model choices. A technically successful pilot is evidence of possibility, not yet evidence of an enterprise capability.",["1,000+ employees reached through AI literacy and adoption","1,500+ practitioners engaged through enterprise AI communities","Business use cases across warranty, sales, aftermarket, manufacturing, supply chain, logistics and marketing"]),
            ("Adoption","Training is not adoption","Capability building has to connect to real workflows, decisions, ownership and confidence. Literacy improves the quality of demand and use, but adoption only becomes visible when behavior and operating routines change.",["Practical GenAI literacy and responsible-use programs","Cross-functional use-case discovery and business translation","Connecting AI adoption with governance and data foundations"]),
            ("Scale","Governance should help good work move faster","I prefer governance mechanisms that clarify ownership, evidence and risk so teams know how to move. The useful question is not how many approvals exist, but whether the organization can distinguish low-risk experimentation from work that needs stronger evidence before it reaches customers, employees or critical processes.",["Lifecycle stage-gates and scale-readiness criteria","Risk-aware portfolio choices","Responsible AI positioned as an enabler of trusted adoption"]),
        ],
    )


def consulting() -> str:
    return role_lens(
        "Role lens · Business-Driven AI & Consulting",
        "Executive AI conversations grounded in what happens after the strategy deck.",
        "For consulting and advisory leadership where clients need a credible bridge between business priorities, technology choices, governance, adoption and delivery reality. My perspective is shaped by having worked on the operating side of that change as well as in client-facing technology roles.",
        "The differentiator I bring to advisory work is practical consequence. Recommendations have to survive data quality, architecture, governance, competing priorities and the people who will actually use the capability after the consulting team leaves.",
        [
            ("Advisory value","Lived enterprise experience on the client side of AI change","Experience from the operating side of global organizations — where recommendations have to survive architecture constraints, data realities, governance, adoption and competing priorities. That changes the questions I ask before recommending a target state.",["AI value discovery across EMEA business units","Enterprise portfolio and operating-model work","Executive and cross-functional communication across business and technology"]),
            ("Commercial relevance","Shape the problem before shaping the solution","My background includes consulting, client-facing technology work, IBM Watson solution design and supporting the development and sale of cognitive solutions. I am strongest in advisory selling built around a real business problem rather than a pre-packaged AI proposition.",["Business problem and value discovery","Solution and proposition shaping","Executive workshops and stakeholder dialogue"]),
            ("Differentiator","Strategy connected to operating reality","The strongest advisory work is not a recommendation that stops at the presentation. It creates decisions, ownership and a realistic path into execution, while making assumptions and dependencies visible enough for the client to act on them.",["Portfolio prioritization and decision mechanisms","Governance and data-readiness implications","Adoption and internal capability building"]),
        ],
    )
