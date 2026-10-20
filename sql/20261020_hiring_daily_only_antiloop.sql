-- Hiring predictor: strict once-per-24h batch only; no other automatic rechecks.
-- Runs at 06:00 UTC daily, constant 24h cadence, independent of UI session.
DO $drop_hourly$
BEGIN
 IF EXISTS (SELECT 1 FROM cron.job WHERE jobname='hiring-new-evidence-hourly') THEN
   PERFORM cron.unschedule('hiring-new-evidence-hourly');
 END IF;
 IF (SELECT count(*) FROM cron.job
      WHERE jobname='hiring-daily-calendar-0600-utc'
        AND schedule='0 6 * * *' AND active) <> 1 THEN
   RAISE EXCEPTION 'Expected exactly one active daily hiring cron job';
 END IF;
END;
$drop_hourly$;

CREATE OR REPLACE FUNCTION private.careersite_run_hiring_daily_recheck()
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
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
 -- Single-flight: simultaneous scheduler/page calls never compete for writes.
 IF NOT pg_catalog.pg_try_advisory_xact_lock(191000, 24) THEN
   RETURN pg_catalog.jsonb_build_object(
     'status','already_running','forecast_day',d,'recorded',false);
 END IF;
 -- Exactly one evaluated source state per Stockholm date. Do this BEFORE
 -- the expensive model and market reads, even when inputs have changed.
 IF EXISTS (
   SELECT 1 FROM public.careersite_hiring_daily_rechecks
   WHERE forecast_day=d
     AND owner_user_id='210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
 ) THEN
   RETURN pg_catalog.jsonb_build_object(
     'status','already_checked_today','forecast_day',d,'recorded',false);
 END IF;
 calc := private.careersite_hiring_core_v3();
 SELECT pg_catalog.md5(coalesce(
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
 p_sig := pg_catalog.md5(coalesce((calc->'top_processes')::text,'[]'));
 t_sig := pg_catalog.md5(coalesce((calc->'leading_stage_scenario')::text,'{}'));
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
$function$;

-- The browser may read the archived daily outcome; it must not itself
-- trigger a second calculation or bypass the 24h cadence.
REVOKE EXECUTE ON FUNCTION public.careersite_hiring_daily_recheck_v1()
  FROM PUBLIC, anon, authenticated;
