# Jair Ribeiro — Enterprise AI & Data Leadership Site

Professional website for Jair Ribeiro, positioned around one core identity:

> **Enterprise AI & Data Leader — building the decision system around AI so strategy becomes operating capability, adoption and measurable business value.**

Core point of view:

> **AI scales as a system, not as a model.**

The site is designed for recruiters, hiring managers, executive-search consultants, technical leaders and referrers evaluating senior AI, Data and Analytics leadership mandates.

## Strategic purpose

This is not a digital CV and not an AI-engineering demo portfolio. It is a decision-support site for senior hiring conversations.

The website adds evidence that a CV cannot carry well: leadership cases, sanitized operating frameworks, role-specific lenses, external recommendations, technical-judgment signals and thought leadership.

Public availability language is intentionally restrained. The site does not publish unemployment status, urgency, "Open to Work" language or immediate-availability signals.

The differentiating positioning idea is the **decision system around AI**: the combination of business priorities, portfolio choices, data and architecture, governance, adoption, ownership and value evidence that determines whether AI can move from experimentation to repeatable enterprise capability. This should remain more central than generic “AI ambition to value” language.

## Homepage reading model

The homepage is optimized for three reading times:

- **10 seconds** — Who is Jair?
- **30 seconds** — Why might I interview him?
- **90 seconds** — What proves it?

The homepage hierarchy is:

1. Hero positioning
2. Four evidence metrics
3. Front-door mandate selector
4. Three leadership cases
5. Leadership-framework teaser
6. External perspective
7. Contact CTA

The hero leads with the proprietary point of view **“AI scales as a system, not as a model”** and then explains the decision system around AI. Location is expressed simply as **“Based in Gothenburg · Sweden & international mandates.”**

The evidence strip deliberately separates overall career maturity from modern AI leadership:

- **20+ years enterprise technology** — supported by the public career timeline beginning in 2004.
- **8+ years AI / data / analytics leadership** — anchored to the leadership arc beginning in 2018.

These figures must remain distinct. The site must never imply 20+ years specifically in modern AI.

The front-door mandate selector lets a visitor self-select into:

- Enterprise AI & Data Leadership
- AI Transformation & Capability
- Business-Driven AI & Consulting

AI Governance & Operating Model remains available as a direct/shareable role lens.

## Navigation standard

Every public page is reachable from the persistent top navigation.

Primary menu:

- Home
- Leadership Impact
- Thinking
- About
- Role lenses
- Contact

The **Role lenses** submenu contains all four role-specific pages:

- Enterprise AI & Data Leadership
- AI Transformation & Capability
- AI Governance & Operating Model
- Business-Driven AI & Consulting

The analytics dashboard is deliberately **not** a public navigation item.

## Leadership evidence standard

Leadership cases use this structure wherever the source material supports it:

> **Inherited problem → What Jair owned → Decision / trade-off → What he chose or shaped → What changed**

The site must not manufacture decision authority, financial ROI, direct-report counts, budget ownership, commercial results or delivery scope that are not supported by source material.

## Sanitized leadership artifacts

The Leadership Impact page includes generic reconstructions of recurring enterprise-AI decision patterns:

- **AI portfolio lifecycle** — problem framing → qualification → value/feasibility discovery → experiment/pilot → scale-readiness → operated value.
- **Enterprise AI operating model** — business ownership, portfolio/CoE orchestration, product/delivery, data & architecture, governance/risk, adoption and value.
- **Pilot → enterprise scale framework** — business ownership, value hypothesis, data readiness, technical readiness, governance readiness and adoption readiness.
- **Governance decision matrix** — control intensity matched to consequence and uncertainty.

These are illustrative leadership artifacts. They must never reproduce confidential company material, internal thresholds, proprietary templates or employer-specific governance details.

## Technical-fluency positioning

Technical credibility is expressed through **technical judgment**, not coding theatre.

The site should demonstrate the ability to reason across:

- enterprise AI architecture;
- data platforms, quality, lineage and stewardship;
- security and AI risk;
- MLOps principles and operational readiness;
- scalability, maintainability and integration;
- cost / accuracy / autonomy trade-offs;
- vendor and solution choices.

The site should not drift into a hands-on AI-engineer archetype built around toy RAG applications, LangChain demos, coding exercises or model showcases. The public GitHub repository can support credibility quietly, but GitHub is not a primary navigation or positioning element.

## External perspective standard

Selected recommendations are used for complementary evidence, not enthusiasm:

- **Claes Sandros** — direct-manager evidence for senior leadership, strategic judgment, technical credibility and business value.
- **Anna Börjesson Sandberg** — VP-level cross-functional evidence for clarity, influence and direction.
- **Kumara Datta** — AI peer evidence for technical/business translation, AI credibility and adoption.
- **Jim Edwards** — transformation / consulting evidence for bringing people along, education and executive communication.

Recommendations are shown as intact excerpts. No ratings, stars or testimonial-wall treatment should be introduced.

## Public pages

- **Home** — positioning, evidence metrics, mandate selector, leadership cases, framework teaser, external perspective and contact.
- **Leadership Impact** — decision-based cases, sanitized leadership artifacts, recurring trade-offs and technical foundations.
- **Thinking** — curated enterprise-AI thought leadership.
- **About** — career arc, leadership approach, operating-system lens, technical fluency, credentials and languages.
- **Contact** — low-friction leadership-opportunity contact page.
- **Enterprise AI & Data Leadership** — role lens.
- **AI Transformation & Capability** — role lens.
- **AI Governance & Operating Model** — role lens.
- **Business-Driven AI & Consulting** — role lens.

A separate hidden analytics route exists for site-owner reporting and is not part of the public page architecture.

## Repository structure

The default branch intentionally contains only active production material:

```text
.
├── .github/workflows/        # CI and media-quality checks
├── .streamlit/               # Streamlit configuration
├── assets/                   # canonical production media only
│   ├── README.md
│   └── site_photos_bundle/
├── docs/
│   ├── ANALYTICS.md          # event taxonomy, attribution and reporting contract
│   └── ARCHITECTURE.md
├── src/                      # active application code
│   ├── page_*.py             # public pages plus hidden analytics page
│   ├── site_analytics.py
│   ├── site_*.py
│   └── __init__.py
├── static/                   # public downloadable CV
├── tests/
│   └── test_runtime.py
├── app.py                    # Streamlit entry point
├── README.md
└── requirements.txt
```

Development-history media bundles, temporary patch modules, empty placeholder files and obsolete image-build tooling are excluded from `main`.

The repository state immediately before this cleanup is preserved on:

`archive/pre-public-cleanup-2026-09-16`

## Runtime

- Python 3.12
- Streamlit 1.53.0
- fpdf2 2.8.8
- Entrypoint: `app.py`

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The analytics client has sensible production defaults for the shared first-party Supabase event store. They can be overridden with:

- `CAREERSITE_ANALYTICS_URL`
- `CAREERSITE_ANALYTICS_PUBLISHABLE_KEY`

The browser key is intentionally publishable; Row Level Security is the enforcement boundary.

## Validation

GitHub Actions validates:

- Python compilation;
- smoke tests for CV delivery, media loading, navigation coverage, career-tenure positioning, core homepage positioning and analytics taxonomy/privacy/attribution constraints;
- Streamlit startup and health;
- integrity and expected dimensions of the canonical leadership-photo bundle.

## SEO and behavioral measurement

`site_meta.py` owns page descriptions, canonical URLs, OpenGraph/Twitter metadata and `Person` JSON-LD.

`site_analytics.py` owns behavioral measurement. Both Streamlit and Lovable are required to use the same seven-event taxonomy:

- `page_view`
- `impact_view`
- `lens_view`
- `cv_download`
- `email_click`
- `linkedin_click`
- `article_click`

Events are written to a shared Supabase table using anonymous insert-only access. The application does not use analytics cookies, persistent visitor IDs, heatmaps or session recordings. A random per-tab UUID is stored only in `sessionStorage` so one visit can be reconstructed as a funnel. The application-owned analytics table does not store IP addresses, user-agent strings, names or email addresses.

### Job-search attribution

Preferred attributed links use `source` and an optional `role` label:

```text
https://jairribeiro-ai.streamlit.app/?source=linkedin
https://jairribeiro-ai.streamlit.app/?source=cv
https://jairribeiro-ai.streamlit.app/?source=outreach
https://jairribeiro-ai.streamlit.app/?source=application&role=ai-transformation
```

Attribution is retained only for the current browser tab/session, allowing later Impact, lens and CV actions to be associated with the original job-search activity without identifying an individual. Legacy `utm_source`, `src` and `utm_campaign` remain supported.

The hidden site-owner dashboard is available at:

```text
https://jairribeiro-ai.streamlit.app/?page=analytics
```

It is excluded from public navigation, marked noindex and protected by a separate access code. The dashboard receives aggregate data from an access-controlled database function; raw analytics rows remain unreadable to anonymous clients.

Existing `data-hq-event` attributes remain useful instrumentation hooks, but their many raw names are mapped into the reduced seven-event taxonomy before storage. Full implementation and reporting semantics are documented in `docs/ANALYTICS.md`.

## Content guardrails

- Keep the primary identity broad and senior: **Enterprise AI & Data Leader**.
- Keep **“AI scales as a system, not as a model”** and the **decision system around AI** central to the positioning; do not dilute the site back into generic AI-transformation language.
- Use **20+ years enterprise technology** and **8+ years AI / data / analytics leadership** as separate chronology signals; never imply 20+ years in modern AI.
- Use **“Based in Gothenburg · Sweden & international mandates”** when a compact location/mandate line is needed; avoid repetitive constructions such as “Gothenburg, Sweden · Sweden / International.”
- Prefer evidence, trade-offs and operating impact over adjectives.
- Never publish "Open to Work", unemployment status, immediate availability or urgency signals.
- Do not reposition Jair as an ML engineer, generic project/program manager, AI influencer or independent consultant selling packaged services.
- Keep employment dates factual and consistent with the canonical CV.
- Do not invent ROI, budgets, team sizes, direct reports or commercial ownership.
- Use authentic photography; avoid stock/futuristic AI imagery.
- Keep leadership artifacts generic and sanitized.
- Keep GitHub as quiet supporting evidence, not a prominent site destination.
- Keep analytics limited to the seven approved events and the privacy model in `docs/ANALYTICS.md`.
- Use attribution to classify job-search activity, never to identify individual visitors.
- English remains the primary site language.
