-- Historical internal QA: retain raw telemetry but remove from reader-facing aggregates.
CREATE TABLE IF NOT EXISTS public.careersite_internal_qa_sessions_v1 (
 session_id uuid PRIMARY KEY,
 reason text NOT NULL CHECK (reason IN ('historical_workflow_path_match')),
 classified_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.careersite_internal_qa_sessions_v1 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.careersite_internal_qa_sessions_v1 FROM PUBLIC, anon, authenticated;

WITH session_paths AS (
 SELECT e.session_id,
  array_agg(e.page ORDER BY e.occurred_at) FILTER (WHERE e.event_name='page_view') AS path,
  max(e.browser_family) FILTER (WHERE e.browser_family IS NOT NULL) AS browser,
  max(e.os_family) FILTER (WHERE e.os_family IS NOT NULL) AS operating_system,
  max(e.timezone) FILTER (WHERE e.timezone IS NOT NULL) AS timezone,
  max(e.country_code) FILTER (WHERE e.country_code IS NOT NULL) AS country
 FROM public.careersite_analytics_events e
 WHERE e.occurred_at >= timestamptz '2026-11-01 00:00:00+01'
 GROUP BY e.session_id
)
INSERT INTO public.careersite_internal_qa_sessions_v1(session_id,reason)
SELECT session_id,'historical_workflow_path_match'
FROM session_paths
WHERE browser='Chrome' AND operating_system='Linux' AND timezone='UTC' AND country='US'
 AND path IN (
  ARRAY['home','impact','thinking','briefings','briefing','ai-data-governance','about','contact','advisory','privacy','briefing','briefing','briefing']::text[],
  ARRAY['home','impact','thinking','briefings','briefing','ai-data-governance','about','contact','briefing','briefing','briefing','briefing','home']::text[],
  ARRAY['home','impact','briefings','briefing','ai-data-governance','about','contact','briefing','briefing','briefing','briefing','home']::text[]
 )
ON CONFLICT(session_id) DO NOTHING;

CREATE OR REPLACE VIEW public.careersite_reporting_events_v1
WITH (security_invoker=true) AS
SELECT e.*
FROM public.careersite_analytics_events AS e
WHERE NOT EXISTS (
 SELECT 1 FROM public.careersite_internal_qa_sessions_v1 AS qa
 WHERE qa.session_id=e.session_id
)
AND NOT (
 lower(coalesce(e.attribution_source,''))='internal_qa'
 AND lower(coalesce(e.attribution_role,''))='smoke'
);
REVOKE ALL ON public.careersite_reporting_events_v1 FROM PUBLIC,anon,authenticated;

-- Rewire only read-only aggregate reports, not collection or reset functions.
DO $$
DECLARE f record; definition text; updated integer:=0;
BEGIN
 FOR f IN SELECT p.oid,p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='public' AND p.proname=ANY(ARRAY[
   'careersite_analytics_dashboard','careersite_analytics_dashboard_v2',
   'careersite_analytics_articles','careersite_analytics_articles_v2',
   'careersite_content_intelligence','careersite_content_intelligence_v2',
   'careersite_lifetime_views_v1','careersite_public_article_reads',
   'careersite_thinking_rank_windows_v2','careersite_thinking_recent_views_v1',
   'careersite_featured_article_candidate','careersite_page_sources',
   'careersite_entry_domain_report_v1','careersite_behavior_intelligence',
   'careersite_weekly_audio_analytics_v1','careersite_portfolio_signals_daily_v1',
   'careersite_hiring_predictor_actions_v1','__owner_inner_careersite_hiring_intelligence_v1'
  ])
 LOOP
  definition:=pg_get_functiondef(f.oid);
  IF position('public.careersite_analytics_events' IN definition)=0 THEN
   RAISE EXCEPTION 'Expected analytics source missing in %',f.proname;
  END IF;
  EXECUTE replace(definition,'public.careersite_analytics_events','public.careersite_reporting_events_v1');
  updated:=updated+1;
 END LOOP;
 IF updated<>18 THEN RAISE EXCEPTION 'Unexpected report function count: %',updated; END IF;
END $$;
