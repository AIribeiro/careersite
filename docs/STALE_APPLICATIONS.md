# Stale Applications — Evidence Policy and UI

Baseline: 15 October 2026. Source of truth: Supabase project
`rnqweoxtynelfirffmlr`. Scope: owner Admin, public Analytics and private forecast.

## Counting and treatment

Applications are never rejected because of age or silence. Application
acknowledgements and viewed/submitted notifications are not substantive
recruiting contact. Waiting 0–20 days is recent; 21–44 days needs follow-up
review; 45–59 days is elevated; 60+ days is long-silent. Verified dormant
is a separate, reversible evidence decision. Once a recruiter responds or
the review expires, the process must be reassessed. Past application events
are retained for historical conversion denominators.

Database sources:
- `job_search_analytics`: original event and dated application records.
- `job_application_evidence`: provider evidence and application identity clues.
- `job_rejection_analysis`: recorded outcomes; never silence.
- `job_application_staleness_review`: verification ledger and expiry evidence.
- `careersite_stale_application_pipeline_v1`: original protected ageing view.
- `careersite_stale_application_pipeline_v2`: protected mutually exclusive status,
  first/last qualifying response, next-step and review-expiry indicators.
- `careersite_public_pipeline_health_v1()`: anonymous, aggregate-only
  dated cohorts, rates, status counts, response latency, and data quality.
- `careersite_public_hiring_inputs_v1()`: original aggregate forecast
  inputs; already zeroes stages for valid verified dormancy.

Private predictor version `hiring-beta-4.2-verified-dormancy` now reads the
current v2 view. A valid verified dormant process has **zero** active
stage weight. Unverified stale applications retain their existing 1.0
active / 0.35 fallback stage weight. Other known hiring pauses can still
change weight based on explicit evidence. Age never produces arbitrary
numeric discounts. If the private dormancy view cannot be loaded, the
owner forecast is withheld rather than silently restoring stale entries.

## Website

- Public Analytics Overview: compact Pipeline Health interpretive section.
- Public Analytics > Job Search > Pipeline Health: ageing distribution,
  monthly cohort outcomes, follow-up backlog and first-response latency.
- Owner Admin > Stale applications: private verification queue and evidence
  scope. No Admin page action claims to have verified email on its own.
- Owner Admin > Detailed job analytics > Stale applications: equivalent
  private inspection within the wider application evidence view.
- Owner decision overview: private Pipeline Health and dormancy-aware
  hiring prediction; status sources refresh with the owner session.

Public dashboards never receive employer names, job titles or mailbox
metadata from the private review view. The anonymized RPC exposes only
cohort and aggregate counts. See existing RLS for source ownership.

## Quality, cohorts, and limitations

Each reporting row is a **canonical employer–role process**, excluding
placeholder aliases. This is *not necessarily a unique requisition*. A
verified requisition/platform ID should take precedence once individual
mapping is reconciled; no distinct job IDs are merged or split without
proof. Application event counts, unique employer-role process counts,
and fully verified requisition counts must not be presented as equal.

Response-time statistics require a dated application and substantive
subsequent evidence. Unanswered cases are right-censored. Cohort
response shares only display for 21-day mature month cohorts; closed
cases can also have received a response. A separate missing-date
metric includes closed/engaged processes that cannot enter age analysis.

As of 15 October 2026, 295 process rows (excluding four aliases), 195
unanswered, 158 stale, 157 pending evidence checks, one verified dormant,
31 missing application dates across all statuses, and 11 currently classified
as date-unverified. There are distinct platform-ID collisions requiring
reconciliation, so these are provisional process totals, not a final
unique-requisition census.

### Explicit 30-day assumption · 15 October 2026

The owner directed that the **11 date-unverified, unanswered processes**
be shown as 30 days old on 15 October. The fixed analytical proxy date is
**15 September 2026**, not a rolling 30-day reset. This assumption is stored
in `job_application_staleness_review.analysis_assumed_applied_on`, with
`analysis_assumption_anchor_date=2026-10-15` and age=30 days.
`job_search_analytics.event_date` and the original verified application
date remain unchanged (unknown), so there is no fabricated historical event.

The owner-private `careersite_stale_application_pipeline_v2` uses the
assumed date for ageing and review, emits `date_assumed=true`, and
preserves `original_applied_on=NULL`. The 11 processes move from
`date_unverified` to `stale_21_44`; they remain **unverified** and do
not qualify for evidence-backed dormant status. The review queue labels
the assumed date and prioritizes source-date reconciliation.

Both public and owner-only forecasts include these 11 as **provisional
application-stage inputs at the existing unresolved fallback weight 0.35**.
They do not count as an observed dated submission for historical
application totals, recruiter conversion, first-response latency,
or observed monthly cohorts. A later verified date or actual
progression supersedes the assumption automatically.

A separate 20 processes remain without an ageable date because they have
already recorded closed or recruiter-engaged status. The original source
still has 31 missing submission dates altogether.

Remaining work: full mailbox/source verification of the backlog, canonical
requisition-ID reconstruction, historical calibration of channel- and
role-specific first-response curves, and empirical forecasting of personal
offer probabilities. Do not label these as completed.

## Validation

Postgres view and RPC counts were checked against the 15 October snapshot.
Anonymous users cannot select from the owner-only v2 view. The public RPC
is read-only and returns no process identities. Streamlit CI runs compile,
smoke and regression checks on each commit.

Receipt-only application notifications are explicitly excluded from
substantive employer engagement. The 15 October receipt guard corrected one
previously misclassified process; the final baseline has seven engaged
employer–role processes and 33 applications in the 21–44-day stale band.
