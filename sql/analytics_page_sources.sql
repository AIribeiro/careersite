-- Aggregate-only page attribution; same public analytics access contract.
CREATE OR REPLACE FUNCTION public.careersite_page_sources(p_token text,p_days integer DEFAULT 30,p_window text DEFAULT 'days')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE base jsonb; result jsonb;
BEGIN
 base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
 WITH views AS (
 SELECT id,occurred_at,page,session_id,
 coalesce(nullif(btrim(attribution_source),''),nullif(btrim(utm_source),''),'direct/unknown') AS tag
 FROM public.careersite_analytics_events
 WHERE occurred_at >= (base->>'period_since')::timestamptz AND occurred_at <= now()
 AND event_name='page_view' AND article_slug IS NULL
 AND content_kind IS DISTINCT FROM 'article'
 AND (content_kind='page' OR page IS DISTINCT FROM 'thinking')
 AND page IS NOT NULL
 AND NOT(lower(coalesce(attribution_source,''))='application' AND lower(coalesce(attribution_role,''))='test')
 ), visits AS (
 SELECT DISTINCT ON(page,session_id) page,session_id,tag
 FROM views ORDER BY page,session_id,occurred_at,id
 ), grouped AS (
 SELECT page,lower(tag) AS attribution_source,count(*) AS sessions FROM visits GROUP BY page,lower(tag)
 )
 SELECT jsonb_build_object('sources',coalesce(jsonb_agg(to_jsonb(grouped) ORDER BY sessions DESC,page,attribution_source),'[]'::jsonb),
 'period_since',base->'period_since') INTO result FROM grouped;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_page_sources(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_page_sources(text,integer,text) TO anon,authenticated,service_role;
