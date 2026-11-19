CREATE OR REPLACE VIEW public.careersite_followup_engaged_v1 AS
 WITH human_evidence AS (
         SELECT concat_ws('|'::text, regexp_replace(lower(e.employer), '[^a-z0-9]'::text, ''::text, 'g'::text), regexp_replace(regexp_replace(lower(e.role), '^(position of |open position of |position |role: |as )'::text, ''::text), '[^a-z0-9]'::text, ''::text, 'g'::text)) AS evidence_identity_key,
            max(e.event_date) AS last_human_engagement_on,
            bool_or(e.is_interview IS TRUE AND (e.interaction_type = ANY (ARRAY['interview'::text, 'interview_completed'::text, 'interview_invitation'::text, 'interview_scheduled'::text, 'interview_reschedule'::text, 'hiring_manager_email'::text]))) AS human_interview_evidence,
            bool_or((e.interaction_direction = ANY (ARRAY['inbound'::text, 'two_way'::text])) AND ((e.interaction_type = ANY (ARRAY['recruiter_email'::text, 'recruiter_message'::text, 'recruiter_call'::text, 'reference_check'::text, 'hiring_manager_email'::text, 'executive_direct_message'::text, 'post_interview_response'::text])) OR e.interaction_type = 'follow_up'::text AND e.is_recruiter_interaction IS TRUE OR e.is_interview IS TRUE AND (e.interaction_type = ANY (ARRAY['interview'::text, 'interview_completed'::text, 'interview_invitation'::text, 'interview_scheduled'::text, 'interview_reschedule'::text])))) AS positive_reply_evidence,
            max(e.id) AS latest_analytics_evidence_id
           FROM job_search_analytics e
          WHERE e.event_date IS NOT NULL AND e.is_human_interaction IS TRUE AND lower(COALESCE(e.status, ''::text)) !~ '(reject|cancel|withdraw|closed|not selected|filled)'::text AND lower(COALESCE(e.stage_outcome, ''::text)) !~ '(reject|cancel|withdraw|not selected|filled)'::text AND (e.is_interview IS TRUE AND (e.interaction_type = ANY (ARRAY['interview'::text, 'interview_completed'::text, 'interview_invitation'::text, 'interview_scheduled'::text, 'interview_reschedule'::text, 'hiring_manager_email'::text])) OR (e.interaction_direction = ANY (ARRAY['inbound'::text, 'two_way'::text])) AND ((e.interaction_type = ANY (ARRAY['recruiter_email'::text, 'recruiter_message'::text, 'recruiter_call'::text, 'reference_check'::text, 'hiring_manager_email'::text, 'executive_direct_message'::text, 'post_interview_response'::text])) OR e.interaction_type = 'follow_up'::text AND e.is_recruiter_interaction IS TRUE) AND lower(concat_ws(' '::text, e.status, e.stage_outcome, e.interaction_notes, e.evidence_detail)) ~ '(interview|invitation|hiring.manager|client|reference|profile|shortlist|review|reschedul|re.surface|recruiter.engaged|next stage|process active|ongoing|qualified|follow.up|manager review|forward)'::text)
          GROUP BY (concat_ws('|'::text, regexp_replace(lower(e.employer), '[^a-z0-9]'::text, ''::text, 'g'::text), regexp_replace(regexp_replace(lower(e.role), '^(position of |open position of |position |role: |as )'::text, ''::text), '[^a-z0-9]'::text, ''::text, 'g'::text)))
        ), meetings AS (
         SELECT careersite_recruiter_meetings.opportunity_id,
            max(careersite_recruiter_meetings.scheduled_date) FILTER (WHERE careersite_recruiter_meetings.attendance = 'attended'::text) AS last_meeting_invitation_on,
            max(careersite_recruiter_meetings.scheduled_date) FILTER (WHERE careersite_recruiter_meetings.attendance = 'unverified'::text) AS unverified_invitation_on,
            bool_or(careersite_recruiter_meetings.attendance = 'attended'::text AND careersite_recruiter_meetings.meeting_type <> 'recruiter_screening'::text) AS attended_meeting,
            bool_or(careersite_recruiter_meetings.attendance = 'attended'::text AND careersite_recruiter_meetings.meeting_type = 'recruiter_screening'::text) AS attended_screening,
            bool_or(careersite_recruiter_meetings.attendance = 'unverified'::text) AS invitation_to_confirm
           FROM careersite_recruiter_meetings
          WHERE careersite_recruiter_meetings.opportunity_id IS NOT NULL AND (careersite_recruiter_meetings.meeting_type = ANY (ARRAY['interview'::text, 'recruiter_screening'::text, 'hiring_manager'::text])) AND (careersite_recruiter_meetings.attendance = ANY (ARRAY['attended'::text, 'unverified'::text]))
          GROUP BY careersite_recruiter_meetings.opportunity_id
        ), raw AS (
         SELECT c.source_type,
            c.source_ref,
            c.opportunity_id,
            c.employer,
            c.role_title,
            c.source_status,
            c.application_date,
            c.interview_date,
            c.next_interview_date,
            c.action,
            c.due_date,
            c.decision_reason,
            c.recipient_email,
            c.source_checked_at,
            c.evidence_sources,
            c.identity_key,
            c.contact_not_managed,
            m.last_meeting_invitation_on,
            m.unverified_invitation_on,
            m.attended_meeting,
            m.attended_screening,
            m.invitation_to_confirm,
            h.last_human_engagement_on,
            h.human_interview_evidence,
            h.positive_reply_evidence,
            h.latest_analytics_evidence_id,
            x.engagement_type AS curated_engagement_type,
            x.engagement_on AS curated_engagement_on,
            x.evidence_source AS curated_evidence_source,
            x.confidence AS curated_confidence,
            x.contact_name AS curated_contact_name
           FROM careersite_followup_application_coverage_v1 c
             LEFT JOIN meetings m ON c.opportunity_id = m.opportunity_id
             LEFT JOIN human_evidence h ON h.evidence_identity_key = c.identity_key
             LEFT JOIN careersite_followup_engagement_evidence x ON x.opportunity_id = c.opportunity_id
        )
 SELECT source_type,
    source_ref,
    opportunity_id,
    employer,
    role_title,
    source_status,
    application_date,
    interview_date,
    next_interview_date,
    action,
    due_date,
    decision_reason,
    recipient_email,
    source_checked_at,
    evidence_sources,
    identity_key,
    contact_not_managed,
        CASE
            WHEN attended_meeting IS TRUE THEN 'interview_completed'::text
            WHEN attended_screening IS TRUE THEN 'recruiter_screening_completed'::text
            WHEN curated_engagement_type IS NOT NULL THEN curated_engagement_type
            WHEN invitation_to_confirm IS TRUE THEN 'interview_invitation'::text
            WHEN human_interview_evidence IS TRUE THEN 'interview_event'::text
            WHEN positive_reply_evidence IS TRUE THEN 'positive_human_reply'::text
            ELSE NULL::text
        END AS engagement_basis,
    GREATEST(last_meeting_invitation_on, last_human_engagement_on, curated_engagement_on,
        CASE
            WHEN attended_meeting IS TRUE OR attended_screening IS TRUE THEN NULL::date
            ELSE unverified_invitation_on
        END) AS last_engagement_on,
        CASE
            WHEN curated_confidence = 'provisional'::text THEN 'provisional'::text
            WHEN curated_confidence = 'confirmed'::text THEN 'recorded'::text
            WHEN invitation_to_confirm IS TRUE AND attended_meeting IS NOT TRUE THEN 'invitation_only'::text
            ELSE 'recorded'::text
        END AS engagement_confidence,
    COALESCE(curated_evidence_source,
        CASE
            WHEN attended_meeting IS TRUE OR attended_screening IS TRUE OR invitation_to_confirm IS TRUE THEN 'Recruiter meeting evidence'::text
            WHEN human_interview_evidence IS TRUE OR positive_reply_evidence IS TRUE THEN 'Job Search Analytics human interaction '::text || latest_analytics_evidence_id::text
            ELSE NULL::text
        END) AS engagement_source
   FROM raw
  WHERE (attended_meeting IS TRUE OR attended_screening IS TRUE OR invitation_to_confirm IS TRUE OR curated_engagement_type IS NOT NULL OR human_interview_evidence IS TRUE OR positive_reply_evidence IS TRUE) AND NOT (source_type <> 'managed'::text AND lower(employer) = 'hcltech'::text AND lower(role_title) ~~ 'client delivery director%'::text) AND NOT (source_type <> 'managed'::text AND lower(employer) ~~ 'leovegas%'::text AND lower(role_title) ~~ 'ai strategy and transformation lead'::text AND source_type = 'jobwise'::text);
;