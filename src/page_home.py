from __future__ import annotations

from site_assets import CV_URI, HERO_URI, LINKEDIN
from site_components import nav, footer, CV_DOWNLOAD_NAME
from page_home_featured import home_featured_article
from home_whats_new import home_whats_new
from home_employer_strip import home_employer_strip
from home_pathways import home_pathways
from portfolio_operating_evidence import home_evidence
from career_facts import PROFILE_TECH_YEARS, MSX_PUBLIC_DATES


def home() -> str:
    return f'''{nav("home")}<main>
<section class="hero" data-portfolio-release="operating-evidence-2.0"><div class="container heroin"><div><p class="eyebrow">Enterprise AI · Data · Analytics</p><h1>Jair Ribeiro<span>Enterprise AI &amp; Data Leader</span></h1><p class="deck">I lead enterprise AI and Data work from strategy and portfolio decisions through product development, governance and adoption. My background in enterprise technology helps me work directly with delivery teams, develop people and turn business priorities into capabilities teams can build, own and use.</p><p class="context">Based in Gothenburg, Sweden · {PROFILE_TECH_YEARS} years in enterprise technology</p><div class="actions"><a class="btn primary" href="?page=impact" target="_self" data-hq-event="impact_home">Explore my AI leadership →</a><a class="btn text" href="?page=ai-data-governance" target="_self" data-hq-event="governance_home">AI &amp; Data Governance →</a><a class="btn text" href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_home">Download CV ↓</a></div></div><div class="portrait"><img src="{HERO_URI}" alt="Jair Ribeiro contributing to an executive AI panel" loading="eager" fetchpriority="high" decoding="async"><div class="note"><span>Operating perspective</span><strong>Working AI needs a business owner, a useful workflow and a team ready to operate it.</strong></div></div></div></section>


{home_employer_strip()}


{home_pathways()}

{home_evidence()}

{home_whats_new()}

{home_featured_article(instant=True)}

<section class="cta"><div class="container ctain"><div><h2>For enterprise AI and Data mandates.</h2><p>Experience leading AI opportunities, testing practical solutions, guiding investment choices and developing people and operating models across international teams.</p></div><div class="actions"><a class="btn ghost" href="?page=contact" target="_self" data-hq-event="contact_home_final">Contact →</a><a class="btn ghost" href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_home_final">LinkedIn ↗</a></div></div></section>
</main>{footer()}'''
