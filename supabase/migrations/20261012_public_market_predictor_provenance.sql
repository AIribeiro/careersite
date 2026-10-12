CREATE OR REPLACE FUNCTION public.careersite_public_market_summary_v1()
RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=''
AS $fn$
  SELECT jsonb_build_object(
    'as_of',(now() AT TIME ZONE 'Europe/Stockholm')::date,
    'signals',
    coalesce(jsonb_agg(to_jsonb(x) ORDER BY x.observation_date DESC,x.indicator_name),'[]'::jsonb)
  )
  FROM (
    SELECT DISTINCT ON (indicator_key)
      indicator_key,indicator_name,observation_date,period_label,
      region,sector,metric_value,metric_unit,change_value,
      signal_score,confidence_score,relevance_score,insight_summary,
      source_organization,source_url,published_at,first_seen_at,valid_until,is_current
    FROM public.job_market_insights
    WHERE coalesce(is_current,true)
      AND indicator_key IS NOT NULL
      AND observation_date IS NOT NULL
    ORDER BY indicator_key,observation_date DESC
    LIMIT 200
  ) x;
$fn$;

REVOKE ALL ON FUNCTION public.careersite_public_market_summary_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_public_market_summary_v1() TO anon,authenticated;
