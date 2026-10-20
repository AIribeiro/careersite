-- Daily and event-sensitive hiring forecast; evaluated in Stockholm calendar days.
-- Generated from the verified pre-change hiring v2 function.
-- Private engine preserves stage scoring, replaces calendar-today anchor with
-- recorded milestone dates and bounded weekly overdue reassessment.
CREATE OR REPLACE FUNCTION private.careersite_hiring_core_v3()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY INVOKER
 SET search_path TO ''
AS $function$
DECLARE
 d date := (pg_catalog.now() AT TIME ZONE 'Europe/Stockholm')::date;
 answer jsonb;
BEGIN

 WITH b AS MATERIALIZED (
   SELECT * FROM public.careersite_job_conversion_process_v1
 ), e AS MATERIALIZED (
   SELECT b.process_key,
    pg_catalog.max(j.event_date) FILTER (WHERE
      (coalesce(j.is_human_interaction,false) OR coalesce(j.is_recruiter_interaction,false))
      AND pg_catalog.lower(coalesce(j.interaction_direction,'')) IN ('inbound','two_way')
      AND pg_catalog.lower(coalesce(j.interaction_type,'')) !~ '(auto|bot)') human_on,
    pg_catalog.max(j.event_date) FILTER (WHERE
      pg_catalog.lower(coalesce(j.stage_outcome,'')) ~
        '(hiring.manager interview completed|first interview completed|interview completed|interview held|interview conducted|screening.*completed)'
      AND pg_catalog.lower(coalesce(j.stage_outcome,'')) !~ '(second|third|final).*interview') first_done,
    pg_catalog.max(j.event_date) FILTER (WHERE
      pg_catalog.lower(coalesce(j.stage_outcome,'')) ~
        '(second|third|final).{0,28}interview.{0,20}(completed|held|conducted)') next_done,
    pg_catalog.max(j.event_date) FILTER (WHERE
      j.interaction_type IN ('interview_invitation','interview_scheduled')
      AND pg_catalog.lower(coalesce(j.interaction_direction,''))='inbound'
      AND pg_catalog.lower(coalesce(j.stage_outcome,'')) !~ '(second|third|final)') first_invited,
    pg_catalog.max(j.event_date) FILTER (WHERE
      pg_catalog.lower(coalesce(j.stage_outcome,'')) ~ '(advanced to second interview|second interview scheduled|second interview participants confirmed)'
      AND pg_catalog.lower(coalesce(j.interaction_direction,''))='inbound') next_invited,
    pg_catalog.max(CASE WHEN j.interaction_type='interview_scheduled'
      AND pg_catalog.lower(coalesce(j.stage_outcome,'')) !~ '(second|third|final)'
      AND (j.raw_data->>'interview_date') ~ '^\d{4}-\d{2}-\d{2}$'
      THEN (j.raw_data->>'interview_date')::date END) first_meeting,
    pg_catalog.max(CASE WHEN j.interaction_type='interview_scheduled'
      AND pg_catalog.lower(coalesce(j.stage_outcome,'')) ~ '(second|third|final)'
      AND (j.raw_data->>'interview_date') ~ '^\d{4}-\d{2}-\d{2}$'
      THEN (j.raw_data->>'interview_date')::date END) next_meeting
   FROM b LEFT JOIN public.job_search_analytics j
    ON pg_catalog.lower(pg_catalog.btrim(j.employer))||'|'||pg_catalog.lower(pg_catalog.btrim(j.role))=b.process_key
    AND j.record_type IN ('evidence_event','history_event')
    AND j.event_date<=d
    AND (b.original_applied_on IS NULL OR j.event_date>=b.original_applied_on)
   GROUP BY b.process_key
 ), r AS MATERIALIZED (
   SELECT b.*,e.human_on,e.first_done,e.next_done,e.first_invited,e.next_invited,e.first_meeting,e.next_meeting,
    greatest(e.human_on,e.first_done,e.next_done,e.first_invited,e.next_invited) progressed_on,
    (e.next_invited IS NOT NULL OR e.next_meeting>=d) next_confirmed,
    ((b.health_segment='closed' OR b.outcome_class='other_closed_or_unreconciled')
      AND e.next_invited IS NOT NULL AND b.linked_employer_decision IS NULL
      AND NOT coalesce(b.exclude_from_active_forecast,false)) conflict_reconciled
   FROM b JOIN e USING(process_key)
 ), stages AS MATERIALIZED (
   SELECT r.*,
    CASE WHEN verified_offer THEN 'verified_offer'
      WHEN next_done IS NOT NULL THEN 'subsequent_interview_completed'
      WHEN next_confirmed THEN 'subsequent_interview_scheduled'
      WHEN first_done IS NOT NULL THEN 'first_interview_completed'
      WHEN first_invited IS NOT NULL OR first_meeting>=d THEN 'first_interview_scheduled'
      WHEN meaningful_human_response OR human_on IS NOT NULL THEN 'human_response'
      ELSE 'application_only' END stage,
    CASE WHEN outcome_class='employer_rejection' OR linked_employer_decision IN ('rejected','not_selected') THEN 'employer_rejection'
      WHEN verified_offer THEN 'offer'
      WHEN exclude_from_active_forecast THEN 'excluded_verified'
      WHEN conflict_reconciled THEN 'active_reconciled'
      WHEN outcome_class='other_closed_or_unreconciled' OR health_segment='closed' THEN 'closed_unreconciled'
      WHEN outcome_class='stale_no_decision' THEN 'stale_unknown'
      ELSE 'active_unknown_decision' END pipeline_status,
    CASE job_family WHEN 'A' THEN 1.0 WHEN 'B' THEN 0.94 WHEN 'C' THEN 0.92 ELSE 0.82 END::numeric role_factor,
    greatest(0,d-coalesce(progressed_on,applied_on,d-90)) days_idle
   FROM r
 ), weighted AS MATERIALIZED (
   SELECT s.*,
    CASE stage
      WHEN 'verified_offer' THEN 0.95
      WHEN 'subsequent_interview_completed' THEN 0.65
      WHEN 'subsequent_interview_scheduled' THEN 0.58
      WHEN 'first_interview_completed' THEN 0.45
      WHEN 'first_interview_scheduled' THEN 0.22
      WHEN 'human_response' THEN 0.15 ELSE 0.05 END::numeric stage_weight,
    CASE WHEN days_idle<=14 THEN 1.0 WHEN days_idle<=30 THEN 0.9
     WHEN days_idle<=45 THEN 0.72 WHEN days_idle<=60 THEN 0.5 ELSE 0.2 END::numeric freshness,
    CASE WHEN stage='subsequent_interview_scheduled' AND next_invited IS NOT NULL THEN 0.03
      ELSE 0 END::numeric employer_progression_bonus
   FROM stages s
 ), scores AS MATERIALIZED (
   SELECT w.*,
    pg_catalog.round(100* CASE WHEN pipeline_status IN
      ('employer_rejection','excluded_verified','closed_unreconciled','stale_unknown') THEN 0
     ELSE least(1,stage_weight*role_factor*freshness*
       (CASE WHEN date_assumed AND progressed_on IS NULL THEN 0.5 ELSE 1 END)
       +employer_progression_bonus) END,1) credibility,
    CASE WHEN stage='subsequent_interview_scheduled' AND next_meeting>=d THEN next_meeting
     WHEN stage='first_interview_scheduled' AND first_meeting>=d THEN first_meeting
     ELSE NULL END upcoming_meeting
   FROM weighted w
 ), live AS MATERIALIZED (
   SELECT s.*,pg_catalog.row_number() OVER
     (ORDER BY credibility DESC,progressed_on DESC NULLS LAST,process_key) ranking
   FROM scores s WHERE credibility>0
 ), top_anchor AS (
   SELECT l.*,
    CASE stage
      WHEN 'subsequent_interview_scheduled' THEN pg_catalog.coalesce(upcoming_meeting,next_invited,progressed_on,d)
      WHEN 'subsequent_interview_completed' THEN pg_catalog.coalesce(next_done,progressed_on,d)
      WHEN 'first_interview_completed' THEN pg_catalog.coalesce(first_done,progressed_on,d)
      WHEN 'first_interview_scheduled' THEN pg_catalog.coalesce(upcoming_meeting,first_invited,progressed_on,d)
      WHEN 'human_response' THEN pg_catalog.coalesce(human_on,progressed_on,d)
      ELSE pg_catalog.coalesce(applied_on,d) END AS timing_anchor,
    CASE stage WHEN 'subsequent_interview_scheduled' THEN 14
      WHEN 'subsequent_interview_completed' THEN 10
      WHEN 'first_interview_completed' THEN 21
      WHEN 'first_interview_scheduled' THEN 30
      WHEN 'human_response' THEN 42 ELSE 60 END AS early_days,
    CASE stage WHEN 'subsequent_interview_scheduled' THEN 28
      WHEN 'subsequent_interview_completed' THEN 21
      WHEN 'first_interview_completed' THEN 42
      WHEN 'first_interview_scheduled' THEN 56
      WHEN 'human_response' THEN 70 ELSE 90 END AS middle_days,
    CASE stage WHEN 'subsequent_interview_scheduled' THEN 49
      WHEN 'subsequent_interview_completed' THEN 45
      WHEN 'first_interview_completed' THEN 70
      WHEN 'first_interview_scheduled' THEN 90
      WHEN 'human_response' THEN 110 ELSE 140 END AS late_days
   FROM live l WHERE ranking=1
 ), top_base AS (
   SELECT a.*, timing_anchor+early_days AS base_early,
          timing_anchor+middle_days AS base_middle,
          timing_anchor+late_days AS base_late
   FROM top_anchor a
 ), top_roll AS (
   SELECT w.*, (base_middle + 7 * pg_catalog.greatest(0,
     pg_catalog.ceil(pg_catalog.greatest(0,d-(base_middle-7))::numeric / 7)::integer)
   )::date AS roll_central
   FROM top_base w
 ), top_stage AS (
   SELECT t.*,
    CASE WHEN d>base_late+14 THEN NULL::date
       ELSE pg_catalog.greatest(base_early,d+2) END AS offer_early,
    CASE WHEN d>base_late+14 THEN NULL::date
       ELSE roll_central END AS offer_central,
    CASE WHEN d>base_late+14 THEN NULL::date
       ELSE pg_catalog.greatest(base_late,roll_central+14) END AS offer_late,
    (roll_central - base_middle) AS calendar_shift_days,
    CASE WHEN d>base_late+14 THEN 'expired_requires_new_employer_evidence'
      WHEN d>base_middle-7 THEN 'overdue_reassessed_weekly'
      WHEN d>base_early THEN 'earliest_elapsed'
      ELSE 'within_original_window' END AS window_state
   FROM top_roll t
 )
 SELECT pg_catalog.jsonb_build_object(
  'model_version','hiring-v2-stage-evidence-provisional','as_of',d,
  'timing_policy','milestone-anchored-weekly-reassessment-v1',
  'score_definition','Relative pipeline credibility (0–100), NOT offer probability',
  'offer_probability_30d',NULL,'offer_probability_60d',NULL,'offer_probability_90d',NULL,
  'portfolio_credibility_index',(SELECT pg_catalog.round(
    coalesce(pg_catalog.sum(credibility*
      CASE ranking WHEN 1 THEN 0.50 WHEN 2 THEN 0.25 WHEN 3 THEN 0.15
       WHEN 4 THEN 0.07 WHEN 5 THEN 0.03 ELSE 0 END),0),1)
     FROM live WHERE ranking<=5),
  'cohort',pg_catalog.jsonb_build_object(
    'total',(SELECT count(*) FROM scores),
    'human_response_v1',(SELECT count(*) FROM scores WHERE meaningful_human_response),
    'first_interview_v1',(SELECT count(*) FROM scores WHERE first_interview),
    'completed_first_v2',(SELECT count(*) FROM scores WHERE first_done IS NOT NULL),
    'scheduled_first_v2',(SELECT count(*) FROM scores WHERE stage='first_interview_scheduled'),
    'subsequent_stage_v2',(SELECT count(*) FROM scores WHERE stage IN ('subsequent_interview_scheduled','subsequent_interview_completed')),
    'offers',(SELECT count(*) FROM scores WHERE verified_offer),
    'closed_rejections',(SELECT count(*) FROM scores WHERE pipeline_status='employer_rejection'),
    'stale_not_rejected',(SELECT count(*) FROM scores WHERE pipeline_status='stale_unknown'),
    'reconciled_active',(SELECT count(*) FROM scores WHERE pipeline_status='active_reconciled'),
    'eligible_scored',(SELECT count(*) FROM live)
  ),
  'stage_breakdown',(SELECT coalesce(pg_catalog.jsonb_object_agg(stage,n),'{}'::jsonb)
   FROM (SELECT stage,count(*) n FROM live GROUP BY stage) x),
  'leading_stage_scenario',(SELECT pg_catalog.jsonb_build_object(
    'employer',employer,'role',role,'stage',stage,'meeting',upcoming_meeting,
    'timing_anchor',timing_anchor,'original_offer_central',base_middle,
    'calendar_shift_days',calendar_shift_days,'window_state',window_state,
    'days_to_offer',offer_central-d,
    'offer_earliest',offer_early,'offer_central',offer_central,'offer_latest',offer_late,
    'start_earliest',offer_early+14,'start_central',offer_central+28,'start_latest',offer_late+42,
    'disclaimer','Milestone-anchored conditional planning range; calendar-only weekly reassessments after central-window approach; not calibrated probability') FROM top_stage),
  'top_processes',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
    'rank',ranking,'process_key',process_key,'employer',employer,'role',role,'job_family',job_family,
    'stage',stage,'status',pipeline_status,'credibility_index',credibility,
    'stage_weight',stage_weight,'freshness_factor',freshness,'role_factor',role_factor,
    'last_progress',progressed_on,'next_interview',upcoming_meeting,
    'first_interview_completed',first_done,'subsequent_completed',next_done,
    'conflicting_closed_record_reconciled',conflict_reconciled
  ) ORDER BY ranking),'[]'::jsonb) FROM live WHERE ranking<=12),
  'diagnostics',pg_catalog.jsonb_build_object(
    'v1_interview_evidence_not_completed_in_v2',(SELECT count(*) FROM scores
       WHERE first_interview AND first_done IS NULL AND next_done IS NULL),
    'active_closed_conflicts_reconciled',(SELECT count(*) FROM scores WHERE conflict_reconciled),
    'provisional_application_dates',(SELECT count(*) FROM scores WHERE date_assumed),
    'no_response_as_rejection',false,
    'model_formula','stage weight x role-fit x freshness; confirmed advancement bonus; weighted top five 50/25/15/7/3'),
  'geographic_assumptions',pg_catalog.jsonb_build_object(
    'gothenburg','preferred, not a hard restriction','stockholm_penalty',false,
    'travel','acceptable','relocation','conditional for high-quality opportunities',
    'missing_work_model','unverified, no automatic disqualification'),
  'external_market_role','Contextual only: not used as individual conversion evidence',
  'generated_at',pg_catalog.now()
 ) INTO answer;
 RETURN answer;
END;
$function$

CREATE OR REPLACE FUNCTION public.careersite_hiring_prediction_v2()
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path TO ''
AS $wrapper$
BEGIN
 IF auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
    OR pg_catalog.lower(pg_catalog.coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
    OR pg_catalog.coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
 THEN RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501'; END IF;
 RETURN private.careersite_hiring_core_v3();
END;
$wrapper$;
REVOKE ALL ON FUNCTION public.careersite_hiring_prediction_v2() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_prediction_v2() TO authenticated;

-- Date-sensitive snapshot, separately materialised from on-page analytics.
CREATE TABLE IF NOT EXISTS public.careersite_hiring_daily_rechecks (
 id bigint generated always as identity primary key,
 owner_user_id uuid NOT NULL DEFAULT '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid,
 forecast_day date NOT NULL,
 model_version text NOT NULL,
 timing_policy text NOT NULL,
 trigger_reason text NOT NULL,
 market_signature text NOT NULL,
 pipeline_signature text NOT NULL,
 timing_signature text NOT NULL,
 scenario jsonb NOT NULL,
 market_context jsonb NOT NULL,
 generated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT careersite_daily_rechecks_unique UNIQUE(forecast_day,market_signature,pipeline_signature,timing_signature)
);
ALTER TABLE public.careersite_hiring_daily_rechecks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.careersite_hiring_daily_rechecks FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.careersite_hiring_daily_rechecks TO authenticated;
CREATE POLICY careersite_daily_rechecks_owner_read
 ON public.careersite_hiring_daily_rechecks FOR SELECT TO authenticated
 USING (owner_user_id=(SELECT auth.uid()) AND
 pg_catalog.lower(pg_catalog.coalesce((SELECT auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 AND pg_catalog.coalesce((SELECT auth.jwt())->>'is_anonymous','false')='false');
CREATE INDEX IF NOT EXISTS careersite_daily_rechecks_by_date ON
 public.careersite_hiring_daily_rechecks(forecast_day DESC,generated_at DESC);

-- Context-only shadow history schema was left at v1 while the app advanced
-- to v2 role-mandates. Permit both versions; do not weaken no-scoring checks.
ALTER TABLE public.careersite_hiring_market_shadow_history
 DROP CONSTRAINT IF EXISTS careersite_shadow_version_check;
ALTER TABLE public.careersite_hiring_market_shadow_history
 ADD CONSTRAINT careersite_shadow_version_check CHECK
 (shadow_model_version IN ('market-shadow-v1-context-only',
                           'market-shadow-v2-role-mandates-context-only'));

CREATE OR REPLACE FUNCTION private.careersite_run_hiring_daily_recheck()
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO ''
AS $run$
DECLARE
 d date := (now() AT TIME ZONE 'Europe/Stockholm')::date;
 calc jsonb;
 m_sig text;
 p_sig text;
 t_sig text;
 ctx jsonb;
 prior record;
 reason text;
 stored_id bigint;
BEGIN
 calc := private.careersite_hiring_core_v3();
 SELECT pg_catalog.md5(pg_catalog.coalesce(
   pg_catalog.string_agg(
     pg_catalog.concat_ws('|',id,source_registry_key,indicator_key,metric_value,
       metric_value_text,updated_at,last_confirmed_at,first_seen_at),
     ';' ORDER BY id
   ),''
 )) INTO m_sig
 FROM public.job_market_insights
 WHERE source_registry_key IN ('af_jobtech_target_demand','af_jobtech_historical_ads',
  'af_jobsearch_current','trr_professional_transitions',
  'brg_gothenburg_business_cycle','scb_enterprise_ai_adoption',
  'unionen_branschbarometern','almega_services_indicator')
 AND (first_seen_at IS NULL OR first_seen_at <= now());
 p_sig := pg_catalog.md5(pg_catalog.coalesce((calc->'top_processes')::text,'[]'));
 t_sig := pg_catalog.md5(pg_catalog.coalesce((calc->'leading_stage_scenario')::text,'{}'));
 SELECT id,forecast_day,market_signature,pipeline_signature,timing_signature
 INTO prior FROM public.careersite_hiring_daily_rechecks
 ORDER BY generated_at DESC,id DESC LIMIT 1;
 reason := CASE
    WHEN prior.id IS NULL THEN 'initial_daily_baseline'
    WHEN prior.forecast_day<>d AND prior.market_signature<>m_sig THEN 'calendar_and_external_update'
    WHEN prior.forecast_day<>d THEN 'calendar_day'
    WHEN prior.market_signature<>m_sig THEN 'external_update'
    WHEN prior.pipeline_signature<>p_sig THEN 'recruitment_evidence_update'
    WHEN prior.timing_signature<>t_sig THEN 'timing_window_update'
    ELSE 'unchanged'
 END;
 ctx := pg_catalog.jsonb_build_object(
   'market_effect','context_only_not_scored',
   'source_refresh_detected',prior.id IS NOT NULL AND prior.market_signature<>m_sig,
   'source_families',(SELECT count(distinct source_registry_key)
                      FROM public.job_market_insights
                      WHERE source_registry_key IN (
                       'af_jobtech_target_demand','trr_professional_transitions',
                       'brg_gothenburg_business_cycle','scb_enterprise_ai_adoption',
                       'unionen_branschbarometern','almega_services_indicator')),
   'observations',(SELECT count(*) FROM public.job_market_insights
      WHERE source_registry_key IN ('af_jobtech_target_demand',
       'trr_professional_transitions','brg_gothenburg_business_cycle',
       'scb_enterprise_ai_adoption','unionen_branschbarometern',
       'almega_services_indicator')),
   'classification','not_validated_for_personal_offer_timing');
 IF reason<>'unchanged' THEN
   INSERT INTO public.careersite_hiring_daily_rechecks(
     owner_user_id,forecast_day,model_version,timing_policy,trigger_reason,
     market_signature,pipeline_signature,timing_signature,scenario,market_context
   ) VALUES(
     '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid,
     d,calc->>'model_version',calc->>'timing_policy',reason,
     m_sig,p_sig,t_sig,calc,ctx)
   ON CONFLICT(forecast_day,market_signature,pipeline_signature,timing_signature)
   DO NOTHING RETURNING id INTO stored_id;
   -- The public projection contains only dates, no private process metadata.
   IF (calc->'leading_stage_scenario'->>'offer_central') IS NOT NULL THEN
     INSERT INTO public.careersite_public_hiring_timing_v2(
       id,model_version,as_of,offer_central,offer_earliest,offer_latest,
       start_central,start_earliest,start_latest,published_at)
     VALUES(1,calc->>'model_version',d,
       (calc->'leading_stage_scenario'->>'offer_central')::date,
       (calc->'leading_stage_scenario'->>'offer_earliest')::date,
       (calc->'leading_stage_scenario'->>'offer_latest')::date,
       (calc->'leading_stage_scenario'->>'start_central')::date,
       (calc->'leading_stage_scenario'->>'start_earliest')::date,
       (calc->'leading_stage_scenario'->>'start_latest')::date,now())
     ON CONFLICT(id) DO UPDATE SET
       model_version=excluded.model_version,as_of=excluded.as_of,
       offer_central=excluded.offer_central,offer_earliest=excluded.offer_earliest,
       offer_latest=excluded.offer_latest,start_central=excluded.start_central,
       start_earliest=excluded.start_earliest,start_latest=excluded.start_latest,
       published_at=excluded.published_at;
   ELSE
     -- A lapsed scenario must not be advertised as a current public estimate.
     DELETE FROM public.careersite_public_hiring_timing_v2 WHERE id=1;
   END IF;
 END IF;
 RETURN pg_catalog.jsonb_build_object('status',reason,'forecast_day',d,
   'recorded',stored_id IS NOT NULL,'timing_policy',calc->>'timing_policy',
   'offer_central',calc->'leading_stage_scenario'->>'offer_central',
   'start_central',calc->'leading_stage_scenario'->>'start_central',
   'window_state',calc->'leading_stage_scenario'->>'window_state',
   'calendar_shift_days',calc->'leading_stage_scenario'->>'calendar_shift_days');
END;
$run$;
REVOKE ALL ON FUNCTION private.careersite_hiring_core_v3() FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION private.careersite_run_hiring_daily_recheck() FROM PUBLIC,anon,authenticated;

CREATE OR REPLACE FUNCTION public.careersite_hiring_daily_recheck_v1()
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path TO ''
AS $owner$
BEGIN
 IF auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
    OR pg_catalog.lower(pg_catalog.coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
    OR pg_catalog.coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
 THEN RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501'; END IF;
 RETURN private.careersite_run_hiring_daily_recheck();
END;
$owner$;
REVOKE ALL ON FUNCTION public.careersite_hiring_daily_recheck_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_daily_recheck_v1() TO authenticated;

-- One daily calendar run, plus hourly checks for newly ingested evidence.
-- Hourly checks do not append duplicate rows when all inputs are unchanged.
SELECT cron.schedule('hiring-daily-calendar-0600-utc','0 6 * * *',
 'SELECT private.careersite_run_hiring_daily_recheck();');
SELECT cron.schedule('hiring-new-evidence-hourly','15 * * * *',
 'SELECT private.careersite_run_hiring_daily_recheck();');
