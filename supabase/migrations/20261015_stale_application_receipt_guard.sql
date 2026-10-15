-- Harden v1 against receipt and outbound-contact false positives.
-- Owner restricted, same output fields and review-ledger semantics.
CREATE OR REPLACE VIEW public.careersite_stale_application_pipeline_v1 WITH (security_invoker=true) AS
 WITH application_processes AS (
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
        ), process_signals AS (
         SELECT lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm,
            bool_or(COALESCE(r_1.is_negative_decision, false) OR COALESCE(r_1.is_closed_or_paused, false) OR COALESCE(r_1.status, ''::text) ~* 'reject|unsuccessful|not selected|position filled|withdrawn|cancelled|canceled|closed|not progressing'::text) AS has_terminal_signal,
            bool_or(
             NOT COALESCE(r_1.is_application, false)
             AND COALESCE(r_1.event_type, ''::text) !~* '(receipt|acknowledg|application.view|application.submitted)'::text
             AND (
               COALESCE(r_1.is_interview, false)
               OR ((COALESCE(r_1.is_recruiter_interaction,false)
                    OR COALESCE(r_1.response_received,false)
                    OR COALESCE(r_1.is_human_interaction,false))
                   AND COALESCE(r_1.interaction_direction, ''::text) IN ('inbound','two_way'))
               OR COALESCE(r_1.status, ''::text) ~*
                  'interview|recruiter.engaged|recruiter.response|references being|assessment completed|recruiter.qualified|hiring.manager|second interview|candidate response|employer update promised|manager review|recruiter.progress'::text
               OR COALESCE(r_1.event_type, ''::text) ~*
                  'interview|recruiter|assessment|candidate response|executive|hiring.manager'::text
             )
           ) AS has_recruiting_engagement
           FROM job_search_analytics r_1
          WHERE r_1.employer IS NOT NULL AND r_1.role IS NOT NULL
          GROUP BY (lower(regexp_replace(btrim(r_1.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(r_1.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), rejection_signals AS (
         SELECT lower(regexp_replace(btrim(job_rejection_analysis.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(job_rejection_analysis.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm
           FROM job_rejection_analysis
          GROUP BY (lower(regexp_replace(btrim(job_rejection_analysis.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(job_rejection_analysis.role), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), outcome_evidence AS (
         SELECT lower(regexp_replace(btrim(job_application_evidence.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS employer_norm,
            lower(regexp_replace(btrim(job_application_evidence.role_title), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)) AS role_norm
           FROM job_application_evidence
          WHERE job_application_evidence.evidence_kind = 'application_outcome'::text
          GROUP BY (lower(regexp_replace(btrim(job_application_evidence.employer), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text))), (lower(regexp_replace(btrim(job_application_evidence.role_title), '[^a-zA-Z0-9]+'::text, ''::text, 'g'::text)))
        ), identified AS (
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
     LEFT JOIN job_application_staleness_review r ON r.process_key = a.process_key;;
