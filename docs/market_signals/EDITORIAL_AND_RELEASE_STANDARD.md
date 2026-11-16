# AI & Data Market Signals — Source, Interpretation and Release Standard
Version 1.0 · 16 November 2026 · Editorial owner: Jair Ribeiro

## Product boundary
Sweden-first AI/Data leadership and capability intelligence. This is neither a comprehensive job board nor an individual hiring forecast. The private career-intelligence database must never be exposed.

## Source-of-truth layers
1. Ingestion: existing monitored internal source registry and observations. A successful source check does not qualify evidence for public release.
2. Curated publication: public.portfolio_market_signal_points holds only approved observations, source lineages, vintages, populations, methods and limitations. public.portfolio_market_signal_briefs holds authored interpretations tied to exact point codes.
3. Member app: only fetches those two curated, RLS-protected publication tables through the current verified member JWT.

## Source validation, no exceptions
- Primary observation: confirm publisher, exact metric, denominator, geography, units, observation window, publication date and verification date.
- Derived observation: retain versioned algorithm and input API, reproduce results, document exclusions/deduplication and zero failed pages.
- Contextual observation: explicitly distinguish overall consulting/economic data from AI-specific evidence.
- Cross-source interpretations require at least two independent source families, but triangulation does not establish causality or replicate an identical measurement.
- Every decision brief requires a counterargument, limitations, source links and first actionable leadership step.
- Retain revisions and original vintage; no silent history overwrites. Never increase verified_on merely because a scheduler ran.

## Initial editorial edition
31 curated observations from 3 source families and 4 authored decision interpretations; not 31 mature historical series.
- SCB enterprise AI use and Data capability survey (2026). Subgroup denominators vary, particularly adoption barriers among AI non-adopters. Sector scope comparisons can break.
- Arbetsförmedlingen JobTech high-signal AI/Data leadership title-basket v1. Counts represent selective adverts, not total vacancies. Five complete months June-October; November 1-15 partial, excluded from monthly trend.
- Brainville Sweden consulting marketplace figures. NOT AI-specific consulting assignment counts.

## Distribution and reliability
- Public introduction: ?page=advisory-market-signals.
- Private workspace: ?page=advisory-access&view=market-signals.
- Reader Library provides contextual discovery without weakening Advisory account verification.
- Account, owner controls, service disable and role checks remain native to the existing portfolio.
- PostgreSQL RLS allows published evidence only for active verified Advisory members and only while enabled; verified admins retain test access when disabled. Anonymous users cannot SELECT.
- Reject bad URLs, missing dates, broken evidence codes or false independent-source labels. Fail closed rather than show a guessed number.
- Exports: source ledger CSV; source-linked topic-specific decision PDF; comprehensive market review with original vector charts, agenda and publisher appendix.

## Publication sequence
1. Verify upstream publication and stage a candidate observation with exact release provenance.
2. Review revision differences, source agreement/disagreement and comparable periods.
3. Approve source observations and authored interpretations as a single edition.
4. Run RLS, login, source integrity, PDF byte/page count, mobile charts and same-session route tests.
5. Keep the service disabled on any unresolved material regression. Enable using the existing owner service-visibility control only after production smoke checks.
6. Preserve last verified publication and clearly mark source review overdue if a future check fails. No zeros, projections or fabricated replacements.

## Editorial safeguards
Publisher datasets retain attribution and links. Recreate charts from permitted numeric observations; do not republish publisher figures/PDFs wholesale without license confirmation. Publish no private interviews, opportunity pipeline or individual offer probabilities.

## Release metrics
100% published source provenance coverage, zero broken evidence codes, zero false cross-source claims, zero incomplete months misrepresented as complete, and a valid three-or-more-page decision brief with source trace and explicit limitations.