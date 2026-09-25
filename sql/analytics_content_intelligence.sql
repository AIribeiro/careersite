-- Additive upgrade. Existing events, RPCs, grants and reset baseline are retained.
ALTER TABLE public.careersite_analytics_events
 ADD COLUMN IF NOT EXISTS content_kind text CHECK (content_kind IN ('page','article')),
 ADD COLUMN IF NOT EXISTS tracking_version integer CHECK (tracking_version BETWEEN 1 AND 10),
 ADD COLUMN IF NOT EXISTS page_engaged_ms integer CHECK (page_engaged_ms BETWEEN 0 AND 86400000),
 ADD COLUMN IF NOT EXISTS scroll_depth integer CHECK (scroll_depth BETWEEN 0 AND 100);

-- This aggregate-only endpoint follows the established public readonly reporting
-- contract. Raw events remain inaccessible to anon; no session IDs are returned.
CREATE OR REPLACE FUNCTION public.careersite_content_intelligence(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE base jsonb; since_at timestamptz; result jsonb;
BEGIN
 base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
 since_at := (base->>'period_since')::timestamptz;
 WITH scoped AS MATERIALIZED (
  SELECT *,
   CASE WHEN content_kind='article' OR (article_slug IS NOT NULL AND event_name<>'article_click') THEN 'article'
        WHEN content_kind='page' THEN 'page'
        WHEN page='thinking' THEN 'legacy_thinking' ELSE 'page' END AS kind
  FROM public.careersite_analytics_events
  WHERE occurred_at >= since_at AND occurred_at <= now()
   AND NOT (lower(coalesce(attribution_source,''))='application' AND lower(coalesce(attribution_role,''))='test')
 ), views AS MATERIALIZED (
  SELECT *, CASE WHEN event_name='article_view' THEN 'article:'||article_slug ELSE page END AS content
  FROM scoped WHERE event_name='article_view' OR (event_name='page_view' AND kind<>'article')
 ), content_sessions AS (
  SELECT kind, page, CASE WHEN kind='article' THEN article_slug END AS slug, session_id,
   count(*) FILTER(WHERE event_name=CASE WHEN kind='article' THEN 'article_view' ELSE 'page_view' END) AS views,
   min(occurred_at) FILTER(WHERE event_name=CASE WHEN kind='article' THEN 'article_view' ELSE 'page_view' END) AS opened,
   max(CASE WHEN kind='article' THEN article_engaged_ms ELSE page_engaged_ms END) AS active_ms,
   max(scroll_depth) AS depth,
   bool_or(tracking_version=3) AS measured,
   count(*) FILTER(WHERE event_name='article_share') AS shares,
   bool_or(event_name IN ('cv_download','email_click','linkedin_click')) AS action_on_content
  FROM scoped WHERE event_name<>'article_click'
  GROUP BY kind,page,CASE WHEN kind='article' THEN article_slug END,session_id
 ), quality AS MATERIALIZED (
  SELECT c.*,
   EXISTS(SELECT 1 FROM scoped e WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened AND e.event_name='cv_download') AS later_cv,
   EXISTS(SELECT 1 FROM scoped e WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened AND e.event_name IN ('email_click','linkedin_click')) AS later_contact,
   EXISTS(SELECT 1 FROM views v WHERE v.session_id=c.session_id AND v.occurred_at>c.opened AND v.kind='page' AND v.page<>'thinking') AS later_portfolio
  FROM content_sessions c WHERE views>0
 ), performance AS (
  SELECT kind,coalesce(slug,page) AS content,
   count(*) AS sessions, sum(views) AS views,
   count(*) FILTER(WHERE active_ms>=10000) AS engaged_sessions,
   count(*) FILTER(WHERE active_ms>=5000) AS confirmed_sessions,
   round((avg(active_ms) FILTER(WHERE active_ms>=5000))/1000.0,1) AS avg_active_seconds,
   count(*) FILTER(WHERE depth IS NOT NULL) AS depth_measured_sessions,
   count(*) FILTER(WHERE depth>=50) AS halfway_sessions,
   count(*) FILTER(WHERE depth>=90) AS bottom_sessions,
   count(*) FILTER(WHERE depth>=90 AND active_ms>=30000) AS deep_read_sessions,
   sum(shares) AS shares,
   count(*) FILTER(WHERE shares>0) AS sharing_sessions,
   count(*) FILTER(WHERE action_on_content) AS action_sessions,
   count(*) FILTER(WHERE later_cv) AS later_cv_sessions,
   count(*) FILTER(WHERE later_contact) AS later_contact_sessions,
   count(*) FILTER(WHERE later_portfolio) AS later_portfolio_sessions
  FROM quality GROUP BY kind,coalesce(slug,page)
 ), ordered_views AS (
  SELECT *,lead(content) OVER(PARTITION BY session_id ORDER BY occurred_at,id) AS next_content
  FROM views
 ), journeys AS (
  SELECT content AS from_content,next_content AS to_content,count(*) AS transitions,count(DISTINCT session_id) AS sessions
  FROM ordered_views WHERE next_content IS NOT NULL AND next_content<>content
  GROUP BY content,next_content ORDER BY sessions DESC LIMIT 30
 ), session_sources AS (
  SELECT session_id,
   (array_agg(coalesce(attribution_source,utm_source,'direct/unknown') ORDER BY occurred_at,id))[1] AS channel,
   (array_agg(coalesce(utm_campaign,attribution_role,'untagged') ORDER BY occurred_at,id))[1] AS campaign,
   bool_or(event_name='cv_download') AS cv,
   bool_or(event_name IN ('email_click','linkedin_click')) AS contact,
   bool_or(event_name='article_view') AS reader,
   max(engaged_ms)>=10000 AS engaged
  FROM scoped GROUP BY session_id
 ), campaigns AS (
  SELECT channel,campaign,count(*) AS sessions,count(*) FILTER(WHERE engaged) AS engaged_sessions,
   count(*) FILTER(WHERE reader) AS reader_sessions,count(*) FILTER(WHERE cv) AS cv_sessions,
   count(*) FILTER(WHERE contact) AS contact_sessions
  FROM session_sources GROUP BY channel,campaign ORDER BY sessions DESC LIMIT 40
 ), entry_exit AS (
  SELECT session_id,(array_agg(content ORDER BY occurred_at,id))[1] AS entry,
   (array_agg(content ORDER BY occurred_at DESC,id DESC))[1] AS last_content,
   count(*) AS views FROM views GROUP BY session_id
 ), entrances AS (
  SELECT entry AS content,count(*) AS sessions,count(*) FILTER(WHERE views=1) AS single_view_sessions
  FROM entry_exit GROUP BY entry ORDER BY sessions DESC
 ), exits AS (
  SELECT last_content AS content,count(*) AS sessions FROM entry_exit GROUP BY last_content ORDER BY sessions DESC
 )
 SELECT jsonb_build_object(
  'generated_at',now(),'period_since',since_at,'period_label',base->'period_label',
  'performance',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY sessions DESC) FROM performance p),'[]'::jsonb),
  'journeys',coalesce((SELECT jsonb_agg(to_jsonb(j)) FROM journeys j),'[]'::jsonb),
  'campaigns',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM campaigns c),'[]'::jsonb),
  'entrances',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM entrances e),'[]'::jsonb),
  'exits',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM exits e),'[]'::jsonb),
  'quality',jsonb_build_object(
   'last_event_at',(SELECT max(occurred_at) FROM scoped),
   'new_measurement_since',(SELECT min(occurred_at) FROM scoped WHERE tracking_version=3),
   'measured_content_sessions',(SELECT count(*) FROM quality WHERE measured),
   'content_sessions',(SELECT count(*) FROM quality),
   'legacy_thinking_views',(SELECT count(*) FROM views WHERE kind='legacy_thinking'),
   'contact_sessions',(SELECT count(*) FROM session_sources WHERE contact),
   'page_sessions',(SELECT count(DISTINCT session_id) FROM views WHERE kind='page'),
   'page_views',(SELECT count(*) FROM views WHERE kind='page'),
   'article_sessions',(SELECT count(DISTINCT session_id) FROM views WHERE kind='article'),
   'article_views',(SELECT count(*) FROM views WHERE kind='article'))
 ) INTO result;
 RETURN result;
END; $$;
REVOKE ALL ON FUNCTION public.careersite_content_intelligence(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_content_intelligence(text,integer,text) TO anon,authenticated,service_role;
