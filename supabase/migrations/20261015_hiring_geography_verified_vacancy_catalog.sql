-- Owner-only location enrichment, with two ranked, source-backed
-- fallbacks. Jobwise applications are scoped to workspaces explicitly linked
-- to this owner's job-search evidence. Vacancy catalog matches require a
-- verified advertisement and unique company/title/location attribution.
CREATE OR REPLACE FUNCTION public.careersite_hiring_geography_evidence_v1()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE result jsonb;
BEGIN
    IF auth.uid() IS NULL
       OR lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
       OR coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
    THEN
        RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501';
    END IF;

    WITH owner_workspaces AS MATERIALIZED (
        SELECT DISTINCT NULLIF(trim(raw_data->>'jobwise_workspace_id'),'') workspace_id
        FROM public.job_search_analytics
        WHERE source_file = 'Jobwise user-recorded applications reconciliation 2026-10-13'
          AND is_primary_analytics_record IS TRUE
          AND raw_data ? 'jobwise_workspace_id'
    ),
    processes AS MATERIALIZED (
        SELECT DISTINCT lower(trim(employer)) employer_key,
                        lower(trim(role)) role_key
        FROM public.job_search_analytics
        WHERE record_type IN ('evidence_event','history_event','activity_summary')
          AND is_primary_analytics_record IS TRUE
          AND event_date <= (now() AT TIME ZONE 'Europe/Stockholm')::date
          AND employer IS NOT NULL AND role IS NOT NULL
    ),
    owner_app_sources AS (
        SELECT p.employer_key,p.role_key,
               NULLIF(trim(a.payload->>'location'),'') loc,
               NULLIF(trim(a.payload->>'country'),'') country
        FROM processes p
        JOIN public.jobwise_applications a
          ON lower(trim(a.payload->>'company'))=p.employer_key
         AND lower(trim(a.payload->>'title'))=p.role_key
        JOIN owner_workspaces w ON w.workspace_id=a.workspace_id
        WHERE NULLIF(trim(a.payload->>'location'),'') IS NOT NULL
    ),
    app_unique AS (
        SELECT employer_key,role_key, max(loc) location,max(country) country,
               count(distinct lower(trim(loc))) variants,
               count(distinct lower(trim(coalesce(country,'')))) country_variants
        FROM owner_app_sources
        GROUP BY 1,2
    ),
    catalog_sources AS (
        SELECT p.employer_key,p.role_key,
               NULLIF(trim(v.location_text),'') loc,
               NULLIF(trim(v.country_name),'') country
        FROM processes p
        JOIN public.jobwise_vacancies v
          ON lower(trim(v.company_name))=p.employer_key
         AND lower(trim(v.title))=p.role_key
        WHERE v.is_verified IS TRUE
          AND NULLIF(trim(v.location_text),'') IS NOT NULL
          AND v.first_seen_at <= now()
    ),
    catalog_unique AS (
        SELECT employer_key,role_key,max(loc) location,max(country) country,
               count(distinct lower(trim(loc))) variants,
               count(distinct lower(trim(coalesce(country,'')))) country_variants
        FROM catalog_sources GROUP BY 1,2
    ),
    candidates AS (
        SELECT employer_key,role_key,location,country,
               'jobwise_application_metadata'::text source,2 priority
        FROM app_unique WHERE variants=1 AND country_variants<=1
        UNION ALL
        SELECT employer_key,role_key,location,country,
               'verified_jobwise_vacancy_catalog'::text source,1 priority
        FROM catalog_unique WHERE variants=1 AND country_variants<=1
    ),
    chosen AS (
        SELECT DISTINCT ON (employer_key,role_key)
               employer_key,role_key,location,country,source
        FROM candidates
        ORDER BY employer_key,role_key,priority DESC
    )
    SELECT jsonb_build_object(
        'method','owner_workspace_and_verified_catalog_unique_company_title',
        'unique_locations',coalesce(jsonb_agg(jsonb_build_object(
            'employer_key', employer_key,
            'role_key', role_key,
            'advertised_location', location,
            'country',country,
            'evidence_source',source,
            'quality','exact_company_role_unique_location'
        )),'[]'::jsonb),
        'matched_count',count(*)
    ) INTO result FROM chosen;
    RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_hiring_geography_evidence_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_geography_evidence_v1() TO authenticated;
