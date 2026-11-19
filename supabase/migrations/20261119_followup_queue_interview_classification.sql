CREATE OR REPLACE VIEW public.careersite_followup_queue_v1 AS
 WITH latest_done AS (
         SELECT DISTINCT ON (careersite_recruiter_meetings.opportunity_id) careersite_recruiter_meetings.opportunity_id,
            careersite_recruiter_meetings.id AS meeting_id,
            careersite_recruiter_meetings.scheduled_date AS interview_date,
            careersite_recruiter_meetings.stage,
            careersite_recruiter_meetings.contact_name,
            careersite_recruiter_meetings.follow_up_status,
            careersite_recruiter_meetings.follow_up_sent_at
           FROM careersite_recruiter_meetings
          WHERE careersite_recruiter_meetings.opportunity_id IS NOT NULL AND careersite_recruiter_meetings.attendance = 'attended'::text AND careersite_recruiter_meetings.meeting_type IN ('interview', 'hiring_manager')
          ORDER BY careersite_recruiter_meetings.opportunity_id, careersite_recruiter_meetings.scheduled_date DESC, careersite_recruiter_meetings.stage DESC NULLS LAST, careersite_recruiter_meetings.id DESC
        ), next_meet AS (
         SELECT DISTINCT ON (careersite_recruiter_meetings.opportunity_id) careersite_recruiter_meetings.opportunity_id,
            careersite_recruiter_meetings.id AS next_meeting_id,
            careersite_recruiter_meetings.scheduled_date AS next_interview_date,
            careersite_recruiter_meetings.stage AS next_stage
           FROM careersite_recruiter_meetings
          WHERE careersite_recruiter_meetings.opportunity_id IS NOT NULL AND (careersite_recruiter_meetings.attendance <> ALL (ARRAY['cancelled'::text, 'no_show'::text, 'attended'::text])) AND careersite_recruiter_meetings.scheduled_date >= (now() AT TIME ZONE 'Europe/Stockholm'::text)::date
          ORDER BY careersite_recruiter_meetings.opportunity_id, careersite_recruiter_meetings.scheduled_date, careersite_recruiter_meetings.id
        ), market AS (
         SELECT job_market_analysis_snapshots.snapshot_date,
            job_market_analysis_snapshots.hiring_lag_pressure,
            job_market_analysis_snapshots.analysis_confidence
           FROM job_market_analysis_snapshots
          ORDER BY job_market_analysis_snapshots.snapshot_at DESC
         LIMIT 1
        ), base AS (
         SELECT o.id AS opportunity_id,
            o.process_key,
            o.forecast_process_key,
            o.employer,
            o.role_title,
            o.outcome,
            o.application_date,
            o.application_date_basis,
            d.meeting_id,
            d.interview_date,
            d.stage,
            d.follow_up_status AS interview_follow_up_status,
            n.next_meeting_id,
            n.next_interview_date,
            n.next_stage,
            f.recipient_name,
            f.recipient_email,
            f.recipient_role,
            f.email_source,
            f.expected_reply_by,
            f.expected_reply_evidence,
            f.last_employer_reply_at,
            f.last_candidate_message_at,
            f.last_followup_sent_at,
            f.followups_sent_count,
            f.last_message_evidence,
            f.source_checked_at,
            f.context_line,
            f.manual_hold_until,
            COALESCE(f.suppressed, false) AS suppressed,
            f.private_notes,
            f.updated_at,
            m.snapshot_date AS market_snapshot_date,
            m.hiring_lag_pressure,
            m.analysis_confidence,
                CASE
                    WHEN m.snapshot_date >= ((now() AT TIME ZONE 'Europe/Stockholm'::text)::date - 35) AND m.hiring_lag_pressure >= 0.70 THEN 1
                    ELSE 0
                END AS market_lag_days,
            (now() AT TIME ZONE 'Europe/Stockholm'::text)::date AS local_today
           FROM careersite_recruiting_opportunities o
             LEFT JOIN latest_done d ON d.opportunity_id = o.id
             LEFT JOIN next_meet n ON n.opportunity_id = o.id
             LEFT JOIN careersite_followup_actions f ON f.opportunity_id = o.id
             CROSS JOIN market m
        ), due AS (
         SELECT b.opportunity_id,
            b.process_key,
            b.forecast_process_key,
            b.employer,
            b.role_title,
            b.outcome,
            b.application_date,
            b.application_date_basis,
            b.meeting_id,
            b.interview_date,
            b.stage,
            b.interview_follow_up_status,
            b.next_meeting_id,
            b.next_interview_date,
            b.next_stage,
            b.recipient_name,
            b.recipient_email,
            b.recipient_role,
            b.email_source,
            b.expected_reply_by,
            b.expected_reply_evidence,
            b.last_employer_reply_at,
            b.last_candidate_message_at,
            b.last_followup_sent_at,
            b.followups_sent_count,
            b.last_message_evidence,
            b.source_checked_at,
            b.context_line,
            b.manual_hold_until,
            b.suppressed,
            b.private_notes,
            b.updated_at,
            b.market_snapshot_date,
            b.hiring_lag_pressure,
            b.analysis_confidence,
            b.market_lag_days,
            b.local_today,
                CASE
                    WHEN b.expected_reply_by IS NOT NULL THEN careersite_followup_workdays_after(b.expected_reply_by, 3)
                    WHEN b.interview_date IS NOT NULL THEN careersite_followup_workdays_after(b.interview_date,
                    CASE
                        WHEN COALESCE(b.stage::integer, 1) >= 2 THEN 5
                        ELSE 7
                    END + b.market_lag_days)
                    WHEN b.last_employer_reply_at IS NOT NULL THEN careersite_followup_workdays_after((b.last_employer_reply_at AT TIME ZONE 'Europe/Stockholm'::text)::date, 7 + b.market_lag_days)
                    WHEN b.application_date IS NOT NULL THEN careersite_followup_workdays_after(b.application_date, 10 + b.market_lag_days)
                    ELSE NULL::date
                END AS anchor_due,
            GREATEST(careersite_followup_workdays_after((b.last_candidate_message_at AT TIME ZONE 'Europe/Stockholm'::text)::date, 5), careersite_followup_workdays_after((b.last_followup_sent_at AT TIME ZONE 'Europe/Stockholm'::text)::date, 8), careersite_followup_workdays_after((b.last_employer_reply_at AT TIME ZONE 'Europe/Stockholm'::text)::date, 5)) AS communication_floor
           FROM base b
        ), scored AS (
         SELECT due.opportunity_id,
            due.process_key,
            due.forecast_process_key,
            due.employer,
            due.role_title,
            due.outcome,
            due.application_date,
            due.application_date_basis,
            due.meeting_id,
            due.interview_date,
            due.stage,
            due.interview_follow_up_status,
            due.next_meeting_id,
            due.next_interview_date,
            due.next_stage,
            due.recipient_name,
            due.recipient_email,
            due.recipient_role,
            due.email_source,
            due.expected_reply_by,
            due.expected_reply_evidence,
            due.last_employer_reply_at,
            due.last_candidate_message_at,
            due.last_followup_sent_at,
            due.followups_sent_count,
            due.last_message_evidence,
            due.source_checked_at,
            due.context_line,
            due.manual_hold_until,
            due.suppressed,
            due.private_notes,
            due.updated_at,
            due.market_snapshot_date,
            due.hiring_lag_pressure,
            due.analysis_confidence,
            due.market_lag_days,
            due.local_today,
            due.anchor_due,
            due.communication_floor,
                CASE
                    WHEN (lower(btrim(COALESCE(due.outcome, ''::text))) = ANY (ARRAY['rejected'::text, 'cancelled'::text, 'canceled'::text, 'withdrawn'::text])) OR due.next_interview_date IS NOT NULL THEN NULL::date
                    ELSE GREATEST(due.anchor_due, due.communication_floor, due.manual_hold_until)
                END AS due_date,
                CASE
                    WHEN lower(btrim(COALESCE(due.outcome, ''::text))) = ANY (ARRAY['rejected'::text, 'cancelled'::text, 'canceled'::text, 'withdrawn'::text, 'closed'::text, 'offer'::text, 'hired'::text, 'accepted'::text]) THEN 'hold'::text
                    WHEN due.suppressed THEN 'hold'::text
                    WHEN due.next_interview_date IS NOT NULL THEN 'wait'::text
                    WHEN (EXISTS ( SELECT 1
                       FROM careersite_recruiter_meetings pending
                      WHERE pending.opportunity_id = due.opportunity_id AND pending.attendance = 'unverified'::text AND pending.scheduled_date < due.local_today AND pending.scheduled_date >= COALESCE(due.interview_date, '1900-01-01'::date))) THEN 'hold'::text
                    WHEN due.recipient_email IS NULL OR due.recipient_email !~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'::text THEN 'hold'::text
                    WHEN due.followups_sent_count >= 2 AND (due.last_employer_reply_at IS NULL OR due.last_followup_sent_at >= due.last_employer_reply_at) THEN 'hold'::text
                    WHEN GREATEST(COALESCE(due.interview_date, due.application_date, '1900-01-01'::date), COALESCE((due.last_employer_reply_at AT TIME ZONE 'Europe/Stockholm'::text)::date, '1900-01-01'::date)) < (due.local_today - 45) THEN 'hold'::text
                    WHEN GREATEST(due.anchor_due, due.communication_floor, due.manual_hold_until) IS NULL THEN 'hold'::text
                    WHEN GREATEST(due.anchor_due, due.communication_floor, due.manual_hold_until) <= due.local_today THEN 'follow_up_now'::text
                    ELSE 'upcoming'::text
                END AS action,
                CASE
                    WHEN lower(btrim(COALESCE(due.outcome, ''::text))) = ANY (ARRAY['rejected'::text, 'cancelled'::text, 'canceled'::text, 'withdrawn'::text]) THEN 'Excluded final outcome'::text
                    WHEN lower(btrim(COALESCE(due.outcome, ''::text))) = ANY (ARRAY['closed'::text, 'offer'::text, 'hired'::text, 'accepted'::text]) THEN 'Terminal outcome; manual review only'::text
                    WHEN due.suppressed THEN 'Manually paused'::text
                    WHEN due.next_interview_date IS NOT NULL THEN 'Next interview confirmed; wait until afterwards'::text
                    WHEN (EXISTS ( SELECT 1
                       FROM careersite_recruiter_meetings pending
                      WHERE pending.opportunity_id = due.opportunity_id AND pending.attendance = 'unverified'::text AND pending.scheduled_date < due.local_today AND pending.scheduled_date >= COALESCE(due.interview_date, '1900-01-01'::date))) THEN 'Previous interview attendance needs verification'::text
                    WHEN due.recipient_email IS NULL THEN 'No verified contact; identify recruiter or application-status channel'::text
                    WHEN due.followups_sent_count >= 2 AND (due.last_employer_reply_at IS NULL OR due.last_followup_sent_at >= due.last_employer_reply_at) THEN 'Already followed up twice without a new reply'::text
                    WHEN GREATEST(COALESCE(due.interview_date, due.application_date, '1900-01-01'::date), COALESCE((due.last_employer_reply_at AT TIME ZONE 'Europe/Stockholm'::text)::date, '1900-01-01'::date)) < (due.local_today - 45) THEN 'Old process; verify it remains open'::text
                    WHEN due.anchor_due IS NULL THEN 'Missing dated application, interview or employer response; verify history'::text
                    WHEN due.expected_reply_by IS NOT NULL THEN 'Employer response window plus three Swedish business days'::text
                    WHEN due.interview_date IS NOT NULL THEN 'Interview-stage checkpoint, with market pacing'::text
                    WHEN due.last_employer_reply_at IS NOT NULL THEN 'Recruiter correspondence checkpoint'::text
                    ELSE 'Application-stage checkpoint; verified contact required before sending'::text
                END AS decision_reason
           FROM due
        )
 SELECT opportunity_id,
    process_key,
    forecast_process_key,
    employer,
    role_title,
    outcome,
    application_date,
    application_date_basis,
    meeting_id,
    interview_date,
    stage,
    interview_follow_up_status,
    next_meeting_id,
    next_interview_date,
    next_stage,
    recipient_name,
    recipient_email,
    recipient_role,
    email_source,
    expected_reply_by,
    expected_reply_evidence,
    last_employer_reply_at,
    last_candidate_message_at,
    last_followup_sent_at,
    followups_sent_count,
    last_message_evidence,
    source_checked_at,
    context_line,
    manual_hold_until,
    suppressed,
    private_notes,
    updated_at,
    market_snapshot_date,
    hiring_lag_pressure,
    analysis_confidence,
    market_lag_days,
    local_today,
    anchor_due,
    communication_floor,
    due_date,
    action,
    decision_reason,
        CASE
            WHEN action = 'follow_up_now'::text AND (source_checked_at IS NULL OR source_checked_at < (now() - '7 days'::interval)) THEN true
            ELSE false
        END AS verify_correspondence_first,
        CASE
            WHEN recipient_name IS NOT NULL AND btrim(recipient_name) <> ''::text THEN split_part(btrim(recipient_name), ' '::text, 1)
            ELSE 'there'::text
        END AS salutation,
    (('Follow-up: '::text || role_title) || ' at '::text) || employer AS email_subject,
    (((((('Hi '::text ||
        CASE
            WHEN recipient_name IS NOT NULL AND btrim(recipient_name) <> ''::text THEN split_part(btrim(recipient_name), ' '::text, 1)
            ELSE 'there'::text
        END) || ','::text) || '

'::text) ||
        CASE
            WHEN interview_date IS NOT NULL THEN ('I hope you are well. I wanted to check whether there is any update on the next steps for the '::text || role_title) || ' role.'::text
            ELSE ('I hope you are well. I wanted to ask if there is any update on the timeline for the '::text || role_title) || ' position.'::text
        END) ||
        CASE
            WHEN context_line IS NOT NULL AND btrim(context_line) <> ''::text THEN '

'::text || btrim(context_line)
            ELSE ''::text
        END) || '

I remain interested and would be happy to provide anything else you need.'::text) || '

Best,
Jair'::text AS email_body
   FROM scored;
;