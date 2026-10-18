-- Reduce automatic new-article highlight from 48 to 24 hours.
-- Keep five-minute reconciliation and readership-based fallback unchanged.
CREATE OR REPLACE FUNCTION public.careersite_featured_article_candidate(p_as_of timestamp with time zone DEFAULT now())
 RETURNS uuid
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  WITH reading_visits AS (
    SELECT e.article_slug, count(DISTINCT e.session_id)::bigint AS reads
    FROM public.careersite_analytics_events e
    WHERE e.event_name = 'article_view'
      AND e.article_slug IS NOT NULL
      AND e.session_id IS NOT NULL
      AND e.occurred_at >= coalesce(
        (SELECT c.reset_at
         FROM public.careersite_analytics_admin_config c LIMIT 1),
        '-infinity'::timestamptz
      )
    GROUP BY e.article_slug
  ), candidates AS (
    SELECT a.id, a.published_at,
           (a.published_at <= p_as_of
            AND p_as_of < a.published_at + interval '24 hours') AS within_window,
           coalesce(r.reads, 0)::bigint AS reads
    FROM public.careersite_articles a
    LEFT JOIN reading_visits r ON r.article_slug = a.slug
    WHERE a.status = 'published'
      AND coalesce(a.kind, '') <> 'Weekly Brief'
      AND coalesce(a.category, '') <> 'Weekly AI'
  )
  SELECT id
  FROM candidates
  ORDER BY within_window DESC NULLS LAST,
           CASE WHEN within_window THEN published_at END DESC NULLS LAST,
           CASE WHEN NOT within_window THEN reads END DESC NULLS LAST,
           published_at DESC NULLS LAST,
           id
  LIMIT 1
$function$;
