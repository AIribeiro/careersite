-- Restore the COMPLETE external-market history to public Analytics.
-- Safe, explicitly projected *non-personal* indicators only: no raw_data,
-- source sync IDs, private job rows, user-specific processes or credentials.
-- Revision rows of the same observation/series do not masquerade as releases.
CREATE OR REPLACE FUNCTION public.careersite_public_market_history_v1()
RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=''
AS $fn$
  WITH revisions AS MATERIALIZED (
    SELECT DISTINCT ON (
      COALESCE(NULLIF(series_key,''),concat_ws('|',indicator_key,frequency,region,sector,role_family,metric_unit)),
      COALESCE(period_end,observation_date)
    )
      COALESCE(NULLIF(series_key,''),concat_ws('|',indicator_key,frequency,region,sector,role_family,metric_unit)) series_key,
      indicator_key,indicator_name,record_type,
      observation_date,period_start,period_end,period_label,frequency,
      published_at,region,sector,role_family,
      metric_value,metric_value_text,metric_unit,
      comparison_value,change_value,signal_score,confidence_score,
      relevance_score,is_leading_indicator,expected_lag_days,
      insight_summary,job_search_implication,methodology_note,
      source_organization,source_title,source_url,
      is_current,valid_until,is_quantitative,
      first_seen_at,last_confirmed_at,updated_at,source_registry_key
    FROM public.job_market_insights
    WHERE nullif(indicator_key,'') IS NOT NULL
      AND observation_date IS NOT NULL
      AND observation_date <= (now() AT TIME ZONE 'Europe/Stockholm')::date
    ORDER BY
      COALESCE(NULLIF(series_key,''),concat_ws('|',indicator_key,frequency,region,sector,role_family,metric_unit)),
      COALESCE(period_end,observation_date),
      COALESCE(last_confirmed_at,updated_at) DESC NULLS LAST,
      updated_at DESC NULLS LAST,id DESC
  ),
  latest AS (
    SELECT DISTINCT ON (series_key) *
    FROM revisions
    ORDER BY series_key,COALESCE(period_end,observation_date) DESC,
      published_at DESC NULLS LAST
  )
  SELECT jsonb_build_object(
    'as_of',(now() AT TIME ZONE 'Europe/Stockholm')::date,
    'method','external-source-full-history-revision-dedup-v1',
    'historical_observations',(SELECT count(*) FROM revisions),
    'series',(SELECT count(*) FROM latest),
    'history',(SELECT COALESCE(jsonb_agg(to_jsonb(x)
      ORDER BY x.series_key,x.observation_date),'[]'::jsonb) FROM revisions x),
    'latest',(SELECT COALESCE(jsonb_agg(to_jsonb(x)
      ORDER BY x.relevance_score DESC NULLS LAST,x.indicator_name),'[]'::jsonb)
      FROM latest x)
  );
$fn$;
REVOKE ALL ON FUNCTION public.careersite_public_market_history_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_public_market_history_v1() TO anon,authenticated;
