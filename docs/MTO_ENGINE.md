# Meetings-to-offer (MTO) engine

This is an **evidence-informed planning estimate**, not an empirical hiring benchmark, probability of offer, or statement that the employer has selected the candidate.

## Source of truth

- Pure estimator: `src/meeting_to_offer.py` (`estimate_mto`)
- Portfolio comparison: `src/hiring_opportunity_comparison.py`
- Private evidence loader and forecast UI: `src/page_hiring_prediction_v2.py`
- Supabase: `public.careersite_recruiting_opportunities` and `public.careersite_recruiter_meetings`; exact `opportunity_id` and `forecast_process_key` associations prevent mixing vacancies from the same employer.

## Decision rules

1. Initial role-based prior if no employer-confirmed role-specific hiring sequence exists: contracts 2–3, experienced hires 2–4, manager/lead 3–4, director/head 3–5, C-level/executive 4–6 candidate meetings. These are **configurable heuristics, not observed industry averages**.
2. Distinct, documented **attended** interview meetings count once each, including recruiter screenings; panel members in one calendar meeting count as one meeting. Do not count scheduled, cancelled, unverified, networking, tests, follow-ups or recruiter emails.
3. Evaluate decision authority before the raw round number: recruiter → hiring manager → stakeholder/panel → executive sponsor → accountable functional owner → explicitly verified final decision-maker. Job title alone does not establish final sign-off. When authority is unknown, retain a broad range.
4. An employer-confirmed requisition-specific total or remaining plan overrides heuristic ranges only when `mto_source_type='employer_confirmed'`. General published recruiting guidance is **not** a requisition-specific schedule. Record the underlying source in `mto_source_note` and its date before marking a plan confirmed.
5. A *confirmed upcoming* interview is uncompleted, but requires a nonzero remaining lower bound. Do not extrapolate planned dates from the MTO count.
6. The model never silently exceeds a verified completed count; unexpected additional completed stages extend the planning range.
7. Unknown meeting ledger must remain **unknown**, not "0 held". Do not silently reconcile inconsistent stage status and attendance count. The interface discloses evidence level, range and reason.

## Reusability

**No employer or person is hardcoded into the estimator.** Any newly tracked vacancy with a `forecast_process_key` automatically uses the role baseline; as meetings and attendee roles are recorded for that vacancy the estimate recalculates at read time. Employer plans are optional; historical examples are evidence records, not algorithmic exemptions. 

MTO is conditional on a still-live hiring process reaching an offer decision; it is **not** the chance of receiving an offer. A `0–1 remaining` range may mean the employer will decide without further interviews, including a rejection. No numerical model-confidence percentages are shown; confidence labels indicate evidence specificity only, not statistical calibration.

## Validation and future calibration

Targeted regression: `python -m unittest tests/test_meeting_to_offer.py tests/test_hiring_opportunity_comparison.py -v`. GitHub workflow `.github/workflows/mto-tests.yml` checks the estimator and UI separately from legacy site tests.

Future calibration requires a cohort of **closed, verified recruiting processes** with consistent interview counts, requisition seniority, final-decision authority and interview-to-offer outcomes. Validate ranges on hold-out data, track coverage and interval error, and only then replace heuristics with empirical priors. Do not present the historical sample of current job applications as sufficiently representative for calibrated market statistics.
