from __future__ import annotations

from site_components import nav, footer, opportunity
from site_assets import (
    HERO_URI,
    WORKSHOP_URI,
    PANEL_DIALOGUE_URI,
    THINKING_PANEL_URI,
    AI_PANEL_URI,
    CONTACT_URI,
    ABOUT_BW_URI,
)


DFM_2026_IMAGE = "https://www.digitalfirstmagazine.com/wp-content/uploads/2026/06/Jair-Ribeiro.jpeg"
DFM_2023_IMAGE = "https://www.digitalfirstmagazine.com/wp-content/uploads/2023/05/800_480-Jair-Ribeiro-550x330.jpg"


def _media(uri: str, alt: str, *, contain: bool = False) -> str:
    if not uri:
        return ""
    mode = " contain" if contain else ""
    return (
        f'<div class="presence-media{mode}">'
        f'<img src="{uri}" alt="{alt}" loading="lazy" decoding="async">'
        '</div>'
    )


def presence() -> str:
    return f'''{nav("presence")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Speaking &amp; Thought Leadership</p><h1>Selected external work that complements operating experience.</h1><p>Speaking, publishing and expert participation are useful when they show an ability to explain complex choices, represent an organization credibly and contribute to serious industry discussion. This is a selected record rather than a complete archive.</p></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Selected speaking</p><h2>Enterprise AI, adoption, governance and the operating questions around scale.</h2></div><p>The emphasis is on externally verifiable engagements where the subject connects directly to the leadership work represented elsewhere in this portfolio.</p></div>
<div class="grid3">
<article class="card presence-card">{_media(HERO_URI, "Jair Ribeiro speaking at SMAU")}<div class="presence-body"><span class="org">SMAU Stockholm · 2026</span><h3>Driving Transformation through AI and Digitalisation</h3><p>Panel discussion with Microsoft, Politecnico di Milano and SSE Business Lab on how AI and digitalisation are shaping business ecosystems and practical use cases.</p><p><a href="https://www.smau.it/stockholm/schedule/driving-transformation-through-ai-and-digitalisation" target="_blank" rel="noopener" data-hq-event="article_presence_smau_stockholm">Official event record ↗</a></p></div></article>
<article class="card presence-card">{_media(AI_PANEL_URI, "Jair Ribeiro in an industry discussion at SMAU")}<div class="presence-body"><span class="org">SMAU Milano · 2025</span><h3>Digitalization &amp; Innovation: Powering the Future of Smart Cities</h3><p>Round-table discussion on AI, data, mobility and human-centered digitalisation, in collaboration with the Italian Trade Agency.</p><p><a href="https://www.smau.it/milano/2025/programma/digitalization-innovation-powering-the-future-of-smart-cities" target="_blank" rel="noopener" data-hq-event="article_presence_smau_milan">Official event record ↗</a></p></div></article>
<article class="card presence-card">{_media(CONTACT_URI, "Jair Ribeiro speaking at an AI leadership event")}<div class="presence-body"><span class="org">Chief AI Officer Exchange Europe · 2024</span><h3>Getting the Business on Board</h3><p>Keynote on connecting people and AI through storytelling, AI literacy and cross-functional adoption. Also contributed to the event's discussion on AI ownership and accountability.</p><p><a href="https://eco-cdn.iqpc.com/eco/files/event_content/chief-ai-officcer-exchange-europe-event-agenda-2024SUq6T8hBKVXfnBqCHm3LLUYAgsH9fL5OPo5cKlEK.pdf" target="_blank" rel="noopener" data-hq-event="article_presence_caio">Official agenda ↗</a></p></div></article>
<article class="card presence-card">{_media(THINKING_PANEL_URI, "Jair Ribeiro on stage at an AI conference")}<div class="presence-body"><span class="org">GAIA Conference · Gothenburg · 2024</span><h3>Ethics, law and responsible AI</h3><p>Panel contribution at Gothenburg's applied AI and data conference, alongside participants from academia, industry and the public sphere.</p><p><a href="https://www.gaia.fish/2024" target="_blank" rel="noopener" data-hq-event="article_presence_gaia">Conference record ↗</a></p></div></article>
<article class="card presence-card">{_media(WORKSHOP_URI, "Jair Ribeiro addressing an enterprise AI audience")}<div class="presence-body"><span class="org">Generative AI Summit · London · 2024</span><h3>Enterprise Generative AI</h3><p>Speaker at the second annual summit focused on moving Generative AI from initial trials toward enterprise use and operational value.</p><p><a href="https://aiml.events/events/generative-ai-summit-2024" target="_blank" rel="noopener" data-hq-event="article_presence_genai">Event record ↗</a></p></div></article>
<article class="card presence-card">{_media(PANEL_DIALOGUE_URI, "Jair Ribeiro on the Financial Times Future of AI Summit stage")}<div class="presence-body"><span class="org">Financial Times Future of AI Summit · 2023</span><h3>Infusing AI into the business</h3><p>Panel discussion moderated by the Financial Times on how organizations move AI beyond specialist teams and into business operations.</p><p><a href="https://www.edreamsodigeo.com/press-releases/2023/11/edreams-odigeo-shares-insights-on-infusing-ai-into-business-operations-at-the-financial-times-future-of-ai-summit/" target="_blank" rel="noopener" data-hq-event="article_presence_ft">Independent event coverage ↗</a></p></div></article>
</div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">Selected publications &amp; media</p><h2>Writing that stays close to enterprise choices.</h2></div><p>The strongest pieces connect technology with governance, data, work, adoption and management responsibility rather than treating AI as a technology trend in isolation.</p></div>
<div class="grid3">
<article class="card presence-card">{_media(DFM_2026_IMAGE, "Digital First Magazine feature with Jair Ribeiro", contain=True)}<div class="presence-body"><span class="org">Digital First Magazine · 2026</span><h3>AI Governance Is Not About Control. It Is About Scale.</h3><p>Expert opinion on governance as an operating capability for ownership, trust and repeatable enterprise use.</p><p><a href="https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/" target="_blank" rel="noopener" data-hq-event="article_presence_dfm_2026">Read publication ↗</a></p></div></article>
<article class="card presence-card">{_media(DFM_2023_IMAGE, "Digital First Magazine cover-story image for Jair Ribeiro", contain=True)}<div class="presence-body"><span class="org">Digital First Magazine · 2023</span><h3>Navigating the Ethical AI Landscape</h3><p>Cover story in the magazine's June 2023 issue on responsible AI and the leadership responsibility around ethical development and use.</p><p><a href="https://www.digitalfirstmagazine.com/june-2023-10-must-watch-innovators-to-follow-in-2023/" target="_blank" rel="noopener" data-hq-event="article_presence_dfm_2023">Issue record ↗</a></p></div></article>
<article class="card presence-card">{_media(ABOUT_BW_URI, "Jair Ribeiro, featured by CIO Applications Europe")}<div class="presence-body"><span class="org">CIO Applications Europe</span><h3>Transforming the Trucking Industry with Data Analytics and AI</h3><p>Interview on data quality, data culture, Generative AI and the practical conditions required to use analytics effectively in a large enterprise.</p><p><a href="https://www.cioapplicationseurope.com/cxoinsights/transforming-the-trucking-industry-with-data-analytics-and-ai-nid-3643.html" target="_blank" rel="noopener" data-hq-event="article_presence_cio_trucking">Read interview ↗</a></p></div></article>
</div></div></section>

<section class="section white"><div class="container twocol"><div><p class="eyebrow">Books &amp; longer-form work</p><h2>Long-form writing as a way to develop and test a point of view.</h2><p class="muted">Books and longer essays have been a secondary part of my professional work, not a separate career identity. The common thread is making technical and organizational questions understandable enough for leaders, practitioners and wider audiences to discuss them seriously.</p></div><div><div class="timeline">
<div class="trow"><b>2025</b><div><strong>The Last Human Question</strong><span>How Leaders and Workers Can Protect Human Roles in an AI-Driven European Job Market. Published through Amazon KDP; independently indexed by Google Books.</span><span><a href="https://books.google.com/books/about/The_Last_Human_Question.html?id=ZfG40QEACAAJ" target="_blank" rel="noopener" data-hq-event="article_presence_last_human">Google Books ↗</a></span></div></div>
<div class="trow"><b>2021</b><div><strong>AI, Robotics and Coding (for Parents)</strong><span>An accessible guide to AI, robotics and coding for parents thinking about children's skills, technology and ethical awareness.</span><span><a href="https://www.goodreads.com/book/show/57115956-ai-robotics-and-coding" target="_blank" rel="noopener" data-hq-event="article_presence_parents_book">Book record ↗</a></span></div></div>
<div class="trow"><b>2021</b><div><strong>A.I. in 2020: A Year Writing about Artificial Intelligence</strong><span>A collection of explanatory essays on AI concepts written for a broad audience.</span><span><a href="https://www.thinkers360.com/tl/jairribeiro" target="_blank" rel="noopener" data-hq-event="article_presence_ai2020">Publication record ↗</a></span></div></div>
</div></div></div></section>

<section class="section soft"><div class="container"><div class="head"><div><p class="eyebrow">External recognition &amp; networks</p><h2>Useful as third-party context, not as a substitute for operating evidence.</h2></div><p>Recognition is kept deliberately secondary on this portfolio. It matters only where an external organization has independently documented the contribution.</p></div><div class="grid3">
<div class="card"><span class="org">Thinkers360 · 2021</span><h3>Top 50 Global Thought Leaders and Influencers on AI</h3><p>Included in Thinkers360's June 2021 global AI leaderboard while working at Volvo Group.</p><p><a href="https://www.thinkers360.com/top-50-global-thought-leaders-and-influencers-on-ai-june-2021/" target="_blank" rel="noopener" data-hq-event="article_presence_thinkers360">Source ↗</a></p></div>
<div class="card"><span class="org">SwissCognitive</span><h3>Global AI Ambassador</h3><p>Member of SwissCognitive's international ambassador network, with a focus on responsible, human-centered AI discussion.</p><p><a href="https://swisscognitive.com/ambassadors/jair-ribeiro" target="_blank" rel="noopener" data-hq-event="article_presence_swisscognitive">Profile ↗</a></p></div>
<div class="card"><span class="org">Enterprise learning</span><h3>100+ AI learning sessions at Volvo Group</h3><p>The public speaking record sits alongside a larger body of internal AI literacy and adoption work. Across my Volvo AI roles, I delivered more than 100 sessions and learning opportunities for employees and practitioners.</p></div>
</div></div></section>

<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Earlier selected archive</p><h2>A longer record, kept subordinate to the current leadership story.</h2></div><p>Earlier appearances are useful mainly because they show continuity: translating AI and emerging technology for business audiences has been part of the work for several years.</p></div><div class="timeline">
<div class="trow"><b>2022</b><div><strong>IT Manager of Tomorrow</strong><span>Navigating career and skill development in the era of AI · Kimberly-Clark.</span><span><a href="https://www.tlt-summit.com/edition/2022" target="_blank" rel="noopener" data-hq-event="article_presence_itmt">Event archive ↗</a></span></div></div>
<div class="trow"><b>2019</b><div><strong>Codiax · Cluj-Napoca</strong><span>How to create a successful Artificial Intelligence strategy in business · Volvo Group.</span><span><a href="https://www.iqads.ro/articol/48601/codiax-2019-deep-tech-fueling-innovation" target="_blank" rel="noopener" data-hq-event="article_presence_codiax">Event coverage ↗</a></span></div></div>
<div class="trow"><b>2019</b><div><strong>TechFika · Wrocław</strong><span>Autonomous Vehicles — what's the technology behind them?</span><span><a href="https://crossweb.pl/wydarzenia/techfika-vol-3/" target="_blank" rel="noopener" data-hq-event="article_presence_techfika">Event archive ↗</a></span></div></div>
</div></div></section>
{opportunity()}</main>{footer()}'''
