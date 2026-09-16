# Architecture

This repository is intentionally small. It is a professional leadership website, not an application portfolio.

## Structure

- `app.py` — Streamlit entry point and route dispatch.
- `src/` — active application code: pages, shared components, design system, metadata, media loading, CV generation and role lenses.
- `assets/` — canonical production media only.
- `static/` — public downloadable CV served by Streamlit.
- `tests/` — smoke tests for media, CV delivery and navigation coverage.
- `.github/workflows/` — CI and media-quality validation.

## Design intent

The site positions Jair Ribeiro as an Enterprise AI & Data Leader. Technical credibility is expressed through technical judgment across architecture, data, security, MLOps principles, economics, scalability and operating readiness. The repository should therefore remain quiet supporting evidence rather than evolve into a gallery of coding demos, toy RAG applications or framework experiments.

## Content boundaries

- No confidential employer material.
- No invented financial ROI, budget, team-size or decision-authority claims.
- No unemployment, urgency or "Open to Work" language.
- Leadership artifacts are sanitized generic reconstructions of enterprise practice.
- GitHub is not a primary navigation or positioning element on the public site.

## History

The repository state before the public-cleanup pass is preserved on `archive/pre-public-cleanup-2026-09-16`. Development-history media bundles and temporary patch modules are intentionally excluded from the default branch.
