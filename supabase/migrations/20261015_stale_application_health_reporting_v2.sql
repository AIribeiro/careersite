-- Evidence-backed ageing with owner-only identities, plus anonymous aggregates.
CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v2
WITH (security_invoker=true) AS
WITH meaningful AS (
 SELECT p.process_key,min(j.event_date) first_response_on,max(j.event_date) last_response_on
 FROM public.careersite_stale_application_pipeline_v1 p
 JOIN public.job_search_analytics j
 ON lower(btrim(j.employer))||'|'||lower(btrim(j.role))=p.process_key
 WHERE j.event_date>=p.applied_on AND coalesce(j.is_application,false)=false
 AND (coalesce(j.is_interview,false) OR coalesce(j.is_negative_decision,false)
      OR ((coalesce(j.is_human_interaction,false) OR coalesce(j.is_recruiter_interaction,false))
      AND lower(coalesce(j.interaction_direction,'')) IN ('inbound','two_way')))
 AND lower(coalesce(j.event_type,'')) !~ 'application.(receipt|acknowledg|submi|view)|auto.acknowledg'
 GROUP BY p.process_key
)
SELECT p.*,m.first_response_on,m.last_response_on,
 CASE
 WHEN p.placeholder_alias THEN 'identity_alias'
 WHEN p.terminal_recorded OR p.pipeline_segment='closed_verified' THEN 'closed'
 WHEN p.engagement_recorded OR p.pipeline_segment='engaged_verified' THEN 'recruiter_engaged'
 WHEN p.applied_on IS NULL OR p.days_since_application<0 THEN 'date_unverified'
 WHEN p.pipeline_segment='dormant_verified' AND p.exclude_from_active_forecast THEN 'verified_dormant'
 WHEN p.days_since_application>=60 THEN 'stale_60_plus'
 WHEN p.days_since_application>=45 THEN 'stale_45_59'
 WHEN p.days_since_application>=21 THEN 'stale_21_44'
 ELSE 'recent_awaiting_response' END health_segment,
 CASE WHEN p.exclude_from_active_forecast AND p.pipeline_segment='dormant_verified' THEN 'confirmed'
 WHEN p.pipeline_segment IN ('engaged_verified','closed_verified') THEN 'confirmed'
 WHEN p.evidence_scope IS NOT NULL AND p.verified_at IS NOT NULL THEN 'partial'
 ELSE 'unverified' END evidence_quality,
 CASE WHEN p.placeholder_alias THEN 'no_action'
 WHEN p.terminal_recorded OR p.engagement_recorded OR p.exclude_from_active_forecast THEN 'monitor'
 WHEN p.applied_on IS NULL THEN 'reconcile_date'
 WHEN p.days_since_application>=45 THEN 'verify_evidence'
 WHEN p.days_since_application>=21 THEN 'review_follow_up'
 ELSE 'monitor' END next_step,
 (p.pipeline_segment='dormant_verified' AND NOT p.exclude_from_active_forecast) review_expired_or_overridden
FROM public.careersite_stale_application_pipeline_v1 p LEFT JOIN meaningful m USING(process_key);
REVOKE ALL ON public.careersite_stale_application_pipeline_v2 FROM PUBLIC,anon;
GRANT SELECT ON public.careersite_stale_application_pipeline_v2 TO authenticated,service_role;

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
 count(*) FILTER(WHERE health_segment IN ('stale_21_44','stale_45_59','stale_60_plus') OR review_expired_or_overridden)::int verification_backlog,
 count(*) FILTER(WHERE health_segment='date_unverified')::int undated,
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