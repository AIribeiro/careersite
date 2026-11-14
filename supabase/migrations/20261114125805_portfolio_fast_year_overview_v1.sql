-- Fast, aggregate-only Year and All portfolio overview.
-- Read-only: raw events and existing traffic classification remain untouched.
CREATE OR REPLACE FUNCTION public.careersite_portfolio_overview_fast_v1(
  p_token text DEFAULT 'public-readonly-v1',
  p_window text DEFAULT 'this_year'
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE SECURITY DEFINER
SET search_path TO ''
AS $fn$
DECLARE
  v_since timestamptz;
  v_until timestamptz := now();
  v_reset timestamptz;
  v_result jsonb;
BEGIN
  IF p_token IS DISTINCT FROM 'public-readonly-v1' THEN
    RAISE EXCEPTION 'invalid analytics access code' USING ERRCODE='28000';
  END IF;
  IF p_window NOT IN ('this_year','all') THEN
    RAISE EXCEPTION 'unsupported overview reporting window' USING ERRCODE='22023';
  END IF;
  SELECT c.reset_at INTO v_reset
    FROM public.careersite_analytics_admin_config c WHERE c.singleton = true;
  IF p_window='this_year' THEN
    v_since := date_trunc('year',now() AT TIME ZONE 'Europe/Stockholm')
                 AT TIME ZONE 'Europe/Stockholm';
  ELSE
    v_since := '-infinity'::timestamptz;
  END IF;
  v_since := greatest(v_since,coalesce(v_reset,v_since));

  WITH canonical AS MATERIALIZED (
    SELECT e.session_id, e.event_name,
      CASE
        WHEN e.event_name='article_view' THEN 'article'
        WHEN e.page='thinking' AND e.content_kind IS NULL THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind,
      CASE WHEN e.event_name='article_view' THEN e.article_slug ELSE e.page END AS content,
      coalesce(e.engaged_ms,0) AS engaged_ms
    FROM public.careersite_reporting_events_v1 e
    WHERE e.occurred_at >= v_since
      AND e.occurred_at < v_until
      AND (
        (e.event_name='article_view' AND e.article_slug IS NOT NULL)
        OR (e.event_name='page_view'
            AND e.content_kind IS DISTINCT FROM 'article'
            AND e.article_slug IS NULL)
      )
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
  ),
  performance AS (
    SELECT kind,content, count(*)::bigint AS views,
       count(DISTINCT session_id)::bigint AS sessions,
       count(DISTINCT session_id) FILTER(WHERE engaged_ms>=10000)::bigint AS engaged_sessions
    FROM canonical
    WHERE content IS NOT NULL AND kind <> 'legacy_thinking'
    GROUP BY kind,content
  ),
  quality AS (
    SELECT count(*)::bigint AS site_views,
      count(*) FILTER(WHERE kind='page')::bigint AS page_views,
      count(*) FILTER(WHERE kind='article')::bigint AS article_views,
      count(*) FILTER(WHERE kind='legacy_thinking')::bigint AS legacy_thinking_views,
      count(DISTINCT session_id)::bigint AS site_sessions,
      count(DISTINCT session_id) FILTER(WHERE kind='page')::bigint AS page_sessions,
      count(DISTINCT session_id) FILTER(WHERE kind='article')::bigint AS article_sessions
    FROM canonical
  )
  SELECT jsonb_build_object(
    'period_since',v_since,
    'period_until',v_until,
    'period_label',CASE WHEN p_window='this_year' THEN 'This year' ELSE 'All' END,
    'quality',(SELECT to_jsonb(q) FROM quality q),
    'performance',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY views DESC,content) FROM performance p),'[]'::jsonb),
    'fast_overview',true,
    'generated_at',now()
  ) INTO v_result;
  RETURN v_result;
END;
$fn$;

REVOKE ALL ON FUNCTION public.careersite_portfolio_overview_fast_v1(text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_portfolio_overview_fast_v1(text,text)
  TO anon,authenticated,service_role;
NOTIFY pgrst,'reload schema';
