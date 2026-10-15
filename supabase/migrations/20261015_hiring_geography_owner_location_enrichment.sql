-- Private enrichment of job-search geo evidence from the user's own linked
-- Jobwise workspace. Read-only; no historical job evidence is changed.
CREATE OR REPLACE FUNCTION public.careersite_hiring_geography_evidence_v1()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    result jsonb;
BEGIN
    IF auth.uid() IS NULL
       OR pg_catalog.lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
       OR coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
    THEN
        RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501';
    END IF;

    WITH owned_workspaces AS MATERIALIZED (
        SELECT DISTINCT NULLIF(trim(raw_data->>'jobwise_workspace_id'),'') AS workspace_id
        FROM public.job_search_analytics
        WHERE source_file = 'Jobwise user-recorded applications reconciliation 2026-10-13'
          AND raw_data ? 'jobwise_workspace_id'
          AND is_primary_analytics_record IS TRUE
    ),
    relevant_processes AS MATERIALIZED (
        SELECT DISTINCT lower(trim(employer)) AS employer_key,
                        lower(trim(role)) AS role_key
        FROM public.job_search_analytics
        WHERE record_type IN ('evidence_event','history_event','activity_summary')
          AND is_primary_analytics_record IS TRUE
          AND employer IS NOT NULL AND role IS NOT NULL
          AND event_date <= (now() AT TIME ZONE 'Europe/Stockholm')::date
    ),
    matched AS (
        SELECT p.employer_key, p.role_key,
               NULLIF(trim(a.payload->>'location'),'') AS location,
               NULLIF(trim(a.payload->>'country'),'') AS country
        FROM public.jobwise_applications a
        INNER JOIN owned_workspaces ow ON ow.workspace_id = a.workspace_id
        INNER JOIN relevant_processes p
          ON lower(trim(a.payload->>'company')) = p.employer_key
         AND lower(trim(a.payload->>'title')) = p.role_key
        WHERE nullif(trim(a.payload->>'location'),'') IS NOT NULL
    ),
    unique_processes AS (
        SELECT employer_key,role_key,
               count(distinct lower(trim(location))) AS location_variants,
               count(distinct lower(trim(coalesce(country,'')))) AS country_variants,
               max(location) AS location,
               max(country) AS country
        FROM matched
        GROUP BY employer_key,role_key
    )
    SELECT jsonb_build_object(
        'method','linked_user_workspace_exact_company_title',
        'unique_locations',
        coalesce(jsonb_agg(jsonb_build_object(
            'employer_key',employer_key,
            'role_key',role_key,
            'advertised_location',location,
            'country',country,
            'evidence_source','jobwise_application_metadata',
            'quality','exact_company_role_unique_location'
        )) FILTER (WHERE location_variants=1 AND country_variants <= 1),'[]'::jsonb),
        'conflicting_processes',
        count(*) FILTER (WHERE location_variants>1 OR country_variants>1)
    ) INTO result
    FROM unique_processes;
    RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_hiring_geography_evidence_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_geography_evidence_v1() TO authenticated;
