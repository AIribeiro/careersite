-- Aggregate-only, public article readership for the Thinking section.
-- One recorded article visit per browser session; no raw visitor data leaves the database.
CREATE OR REPLACE FUNCTION public.careersite_public_article_reads()
RETURNS TABLE(slug text, reads bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $function$
  SELECT a.slug, count(DISTINCT e.session_id)::bigint AS reads
  FROM public.careersite_articles AS a
  LEFT JOIN public.careersite_analytics_events AS e
    ON e.article_slug = a.slug
   AND e.event_name = 'article_view'
   AND e.session_id IS NOT NULL
   AND e.occurred_at >= coalesce(
     (SELECT c.reset_at FROM public.careersite_analytics_admin_config AS c LIMIT 1),
     '-infinity'::timestamptz
   )
  WHERE a.status = 'published'
  GROUP BY a.slug;
$function$;
REVOKE ALL ON FUNCTION public.careersite_public_article_reads() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_public_article_reads() TO anon, authenticated;
COMMENT ON FUNCTION public.careersite_public_article_reads()
IS 'Aggregate published-article visits (distinct browser sessions with article_view), since current analytics reset. No visitor data returned.';
