-- Career dashboard freshness: keep source checks distinct from employer evidence.
CREATE TABLE IF NOT EXISTS public.careersite_hiring_source_sync_runs (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 checked_at timestamptz NOT NULL DEFAULT pg_catalog.now(),
 source_name text NOT NULL CHECK (source_name IN ('gmail','outlook','calendar','supabase_reconciliation')),
 check_status text NOT NULL CHECK (check_status IN ('checked','partial','failed')),
 items_checked integer NOT NULL DEFAULT 0 CHECK (items_checked >= 0),
 events_added integer NOT NULL DEFAULT 0 CHECK (events_added >= 0),
 records_changed integer NOT NULL DEFAULT 0 CHECK (records_changed >= 0),
 run_key text UNIQUE,
 note text
);
ALTER TABLE public.careersite_hiring_source_sync_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.careersite_hiring_source_sync_runs FROM anon, authenticated;
GRANT SELECT ON public.careersite_hiring_source_sync_runs TO authenticated;
DROP POLICY IF EXISTS "owner reads source-sync metadata" ON public.careersite_hiring_source_sync_runs;
CREATE POLICY "owner reads source-sync metadata"
 ON public.careersite_hiring_source_sync_runs FOR SELECT TO authenticated
 USING (
   (SELECT auth.uid()) = '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
   AND pg_catalog.lower(coalesce((SELECT auth.jwt())->>'email','')) = 'jair.ribeiro@outlook.it'
   AND coalesce((SELECT auth.jwt())->>'is_anonymous','false') = 'false'
 );

CREATE OR REPLACE FUNCTION public.careersite_owner_current_hiring_pipeline_v1()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO ''
AS $$
BEGIN
 IF auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
 OR pg_catalog.lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
 OR coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
 THEN
    RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501';
 END IF;

 RETURN pg_catalog.jsonb_build_object(
  'generated_at', pg_catalog.now(),
  'source_watermarks', pg_catalog.jsonb_build_object(
    'opportunities', (SELECT max(updated_at) FROM public.careersite_recruiting_opportunities),
    'priorities', (SELECT max(reviewed_at) FROM public.careersite_application_priority_reviews),
    'statuses', (SELECT max(updated_at) FROM public.careersite_followup_process_status),
    'strategic', (SELECT max(updated_at) FROM public.job_search_employer_opportunity_map)
  ),
  'opportunities', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o)) FROM (
    SELECT id,employer,role_title,application_date,outcome,updated_at
    FROM public.careersite_recruiting_opportunities
    ORDER BY updated_at DESC,id DESC LIMIT 150
   ) o
  ),'[]'::jsonb),
  'priorities', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)) FROM (
    SELECT opportunity_id,rank_position,reviewed_on,reviewed_at,priority_band,
           priority_score,pipeline_state,next_action,evidence_note
    FROM public.careersite_application_priority_reviews
    ORDER BY reviewed_at DESC,rank_position ASC NULLS LAST LIMIT 200
   ) r
  ),'[]'::jsonb),
  'statuses', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s)) FROM (
    SELECT source_type,source_ref,status,status_on,status_note,updated_at
    FROM public.careersite_followup_process_status
    WHERE source_type='managed'
    ORDER BY updated_at DESC LIMIT 150
   ) s
  ),'[]'::jsonb),
  'strategic', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(t)) FROM (
    SELECT id,employer,priority,access_status,activity_status,
           hiring_signal,contact_name,next_action,updated_at
    FROM public.job_search_employer_opportunity_map
    WHERE access_status='direct_executive_conversation'
      AND hiring_signal='exploratory_executive_interest_no_open_role'
    ORDER BY updated_at DESC LIMIT 100
   ) t
  ),'[]'::jsonb),
  'unreviewed_active', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(u)) FROM (
    SELECT o.id,o.employer,o.role_title,o.application_date,o.updated_at
    FROM public.careersite_recruiting_opportunities o
    WHERE o.outcome='in_progress'
      AND o.updated_at >= pg_catalog.now() - interval '45 days'
      AND NOT EXISTS (
       SELECT 1 FROM public.careersite_application_priority_reviews p
       WHERE p.opportunity_id=o.id
      )
      AND NOT EXISTS (
       SELECT 1 FROM public.careersite_followup_process_status s
       WHERE s.source_type='managed' AND s.source_ref=o.id::text
         AND s.status IN ('rejected','ignored','withdrawn','closed')
      )
    ORDER BY o.updated_at DESC LIMIT 30
   ) u
  ),'[]'::jsonb),
  'sync_runs', COALESCE((
   SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(a)) FROM (
    SELECT DISTINCT ON (source_name) source_name,check_status,checked_at,
           items_checked,events_added,records_changed
    FROM public.careersite_hiring_source_sync_runs
    ORDER BY source_name,checked_at DESC,id DESC
   ) a
  ),'[]'::jsonb)
 );
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_owner_current_hiring_pipeline_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_owner_current_hiring_pipeline_v1() TO authenticated;
