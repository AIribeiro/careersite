-- Public read-only summaries. No company, recruiter, candidate, free-text,
-- source-file, email, underlying application row or individual job process
-- is returned. The detailed job tables stay inaccessible to anon.
CREATE OR REPLACE FUNCTION public.careersite_public_job_summary_v1(
  p_days integer DEFAULT 30
) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=''
AS $fn$
DECLARE result jsonb;
BEGIN
  IF p_days IS NULL OR p_days<1 OR p_days>730 THEN
    RAISE EXCEPTION 'Unsupported horizon' USING ERRCODE='22023';
  END IF;
  WITH primary_events AS MATERIALIZED (
    SELECT r.event_date AS d,
      lower(btrim(coalesce(r.employer,''))) || '|' ||
      lower(btrim(coalesce(r.role,''))) AS process_key,
      coalesce(r.is_application,false) AS applied,
      coalesce(r.is_human_interaction,false) AND
        lower(coalesce(r.interaction_direction,'')) IN ('inbound','two_way') AS responded,
      lower(coalesce(r.event_type,''))='interview_completed' OR
        lower(coalesce(r.activity,'')) ~ 'interview (held|completed)' AS interviewed,
      coalesce(r.is_negative_decision,false) AND
        lower(coalesce(r.event_type,'')) IN
          ('rejection','rejected','negative_decision','closed_rejected') AS rejected
    FROM public.job_search_analytics r
    WHERE r.is_primary_analytics_record IS TRUE
      AND r.record_type IN ('evidence_event','history_event','activity_summary')
      AND r.event_date BETWEEN
         (now() AT TIME ZONE 'Europe/Stockholm')::date-(p_days-1)
         AND (now() AT TIME ZONE 'Europe/Stockholm')::date
      AND nullif(btrim(coalesce(r.employer,'')),'') IS NOT NULL
      AND nullif(btrim(coalesce(r.role,'')),'') IS NOT NULL
  ),
  daily AS (
    SELECT d,
      count(DISTINCT process_key) FILTER(WHERE applied)::int applications,
      count(DISTINCT process_key) FILTER(WHERE responded)::int responses,
      count(DISTINCT process_key) FILTER(WHERE interviewed)::int interviews,
      count(DISTINCT process_key) FILTER(WHERE rejected)::int rejections
    FROM primary_events GROUP BY d
  ),
  weekly AS (
    SELECT date_trunc('week',d::timestamp)::date week,
      sum(applications)::int applications,sum(responses)::int responses,
      sum(interviews)::int interviews,sum(rejections)::int rejections
    FROM daily GROUP BY 1
  )
  SELECT jsonb_build_object(
    'horizon_days',p_days,
    'through',(now() AT TIME ZONE 'Europe/Stockholm')::date,
    'method','dated-primary-deduplicated-per-process-per-day-v1',
    'totals',jsonb_build_object(
      'applications',coalesce((select sum(applications) from daily),0),
      'responses',coalesce((select sum(responses) from daily),0),
      'interviews',coalesce((select sum(interviews) from daily),0),
      'rejections',coalesce((select sum(rejections) from daily),0)
    ),
    'weekly',(SELECT coalesce(jsonb_agg(to_jsonb(w) ORDER BY w.week),'[]'::jsonb) FROM weekly w),
    'daily',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.d),'[]'::jsonb) FROM daily d)
  ) INTO result;
  RETURN result;
END $fn$;

