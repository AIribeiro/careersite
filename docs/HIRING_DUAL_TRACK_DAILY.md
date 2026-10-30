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

**Evidence track — every 24 hours, in the same batch:** the daily run reads
the recorded recruitment pipeline **and** all registered market-factor rows
at 06:00 UTC. Market releases arriving between runs are included in the next
daily batch. This is a fixed UTC 24-hour cadence, corresponding to 07:00 or
08:00 in Stockholm depending on daylight saving. The previous 15-minutes-
past-each-hour cron job has been unscheduled and will not be recreated by
the corrective migration. The market sources' own ingestion schedules are
not modified by this hiring-forecast cadence change.

**No automatic recalculation from the website:** Decision overview and
Swedish Job Market consume the most recent owner-only daily archive. UI
fragments refresh no more than once every 24 hours while the page stays
open. Opening a page simply reads the existing snapshot; it cannot
trigger a new forecast calculation, public projection update or historic
shadow write. Only the database scheduler produces the next forecast state.

**Anti-loop guard:** the private scheduled function takes a transaction-scoped
advisory lock; if another caller is running, it returns `already_running`.
Before running any expensive model or market scans, it checks for an
existing snapshot for the current Stockholm calendar day. If one exists,
it returns `already_checked_today` without computing or writing. The
owner-facing recheck RPC no longer grants execute permission to
authenticated users. Historical uniqueness and append-only RLS remain.
A failed scheduled run does not invent a no-change observation; the UI
instead labels the most recent verified snapshot as stale.

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
- `public.careersite_hiring_daily_recheck_v1()`: legacy owner recheck endpoint;
  browser EXECUTE permission revoked to enforce scheduler-only calculations.
- `public.careersite_hiring_daily_rechecks`: owner-only, immutable input-state
  snapshots. RLS allows signed-in owner SELECT only; inserts are made by the
  database scheduler, not anonymous clients or the browser. Unique by
  Stockholm date plus market/pipeline/timing evidence signatures. In normal
  operation, precisely one evaluated state per Stockholm calendar day.
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
The single daily job remains active; the former hourly job was removed.
Future executions can be reviewed with `cron.job_run_details` after scheduled runs.

## 30 October 2026 — evidence reconciliation: final interview and rejected process

The source-of-truth hierarchy is **confirmed employer outcome and attended-meeting ledger**,
then **recruiter-confirmed next-stage signal**, then historical forecast snapshots.
Snapshots are dated observations, not a reason to reactivate a process after rejection.

- **LeoVegas / AI Strategy and Transformation Lead:** recruiter explicitly confirmed the
  **final culture-fit interview** for 9 November 2026, 14:00–15:00 CET, with Giulio Calleja.
  Two meetings are confirmed attended (2 October recruiter; 28 October CAIO).
  The third is scheduled, not attended. Its employer-confirmed MTO is 3 total /
  1 remaining, with no offer or offer probability inferred.
- **Betsson Group / Head of SB Product – Data & AI:** rejected by recruiter email
  on 30 October 2026 after hiring-manager consideration. The 23 October recruiter
  screening was attended; the 20 October meeting was cancelled/rescheduled and
  does not increase completed-meeting metrics. Closed roles retain interview and
  rejection history, but must not appear in live MTO or active pipeline.
  Betsson's separate Head of Artificial Intelligence application remains unresolved.
- **Conversion view:** `public.careersite_job_conversion_process_v1` computes
  `exclude_from_active_forecast` from the underlying stale-pipeline flag **or**
  a terminal-recorded state, verified offer, or linked negative employer decision.
  This was applied to the live database on 30 October 2026 using
  `CREATE OR REPLACE VIEW ... WITH (security_invoker = true)` without changing
  existing table rows, view columns or role grants. Verification found
  0 employer-rejection rows still incorrectly marked forecast-eligible, versus
  77 immediately before the correction.
- **Event-level report:** the LeoVegas 30 October event explicitly records
  `Final culture fit interview` and `stage_state=scheduled`,
  `attended=false`. The generic historical analytics recognizes verified
  recruiter/employer booked stages separately from completed interviews and
  counts an explicitly held recruiter screening as completed.

The historical forecasts in `careersite_hiring_daily_rechecks` are never
rewritten to retroactively make previous assessments look prescient. Renderers
must intersect them with current recruiting-opportunity outcomes. Interview
assessments can remain visible when their process is closed, labelled as
historical/closed rather than an active-forecast contribution.

Regression query:

```sql
SELECT count(*) AS incorrectly_active_rejections
FROM public.careersite_job_conversion_process_v1
WHERE outcome_class = 'employer_rejection'
  AND NOT exclude_from_active_forecast;
```

Expected result: **0**.
