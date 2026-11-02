# Executive AI Briefings — contextual reading navigation

**Effective:** 2 November 2026  
**Repository:** `AIribeiro/careersite`  
**Implementation:** `src/briefing_related_navigation.py`; inserted centrally by `src/site_cms.py`.

## Reader experience

After the briefing's argument, evidence and sharing, insert the contextual **Where to go next** section. The shared contact section headed **Have an AI choice that needs a clearer answer?** must remain the **final content section**, directly ahead of the site footer. Earlier issue-specific contact invitations may remain above the recommendations.

The section includes an edition-specific transition, **two relevant next briefings**, a single sentence explaining the connection to each, reading time taken from Content Studio and **Explore the briefing library**. On narrow screens the two cards stack. Focus styling, reduced-motion behavior, clear anchor labels and a labelled navigation region support keyboard and assistive-technology use.

Keep the section **after** the briefing, not inside the executive judgment or infographic. The reader should reach it when ready to continue.

## Initial editorial paths

| Current decision | Next useful read | Then |
| --- | --- | --- |
| AI, ML, GenAI, RAG and Agents | Seven Questions for Better AI Decisions | AI Governance Explained to Executives |
| Seven Questions for Better AI Decisions | Data Governance: What Deserves Funding? | Data Governance vs AI Governance |
| AI Governance Explained to Executives | Data Governance vs AI Governance | EU AI Act: What Executives Must Decide Now |
| EU AI Act: What Executives Must Decide Now | AI Governance Explained to Executives | Data Governance vs AI Governance |
| Data Governance: What Deserves Funding? | Data Governance vs AI Governance | Seven Questions for Better AI Decisions |
| Data Governance vs AI Governance | AI Governance Explained to Executives | Data Governance: What Deserves Funding? |

These are *editorial continuations*, not rankings or a popularity algorithm. Each link has its own brief justification. When new editions appear, add curated paths in `EDITORIAL_PATHS` and `EDITORIAL_INTROS`. Until curated, a deterministic metadata overlap chooses two candidates.

## Data integrity and routing

- Resolve every candidate against **current published CMS records** with `kind='Executive Briefing'` and `status='published'`.
- Never recommend the active edition; never show duplicate, malformed or unpublished destinations.
- Use `site_cms.article_relative_url` rather than constructing unrelated URL patterns. Text and attributes are HTML escaped.
- Include a maximum of two cards; with one available destination show one; with none render nothing.
- The section is inserted **once** immediately **before** the shared `briefings-conversation` contact footer in every independent reader. The governance-specific reader now includes this shared footer. If a future reader omits that footer, related-reading insertion safely falls back to the end of `<main>` until the template is corrected. The shared contact block—not the recommendations—must be the last reader section.
- A failure to fetch published records removes the navigation without breaking the main article.

## Analytics and interpretation

Use the existing first-party tracking rather than a new beacon:
- `data-analytics-section="briefings-related-reading"` measures exposure and eligible attention.
- `data-hq-event="briefing_related_open"` and `data-hq-content-slug` distinguish related-briefing card clicks.
- Canonical article links allow the existing article-card tracker to record target identity. The containing section identifies the placement.
- `briefing_related_library` tracks library intent.

Do **not** append internal marketing UTMs; they would overwrite genuine acquisition attribution. A click is not proof of the destination being read. A future reading-chain conversion metric should join destination page-view events by the privacy-conscious session ID instead of treating clicks as completions.

## Source-level verification

- Confirmed that the six currently published CMS slugs match the six curated editorial paths.
- `tests/test_briefing_related_navigation.py` includes eight cases: per-edition recommendations, published-only eligibility, future-briefing fallback, contact-last placement and idempotence, missing-footer fallback, canonical URLs and analytics, small libraries, and escaped titles.
- All destinations remain subject to the existing briefing anonymity and publication rules.

**Deployment boundary:** GitHub commits confirm source changes. This session did not execute repository tests or visually inspect the live Streamlit pages. Do not claim desktop/mobile rendering or active click measurement until independently verified on the deployed site.
