-- Render 11 explicitly imputed dates as 30-day-old for ageing, never as verified submissions.
-- The original missing date remains intact in v1 and the evidence history.
CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v2
WITH (security_invoker=true)
AS
WITH pipeline AS MATERIALIZED (
 SELECT v.*, 
        CASE WHEN v.pipeline_segment='date_unverified'
                  AND v.applied_on IS NULL AND r.applied_on IS NULL
                  AND r.review_state='date_unverified'
                  AND r.forecast_exclusion_verified IS NOT TRUE
             THEN r.analysis_assumed_applied_on
        END AS analysis_date,
        r.analysis_assumption_anchor_date AS analysis_anchor
 FROM public.careersite_stale_application_pipeline_v1 v
 LEFT JOIN public.job_application_staleness_review r ON r.process_key=v.process_key
),
meaningful AS MATERIALIZED (
 SELECT p.process_key,
        min(j.event_date) first_response_on,
        max(j.event_date) last_response_on
 FROM pipeline p
 JOIN public.job_search_analytics j ON
    lower(btrim(j.employer))||'|'||lower(btrim(j.role))=p.process_key
 WHERE j.event_date >= p.applied_on
   AND coalesce(j.is_application,false) = false
   AND (
      coalesce(j.is_interview,false) OR coalesce(j.is_negative_decision,false)
      OR ((coalesce(j.is_human_interaction,false) OR coalesce(j.is_recruiter_interaction,false))
           AND lower(coalesce(j.interaction_direction,'')) IN ('inbound','two_way'))
   )
   AND lower(coalesce(j.event_type,'')) !~ 'application.(receipt|acknowledg|submi|view)|auto.acknowledg'
 GROUP BY p.process_key
)
SELECT
 p.process_key,
 p.employer,
 p.role,
 coalesce(p.applied_on,p.analysis_date) AS applied_on,
 coalesce(p.days_since_application,
          ((now() AT TIME ZONE 'Europe/Stockholm')::date - p.analysis_date)) AS days_since_application,
 p.primary_application_events,
 p.terminal_recorded,
 p.engagement_recorded,
 p.placeholder_alias,
 CASE WHEN p.analysis_date IS NOT NULL THEN 'stale_21_plus_unverified' ELSE p.pipeline_segment END AS pipeline_segment,
 (p.is_stale_candidate OR p.analysis_date IS NOT NULL) AS is_stale_candidate,
 p.exclude_from_active_forecast,
 p.evidence_scope,
 p.verified_at,
 p.evidence_notes,
 p.evidence_refs,
 m.first_response_on,
 m.last_response_on,
 CASE
  WHEN p.placeholder_alias THEN 'identity_alias'
  WHEN p.terminal_recorded OR p.pipeline_segment='closed_verified' THEN 'closed'
  WHEN p.engagement_recorded OR p.pipeline_segment='engaged_verified' THEN 'recruiter_engaged'
  WHEN coalesce(p.applied_on,p.analysis_date) IS NULL OR
       coalesce(p.days_since_application,
               ((now() AT TIME ZONE 'Europe/Stockholm')::date - p.analysis_date)) < 0
     THEN 'date_unverified'
  WHEN p.pipeline_segment='dormant_verified' AND p.exclude_from_active_forecast THEN 'verified_dormant'
  WHEN coalesce(p.days_since_application,
               ((now() AT TIME ZONE 'Europe/Stockholm')::date - p.analysis_date))>=60 THEN 'stale_60_plus'
  WHEN coalesce(p.days_since_application,
               ((now() AT TIME ZONE 'Europe/Stockholm')::date - p.analysis_date))>=45 THEN 'stale_45_59'
  WHEN coalesce(p.days_since_application,
               ((now() AT TIME ZONE 'Europe/Stockholm')::date - p.analysis_date))>=21 THEN 'stale_21_44'
  ELSE 'recent_awaiting_response'
 END AS health_segment,
 CASE
   WHEN p.analysis_date IS NOT NULL THEN 'assumed'
   WHEN p.exclude_from_active_forecast AND p.pipeline_segment='dormant_verified' THEN 'confirmed'
   WHEN p.pipeline_segment IN ('engaged_verified','closed_verified') THEN 'confirmed'
   WHEN p.evidence_scope IS NOT NULL AND p.verified_at IS NOT NULL THEN 'partial'
   ELSE 'unverified'
 END AS evidence_quality,
 CASE
   WHEN p.placeholder_alias THEN 'no_action'
   WHEN p.terminal_recorded OR p.engagement_recorded OR p.exclude_from_active_forecast THEN 'monitor'
   WHEN p.analysis_date IS NOT NULL THEN 'reconcile_date'
   WHEN p.applied_on IS NULL THEN 'reconcile_date'
   WHEN p.days_since_application>=45 THEN 'verify_evidence'
   WHEN p.days_since_application>=21 THEN 'review_follow_up'
   ELSE 'monitor'
 END AS next_step,
 p.pipeline_segment='dormant_verified' AND NOT p.exclude_from_active_forecast AS review_expired_or_overridden,
 p.applied_on AS original_applied_on,
 (p.analysis_date IS NOT NULL) AS date_assumed,
 p.analysis_anchor AS date_assumption_anchor_date,
 CASE WHEN p.analysis_date IS NOT NULL THEN 'owner_assumed_30d_not_verified'
      WHEN p.applied_on IS NOT NULL THEN 'historical_application_evidence'
      ELSE 'missing_original_date' END AS date_provenance
FROM pipeline p LEFT JOIN meaningful m USING (process_key);
REVOKE ALL ON public.careersite_stale_application_pipeline_v2 FROM PUBLIC,anon;
GRANT SELECT ON public.careersite_stale_application_pipeline_v2 TO authenticated,service_role;