# Architecture

This repository is intentionally small. It powers a curated professional leadership portfolio, not an application portfolio, expanded CV or engineering-demo site.

## Structure

- `app.py` — Streamlit entry point and route dispatch.
- `src/` — active application code: pages, shared components, design system, metadata, analytics, media loading, CV generation and contextual role lenses.
- `assets/` — canonical production media only.
- `static/` — validated public downloadable CV served by Streamlit.
- `tests/` — smoke and regression tests for positioning, evidence attribution, media, CV delivery, navigation and analytics constraints.
- `.github/workflows/` — CI, canonical CV generation and media-quality validation.

## Design intent

The site positions Jair Ribeiro as an **Enterprise AI & Data Leader**. Its purpose is to show the judgment behind the CV: selected situations, trade-offs, leadership across organizational boundaries, examples of recurring enterprise decisions, external perspectives and curated writing.

The central point of view is **“AI scales as a system, not as a model.”** The related idea of the decision system around AI is a leadership perspective rather than a proprietary methodology or product.

Technical credibility is expressed through technical judgment across architecture, data, security, MLOps principles, economics, scalability and operating readiness. Specialist technical depth remains with the specialists responsible for those decisions. The repository should therefore remain quiet supporting evidence rather than evolve into a gallery of coding demos, toy RAG applications or framework experiments.

## Content boundaries

- No confidential employer material.
- No invented financial ROI, budget, team-size, direct-report or decision-authority claims.
- No unemployment, urgency or "Open to Work" language.
- Metric attribution must remain precise; in particular, the 100+ AI initiative evidence belongs across Jair's Volvo AI roles rather than solely to the 2022–2025 role.
- Leadership artifacts are sanitized generic reconstructions of enterprise practice, presented as examples rather than proprietary methodologies.
- Role lenses reorganize selected evidence for a hiring context; they are not mini-CVs or separate professional identities.
- Consulting is secondary and is not presented as packaged services.
- GitHub is not a primary navigation or positioning element on the public site.
- Behavioral analytics remain invisible to normal visitors and use only the approved privacy-conscious taxonomy.

## Public architecture

The public site keeps nine views: Home, Leadership Impact, Thinking, About, Contact and four contextual role lenses. The hidden analytics route is excluded from public navigation.

Home deliberately uses only three broad experience areas — Enterprise AI & Data Leadership, AI Transformation & Adoption, and Governance / Operating Model / Responsible Scale — rather than exposing the job-search taxonomy as a front-door role selector.

## CV delivery

The canonical public PDF is `static/Jair_Ribeiro_Enterprise_AI_Data_Leader_CV_2026.pdf`. It is generated and validated in CI, committed to `main`, and served through Streamlit's app-relative `app/static/...` route. The deployed app reads the committed artifact and does not regenerate it at runtime.

## History

The repository state before the public-cleanup pass is preserved on `archive/pre-public-cleanup-2026-09-16`. Development-history media bundles and temporary patch modules are intentionally excluded from the default branch.
