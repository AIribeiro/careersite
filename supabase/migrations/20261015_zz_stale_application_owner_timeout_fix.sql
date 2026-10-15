-- Fix authenticated Stale applications timeout (57014 / HTTP 500).
-- Postgres's RLS-sensitive cardinality estimate previously re-executed evidence
-- aggregation hundreds of times. Materialize process/evidence grouping once in
-- v1, then reuse that single process set in v2's response aggregation.
-- The owner-only security-invoker views and their existing output columns, JWT/RLS
-- restrictions, verified dormancy gate, and public aggregated RPC stay unchanged.

CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v1
WITH (security_invoker=true) AS
WITH application_processes AS MATERIALIZED (
         SELECT (lower(btrim(r_1.employer)) || '|'::text) || lower(btrim(r_1.role)) AS process_key,
            lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm,
            min(r_1.employer) AS employer,
            min(r_1.role) AS role,
            min(r_1.event_date) AS applied_on,
            max(r_1.event_date) AS most_recent_application_event,
            count(*) AS primary_application_events
           FROM job_search_analytics r_1
          WHERE r_1.is_application IS TRUE AND r_1.employer IS NOT NULL AND btrim(r_1.employer) <> ''::text AND r_1.role IS NOT NULL AND btrim(r_1.role) <> ''::text AND (r_1.event_type <> ALL (ARRAY['application_evidenced_by_rejection'::text, 'duplicate_submission_evidence'::text]))
          GROUP BY ((lower(btrim(r_1.employer)) || '|'::text) || lower(btrim(r_1.role))), (lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), process_signals AS MATERIALIZED (
         SELECT lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm,
            bool_or(COALESCE(r_1.is_negative_decision, false) OR COALESCE(r_1.is_closed_or_paused, false) OR COALESCE(r_1.status, ''::text) ~* 'reject|unsuccessful|not selected|position filled|withdrawn|cancelled|canceled|closed|not progressing'::text) AS has_terminal_signal,
            bool_or(NOT COALESCE(r_1.is_application, false) AND COALESCE(r_1.event_type, ''::text) !~* '(receipt|acknowledg|application.view|application.submitted)'::text AND (COALESCE(r_1.is_interview, false) OR (COALESCE(r_1.is_recruiter_interaction, false) OR COALESCE(r_1.response_received, false) OR COALESCE(r_1.is_human_interaction, false)) AND (COALESCE(r_1.interaction_direction, ''::text) = ANY (ARRAY['inbound'::text, 'two_way'::text])) OR COALESCE(r_1.status, ''::text) ~* 'interview|recruiter.engaged|recruiter.response|references being|assessment completed|recruiter.qualified|hiring.manager|second interview|candidate response|employer update promised|manager review|recruiter.progress'::text OR COALESCE(r_1.event_type, ''::text) ~* 'interview|recruiter|assessment|candidate response|executive|hiring.manager'::text)) AS has_recruiting_engagement
           FROM job_search_analytics r_1
          WHERE r_1.employer IS NOT NULL AND r_1.role IS NOT NULL
          GROUP BY (lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), rejection_signals AS MATERIALIZED (
         SELECT lower(regexp_replace(btrim(job_rejection_analysis.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(job_rejection_analysis.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm
           FROM job_rejection_analysis
          GROUP BY (lower(regexp_replace(btrim(job_rejection_analysis.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(job_rejection_analysis.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), outcome_evidence AS MATERIALIZED (
         SELECT lower(regexp_replace(btrim(job_application_evidence.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(job_application_evidence.role_title), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm
           FROM job_application_evidence
          WHERE job_application_evidence.evidence_kind = 'application_outcome'::text
          GROUP BY (lower(regexp_replace(btrim(job_application_evidence.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(job_application_evidence.role_title), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), identified AS MATERIALIZED (
         SELECT a_1.process_key,
            a_1.employer_norm,
            a_1.role_norm,
            a_1.employer,
            a_1.role,
            a_1.applied_on,
            a_1.most_recent_application_event,
            a_1.primary_application_events,
            COALESCE(s.has_terminal_signal, false) OR j.employer_norm IS NOT NULL OR m.employer_norm IS NOT NULL AS terminal_recorded,
            COALESCE(s.has_recruiting_engagement, false) AS engagement_recorded,
            (EXISTS ( SELECT 1
                   FROM application_processes another
                  WHERE another.employer_norm = a_1.employer_norm AND another.applied_on = a_1.applied_on AND another.role_norm <> a_1.role_norm AND a_1.role ~* 'role not surfaced'::text AND another.role !~* 'role not surfaced'::text)) AS placeholder_alias
           FROM application_processes a_1
             LEFT JOIN process_signals s USING (employer_norm, role_norm)
             LEFT JOIN rejection_signals j USING (employer_norm, role_norm)
             LEFT JOIN outcome_evidence m USING (employer_norm, role_norm)
        )
 SELECT a.process_key,
    a.employer,
    a.role,
    a.applied_on,
        CASE
            WHEN a.applied_on IS NULL THEN NULL::integer
            ELSE (now() AT TIME ZONE 'Europe/Stockholm'::text)::date - a.applied_on
        END AS days_since_application,
    a.primary_application_events,
    a.terminal_recorded,
    a.engagement_recorded,
    a.placeholder_alias,
        CASE
            WHEN r.review_state = ANY (ARRAY['closed_verified'::text, 'engaged_verified'::text, 'dormant_verified'::text]) THEN r.review_state
            WHEN a.placeholder_alias THEN 'identity_alias_not_distinct'::text
            WHEN a.terminal_recorded THEN 'closed_recorded'::text
            WHEN a.engagement_recorded THEN 'recruitment_response_recorded'::text
            WHEN a.applied_on IS NULL THEN 'date_unverified'::text
            WHEN ((now() AT TIME ZONE 'Europe/Stockholm'::text)::date - a.applied_on) >= 45 THEN 'stale_45_plus_unverified'::text
            WHEN ((now() AT TIME ZONE 'Europe/Stockholm'::text)::date - a.applied_on) >= 21 THEN 'stale_21_plus_unverified'::text
            ELSE 'recent_awaiting_response'::text
        END AS pipeline_segment,
        CASE
            WHEN NOT a.terminal_recorded AND NOT a.engagement_recorded AND NOT a.placeholder_alias AND a.applied_on IS NOT NULL AND ((now() AT TIME ZONE 'Europe/Stockholm'::text)::date - a.applied_on) >= 21 THEN true
            ELSE false
        END AS is_stale_candidate,
    r.forecast_exclusion_verified IS TRUE AND r.verified_at IS NOT NULL AND r.applied_on IS NOT NULL AND ((now() AT TIME ZONE 'Europe/Stockholm'::text)::date - r.applied_on) >= 45 AND (r.review_state = 'closed_verified'::text OR r.review_state = 'dormant_verified'::text AND r.verified_at >= (now() - '30 days'::interval) AND NOT a.engagement_recorded AND NOT a.terminal_recorded) AS exclude_from_active_forecast,
    r.evidence_scope,
    r.verified_at,
    r.evidence_notes,
    r.evidence_refs
   FROM identified a
     LEFT JOIN job_application_staleness_review r ON r.process_key = a.process_key;
REVOKE ALL ON public.careersite_stale_application_pipeline_v1 FROM PUBLIC, anon;
GRANT SELECT ON public.careersite_stale_application_pipeline_v1 TO authenticated, service_role;

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
     LEFT JOIN meaningful m USING (process_key);
REVOKE ALL ON public.careersite_stale_application_pipeline_v2 FROM PUBLIC, anon;
GRANT SELECT ON public.careersite_stale_application_pipeline_v2 TO authenticated, service_role;
