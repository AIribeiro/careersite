# AI & Data Market Signals — Owner Operations Runbook

## Entry point
Open the private owner workspace: Advisory Operations → Service management → Market Signals management.
Seven workspaces: Executive overview, Source assurance, Evidence catalogue, Executive interpretations, Editorial editions, Audience & downloads, Editorial audit.

## Source governance
- The source register initially contains only the three curated AI/Data source families: SCB enterprise AI adoption, JobTech v1 AI/Data leadership demand, and Brainville consulting context. The wider internal 28-source job-market registry is not public data.
- The Upstream check, upstream success and observed period describe data ingestion, not editorial sign-off.
- Every source starts `needs_review`. Open the original publisher and verify measured values, denominator, geography, licensing, methodology, revision history, publication date and source URL.
- Record an explicit verification reason (minimum 12 characters), check the confirmation and mark `approved` only after actual review. Use `blocked` when the source is unreliable or publication rights are unclear.
- An upstream refresh does not automatically change editorial review state or a member-facing figure.

## Evidence and corrections
- Evidence points have unique immutable codes, a series key, full dates, a complete/incomplete period flag, population, source URL, evidence grade, method and limitations.
- Create unpublished points as drafts; amend draft fields freely with recorded reason. Published observations cannot be overwritten. For revised figures, create a new unique code; publish it only after a source check.
- Withdrawal is logged and will be refused when an approved interpretation or released edition still depends on the observation. Withdraw dependencies in the proper order.
- A partially observed month must not be plotted as a complete month. The original JobTech title basket v1 must retain its classifier, exclusions and deduplication definition.

## Executive interpretations
- Every analysis has a thesis, interpretation, decision question, practical first step, counterevidence, limitations, evidence-code manifest and support level.
- `independent_sources` requires two different publisher families; it does not prove that two independent publishers measured the same fact.
- Approve from draft only after inspecting every citation and confirming that all cited evidence is published and its sources approved.
- No editing of published analyses. Create a new slug/version and withdraw an old edition or interpretation through the audited workflow.

## Edition release
1. In Source assurance, approve each included source after manual publisher verification.
2. In Evidence catalogue, publish reviewed draft observations. Confirm verified date and original publication.
3. In Executive interpretations, publish reviewed and source-linked analyses.
4. In Editorial editions, create a draft with selected published observations and analyses. An edition is a versioned manifest, not a silent overwrite.
5. Run the preflight gate. It rejects stale verification, blocked/unreviewed publishers, missing/duplicate references, unsupported analysis, unpublished content or fewer than two independent source families.
6. Verify source links, download byte integrity, report page layout, mobile view and member access before ticking the publication checklist.
7. Publish the edition with a specific editorial rationale. The member dashboard and downloads then read the published edition manifest. A successor release requires withdrawal of the previous edition; the audit survives.

## Public visibility
The owner-managed `market-signals` service toggle controls public discovery independently of editions. Do not confuse an enabled service with an editorially approved release. With no published edition, the member experience is labelled a pre-release exploratory preview.
Do not change the public toggle merely to update datasets. Treat an error or absent evidence as a blocking condition and preserve known-good history.

## Audience and privacy
- The member app records whitelisted opens, lens selections, analysis selections, CSV exports and two types of PDF downloads through an authenticated backend function.
- Only owner users can read event logs; activity contains no executive questionnaire text, private career forecast, individual applications or document content.
- Reporting shows distinct active users and volume in the last 30 days. Before instrumentation launched, events were not collected; empty event tables do not imply zero historical readership.

## Audit and recovery
- All owner source, evidence, analysis and edition mutations require an explanation, are enforced by password-backed verified ownership, and are checked by a fresh database read after saving.
- Audit entries include previous and new structured records, actor and timestamp. No edit/delete interface exists for the audit.
- For a source discrepancy, mark the source blocked, investigate the publisher, prepare a corrected evidence code and revised interpretation; do not revise published values in place.
- If the full Market Signals CI fails or public mobile/auth tests do not pass, do not claim production readiness. The global Streamlit CI has some separate legacy test failures and should be interpreted by failed-test names rather than pass/fail alone.

## Security controls
Source controls, edition records, audit and member usage are owner-only RLS tables. Normal authenticated users cannot read these management records or directly insert/update/delete them. Owner actions use scoped, auditable RPCs and confirm the authenticated owner's email plus an active password-backed admin session.