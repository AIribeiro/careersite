-- Correct overlapping expiry backlog and count missing dates across closed cases too.
CREATE OR REPLACE FUNCTION public.careersite_public_pipeline_health_v1()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=''
AS $f$
WITH p AS MATERIALIZED (
 SELECT * FROM public.careersite_stale_application_pipeline_v2 WHERE health_segment <> 'identity_alias'
), counts AS (
 SELECT health_segment AS segment,count(*)::int AS n FROM p GROUP BY health_segment
), metric AS (
 SELECT count(*)::int total_processes,
 count(*) FILTER(WHERE health_segment IN ('recent_awaiting_response','stale_21_44','stale_45_59','stale_60_plus','verified_dormant'))::int unanswered,
 count(*) FILTER(WHERE health_segment IN ('stale_21_44','stale_45_59','stale_60_plus','verified_dormant'))::int stale,
 count(*) FILTER(WHERE health_segment='stale_60_plus')::int long_silent_unverified,
 count(*) FILTER(WHERE health_segment='verified_dormant')::int verified_dormant,
 count(*) FILTER(WHERE health_segment IN ('stale_21_44','stale_45_59','stale_60_plus'))::int verification_backlog,
 count(*) FILTER(WHERE applied_on IS NULL)::int undated,
 count(*) FILTER(WHERE health_segment='date_unverified')::int undated_unresolved,
 count(*) FILTER(WHERE health_segment='recruiter_engaged')::int engaged,
 count(*) FILTER(WHERE health_segment='closed')::int closed,
 count(*) FILTER(WHERE exclude_from_active_forecast AND health_segment='verified_dormant')::int active_forecast_dormant_exclusions,
 count(*) FILTER(WHERE applied_on IS NOT NULL AND days_since_application>=21)::int matured_denominator,
 count(*) FILTER(WHERE applied_on IS NOT NULL AND days_since_application>=21 AND health_segment IN ('stale_21_44','stale_45_59','stale_60_plus','verified_dormant'))::int matured_unanswered,
 count(*) FILTER(WHERE applied_on IS NOT NULL AND first_response_on IS NOT NULL)::int dated_first_responses
 FROM p
), cohort AS (
 SELECT to_char(applied_on,'YYYY-MM') AS cohort_month,count(*)::int applications,
 count(*) FILTER(WHERE health_segment='recruiter_engaged' OR first_response_on IS NOT NULL)::int responded,
 count(*) FILTER(WHERE health_segment IN ('recent_awaiting_response','stale_21_44','stale_45_59','stale_60_plus','verified_dormant'))::int unanswered,
 count(*) FILTER(WHERE health_segment='verified_dormant')::int dormant,
 count(*) FILTER(WHERE health_segment='closed')::int closed,
 (max(applied_on) <= ((now() at time zone 'Europe/Stockholm')::date - 21)) matured_21d
 FROM p WHERE applied_on IS NOT NULL GROUP BY to_char(applied_on,'YYYY-MM')
), latency AS (
 SELECT percentile_cont(.5) WITHIN GROUP (ORDER BY first_response_on-applied_on) median_days,
 count(*)::int eligible FROM p WHERE applied_on IS NOT NULL AND first_response_on IS NOT NULL
)
SELECT jsonb_build_object(
 'as_of',(now() at time zone 'Europe/Stockholm')::date,
 'counting_unit','employer-role process; distinct requisitions require reconciliation',
 'metrics',(SELECT to_jsonb(metric) FROM metric),
 'status',(SELECT coalesce(jsonb_agg(to_jsonb(counts) ORDER BY segment),'[]'::jsonb) FROM counts),
 'cohorts',(SELECT coalesce(jsonb_agg(to_jsonb(cohort) ORDER BY cohort_month),'[]'::jsonb) FROM cohort),
 'first_response',(SELECT to_jsonb(latency) FROM latency),
 'review_validity_days',30,'dormancy_threshold_days',45);
$f$;
REVOKE ALL ON FUNCTION public.careersite_public_pipeline_health_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_public_pipeline_health_v1() TO anon,authenticated,service_role;