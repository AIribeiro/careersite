-- Aggregated quality breakdown for the private dashboard. No raw session IDs are exposed.
CREATE OR REPLACE FUNCTION public.careersite_traffic_quality_audit_v1(
 p_token text DEFAULT 'public-readonly-v1', p_days integer DEFAULT 30, p_window text DEFAULT 'days'
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path TO ''
AS $function$
DECLARE bounds jsonb; result jsonb;
BEGIN
 bounds:=public.careersite_analytics_dashboard(p_token,p_days,p_window);
 WITH session_events AS MATERIALIZED (
  SELECT e.session_id,
   count(*) AS events,
   count(*) FILTER(WHERE e.event_name IN ('page_view','article_view')) AS content_views,
   bool_or(coalesce(e.browser_automation,false)) AS webdriver_seen,
   bool_or(lower(coalesce(e.attribution_source,''))='internal_qa'
     AND lower(coalesce(e.attribution_role,''))='smoke') AS tagged_qa
  FROM public.careersite_analytics_events e
  WHERE e.occurred_at >= (bounds->>'period_since')::timestamptz
    AND e.occurred_at < (bounds->>'period_until')::timestamptz
  GROUP BY e.session_id
 ), categories AS (
  SELECT s.*, CASE
   WHEN qa.session_id IS NOT NULL OR s.tagged_qa THEN 'internal_qa'
   WHEN bot.session_id IS NOT NULL OR s.webdriver_seen THEN 'suspected_automation'
   ELSE 'unclassified' END AS traffic_class
  FROM session_events s
  LEFT JOIN public.careersite_internal_qa_sessions_v1 qa USING(session_id)
  LEFT JOIN public.careersite_suspected_automation_sessions_v1 bot USING(session_id)
 )
 SELECT jsonb_build_object(
  'raw_sessions',count(*),
  'raw_events',coalesce(sum(events),0),
  'raw_content_views',coalesce(sum(content_views),0),
  'internal_qa_sessions',count(*) FILTER(WHERE traffic_class='internal_qa'),
  'internal_qa_events',coalesce(sum(events) FILTER(WHERE traffic_class='internal_qa'),0),
  'internal_qa_views',coalesce(sum(content_views) FILTER(WHERE traffic_class='internal_qa'),0),
  'suspected_automation_sessions',count(*) FILTER(WHERE traffic_class='suspected_automation'),
  'suspected_automation_events',coalesce(sum(events) FILTER(WHERE traffic_class='suspected_automation'),0),
  'suspected_automation_views',coalesce(sum(content_views) FILTER(WHERE traffic_class='suspected_automation'),0),
  'unclassified_sessions',count(*) FILTER(WHERE traffic_class='unclassified'),
  'unclassified_events',coalesce(sum(events) FILTER(WHERE traffic_class='unclassified'),0),
  'unclassified_views',coalesce(sum(content_views) FILTER(WHERE traffic_class='unclassified'),0)
 ) INTO result FROM categories;
 RETURN coalesce(result,'{}'::jsonb) || jsonb_build_object(
  'period_since',bounds->'period_since','period_until',bounds->'period_until',
  'classification_note','Unclassified does not mean verified human. Suspected automation is a conservative browser-automation signal or repeated sub-10-second technical cohort.'
 );
END;
$function$;
REVOKE ALL ON FUNCTION public.careersite_traffic_quality_audit_v1(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_traffic_quality_audit_v1(text,integer,text)
 TO anon,authenticated,service_role;
NOTIFY pgrst, 'reload schema';
