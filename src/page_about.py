from __future__ import annotations

from site_assets import CV_URI, ABOUT_BW_URI
from site_components import nav, footer, CV_DOWNLOAD_NAME
from about_recommendations import recommendations_section


def about() -> str:
    cv = f'<a class="btn dark" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_about">Download full CV ↓</a>' if CV_URI else ""
    return f'''{nav("about")}<main>
<section class="pagehero"><div class="container">
<p class="eyebrow">About</p>
<h1>A life across countries. A career shaped by curiosity.</h1>
<p>I'm Brazilian and have lived outside Brazil since 1998, making my home in Italy, Poland and now Sweden. Over those years, my work has taken me from enterprise technology into AI and data leadership. But my career is only one part of the story.</p>
</div></section>

<section class="section white" id="career-journey"><div class="container about-professional-arc">
<p class="eyebrow">My journey</p><h2>How I got here.</h2>
<figure class="about-arc-photo"><img src="{ABOUT_BW_URI}" alt="Portrait of Jair Ribeiro" loading="lazy" decoding="async"></figure>
<p class="muted">I started my career working with enterprise systems, infrastructure, cloud and consulting, often in roles that brought me close to clients and the people using the technology. It was a practical education. I learned that even a well-designed solution can fall short if it does not fit the people and the organization around it.</p>
<p class="muted">Around 2017, AI became a bigger part of my work. I began with solution design, moved into roles that connected AI with business needs, and later took on wider responsibilities in analytics, AI adoption and leadership. The jobs changed over time, but the most interesting work was often the same: understanding what people were trying to achieve and finding a realistic way forward.</p>
<p class="muted">I've seen promising ideas struggle because the original problem wasn't clear, the people affected weren't involved early enough, or nobody had really thought through what would happen after the project ended. Experiences like those have shaped how I work. I pay as much attention to the conversations around a change as I do to the technology behind it.</p>
<p class="muted">Looking back, the move from technical work to leadership was gradual. I didn't leave my technical background behind; it gave me a way to ask better questions, work with different specialists and understand the choices people face. What I enjoy most now is bringing those perspectives together and helping teams make progress they can sustain.</p>
</div><div class="container">
<div class="timeline">
<div class="trow"><b>Early career</b><div><strong>Learning the foundations</strong><span>Enterprise systems, infrastructure, cloud, consulting and client-facing technology work.</span></div></div>
<div class="trow"><b>From 2017</b><div><strong>A new direction in AI</strong><span>AI solution design and international, business-facing roles brought a new focus to my work.</span></div></div>
<div class="trow"><b>2021–2025</b><div><strong>Broader responsibilities</strong><span>AI strategy and analytics leadership, working across functions and with people responsible for using the results.</span></div></div>
<div class="trow"><b>2025–2026</b><div><strong>Leading across the enterprise</strong><span>A director-level AI &amp; Data role brought together the different parts of my career, from technology and business needs to people and organizational change.</span></div></div>
</div></div></section>

<section class="section soft" id="beyond-work"><div class="container">
<div class="head"><div><p class="eyebrow">Beyond work</p><h2>More than a job title.</h2></div>
<div><p>Living in Italy, Poland and Sweden has given me the chance to experience different cultures and ways of looking at the world. Brazil is where I come from, and those other places have also become part of who I am. Living abroad for so much of my adult life has made that mix feel natural.</p>
<p>I'm also the proud father of three amazing girls. Family is a big part of my life, and away from work I enjoy music, writing and travelling. I like the chance to discover new places, spend time with the people I love and follow interests that have nothing to do with a job description.</p></div>
</div>
<div class="chips"><span>Portuguese — native/bilingual</span><span>Italian — native/bilingual</span><span>English — full professional</span><span>Spanish — professional</span><span>Polish — limited working</span><span>Swedish — elementary</span></div>
</div></section>

{recommendations_section()}

<section class="section paper" id="speaking-publications"><div class="container">
<div class="head"><div><p class="eyebrow">Writing &amp; conversations</p><h2>Ideas I like to share.</h2></div><p>Writing and speaking have become another part of my journey. They give me room to explore questions, learn from other people and share some of what I have seen along the way.</p></div>
<div class="grid3 about-four-grid">
<article class="card"><span class="org">Speaking</span><h3>Conversations beyond my own workplace</h3><p>I've taken part in discussions at events in Stockholm, Milan, Gothenburg and London, among others, about AI and its place in organizations.</p><p><a href="https://www.smau.it/stockholm/schedule/driving-transformation-through-ai-and-digitalisation" target="_blank" rel="noopener">SMAU Stockholm ↗</a> · <a href="https://www.gaia.fish/2024" target="_blank" rel="noopener">GAIA Gothenburg ↗</a></p></article>
<article class="card"><span class="org">Articles &amp; interviews</span><h3>Putting experience into words</h3><p>I write about the questions that keep coming up in my work and have shared those perspectives through articles and interviews.</p><p><a href="https://www.digitalfirstmagazine.com/leaders-are-finally-understanding-ai-governance-is-not-about-control-it-is-about-scale-temp/" target="_blank" rel="noopener">Digital First Magazine ↗</a> · <a href="https://www.cioapplicationseurope.com/cxoinsights/transforming-the-trucking-industry-with-data-analytics-and-ai-nid-3643.html" target="_blank" rel="noopener">CIO Applications Europe ↗</a></p></article>
<article class="card"><span class="org">Books</span><h3>Writing for a wider audience</h3><p>Books and longer pieces let me follow an idea further, including what technology means for families and everyday life.</p><p><a href="https://books.google.com/books/about/The_Last_Human_Question.html?id=ZfG40QEACAAJ" target="_blank" rel="noopener noreferrer">The Last Human Question ↗</a> · <a href="https://www.goodreads.com/book/show/57115956-ai-robotics-and-coding" target="_blank" rel="noopener noreferrer">AI, Robotics and Coding ↗</a></p></article>
</div>
<div class="actions" id="credentials-evidence">{cv}<a class="btn dark" href="https://www.linkedin.com/in/jairribeiro/details/certifications/" target="_blank" rel="noopener" data-hq-event="about_certifications">Credentials on LinkedIn ↗</a></div>
</div></section>
</main>{footer()}'''
