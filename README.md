# Jair Ribeiro — Senior AI & Data Leadership Site

Enterprise AI & Data leadership focused on strategy, operating models, governance, adoption and business value.

## Strategic purpose

The site helps recruiters, hiring managers, executive-search consultants, technical leaders and referrers quickly understand Jair Ribeiro's fit for senior AI, Data and Analytics leadership mandates.

Core positioning:

> **Senior AI & Data Leader — turning enterprise AI ambition into operating capability, adoption and measurable business value.**

Public availability language is intentionally restrained. The site signals receptiveness to the right mandate without publishing unemployment status, urgency, "Open to Work", or immediate availability.

## Content standard

The site should remain concise, but concise does not mean shallow. Headings and metrics should be accompanied by enough context to explain the operating problem, why the concept matters and what judgment sits behind it.

Leadership evidence should use this structure wherever the source material supports it:

> **Inherited problem → What Jair owned → Decision / trade-off → What he chose or shaped → What changed**

Do not manufacture decision authority, financial ROI, team size, budget ownership or commercial results that are not supported by source material.

## Site structure

- **Home** — positioning, evidence, value domains, operating-system lens, leadership style, technical fluency and selected thinking
- **Leadership Impact** — decision-based cases from MSX International, Volvo Group / Volvo Trucks and Kimberly-Clark, plus technical foundations
- **Thinking** — curated enterprise-AI thought leadership with an explicit editorial point of view
- **About** — career arc, research perspective, credentials, languages and shareable role lenses
- **Contact** — low-friction leadership-opportunity contact page
- **Role lenses** — Enterprise AI & Data Leadership; AI Transformation & Capability; Business-Driven AI & Consulting

## Runtime

- Python 3.12
- Streamlit 1.53.0
- fpdf2 2.8.8 for the downloadable canonical CV
- Entrypoint: `app.py`
- No application secrets required

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Streamlit Community Cloud deployment source:

- Repository: `AIribeiro/careersite`
- Branch: `main`
- Main file: `app.py`
- Python: `3.12`

## Repository layout

```text
.
├── .github/workflows/streamlit-ci.yml
├── .streamlit/config.toml
├── app.py                  # routing / entry point
├── site_assets.py          # authentic media + generated PDF CV
├── site_components.py      # navigation, footer, shared content
├── site_meta.py            # metadata, Person schema + conversion event hooks
├── site_styles.py          # executive editorial design system
├── site_lenses.py          # role-specific landing pages
├── page_home.py
├── page_impact.py
├── page_thinking.py
├── page_about.py
├── page_contact.py
├── asset_parts/            # text-safe authentic panel image
├── payload_parts/          # legacy bundle retained only as media source
├── hq_media.zip            # existing higher-quality photography
└── requirements.txt
```

The application logic is normal readable Python. The old embedded application source is no longer executed; the legacy payload is used only to recover existing media assets. The downloadable PDF CV is generated at runtime from the same factual career source used by the site, keeping dates and claims consistent.

## SEO and social metadata

`site_meta.py` adds page descriptions, canonical URLs, OpenGraph/Twitter metadata and `Person` JSON-LD to the browser document. Streamlit remains a client-rendered application, so social crawlers that do not execute client-side JavaScript may not read every dynamically injected tag. If reliable server-rendered social unfurls become a priority, the presentation layer should eventually move to a framework that controls the document `<head>` directly.

## Conversion measurement

Important actions include a `data-hq-event` attribute (CV downloads, contact intent, LinkedIn/Medium outbound links, article opens, Leadership Impact visits and role-lens opens). `site_meta.py` dispatches a first-party `hq-conversion` browser event for those interactions.

No external analytics provider is enabled by default. This is intentional: a privacy-conscious provider such as Plausible or Umami should only be connected once the deployment domain and privacy approach are explicitly configured. The event taxonomy is already in place for that integration.

## Content guardrails

- Keep the primary identity broad and senior: **Senior AI & Data Leader**.
- Prefer evidence, trade-offs and operating impact over adjectives.
- Explain concepts briefly enough that a senior reader understands why they matter; do not rely on slogans alone.
- Never publish "Open to Work", unemployment status, "available immediately", or urgency signals.
- Do not reposition Jair as an ML engineer, generic project/program manager, AI influencer, or independent consultant selling service packages.
- Keep employment dates factual and consistent with the master CV.
- Do not invent ROI, budget, direct-report counts, team sizes or commercial ownership.
- Do not publish MIT coursework references.
- Use authentic photography; avoid stock/futuristic AI imagery.
- English remains the primary site language.
