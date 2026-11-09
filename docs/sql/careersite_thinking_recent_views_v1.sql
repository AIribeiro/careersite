-- Supabase migration applied to rnqweoxtynelfirffmlr on 2026-11-09.
-- Public aggregate-only readership used for hourly Thinking section ordering.
-- This deliberately returns no article slugs, session IDs, visitor profiles
-- or attribution. A view means one recorded article_view event (not a session).
CREATE OR REPLACE FUNCTION public.careersite_thinking_recent_views_v1()
RETURNS TABLE(section_key text, views bigint, window_start timestamptz, as_of timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $function$
  WITH bounds AS (
    SELECT now() AS checked_at,
           greatest(
             now() - interval '60 minutes',
             coalesce(
               (SELECT c.reset_at FROM public.careersite_analytics_admin_config c LIMIT 1),
               '-infinity'::timestamptz
             )
           ) AS lower_bound
  ),
  totals AS (
    SELECT CASE
      WHEN a.kind = 'Weekly Brief' OR a.category = 'Weekly AI' THEN 'weekly_ai'
      WHEN a.kind = 'Executive Briefing' THEN 'briefings'
      ELSE 'articles'
    END AS section_key,
    count(*)::bigint AS views
    FROM public.careersite_analytics_events e
    JOIN public.careersite_articles a ON a.slug = e.article_slug
    CROSS JOIN bounds b
    WHERE e.event_name = 'article_view'
      AND e.page IN ('thinking', 'briefing')
      AND e.occurred_at >= b.lower_bound
      AND e.occurred_at <= b.checked_at
      AND a.status = 'published'
    GROUP BY 1
  )
  SELECT names.section_key,
         coalesce(t.views,0)::bigint AS views,
         b.checked_at - interval '60 minutes' AS window_start,
         b.checked_at AS as_of
  FROM (VALUES ('weekly_ai'::text), ('briefings'::text), ('articles'::text))
    AS names(section_key)
  CROSS JOIN bounds b
  LEFT JOIN totals t ON t.section_key = names.section_key;
$function$;

-- Deliberate, tightly bounded SECURITY DEFINER public API:
-- exactly three aggregated counts, with no free-form arguments or row data.
-- search_path is empty and all relations are schema-qualified.
REVOKE ALL ON FUNCTION public.careersite_thinking_recent_views_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_thinking_recent_views_v1()
  TO anon, authenticated, service_role;
