-- Read-only owner-safe candidate-matched vacancy continuity.
-- The same company/title can have multiple requisitions; this is external
-- market context, never proof that a specific application remains active.
CREATE OR REPLACE FUNCTION public.careersite_hiring_employer_activity_v1()
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=''
AS $$
DECLARE v_result jsonb;
BEGIN
  IF (SELECT auth.uid()) IS NULL
     OR lower(coalesce((SELECT auth.jwt())->>'email','')) <> 'jair.ribeiro@outlook.it'
     OR coalesce((SELECT auth.jwt())->>'is_anonymous','false') <> 'false'
  THEN RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501';
  END IF;
  WITH processes AS MATERIALIZED (
    SELECT DISTINCT lower(trim(employer)) employer_key,
           lower(trim(role)) role_key
    FROM public.job_search_analytics
    WHERE is_primary_analytics_record IS TRUE
      AND record_type IN ('evidence_event','history_event','activity_summary')
      AND event_date <= (now() AT TIME ZONE 'Europe/Stockholm')::date
      AND employer IS NOT NULL AND role IS NOT NULL
  ), listings AS (
    SELECT p.employer_key,p.role_key,
           v.vacancy_id, v.is_active, v.first_seen_at, v.last_seen_at,
           v.is_verified
    FROM processes p JOIN public.jobwise_vacancies v
      ON lower(trim(v.company_name))=p.employer_key
     AND lower(trim(v.title))=p.role_key
    WHERE v.is_verified IS TRUE
  ), grouped AS (
    SELECT employer_key,role_key, count(distinct vacancy_id) matched_vacancies,
           count(*) FILTER (WHERE is_active IS TRUE) advertised_active,
           max(last_seen_at) last_seen_at,
           min(first_seen_at) first_seen_at
    FROM listings GROUP BY employer_key,role_key
  )
  SELECT jsonb_build_object(
    'source','jobwise_verified_vacancy_catalog',
    'matching','company_and_title_only_not_unique_requisition',
    'verified_role_matches',count(*),
    'recently_seen_matches',count(*) FILTER (
      WHERE last_seen_at >= now()-interval '14 days'),
    'vacancies',coalesce(jsonb_agg(jsonb_build_object(
      'employer_key',employer_key,'role_key',role_key,
      'matched_vacancies',matched_vacancies,
      'advertised_active',advertised_active,
      'last_seen_at',last_seen_at,
      'first_seen_at',first_seen_at,
      'requisition_confirmed',false
    )),'[]'::jsonb)
  ) INTO v_result FROM grouped;
  RETURN v_result;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_hiring_employer_activity_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_employer_activity_v1() TO authenticated;
