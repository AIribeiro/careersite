-- Lightweight public aggregate for lifetime view denominators.
-- Preserves canonical event classification and anonymous test exclusions.
-- Scope follows the existing analytics reset marker; never includes raw visitors.
CREATE OR REPLACE FUNCTION public.careersite_lifetime_views_v1(p_token text)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  result jsonb;
BEGIN
  -- This endpoint exposes aggregate public content counts only.
  IF p_token IS DISTINCT FROM 'public-readonly-v1' THEN
    RAISE EXCEPTION 'invalid analytics access code' USING ERRCODE = '28000';
  END IF;

  WITH scoped AS MATERIALIZED (
    SELECT e.event_name, e.content_kind, e.article_slug, e.page, e.session_id,
      CASE
        WHEN e.content_kind='article'
          OR (e.article_slug IS NOT NULL AND e.event_name<>'article_click')
          THEN 'article'
        WHEN e.content_kind='page' THEN 'page'
        WHEN e.page='thinking' THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= (
      SELECT reset_at FROM public.careersite_analytics_admin_config
      WHERE singleton = true
    )
      AND e.occurred_at < now()
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
      AND e.event_name IN ('page_view','article_view')
  ),
  canonical AS MATERIALIZED (
    SELECT *
    FROM scoped e
    WHERE e.event_name='article_view'
       OR (e.event_name='page_view' AND e.kind <> 'article')
  ),
  article_totals AS (
    SELECT article_slug AS content, count(*) AS views,
           count(DISTINCT session_id) AS sessions
    FROM canonical
    WHERE kind='article' AND event_name='article_view'
      AND article_slug IS NOT NULL
    GROUP BY article_slug
  )
  SELECT jsonb_build_object(
    'quality', jsonb_build_object(
      'site_views', (SELECT count(*) FROM canonical),
      'article_views', (SELECT count(*) FROM canonical WHERE kind='article')
    ),
    'performance', coalesce(
      (SELECT jsonb_agg(
          jsonb_build_object(
            'kind','article',
            'content',content,
            'views',views,
            'sessions',sessions
          )
          ORDER BY views DESC, content
       ) FROM article_totals),
      '[]'::jsonb
    )
  ) INTO result;

  RETURN result;
END;
$function$
;
REVOKE ALL ON FUNCTION public.careersite_lifetime_views_v1(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_lifetime_views_v1(text) TO anon, authenticated;
