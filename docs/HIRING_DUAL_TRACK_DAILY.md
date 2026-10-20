# Hiring forecast: autonomous calendar + external evidence (20 October 2026)

## Why

The previous owner-only stage model could use the current calendar day as the
origin for several hiring-stage durations. It risked maintaining the same
time-to-offer each day, despite no further employer evidence. Meanwhile external
factors and forecasts were usually archived only when Admin was opened.

## Two independent change tracks

**Calendar track — every 24 hours:** `pg_cron` runs
`private.careersite_run_hiring_daily_recheck()` at 06:00 UTC daily. The owner-only
on-page model now calls `public.careersite_hiring_prediction_v2()` which securely
delegates to a private milestone-anchored core. The target offer date is fixed
relative to the verified stage milestone or upcoming confirmed interview.
The remaining-days count decreases every day. After the original midpoint
passes without a verified offer, the estimated midpoint can move forward in
bounded **seven-day** steps. After the original latest milestone plus a
**14-day grace period**, the scenario expires and dates are withheld until new
recruitment evidence establishes a credible milestone. Silence is not a
rejection. This rule is a pragmatic planning heuristic, not a calibrated
time-to-offer distribution.

**Evidence track — every hour / on owner page open:** the same internal function
checks for changes in recorded recruitment processes and newly ingested
external market observations. The 15th minute of every hour is a source-change
check; it does **not** copy the previous record or create a new audit entry when
everything is identical. The Admin page also uses a JWT-protected recheck RPC
and refreshes the comparison while it is open. New external records can change
the source fingerprint, market interpretation and risk context, but **never**
apply an unvalidated probability coefficient or move personal offer dates
by themselves. New confirmed interview stages can shift the calendar anchor
and therefore the dated scenario.

## Database source of truth

- `private.careersite_hiring_core_v3()`: non-exposed owner model core. Reuses the
  established stage weights and owner pipeline evidence. Includes
  `timing_anchor`, `original_offer_central`, `calendar_shift_days`,
  `window_state`, `days_to_offer` within its existing v2 response.
- `public.careersite_hiring_prediction_v2()`: unchanged v2 response identifier,
  with explicit owner UID/email/JWT guard; no anon execution.
- `private.careersite_run_hiring_daily_recheck()`: internal, non-exposed scheduled
  read/compare/append function. It updates public date-only projection when the
  conditional scenario is valid; when lapsed, deletes that projection rather
  than leaving a dated forecast that is no longer defensible.
- `public.careersite_hiring_daily_recheck_v1()`: signed-in owner-only
  immediate check, no anonymous access.
- `public.careersite_hiring_daily_rechecks`: owner-only, immutable input-state
  snapshots. RLS allows signed-in owner SELECT only; inserts are made by the
  database scheduler, not anonymous clients or the browser. Unique by
  Stockholm date plus market/pipeline/timing evidence signatures. Saves both
  baseline and changed states without double-counting repeated identical
  refreshes.
- The `market-shadow-v2-role-mandates-context-only` version check is fixed
  in existing shadow history; all records remain non-scoring.

User-facing Admin > Analytics > Decision overview displays the countdown,
original versus reassessed date and the last daily/market/pipeline change
trigger, with an owner-only audit list. Swedish Job Market retains detailed
release-aware contextual interpretation.

## What is not claimed

This does **not** produce a valid 30/60/90-day personal offer probability,
increase confidence based on gross AI adoption, or infer guaranteed hiring
from employer attendance. The weekly overdue shift and 14-day expiry are
transparent conservative operational heuristics, not empirical quantiles.
The previous model version's historic days remain in the earlier archive;
do not overwrite or backdate observations.

## Verification

Manual SQL simulation with milestone 22 Oct 2026, offer centre 19 Nov 2026
and original latest 10 Dec 2026 confirms:

- 20 Oct: offer centre 19 Nov, **30 remaining days**.
- 21 Oct: offer centre 19 Nov, **29 remaining days**.
- 19 Nov: offer centre still 19 Nov, **0 remaining days**.
- 20 Nov: original central date has elapsed; conditional midpoint shifts
  to **26 Nov**, explicitly calendar-driven.
- 27 Nov: midpoint moves to **3 Dec** absent new evidence.
- 25 Dec: the original latest date + 14-day grace has elapsed; no date issued.

The first internal live calculation on 20 Oct returned the existing KPMG
interview anchor of **22 Oct**, indicative central offer **19 Nov** and
start **17 Dec**. A second same-day call created no duplicate snapshot.
The cron jobs were verified as active. Real future job executions should
be checked with `cron.job_run_details` once the scheduled hours occur.
