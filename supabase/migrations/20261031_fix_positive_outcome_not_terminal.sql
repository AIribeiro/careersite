-- Fix false terminal classification in the recruiting pipeline.
--
-- application_outcome is an evidence category, not a terminal decision.
-- A positive progression email (e.g. advanced_to_second_interview) must never
-- close an active opportunity. Preserve legacy evidence with missing outcome
-- metadata; explicit outcomes must be terminal to count as closure.
--
-- The existing v1 view is modified in place to retain the complete projection,
-- dependent views, existing grants and owner-facing analytics contracts.
-- Idempotent because the database fix was applied to production on 2026-10-31.

DO $repair$
DECLARE
  existing_definition text;
  old_predicate constant text := 'WHERE job_application_evidence.evidence_kind = ''application_outcome''::text';
  corrected_predicate constant text := 'WHERE job_application_evidence.evidence_kind = ''application_outcome''::text AND (NULLIF(btrim(lower(job_application_evidence.metadata ->> ''outcome''::text)), '''') IS NULL OR lower(btrim(job_application_evidence.metadata ->> ''outcome''::text)) = ANY (ARRAY[''rejected''::text, ''not_selected''::text, ''position_filled''::text, ''role_cancelled''::text, ''position_cancelled''::text, ''withdrawn''::text, ''cancelled''::text, ''canceled''::text, ''closed''::text, ''declined''::text, ''unsuccessful''::text]))';
BEGIN
  existing_definition := pg_get_viewdef('public.careersite_stale_application_pipeline_v1'::regclass, true);
  IF position('NULLIF(btrim(lower(job_application_evidence.metadata' IN existing_definition) > 0 THEN
    RAISE NOTICE 'Positive-outcome closure guard already installed';
  ELSE
    IF position(old_predicate IN existing_definition) = 0 THEN
      RAISE EXCEPTION 'Unexpected view definition for careersite_stale_application_pipeline_v1';
    END IF;
    EXECUTE 'CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v1 AS ' ||
      replace(existing_definition, old_predicate, corrected_predicate);
  END IF;
END
$repair$;
