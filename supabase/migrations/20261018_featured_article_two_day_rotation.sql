-- Automatic featured article rotation: each new publication leads for exactly
-- 48 hours, then the published essay with the most recorded article sessions wins.
-- Weekly AI briefs remain in their own independent featured slot.
-- The landing page evaluates this policy at read time; pg_cron reconciles the
-- persisted CMS flag within 5 minutes without relying on website traffic.

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
            AND p_as_of < a.published_at + interval '48 hours') AS within_window,
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
$function$


CREATE OR REPLACE FUNCTION public.careersite_sync_featured_article()
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  v_winner uuid;
BEGIN
  v_winner := public.careersite_featured_article_candidate(now());
  UPDATE public.careersite_articles a
  SET featured = (
    a.status = 'published' AND a.id = v_winner
  )
  WHERE a.featured IS DISTINCT FROM (
    a.status = 'published' AND a.id = v_winner
  );
  RETURN v_winner;
END
$function$


CREATE OR REPLACE FUNCTION public.careersite_articles_touch()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
BEGIN
  IF TG_OP = 'INSERT' THEN
    NEW.updated_at := now();
  ELSE
    IF NEW.status = 'published' AND OLD.status IS DISTINCT FROM NEW.status THEN
      NEW.published_at := now();
    END IF;
    IF (to_jsonb(NEW) - 'updated_at' - 'featured')
       IS DISTINCT FROM
       (to_jsonb(OLD) - 'updated_at' - 'featured') THEN
      NEW.updated_at := now();
    ELSE
      NEW.updated_at := OLD.updated_at;
    END IF;
  END IF;
  IF NEW.status = 'published' AND NEW.published_at IS NULL THEN
    NEW.published_at := now();
  END IF;
  RETURN NEW;
END
$function$


CREATE OR REPLACE FUNCTION public.careersite_refresh_feature_on_publish()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status = 'published' THEN
      PERFORM public.careersite_sync_featured_article();
    END IF;
  ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
    PERFORM public.careersite_sync_featured_article();
  END IF;
  RETURN NULL;
END
$function$


DROP TRIGGER IF EXISTS careersite_featured_on_publish_trg ON public.careersite_articles;
CREATE TRIGGER careersite_featured_on_publish_trg
AFTER INSERT OR UPDATE OF status ON public.careersite_articles
FOR EACH ROW EXECUTE FUNCTION public.careersite_refresh_feature_on_publish();

REVOKE ALL ON FUNCTION public.careersite_featured_article_candidate(timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.careersite_sync_featured_article() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.careersite_refresh_feature_on_publish() FROM PUBLIC;

SELECT cron.schedule('careersite-featured-rotation', '*/5 * * * *',
  'SELECT public.careersite_sync_featured_article();');
SELECT public.careersite_sync_featured_article();
