-- Restore reliable, owner-restricted Stale applications tab loads.
-- The previous v2 view inlined v1 twice, causing PostgREST's authenticated
-- execution plan to exceed the 8s statement timeout (SQLSTATE 57014).
-- Materializing the v1 process rows once prevents duplicate expansion while
-- preserving the exact classification, RLS and forecast semantics.
-- As deployed and verified on 15 October 2026.
CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v2
WITH (security_invoker=true) AS
WITH pipeline AS MATERIALIZED (
         SELECT careersite_stale_application_pipeline_v1.process_key,
            careersite_stale_application_pipeline_v1.employer,
            careersite_stale_application_pipeline_v1.role,
            careersite_stale_application_pipeline_v1.applied_on,
            careersite_stale_application_pipeline_v1.days_since_application,
            careersite_stale_application_pipeline_v1.primary_application_events,
            careersite_stale_application_pipeline_v1.terminal_recorded,
            careersite_stale_application_pipeline_v1.engagement_recorded,
            careersite_stale_application_pipeline_v1.placeholder_alias,
            careersite_stale_application_pipeline_v1.pipeline_segment,
            careersite_stale_application_pipeline_v1.is_stale_candidate,
            careersite_stale_application_pipeline_v1.exclude_from_active_forecast,
            careersite_stale_application_pipeline_v1.evidence_scope,
            careersite_stale_application_pipeline_v1.verified_at,
            careersite_stale_application_pipeline_v1.evidence_notes,
            careersite_stale_application_pipeline_v1.evidence_refs
           FROM careersite_stale_application_pipeline_v1
        ), meaningful AS MATERIALIZED (
         SELECT p_1.process_key,
            min(j.event_date) AS first_response_on,
            max(j.event_date) AS last_response_on
           FROM pipeline p_1
             JOIN job_search_analytics j ON ((lower(btrim(j.employer)) || '|'::text) || lower(btrim(j.role))) = p_1.process_key
          WHERE j.event_date >= p_1.applied_on AND COALESCE(j.is_application, false) = false AND (COALESCE(j.is_interview, false) OR COALESCE(j.is_negative_decision, false) OR (COALESCE(j.is_human_interaction, false) OR COALESCE(j.is_recruiter_interaction, false)) AND (lower(COALESCE(j.interaction_direction, ''::text)) = ANY (ARRAY['inbound'::text, 'two_way'::text]))) AND lower(COALESCE(j.event_type, ''::text)) !~ 'application.(receipt|acknowledg|submi|view)|auto.acknowledg'::text
          GROUP BY p_1.process_key
        )
 SELECT p.process_key,
    p.employer,
    p.role,
    p.applied_on,
    p.days_since_application,
    p.primary_application_events,
    p.terminal_recorded,
    p.engagement_recorded,
    p.placeholder_alias,
    p.pipeline_segment,
    p.is_stale_candidate,
    p.exclude_from_active_forecast,
    p.evidence_scope,
    p.verified_at,
    p.evidence_notes,
    p.evidence_refs,
    m.first_response_on,
    m.last_response_on,
        CASE
            WHEN p.placeholder_alias THEN 'identity_alias'::text
            WHEN p.terminal_recorded OR p.pipeline_segment = 'closed_verified'::text THEN 'closed'::text
            WHEN p.engagement_recorded OR p.pipeline_segment = 'engaged_verified'::text THEN 'recruiter_engaged'::text
            WHEN p.applied_on IS NULL OR p.days_since_application < 0 THEN 'date_unverified'::text
            WHEN p.pipeline_segment = 'dormant_verified'::text AND p.exclude_from_active_forecast THEN 'verified_dormant'::text
            WHEN p.days_since_application >= 60 THEN 'stale_60_plus'::text
            WHEN p.days_since_application >= 45 THEN 'stale_45_59'::text
            WHEN p.days_since_application >= 21 THEN 'stale_21_44'::text
            ELSE 'recent_awaiting_response'::text
        END AS health_segment,
        CASE
            WHEN p.exclude_from_active_forecast AND p.pipeline_segment = 'dormant_verified'::text THEN 'confirmed'::text
            WHEN p.pipeline_segment = ANY (ARRAY['engaged_verified'::text, 'closed_verified'::text]) THEN 'confirmed'::text
            WHEN p.evidence_scope IS NOT NULL AND p.verified_at IS NOT NULL THEN 'partial'::text
            ELSE 'unverified'::text
        END AS evidence_quality,
        CASE
            WHEN p.placeholder_alias THEN 'no_action'::text
            WHEN p.terminal_recorded OR p.engagement_recorded OR p.exclude_from_active_forecast THEN 'monitor'::text
            WHEN p.applied_on IS NULL THEN 'reconcile_date'::text
            WHEN p.days_since_application >= 45 THEN 'verify_evidence'::text
            WHEN p.days_since_application >= 21 THEN 'review_follow_up'::text
            ELSE 'monitor'::text
        END AS next_step,
    p.pipeline_segment = 'dormant_verified'::text AND NOT p.exclude_from_active_forecast AS review_expired_or_overridden
   FROM pipeline p
     LEFT JOIN meaningful m USING (process_key);;
REVOKE ALL ON public.careersite_stale_application_pipeline_v2 FROM PUBLIC, anon;
GRANT SELECT ON public.careersite_stale_application_pipeline_v2 TO authenticated, service_role;
