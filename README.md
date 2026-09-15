# Jair Ribeiro — Senior AI & Data Leadership Site

A Streamlit career site designed as a senior-leadership hiring conversion asset rather than an online CV or consulting sales funnel.

## Strategic purpose

The site helps recruiters, hiring managers, executive-search consultants, technical leaders and referrers quickly understand Jair Ribeiro's fit for senior AI, Data and Analytics leadership mandates.

Core positioning:

> **Senior AI & Data Leader — turning enterprise AI ambition into operating capability, adoption and measurable business value.**

Public availability language is intentionally restrained. The site signals receptiveness to the right mandate without publishing unemployment status, urgency, "Open to Work", or immediate availability.

## Site structure

- **Home** — positioning, evidence, value domains, leadership style, technical fluency and selected thinking
- **Leadership Impact** — evidence-based cases from MSX International, Volvo Group / Volvo Trucks, Kimberly-Clark and earlier technical roles
- **Thinking** — curated enterprise-AI thought leadership
- **About** — career arc, credentials, languages and shareable role lenses
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

## Content guardrails

- Keep the primary identity broad and senior: **Senior AI & Data Leader**.
- Prefer evidence, trade-offs and operating impact over adjectives.
- Never publish "Open to Work", unemployment status, "available immediately", or urgency signals.
- Do not reposition Jair as an ML engineer, generic project/program manager, AI influencer, or independent consultant selling service packages.
- Keep employment dates factual and consistent with the master CV.
- Do not invent ROI, budget, direct-report counts, team sizes or commercial ownership.
- Use authentic photography; avoid stock/futuristic AI imagery.
- English remains the primary site language.
