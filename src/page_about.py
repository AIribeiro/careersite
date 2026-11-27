from __future__ import annotations

from html import escape

from site_assets import CV_URI, ABOUT_BW_URI
from site_media import _uri as portfolio_photo_uri
from site_components import nav, footer, CV_DOWNLOAD_NAME
from about_recommendations import recommendations_section
from about_next_navigation import about_next_navigation



# Use the same verified, versioned public media URLs as the rest of the site.
# The app-local /portfolio-image route does not consistently resolve in the
# deployed Streamlit browser context. The committed WebP originals are small
# enough to serve directly without pretending ?w= creates image variants.
FAMILY_PHOTOS = (
    ("about-family-portrait.webp", "Family portrait with Jair, his wife and two daughters", 1448, 1086, "portrait"),
    ("about-family-moments.webp", "A collection of candid moments from family life and travel", 1024, 1536, "moments"),
    ("about-family-visit.webp", "Jair with his family visiting a Volvo truck display", 1431, 2798, "visit"),
)


def _family_gallery() -> str:
    figures = []
    for filename, alt, width, height, kind in FAMILY_PHOTOS:
        url = portfolio_photo_uri(filename)
        if not url:
            continue
        loading = "eager" if kind == "portrait" else "lazy"
        figures.append(
            f'<figure class="about-family-photo about-family-photo--{kind}">'
            f'<img src="{url}" width="{width}" height="{height}" alt="{alt}" '
            f'loading="{loading}" decoding="async"></figure>'
        )
    if not figures:
        return ""
    return '<div class="about-family-gallery" aria-label="Family photographs">' + "".join(figures) + '</div>'

# Keep the published proficiency labels exact; this is a professional capability
# statement, not an assertion of equal fluency across all six languages.
LANGUAGE_CAPABILITIES = (
    ("Portuguese", "Native / bilingual", "PT", "professional"),
    ("Italian", "Native / bilingual", "IT", "professional"),
    ("English", "Full professional", "EN", "professional"),
    ("Spanish", "Professional", "ES", "professional"),
    ("Polish", "Limited working", "PL", "developing"),
    ("Swedish", "Elementary", "SV", "developing"),
)


# Country flags are visual shorthand for languages, not equivalences.
# Render the icon geometry with CSS (not inline SVG): Streamlit's HTML layer
# may filter SVG children, leaving a blank badge on Safari/iPad.
LANGUAGE_FLAGS = {
    "PT": ("br", "Brazil"),
    "IT": ("it", "Italy"),
    "EN": ("gb", "United Kingdom"),
    "ES": ("es", "Spain"),
    "PL": ("pl", "Poland"),
    "SV": ("se", "Sweden"),
}


def _language_tile(name: str, proficiency: str, code: str) -> str:
    flag_class, country = LANGUAGE_FLAGS[code]
    return (
        '<div class="about-language-tile">'
        '<span class="about-language-mark" aria-hidden="true">'
        f'<span class="about-language-flag about-language-flag--{flag_class}"></span>'
        '</span>'
        '<span class="about-language-detail">'
        f'<strong>{escape(name)}</strong>'
        f'<span>{escape(proficiency)}</span>'
        '</span></div>'
    )


def _languages_section() -> str:
    professional = "".join(
        _language_tile(name, proficiency, code)
        for name, proficiency, code, group in LANGUAGE_CAPABILITIES
        if group == "professional"
    )
    developing = "".join(
        _language_tile(name, proficiency, code)
        for name, proficiency, code, group in LANGUAGE_CAPABILITIES
        if group == "developing"
    )
    return (
        '<section class="section about-languages-section" id="languages-leadership" '
        'aria-labelledby="languages-leadership-title">'
        '<div class="container about-languages-layout">'
        '<div class="about-languages-story">'
        '<div class="about-languages-intro">'
        '<p class="eyebrow">International leadership</p>'
        '<h2 id="languages-leadership-title">Communicating across cultures.</h2>'
        '</div>'
        '<div class="about-languages-copy">'
        '<p>Living and working across countries has made speaking several '
        'languages a practical part of how I lead. It helps me listen for '
        'nuance, build relationships and make space for perspectives that '
        'might otherwise be lost in translation.</p>'
        '<p>In AI and Data leadership, that matters when people from '
        'different functions, markets and backgrounds need to understand '
        'one another and make decisions together.</p>'
        '<div class="about-languages-takeaway">'
        '<span>What this adds to my work</span>'
        '<strong>Trust, clarity and influence across cultural and '
        'organizational boundaries.</strong>'
        '</div></div></div>'
        '<div class="about-languages-profile" aria-label="Languages and proficiency">'
        '<p class="about-language-group-label">Professional communication</p>'
        '<div class="about-language-grid">' + professional + '</div>'
        '<p class="about-language-group-label about-language-group-label--secondary">'
        'Developing proficiency</p>'
        '<div class="about-language-grid about-language-grid--secondary">' + developing + '</div>'
        '</div></div></section>'
    )


def about() -> str:
    family_gallery = _family_gallery()
    cv = f'<a class="btn dark" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_about">Download full CV ↓</a>' if CV_URI else ""
    return f'''{nav("about")}<main>
<section class="pagehero"><div class="container">
<p class="eyebrow">About</p>
<h1>A life across countries. A career shaped by curiosity.</h1>
<p>I'm Brazilian and have spent most of my adult life living abroad. Along the way, my career moved from enterprise technology into AI and data leadership. The work matters to me, but so do the places I've lived, the people around me and the life I've built outside it.</p>
</div></section>

<section class="section white" id="career-journey"><div class="container about-professional-arc">
<p class="eyebrow">My journey</p><h2>How I got here.</h2>
<figure class="about-arc-photo"><img src="{ABOUT_BW_URI}" alt="Portrait of Jair Ribeiro" loading="lazy" decoding="async"></figure>
<p class="muted">I built my technical foundations in Italy, working with enterprise systems, infrastructure, cloud and consulting, including at HPE in Milano. Those roles brought me close to clients and the people using the technology. It was a practical education. I learned that even a well-designed solution can fall short if it does not fit the people and the organization around it.</p>
<p class="muted">My AI experience began with IBM Watson in Wrocław, Poland, in 2016. I moved into business-facing AI at Volvo Group and later into EMEA AI strategy at Kimberly-Clark in Kraków. Moving to Sweden in 2022 brought me to Gothenburg, where I took on broader AI and analytics responsibilities at Volvo Trucks and later led AI and Data strategy and governance at MSX International. Across those countries and organizations, the most interesting work remained the same: understanding what people were trying to achieve and finding a realistic way forward.</p>
<p class="muted">I've seen promising ideas struggle because the original problem wasn't clear, the people affected weren't involved early enough, or nobody had really thought through what would happen after the project ended. Experiences like those have shaped how I work. I pay as much attention to the conversations around a change as I do to the technology behind it.</p>
<p class="muted">Looking back, the move from technical work to leadership was gradual. I didn't leave my technical background behind; it gave me a way to work directly with developers, architects and IT teams on requirements, testing, architecture and delivery decisions. Experience with Azure, AWS and Databricks and responsibility for shared enterprise analytics capacity reinforced that connection. What I enjoy most now is bringing those perspectives together: setting direction, making difficult decisions clearer, coaching people and enabling teams to take ownership, even when they do not report to me.</p>
</div><div class="container">
<div class="timeline">
<div class="trow"><b>Early career</b><div><strong>Learning the foundations</strong><span>In Italy, including my years at HPE in Milano, I developed my foundations in enterprise systems, infrastructure, cloud and client-facing technology work.</span></div></div>
<div class="trow"><b>From 2016</b><div><strong>A new direction in AI</strong><span>In Wrocław, Poland, IBM Watson introduced me to AI solution design, followed by business-facing AI and product work with international teams at Volvo Group.</span></div></div>
<div class="trow"><b>2021–2025</b><div><strong>Broader responsibilities</strong><span>From EMEA AI strategy at Kimberly-Clark in Kraków, Poland, to AI and analytics leadership at Volvo Trucks in Gothenburg, Sweden, I took on wider responsibilities across business and technology teams.</span></div></div>
<div class="trow"><b>2025–2026</b><div><strong>Leading across the enterprise</strong><span>Based in Gothenburg, Sweden, my director-level role at MSX International brought together AI strategy, governance, technical delivery and organizational change across a global business.</span></div></div>
</div></div></section>

{_languages_section()}

{recommendations_section()}

<section class="section paper" id="speaking-publications"><div class="container">
<div class="head"><div><p class="eyebrow">Writing &amp; conversations</p><h2>Ideas I like to share.</h2></div><p>Writing and speaking have become another part of my journey. They give me room to explore questions, learn from other people and share some of what I have seen along the way.</p></div>
<div class="grid3 about-four-grid">
<article class="card"><span class="org">Speaking</span><h3>Conversations beyond my own workplace</h3><p>I've taken part in discussions at events in Stockholm, Milan, Gothenburg and London, among others, about AI and its place in organizations.</p><p><a href="https://www.smau.it/stockholm/schedule/driving-transformation-through-ai-and-digitalisation" target="_blank" rel="noopener">SMAU Stockholm ↗</a> · <a href="https://www.gaia.fish/2024" target="_blank" rel="noopener">GAIA Gothenburg ↗</a></p></article>
<article class="card"><span class="org">Articles &amp; interviews</span><h3>Putting experience into words</h3><p>I write about the questions that keep coming up in my work and have shared those perspectives through articles and interviews.</p><p><a href="https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/" target="_blank" rel="noopener">Digital First Magazine ↗</a> · <a href="https://www.cioapplicationseurope.com/cxoinsights/transforming-the-trucking-industry-with-data-analytics-and-ai-nid-3643.html" target="_blank" rel="noopener">CIO Applications Europe ↗</a></p></article>
<article class="card"><span class="org">Books</span><h3>Writing for a wider audience</h3><p>Books and longer pieces let me follow an idea further, including what technology means for families and everyday life.</p><p><a href="https://books.google.com/books/about/The_Last_Human_Question.html?id=ZfG40QEACAAJ" target="_blank" rel="noopener noreferrer">The Last Human Question ↗</a> · <a href="https://www.goodreads.com/book/show/57115956-ai-robotics-and-coding" target="_blank" rel="noopener noreferrer">AI, Robotics and Coding ↗</a></p></article>
<article class="card"><span class="org">Ongoing publications</span><h3>AI decisions, week by week</h3><p>Through Executive AI Briefings and Weekly AI, I examine what AI developments mean for the people making business decisions, from governance and adoption to emerging capabilities.</p><p><a href="?page=briefings" target="_self">Executive AI Briefings ↗</a> · <a href="?page=thinking" target="_self">Weekly AI &amp; Thinking ↗</a></p></article>
</div>
<div class="actions" id="credentials-evidence">{cv}<a class="btn dark" href="?page=certifications" target="_self" data-hq-event="about_certifications">Certifications &amp; credentials →</a><a class="btn dark" href="?page=presence" target="_self" data-hq-event="about_presence">Speaking &amp; publications →</a></div>
</div></section>

<section class="section soft" id="beyond-work"><div class="container">
<div class="head"><div><p class="eyebrow">Beyond work</p><h2>More than a job title.</h2></div>
<div><p>Since 1998, I've lived in Italy, Poland and now Sweden. Living in different countries has given me a chance to experience other cultures and ways of seeing the world. Brazil is where I come from, but the places I've called home since then have become part of my story too.</p>
<p>I'm also the proud father of three amazing girls. Family is a big part of my life, and away from work I enjoy music, writing and travelling. I like the chance to discover new places, spend time with the people I love and follow interests that have nothing to do with a job description.</p></div>
</div>
{family_gallery}
</div></section>

{about_next_navigation()}
</main>{footer()}'''
