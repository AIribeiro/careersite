from __future__ import annotations

import site_assets
from site_assets import CV_URI, EMAIL, LINKEDIN
from site_components import nav, CV_DOWNLOAD_NAME


def contact() -> str:
    cv = f'<a href="{CV_URI}" download="{CV_DOWNLOAD_NAME}" data-hq-event="cv_download_contact">Download CV ↓</a>' if CV_URI else ""
    contact_uri = getattr(site_assets, "CONTACT_URI", site_assets.ABOUT_BW_URI)
    # Contact-specific semantic footer: one final contact block instead of a
    # duplicate sidebar and stacked links. The three actions remain a row.
    contact_footer = f'''<footer class="footer contact-footer" aria-label="Direct contact">
      <div class="container">
        <div class="contact-footer-row">
          <div class="contact-footer-intro">
            <p class="contact-footer-eyebrow">Direct contact</p>
            <p>Email or LinkedIn is the easiest way to reach me.</p>
          </div>
          <nav class="contact-footer-links" aria-label="Contact options">
            <a href="mailto:{EMAIL}" aria-label="Email {EMAIL}" data-hq-event="email_contact">
              <span class="contact-footer-email-full">{EMAIL}</span>
              <span class="contact-footer-email-short">Email</span>
            </a>
            <a href="{LINKEDIN}" target="_blank" rel="noopener" data-hq-event="linkedin_contact">LinkedIn ↗</a>
            {cv}
          </nav>
        </div>
        <p class="contact-footer-copyright">© 2026 Jair Ribeiro · Gothenburg, Sweden</p>
      </div>
    </footer>'''
    return f'''{nav("contact")}<main><section class="pagehero"><div class="container"><p class="eyebrow">Contact</p><h1>Connect on AI &amp; Data leadership.</h1><p>My work connects AI and data strategy with business priorities, responsible adoption and practical results.</p></div></section><section class="section paper"><div class="container contactgrid contactgrid-wide"><div><p class="eyebrow">Where my experience fits</p><h2>Start with the problem, not a long list of titles.</h2><p>The work in this portfolio focuses on helping large organizations make better choices about AI and data, from deciding where to focus to making new capabilities useful in everyday work. It spans:</p><div class="focus"><div>Enterprise AI &amp; Data leadership</div><div>Enterprise AI adoption, productivity and workflow change</div><div>AI / Data operating models and Centers of Excellence</div><div>AI governance and Responsible AI</div><div>AI portfolio and value leadership</div><div>Selected advisory or interim leadership work</div></div><p>Based in Gothenburg · Leadership opportunities across Sweden, including Stockholm · Hybrid, remote and travel arrangements considered.</p></div></div></section><section class="section contact-closing" aria-labelledby="contact-closing-title"><div class="container contactvisual"><div class="contact-closing-copy"><p class="eyebrow contact-closing-eyebrow">A first conversation</p><h2 id="contact-closing-title">Where can AI and data make a real impact?</h2><p>The best conversations start with a business challenge: what needs to improve, what is slowing progress, and what results matter most. From there, we can focus on the priorities, people and decisions that make a difference.</p><span class="contact-closing-rule" aria-hidden="true"></span></div><div class="contact-closing-visual"><figure class="contactportrait"><img src="{contact_uri}" alt="Jair Ribeiro speaking at an industry leadership panel" loading="lazy" decoding="async"></figure></div></div></section></main>{contact_footer}'''
