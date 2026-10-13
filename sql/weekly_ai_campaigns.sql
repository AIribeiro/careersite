-- Additive telemetry dimension; historical missing values remain unknown.
ALTER TABLE public.careersite_analytics_events
  ADD COLUMN IF NOT EXISTS utm_content text CHECK (length(utm_content) <= 100);

-- Extend the existing aggregate endpoint, preserving its grants and access model.
DO $migration$
DECLARE definition text;
BEGIN
 definition := pg_get_functiondef('public.careersite_weekly_audio_analytics_v1(text,integer,text)'::regprocedure);
 IF position('weekly_campaign_breakdown' in definition)=0 THEN
 definition := replace(definition, 'RETURN result;', $body$
 -- weekly_campaign_breakdown: one first-view attribution per edition/session.
 WITH scoped AS MATERIALIZED (
   SELECT * FROM public.careersite_analytics_events
   WHERE occurred_at >= since_at AND occurred_at <= until_at
     AND article_slug ~ '^weekly-ai-[0-9]{4}-[0-9]{2}-[0-9]{2}$'
     AND NOT (lower(coalesce(attribution_source,''))='application'
              AND lower(coalesce(attribution_role,''))='test')
 ), first_views AS (
   SELECT DISTINCT ON (article_slug,session_id)
     article_slug,session_id,occurred_at,
     CASE WHEN lower(coalesce(nullif(trim(attribution_source),''),nullif(trim(utm_source),''),'direct/unknown'))='twitter'
       THEN 'x' ELSE lower(coalesce(nullif(trim(attribution_source),''),nullif(trim(utm_source),''),'direct/unknown')) END channel,
     coalesce(nullif(lower(trim(attribution_role)),''),'untagged') role,
     coalesce(nullif(trim(utm_campaign),''),'untagged') campaign,
     coalesce(nullif(trim(utm_content),''),'unrecorded') content
   FROM scoped WHERE event_name='article_view'
   ORDER BY article_slug,session_id,occurred_at,id
 ), visits AS (
   SELECT f.article_slug,f.session_id,f.channel,f.role,f.campaign,f.content,
     bool_or(coalesce(e.article_engaged_ms,0)>=10000) engaged,
     bool_or(e.event_name='audio_start') audio_started,
     bool_or(e.event_name='article_share') shared
   FROM first_views f JOIN scoped e USING(article_slug,session_id)
   WHERE e.occurred_at >= f.occurred_at
   GROUP BY f.article_slug,f.session_id,f.channel,f.role,f.campaign,f.content
 ), grouped AS (
   SELECT article_slug,channel,role,campaign,content,count(*) reads,
     count(*) FILTER(WHERE engaged) engaged_reads,
     count(*) FILTER(WHERE audio_started) audio_starts,
     count(*) FILTER(WHERE shared) share_sessions
   FROM visits GROUP BY article_slug,channel,role,campaign,content
 )
 SELECT result || jsonb_build_object('campaigns',coalesce(
   (SELECT jsonb_agg(to_jsonb(g) ORDER BY reads DESC,article_slug,channel,campaign,content) FROM grouped g),
   '[]'::jsonb)) INTO result;
 RETURN result;
 $body$);
 -- Guard against silently publishing a no-op when the upstream function changes.
 IF position('weekly_campaign_breakdown' in definition)=0 THEN
   RAISE EXCEPTION 'Weekly analytics return marker changed';
 END IF;
 EXECUTE definition;
 END IF;
END;
$migration$;
