-- Preserve missing source dates while applying a fixed owner-requested 30-day analysis assumption.
-- Imputed dates must never qualify a process for verified-dormancy exclusion.
ALTER TABLE public.job_application_staleness_review
  ADD COLUMN IF NOT EXISTS analysis_assumed_applied_on date,
  ADD COLUMN IF NOT EXISTS analysis_assumption_anchor_date date,
  ADD COLUMN IF NOT EXISTS analysis_assumption_age_days integer;

DO $$
DECLARE v_candidates integer; v_written integer;
BEGIN
  SELECT count(*) INTO v_candidates FROM public.careersite_stale_application_pipeline_v1
  WHERE pipeline_segment='date_unverified' AND applied_on IS NULL;
  IF v_candidates <> 11 THEN
    RAISE EXCEPTION 'Expected exactly 11 date-unverified processes, found %',v_candidates;
  END IF;
  IF (now() AT TIME ZONE 'Europe/Stockholm')::date <> date '2026-10-15' THEN
    RAISE EXCEPTION 'Assumption anchor day is not current Stockholm day';
  END IF;

  INSERT INTO public.job_application_staleness_review
    (process_key,employer,role,applied_on,review_state,evidence_scope,verified_at,
     forecast_exclusion_verified,evidence_notes,evidence_refs,
     analysis_assumed_applied_on,analysis_assumption_anchor_date,analysis_assumption_age_days)
  SELECT process_key, employer,role,NULL::date,'date_unverified',
         'user_request_2026_10_15_fixed_30_day_analysis_assumption',NULL::timestamptz,
         false,
         'Analytical planning assumption: owner instructed the 11 undated processes to be treated as 30 days old on 15 Oct 2026. Actual submission date remains unknown; not proof of receipt or recruiter response.',
         jsonb_build_object('provenance','owner_explicit_request','verified_submission_date',false,'anchor_date','2026-10-15'),
         date '2026-09-15',date '2026-10-15',30
  FROM public.careersite_stale_application_pipeline_v1
  WHERE pipeline_segment='date_unverified' AND applied_on IS NULL
  ON CONFLICT (process_key) DO UPDATE SET
    analysis_assumed_applied_on=EXCLUDED.analysis_assumed_applied_on,
    analysis_assumption_anchor_date=EXCLUDED.analysis_assumption_anchor_date,
    analysis_assumption_age_days=EXCLUDED.analysis_assumption_age_days,
    evidence_scope=EXCLUDED.evidence_scope,
    evidence_notes=EXCLUDED.evidence_notes,
    evidence_refs=EXCLUDED.evidence_refs
  WHERE job_application_staleness_review.review_state='date_unverified'
    AND job_application_staleness_review.applied_on IS NULL
    AND job_application_staleness_review.forecast_exclusion_verified IS FALSE;

  GET DIAGNOSTICS v_written = ROW_COUNT;
  IF v_written <> 11 THEN
    RAISE EXCEPTION 'Expected exactly 11 safe assumption rows; wrote %',v_written;
  END IF;
END $$;