-- Include only owner-assumed, ageable undated applications as provisional 0.35 stages.
-- No synthetic event rows or fabricated historical response-rate denominators.
CREATE OR REPLACE FUNCTION public.careersite_public_hiring_inputs_v1()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  v_today date := (pg_catalog.now() at time zone 'Europe/Stockholm')::date;
  v_result jsonb;
BEGIN
  WITH evidence AS MATERIALIZED (
    SELECT
      pg_catalog.lower(pg_catalog.btrim(coalesce(r.employer,''))) || '|' ||
      pg_catalog.lower(pg_catalog.btrim(coalesce(r.role,''))) AS process_key,
      r.event_date d,
      coalesce(r.snapshot_date,r.event_date) state_at,
      r.id,
      coalesce(r.is_application,false) applied,
      coalesce(r.is_human_interaction,false) AND
        pg_catalog.lower(coalesce(r.interaction_direction,'')) IN ('inbound','two_way') contacted,
      coalesce(r.is_interview,false) AND (
        pg_catalog.lower(coalesce(r.event_type,''))='interview_completed'
        OR pg_catalog.lower(coalesce(r.activity,'')) ~ '(held|completed|conducted)'
        OR pg_catalog.lower(coalesce(r.stage_outcome,'')) ~ '(held|completed|conducted)'
      ) interviewed,
      pg_catalog.lower(coalesce(r.stage_outcome,'')) ~
        '(next.stage|second.interview|final.interview|reference.check|offer)' OR
      pg_catalog.lower(coalesce(r.event_type,'')) ~
        '(next.stage|second.interview|final.interview|reference.check|offer)' progressed,
      pg_catalog.lower(coalesce(r.event_type,'')) ~ '(offer_received|offer_accepted)' OR
        pg_catalog.lower(coalesce(r.stage_outcome,'')) ~ '(offer_received|offer_accepted)' offered,
      coalesce(r.is_active,false) active,
      coalesce(r.is_closed_or_paused,false) OR
        coalesce(r.is_negative_decision,false) closed
    FROM public.job_search_analytics r
    WHERE r.record_type='evidence_event'
      AND r.is_primary_analytics_record IS TRUE
      AND r.event_date<=v_today
      AND nullif(pg_catalog.btrim(coalesce(r.employer,'')),'') IS NOT NULL
      AND nullif(pg_catalog.btrim(coalesce(r.role,'')),'') IS NOT NULL
  ),
  processes AS MATERIALIZED (
    SELECT process_key,
      pg_catalog.min(d) first_event,
      pg_catalog.min(d) FILTER(where applied) applied_date,
      pg_catalog.min(d) FILTER(where contacted) first_contact,
      pg_catalog.max(d) FILTER(where contacted) contact_stage_at,
      pg_catalog.max(d) FILTER(where interviewed) interview_stage_at,
      pg_catalog.max(d) FILTER(where progressed) progression_stage_at,
      pg_catalog.max(d) FILTER(where applied) application_stage_at,
      pg_catalog.bool_or(offered) has_offer,
      (pg_catalog.array_agg(active ORDER BY state_at DESC NULLS LAST,d DESC,id DESC))[1] currently_active,
      (pg_catalog.array_agg(closed ORDER BY state_at DESC NULLS LAST,d DESC,id DESC))[1] currently_closed
    FROM evidence GROUP BY process_key
  ),
  staged AS MATERIALIZED (
    SELECT
      CASE WHEN progression_stage_at IS NOT NULL THEN 'progression'
           WHEN interview_stage_at IS NOT NULL THEN 'interview'
           WHEN contact_stage_at IS NOT NULL THEN 'conversation'
           WHEN application_stage_at IS NOT NULL THEN 'application'
           ELSE NULL END stage,
      CASE WHEN progression_stage_at IS NOT NULL THEN progression_stage_at
           WHEN interview_stage_at IS NOT NULL THEN interview_stage_at
           WHEN contact_stage_at IS NOT NULL THEN contact_stage_at
           ELSE application_stage_at END stage_date,
      CASE WHEN currently_closed THEN 0::numeric
           WHEN EXISTS (
              SELECT 1 FROM public.job_application_staleness_review sr
              WHERE sr.process_key=processes.process_key
                AND sr.forecast_exclusion_verified IS TRUE
                AND sr.review_state='dormant_verified'
                AND sr.verified_at >= pg_catalog.now()-interval '30 days'
                AND sr.applied_on IS NOT NULL
                AND sr.applied_on <= v_today-45
                AND NOT EXISTS (
                  SELECT 1 FROM public.job_search_analytics newer
                  WHERE pg_catalog.lower(pg_catalog.btrim(coalesce(newer.employer,''))) || '|' ||
                        pg_catalog.lower(pg_catalog.btrim(coalesce(newer.role,'')))=processes.process_key
                    AND newer.event_date > sr.verified_at::date
                    AND (coalesce(newer.is_negative_decision,false)
                         OR coalesce(newer.is_human_interaction,false)
                         OR coalesce(newer.is_recruiter_interaction,false)
                         OR coalesce(newer.response_received,false)
                         OR coalesce(newer.is_interview,false))
                )
           ) THEN 0::numeric
           WHEN currently_active THEN 1.0::numeric
           ELSE 0.35::numeric END stage_weight,
      has_offer,first_event,applied_date,first_contact
    FROM processes
  ),
  active_stages AS MATERIALIZED (
    SELECT stage,stage_weight,age_month_index,pg_catalog.sum(n)::int AS n
    FROM (
      SELECT stage,stage_weight,
        least(5,pg_catalog.floor((v_today-stage_date)/30)::int) age_month_index,
        pg_catalog.count(*)::int n
      FROM staged
      WHERE stage IS NOT NULL AND stage_weight>0
        AND stage_date BETWEEN v_today-interval '180 days' AND v_today
      GROUP BY 1,2,3
      UNION ALL
      SELECT 'application'::text stage,0.35::numeric stage_weight,
        least(5,pg_catalog.floor((v_today-p.applied_on)/30)::int) age_month_index,
        pg_catalog.count(*)::int n
      FROM public.careersite_stale_application_pipeline_v2 p
      WHERE p.date_assumed IS TRUE
        AND p.health_segment IN ('recent_awaiting_response','stale_21_44','stale_45_59','stale_60_plus')
        AND p.exclude_from_active_forecast IS NOT TRUE
        AND p.applied_on BETWEEN v_today-interval '180 days' AND v_today
      GROUP BY 1,2,3
    ) combined
    GROUP BY 1,2,3
  ),
  summary AS (
    SELECT pg_catalog.count(*)::int linked_processes,
      pg_catalog.min(first_event) earliest,
      pg_catalog.count(*) FILTER(WHERE applied_date BETWEEN v_today-27 AND v_today)::int recent_applications,
      pg_catalog.count(*) FILTER(WHERE applied_date BETWEEN v_today-55 AND v_today-28)::int prior_applications,
      pg_catalog.count(*) FILTER(WHERE applied_date<=v_today-35)::int matured_applications,
      pg_catalog.count(*) FILTER(WHERE applied_date<=v_today-35 AND first_contact>=applied_date)::int mature_contacts,
      pg_catalog.count(*) FILTER(WHERE has_offer AND stage_weight>0)::int currently_offered
    FROM staged
  ),
  strategy_rows AS MATERIALIZED (
    SELECT
      r.source_key,
      r.snapshot_date,
      r.raw_data,
      coalesce(r.raw_data->>'category','uncategorized') AS category,
      coalesce(r.raw_data->>'priority','unspecified') AS priority
    FROM public.job_search_analytics r
    WHERE r.record_type='snapshot_note'
      AND r.activity='strategic_insight'
      AND r.status='current'
      AND r.source_file='chatgpt_job_hunting_analysis'
      AND coalesce(r.snapshot_date,v_today) <= v_today
  ),
  strategy_summary AS (
    SELECT
      pg_catalog.count(*)::int records_used,
      pg_catalog.count(*) FILTER (WHERE priority='critical')::int critical_records,
      pg_catalog.count(*) FILTER (WHERE priority='high')::int high_records,
      pg_catalog.max(snapshot_date) AS latest_strategy_date,
      coalesce(
        pg_catalog.jsonb_agg(DISTINCT category ORDER BY category),
        '[]'::jsonb
      ) AS categories,
      pg_catalog.bool_or(category='funnel_diagnosis') AS has_funnel_diagnosis,
      pg_catalog.bool_or(category='channel_effectiveness') AS has_human_access_signal,
      pg_catalog.bool_or(category='positioning') AS has_role_positioning,
      pg_catalog.bool_or(category='seniority') AS has_seniority_calibration,
      pg_catalog.bool_or(category='interview_performance') AS has_interview_compression_signal,
      pg_catalog.bool_or(category='evidence_quality') AS has_evidence_quality_signal,
      pg_catalog.bool_or(category='search_execution') AS has_search_execution_signal
    FROM strategy_rows
  ),
  strategy_features AS (
    SELECT pg_catalog.jsonb_build_object(
      'records_used', coalesce(s.records_used,0),
      'latest_strategy_date', s.latest_strategy_date,
      'critical_records', coalesce(s.critical_records,0),
      'high_records', coalesce(s.high_records,0),
      'categories', coalesce(s.categories,'[]'::jsonb),
      'features', pg_catalog.jsonb_build_object(
        'conversion_funnel_focus', coalesce(s.has_funnel_diagnosis,false),
        'human_access_priority', coalesce(s.has_human_access_signal,false),
        'role_positioning_calibrated', coalesce(s.has_role_positioning,false),
        'seniority_calibrated', coalesce(s.has_seniority_calibration,false),
        'interview_compression_risk_tracked', coalesce(s.has_interview_compression_signal,false),
        'evidence_quality_control', coalesce(s.has_evidence_quality_signal,false),
        'targeted_application_strategy', coalesce(s.has_search_execution_signal,false)
      ),
      'model_usage', 'qualitative calibration only; never counted as applications, interviews, conversations or offers',
      'source', 'public.job_search_analytics current non-primary strategic insight records'
    ) AS payload
    FROM strategy_summary s
  ),
  historical_context AS (
    SELECT pg_catalog.jsonb_build_object(
      'records_available', pg_catalog.count(*)::int,
      'latest_snapshot_date', pg_catalog.max(snapshot_date),
      'usage', 'provenance/context only; not treated as current pipeline state'
    ) AS payload
    FROM public.job_search_analytics r
    WHERE r.record_type='snapshot_note'
      AND r.activity='contact_intelligence'
      AND r.status='historical_snapshot'
      AND r.source_file='chatgpt_job_hunting_analysis'
      AND coalesce(r.snapshot_date,v_today) <= v_today
  )
  SELECT pg_catalog.jsonb_build_object(
    'as_of',v_today,
    'method','aggregate-30day-stage-buckets-illustrative-v1-plus-strategy-context',
    'summary',(select pg_catalog.to_jsonb(x) from summary x),
    'stage_buckets',(select coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x)
      ORDER BY x.stage,x.age_month_index,x.stage_weight),'[]'::jsonb)
      from active_stages x),
    'provisional_date_assumption_stage_count',(select pg_catalog.count(*)::int
       from public.careersite_stale_application_pipeline_v2 p
       where p.date_assumed IS TRUE
         and p.health_segment IN ('recent_awaiting_response','stale_21_44','stale_45_59','stale_60_plus')
         and p.exclude_from_active_forecast IS NOT TRUE
         and p.applied_on BETWEEN v_today-interval '180 days' AND v_today),
    'strategy_context',(select payload from strategy_features),
    'historical_contact_context',(select payload from historical_context),
    'model_input_rules',pg_catalog.jsonb_build_object(
      'primary_events_drive_stage_counts',true,
      'current_strategy_records_calibrate_interpretation',true,
      'historical_contact_snapshots_do_not_override_current_stage',true,
      'non_primary_records_do_not_increment_funnel_counts',true,
      'reviewed_dormant_at_least_45d_excluded_from_stage_buckets',true,
      'review_must_be_within_30d',true,
      'owner_assumed_dates_provisional_stage_weight_035',true,
      'assumed_dates_excluded_from_empirical_response_rates',true,
      'no_response_not_a_rejection',true
    ),
    'source','dated job-search evidence plus 0.35-weighted, owner-assumed dates for formerly undated application stages; private identities redacted'
  ) INTO v_result;
  RETURN v_result;
END
$function$
