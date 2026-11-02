# Executive Briefing Infographic Engine — delivery and operating contract

**Date:** 2 November 2026  
**Repository:** `AIribeiro/careersite`  
**Database:** Supabase project `rnqweoxtynelfirffmlr`  
**Status:** Implemented in repository and database; deployment and real-browser visual QA are **not verified**.

## Objective

One original, premium, strategic decision infographic per Executive AI Briefing. The graphic should communicate the briefing's principal executive judgment faster than the article text alone without sacrificing evidence, legal status or editorial accuracy.

## Core architecture

- `src/briefing_infographic_engine.py`: deterministic article-headings-to-visual specification, six visual grammars, specification validation, HTML-safe first-party SVG desktop/mobile renderers, data-URI image fallback and accessible caption.
- `src/briefing_infographic_store.py`: authenticated owner save, approval, rejection, content fingerprinting, approved/current asset selection; public read-only lookup with fail-closed behavior.
- `src/briefing_infographic_admin.py`: Content Studio editing, desktop/mobile preview, accessible alt-text editing, six review criteria, approval/rejection and owner-only readership metrics.
- `src/page_admin.py`: integrated editor, mandatory reviewed infographic before the Executive Briefing publish/update action.
- `src/site_cms.py`: server-side publishing validation; no new published briefing without a current approved infographic.
- `src/page_executive_briefings.py`: shared approved visual insertion into every reader, including special seven-question and governance readers.
- `src/data_governance_funding_briefing.py`, `src/data_vs_ai_governance_briefing.py`: preserve original reader visuals as fallback; use approved CMS infographic as the primary graphic.
- `tests/test_briefing_infographic_engine.py`: six-pattern, semantic XML, mobile, anonymity, stale-version and analytics-markup tests, committed but execution not verified.

The generator uses documented rules and the article's own content. **It does not call a language/image model and must not be described as AI-verified artwork or automated fact-checking.** The ability to edit the structured visual proposal is intentionally part of the editorial process.

## Database and privacy

Table `public.careersite_briefing_infographics` holds one row **per revision**, including article reference, article slug, pattern, spec JSONB, accessible alt text, caption, status (draft/approved/rejected), revision, six review flags, source SHA-256 fingerprint, private editor note and approval timestamp.

- `article_id, revision` unique; previous approved revisions are preserved while later drafts are revised. Public readers select the highest approved revision matching the current article fingerprint.
- Supabase RLS: anonymous readers can access only **approved graphics for published briefings**, and only selected rendering columns (not reviewer notes or checklists). Owner authenticated by the portfolio's existing email-based authorization can read and change drafts and approvals. Direct table writes still require proper role access.
- The article publication trigger `careersite_briefing_requires_approved_infographic` checks that the infographic's SHA-256 fingerprint matches current title, subtitle and body, as well as all required review flags. Any new or modified published Executive Briefing lacking this is rejected (SQLSTATE 23514).
- The legacy employer-anonymity trigger is preserved. Editorial specifications use `briefing_content_policy.validate_briefing_employer_anonymity` to reject known former-employer names.
- The prior approved infographic is not removed when a draft revision is created. A new approved revision becomes the reader's default without a static deployment.
- Owner-only analytics view `public.careersite_briefing_infographic_analytics_v1` measures exposed sessions, unique article sessions, exposure ratio and observed attention from existing `section_view` and `section_attention` events. The event source has an owner-only SELECT policy; anonymous users cannot query the analytics view.

## Six original specifications backfilled

| Edition | Primary pattern | Central visual point |
| --- | --- | --- |
| AI, ML, GenAI, RAG and Agents | Flow | Six complementary capabilities chosen by business purpose |
| Seven Questions for Better AI Decisions | Questions | Seven critical lenses leading to a decision and review gate |
| AI Governance Explained to Executives | Layers | Seven parallel operating control surfaces |
| EU AI Act: What Executives Must Decide Now | Decision | Purpose, legal role, applicable control and approval evidence |
| Data Governance: What Deserves Funding? | Flow | Exposure, causality, minimum control, operating proof |
| Data Governance vs AI Governance | Comparison | Separate information and AI assurance, one business gate |

All six records were inserted as approved *editorial specifications* and confirmed current against published CMS content. These approvals attest to source-level editorial and responsive-layout review. **They are not evidence of actual desktop/mobile visual checks or live deployment success.**

## Content Studio operating sequence

1. Save the new Executive Briefing text as a draft so it has a persistent article ID.
2. Expand **Executive Briefing · Infographic Engine**.
3. Generate a structured proposal from the article or revise an existing one.
4. Edit JSON title/deck/items/conclusion so every label earns its position and the diagram is genuinely strategic. Required fields: `pattern`, `title`, `deck`, `items` (2–7), `conclusion`.
5. Add meaningful alt text (40+ characters) and caption.
6. Preview desktop and mobile SVG at the actual intended scale; edit and save a new draft revision.
7. Sign off accuracy, originality, anonymity, readability, mobile and content fit; **Approve and insert**.
8. Publish the article through the normal Content Studio review. Backend and DB reject missing, stale or unreviewed graphics.
9. If the article title, deck or body changes, re-review its infographic. To edit an already-published article substantially, unpublish as draft, save new text, approve new visual and republish.

## Technical and editorial caveats

- The base generator extracts article headings but is not an automatic graphic designer with semantic understanding; generic drafts require a senior editor to write precise proof points. The six current specifications are specifically curated.
- SVG files are assembled in code from escaped strings, encoded as self-contained data URIs and rendered with `<picture>` desktop/mobile variants. No remote image URL, external font or third-party graphic is used.
- The six templates are diagram grammars, not six fixed borrowed illustrations. A new briefing should choose a grammar that fits its decision rather than copy an existing edition's full layout.
- Desktop/mobile previews are available to a signed-in owner; an image that appears source-valid may still look cramped on an actual phone. Visual QA must include representative long titles, small screens, browser safety and the deployed CMS reader.
- First-party analytics are observed engagement proxies; no heatmap, persistent visitor profiling or unsupported comprehension estimate was introduced.
- `section_attention` is provided by the existing analytics script; the infographic uses `data-analytics-section="briefing-infographic"` to use it. Historic article views may predate the infographic, so reach ratios can be misleading before deployment.

## Verification performed

- Six published CMS articles joined to six approved, current infographic revisions; no stale source fingerprints.
- A direct SQL test attempting to change published article content without reapproval failed as expected.
- Anonymous Postgres role test returned six visible approved infographic records. Review-note column access has been revoked from anon.
- Owner analytics view returned a row for all six briefings; no new infographic views yet.
- GitHub source inspection found wiring to all six readers and dedicated Content Studio functionality.

## Still to verify on deployed application

1. New editor panel opens and saves/approves/rejects a test visual without session regression.
2. Render each infographic in independent reader; ensure placement below judgment, no duplicate primary graphic, no broken image.
3. Desktop, tablet and narrow iPhone widths: labels, caps, contrast, navigation, scroll and captions.
4. Future visual revisions leave prior approved graphic visible.
5. Public REST returns only authorized fields and private notes are not exposed.
6. The six committed Python tests execute and pass in the deployment environment.
7. First-party infographic `section_view`/`section_attention` events appear after real visits.

**Release honesty:** Source committed and SQL migration applied are confirmed. Passing CI, public runtime deployment and real-browser graphical QA are not confirmed. The deployment should be inspected before reporting the feature as visually production-verified.
