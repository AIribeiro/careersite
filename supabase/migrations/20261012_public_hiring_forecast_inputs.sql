-- Release aggregate stage distributions, never employer/recruiter/process
-- identities or event-level job history. This supports an illustrative public
-- planning model; the full personally calibrated Beta remains Admin-only.
CREATE OR REPLACE FUNCTION public.careersite_public_hiring_inputs_v1()
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=''
AS $fn$
DECLARE v_today date := (now() at time zone 'Europe/Stockholm')::date;
        v_result jsonb;
BEGIN
  WITH evidence AS MATERIALIZED (
    SELECT
      lower(btrim(coalesce(r.employer,''))) || '|' ||
      lower(btrim(coalesce(r.role,''))) AS process_key,
      r.event_date d,
      coalesce(r.snapshot_date,r.event_date) state_at,
      r.id,
      coalesce(r.is_application,false) applied,
      coalesce(r.is_human_interaction,false) AND
        lower(coalesce(r.interaction_direction,'')) IN ('inbound','two_way') contacted,
      coalesce(r.is_interview,false) AND (
        lower(coalesce(r.event_type,''))='interview_completed'
        OR lower(coalesce(r.activity,'')) ~ '(held|completed|conducted)'
        OR lower(coalesce(r.stage_outcome,'')) ~ '(held|completed|conducted)'
      ) interviewed,
      lower(coalesce(r.stage_outcome,'')) ~
        '(next.stage|second.interview|final.interview|reference.check|offer)' OR
      lower(coalesce(r.event_type,'')) ~
        '(next.stage|second.interview|final.interview|reference.check|offer)' progressed,
      lower(coalesce(r.event_type,'')) ~ '(offer_received|offer_accepted)' OR
        lower(coalesce(r.stage_outcome,'')) ~ '(offer_received|offer_accepted)' offered,
      coalesce(r.is_active,false) active,
      coalesce(r.is_closed_or_paused,false) OR
        coalesce(r.is_negative_decision,false) closed
    FROM public.job_search_analytics r
    WHERE r.record_type='evidence_event'
      AND r.is_primary_analytics_record IS TRUE
      AND r.event_date<=v_today
      AND nullif(btrim(coalesce(r.employer,'')),'') IS NOT NULL
      AND nullif(btrim(coalesce(r.role,'')),'') IS NOT NULL
  ),
  processes AS MATERIALIZED (
    SELECT process_key,
      min(d) first_event,
      min(d) FILTER(where applied) applied_date,
      min(d) FILTER(where contacted) first_contact,
      max(d) FILTER(where contacted) contact_stage_at,
      max(d) FILTER(where interviewed) interview_stage_at,
      max(d) FILTER(where progressed) progression_stage_at,
      max(d) FILTER(where applied) application_stage_at,
      bool_or(offered) has_offer,
      (array_agg(active ORDER BY state_at DESC NULLS LAST,d DESC,id DESC))[1] currently_active,
      (array_agg(closed ORDER BY state_at DESC NULLS LAST,d DESC,id DESC))[1] currently_closed
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
           WHEN currently_active THEN 1.0::numeric
           ELSE 0.35::numeric END stage_weight,
      has_offer,first_event,applied_date,first_contact
    FROM processes
  ),
  active_stages AS MATERIALIZED (
    SELECT stage,stage_weight,
      least(5, floor((v_today-stage_date)/30)::int) age_month_index,
      count(*)::int n
    FROM staged
    WHERE stage IS NOT NULL AND stage_weight>0
      AND stage_date BETWEEN v_today-interval '180 days' AND v_today
    GROUP BY 1,2,3
  ),
  summary AS (
    SELECT count(*)::int linked_processes,
      min(first_event) earliest,
      count(*) FILTER(WHERE applied_date BETWEEN v_today-27 AND v_today)::int recent_applications,
      count(*) FILTER(WHERE applied_date BETWEEN v_today-55 AND v_today-28)::int prior_applications,
      count(*) FILTER(WHERE applied_date<=v_today-35)::int matured_applications,
      count(*) FILTER(WHERE applied_date<=v_today-35 AND first_contact>=applied_date)::int mature_contacts,
      count(*) FILTER(WHERE has_offer AND stage_weight>0)::int currently_offered
    FROM staged
  )
  SELECT jsonb_build_object(
    'as_of',v_today,
    'method','aggregate-30day-stage-buckets-illustrative-v1',
    'summary',(select to_jsonb(x) from summary x),
    'stage_buckets',(select coalesce(jsonb_agg(to_jsonb(x)
      ORDER BY x.stage,x.age_month_index,x.stage_weight),'[]'::jsonb)
      from active_stages x),
    'source','primary dated job-search evidence; private identities redacted'
  ) INTO v_result;
  RETURN v_result;
END $fn$;
REVOKE ALL ON FUNCTION public.careersite_public_hiring_inputs_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_public_hiring_inputs_v1() TO anon,authenticated;
