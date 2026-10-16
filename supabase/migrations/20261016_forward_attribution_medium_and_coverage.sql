-- New attribution telemetry only. Do not alter or backfill historical events.
ALTER TABLE public.careersite_analytics_events
    ADD COLUMN IF NOT EXISTS utm_medium text;

DO $guard$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_constraint
    WHERE conname='careersite_analytics_utm_medium_safe'
      AND conrelid='public.careersite_analytics_events'::regclass
  ) THEN
    ALTER TABLE public.careersite_analytics_events
      ADD CONSTRAINT careersite_analytics_utm_medium_safe CHECK (
        utm_medium IS NULL OR (
          length(utm_medium) BETWEEN 1 AND 32
          AND utm_medium ~ '^[a-z0-9_-]+$'
        )
      );
  END IF;
END;
$guard$;

-- Epoch is created at the live database change, not inferred for old visits.
CREATE TABLE IF NOT EXISTS public.careersite_attribution_coverage_epoch (
  singleton smallint PRIMARY KEY CHECK (singleton=1),
  started_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO public.careersite_attribution_coverage_epoch (singleton)
VALUES (1) ON CONFLICT (singleton) DO NOTHING;
REVOKE ALL ON public.careersite_attribution_coverage_epoch
  FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.careersite_attribution_coverage_epoch TO service_role;

-- Exact first content entry, disjoint classifications, aggregate-only output.
-- No raw events or session identifiers are returned.
CREATE OR REPLACE FUNCTION public.careersite_attribution_coverage_v1(
  p_days integer DEFAULT 30
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path TO '' AS $fn$
DECLARE
  v_epoch timestamptz;
  v_since timestamptz;
  v_until timestamptz := now();
  v_result jsonb;
BEGIN
  IF p_days NOT IN (7,30,90,365) OR p_days IS NULL THEN
    RAISE EXCEPTION 'Unsupported coverage period' USING ERRCODE='22023';
  END IF;

  -- An authenticated account other than the verified CMS owner is not enough.
  IF coalesce(auth.jwt() ->> 'role','') <> 'service_role'
    AND (
      auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
      OR lower(coalesce(auth.jwt() ->> 'email','')) <> 'jair.ribeiro@outlook.it'
      OR coalesce(auth.jwt() ->> 'is_anonymous','false') <> 'false'
    )
  THEN
    RAISE EXCEPTION 'Owner authentication is required' USING ERRCODE='42501';
  END IF;

  SELECT started_at INTO v_epoch
  FROM public.careersite_attribution_coverage_epoch WHERE singleton=1;
  v_since := greatest(v_epoch,v_until-make_interval(days=>p_days));

  WITH session_origin AS MATERIALIZED (
    SELECT e.session_id,
      min(e.occurred_at) as started_at,
      bool_or(lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test') as is_test
    FROM public.careersite_analytics_events e
    WHERE e.session_id IS NOT NULL
    GROUP BY e.session_id
    HAVING min(e.occurred_at)>=v_since AND min(e.occurred_at)<=v_until
  ),
  first_content AS MATERIALIZED (
    SELECT DISTINCT ON (e.session_id)
      e.session_id, e.occurred_at,
      nullif(lower(btrim(e.attribution_source)),'') as source_tag,
      nullif(lower(btrim(e.utm_source)),'') as utm_source_tag,
      nullif(lower(btrim(e.utm_medium)),'') as medium_tag,
      nullif(btrim(e.utm_campaign),'') as campaign_tag,
      nullif(btrim(e.utm_content),'') as content_tag,
      nullif(btrim(e.referrer_host),'') as referrer
    FROM public.careersite_analytics_events e
    JOIN session_origin s ON s.session_id=e.session_id
    WHERE NOT s.is_test
      AND e.event_name IN ('page_view','article_view')
      AND e.occurred_at>=s.started_at AND e.occurred_at<=v_until
    ORDER BY e.session_id,e.occurred_at,e.id
  ),
  classified AS MATERIALIZED (
    SELECT
      (occurred_at AT TIME ZONE 'Europe/Stockholm')::date as day,
      CASE WHEN coalesce(source_tag,utm_source_tag) IS NOT NULL THEN 'tagged'
           WHEN referrer IS NOT NULL THEN 'referrer_only'
           ELSE 'unknown' END as evidence,
      source_tag IS NOT NULL as has_explicit_source,
      utm_source_tag IS NOT NULL as has_utm_source,
      medium_tag IS NOT NULL as has_medium,
      campaign_tag IS NOT NULL as has_campaign,
      content_tag IS NOT NULL as has_content,
      CASE WHEN source_tag IS NOT NULL AND utm_source_tag IS NOT NULL
             AND source_tag<>utm_source_tag THEN true ELSE false END as conflicting_source,
      coalesce(source_tag,utm_source_tag) as declared_source
    FROM first_content
  ),
  by_day AS (
    SELECT day,count(*)::integer as sessions,
      count(*) FILTER(WHERE evidence='tagged')::integer as tagged,
      count(*) FILTER(WHERE evidence='referrer_only')::integer as referrer_only,
      count(*) FILTER(WHERE evidence='unknown')::integer as unknown
    FROM classified GROUP BY day
  ),
  day_series AS (
    SELECT d::date as day FROM generate_series(
      (v_since AT TIME ZONE 'Europe/Stockholm')::date,
      (v_until AT TIME ZONE 'Europe/Stockholm')::date,interval '1 day'
    ) AS d
  ),
  rows AS (
    SELECT s.day,coalesce(a.sessions,0) as sessions,
      coalesce(a.tagged,0) as tagged,
      coalesce(a.referrer_only,0) as referrer_only,
      coalesce(a.unknown,0) as unknown,
      CASE WHEN coalesce(a.sessions,0)>0
         THEN round(100.0*(a.tagged+a.referrer_only)/a.sessions,1)
         ELSE NULL END as identifiable_pct
    FROM day_series s LEFT JOIN by_day a USING (day)
  )
  SELECT jsonb_build_object(
    'monitoring_started_at',v_epoch,
    'window_from',v_since,'window_through',v_until,
    'method','first-observed-content-session-since-activation; no historical rewrite',
    'overview',(
      SELECT jsonb_build_object(
        'sessions',count(*),
        'tagged',count(*) FILTER(WHERE evidence='tagged'),
        'referrer_only',count(*) FILTER(WHERE evidence='referrer_only'),
        'unknown',count(*) FILTER(WHERE evidence='unknown'),
        'identifiable_pct',CASE WHEN count(*)>0 THEN
          round(100.0*count(*) FILTER(WHERE evidence<>'unknown')/count(*),1)
          ELSE NULL END,
        'utm_source_count',count(*) FILTER(WHERE has_utm_source),
        'medium_count',count(*) FILTER(WHERE has_medium AND evidence='tagged'),
        'campaign_count',count(*) FILTER(WHERE has_campaign AND evidence='tagged'),
        'content_count',count(*) FILTER(WHERE has_content AND evidence='tagged'),
        'tagged_with_medium_pct',CASE WHEN count(*) FILTER(WHERE evidence='tagged')>0
          THEN round(100.0*count(*) FILTER(WHERE evidence='tagged' AND has_medium)
          /count(*) FILTER(WHERE evidence='tagged'),1) ELSE NULL END,
        'tagged_with_campaign_pct',CASE WHEN count(*) FILTER(WHERE evidence='tagged')>0
          THEN round(100.0*count(*) FILTER(WHERE evidence='tagged' AND has_campaign)
          /count(*) FILTER(WHERE evidence='tagged'),1) ELSE NULL END,
        'source_conflicts',count(*) FILTER(WHERE conflicting_source)
      ) FROM classified
    ),
    'daily',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY day),'[]'::jsonb)
             FROM rows r),
    'sources',(SELECT coalesce(jsonb_agg(to_jsonb(s) ORDER BY s.sessions DESC,s.source),'[]'::jsonb)
       FROM (SELECT declared_source AS source,count(*)::integer sessions
             FROM classified WHERE evidence='tagged'
             GROUP BY declared_source) s)
  ) INTO v_result;
  RETURN v_result;
END
$fn$;

REVOKE EXECUTE ON FUNCTION public.careersite_attribution_coverage_v1(integer)
  FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.careersite_attribution_coverage_v1(integer)
  TO authenticated, service_role;
