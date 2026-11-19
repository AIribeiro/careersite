-- Owner-only snapshot for the live job-status panel.
-- Exploratory executive contacts are not job applications or interviews.
CREATE OR REPLACE FUNCTION public.careersite_owner_current_hiring_pipeline_v1()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO ''
AS $$
BEGIN
    IF auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
       OR pg_catalog.lower(coalesce(auth.jwt()->>'email', '')) <> 'jair.ribeiro@outlook.it'
       OR coalesce(auth.jwt()->>'is_anonymous', 'false') <> 'false'
    THEN
        RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE = '42501';
    END IF;

    RETURN pg_catalog.jsonb_build_object(
        'opportunities', COALESCE((
            SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o))
            FROM (
                SELECT id, employer, role_title, application_date, outcome, updated_at
                FROM public.careersite_recruiting_opportunities
                ORDER BY updated_at DESC, id DESC
                LIMIT 150
            ) o
        ), '[]'::jsonb),
        'priorities', COALESCE((
            SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r))
            FROM (
                SELECT opportunity_id, rank_position, reviewed_on, priority_band,
                       priority_score, pipeline_state, next_action, evidence_note
                FROM public.careersite_application_priority_reviews
                ORDER BY reviewed_on DESC, rank_position ASC NULLS LAST
                LIMIT 200
            ) r
        ), '[]'::jsonb),
        'statuses', COALESCE((
            SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s))
            FROM (
                SELECT source_type, source_ref, status, status_on, status_note
                FROM public.careersite_followup_process_status
                WHERE source_type = 'managed'
                LIMIT 150
            ) s
        ), '[]'::jsonb),
        'strategic', COALESCE((
            SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(t))
            FROM (
                SELECT id, employer, priority, access_status, activity_status,
                       hiring_signal, contact_name, next_action, updated_at
                FROM public.job_search_employer_opportunity_map
                WHERE access_status = 'direct_executive_conversation'
                  AND hiring_signal = 'exploratory_executive_interest_no_open_role'
                ORDER BY updated_at DESC
                LIMIT 100
            ) t
        ), '[]'::jsonb)
    );
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_owner_current_hiring_pipeline_v1() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.careersite_owner_current_hiring_pipeline_v1() TO authenticated;
