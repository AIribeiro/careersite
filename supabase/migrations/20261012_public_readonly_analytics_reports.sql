-- Owner elected to make Analytics accessible without login.
-- Public access is to AGGREGATE reporting functions only. Never grant anon
-- table SELECT, CMS mutation, private job evidence, or predictor actions.
DO $block$
DECLARE
  fn text;
  definition text;
  start_guard int;
  end_guard int;
  guard_fragment text;
  target_names text[] := ARRAY[
    'careersite_analytics_dashboard',
    'careersite_analytics_dashboard_v2',
    'careersite_analytics_articles_v2',
    'careersite_hiring_intelligence_v1',
    'careersite_content_intelligence_v2',
    'careersite_content_intelligence',
    'careersite_behavior_intelligence',
    'careersite_page_sources',
    'careersite_weekly_audio_analytics_v1',
    'careersite_portfolio_signals_daily_v1',
    'careersite_cv_attribution_audit_v1',
    'careersite_attribution_integrity_v1'
  ];
BEGIN
  FOREACH fn IN ARRAY target_names LOOP
    SELECT pg_catalog.pg_get_functiondef(p.oid) INTO definition
    FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname='public' AND p.proname=fn AND p.prokind='f';
    IF definition IS NULL THEN
      RAISE EXCEPTION 'Missing aggregate function: %',fn;
    END IF;

    start_guard := pg_catalog.strpos(lower(definition),'if auth.uid() is null');
    IF start_guard = 0 THEN
      RAISE EXCEPTION 'Expected owner check not found for %; aborting',fn;
    END IF;
    guard_fragment := substring(definition FROM start_guard);
    end_guard := pg_catalog.strpos(lower(guard_fragment),'end if;');
    IF end_guard=0
      OR pg_catalog.strpos(lower(left(guard_fragment,end_guard+6)),
          'owner sign-in required')=0 THEN
      RAISE EXCEPTION 'Unexpected owner check for %; aborting',fn;
    END IF;
    definition := substring(definition FROM 1 FOR start_guard-1)
        || E'-- Public aggregate-only analytics: owner gate removed intentionally.\n  '
        || substring(definition FROM start_guard+end_guard+6);
    EXECUTE definition;
  END LOOP;
END
$block$;

-- Explicitly grant ONLY vetted aggregate reporting entry points.
GRANT EXECUTE ON FUNCTION public.careersite_analytics_dashboard(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_analytics_dashboard_v2(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_analytics_articles_v2(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_intelligence_v1(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_content_intelligence_v2(text,integer,text,jsonb) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_content_intelligence(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_behavior_intelligence(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_page_sources(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_weekly_audio_analytics_v1(text,integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_portfolio_signals_daily_v1(integer,date) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_cv_attribution_audit_v1(integer,text) TO anon;
GRANT EXECUTE ON FUNCTION public.careersite_attribution_integrity_v1(integer,text) TO anon;

-- No anonymous table access to private job history or CMS data.
REVOKE SELECT, INSERT, UPDATE, DELETE ON public.job_search_analytics FROM anon;
REVOKE SELECT, INSERT, UPDATE, DELETE ON public.job_market_insights FROM anon;
