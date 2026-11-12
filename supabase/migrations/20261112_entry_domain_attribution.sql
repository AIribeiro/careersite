-- Domain-entry analytics for native Streamlit visits and masked custom-domain embeds.
-- Historical rows stay unmeasured; no retroactive domain guesses or visitor identifiers.
ALTER TABLE public.careersite_analytics_events
  ADD COLUMN IF NOT EXISTS entry_domain text,
  ADD COLUMN IF NOT EXISTS entry_domain_evidence text;

ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_entry_domain_valid
    CHECK (entry_domain IS NULL OR entry_domain IN ('jairribeiro.com', 'jairibeiro-ai.streamlit.app')),
  ADD CONSTRAINT careersite_entry_domain_evidence_valid
    CHECK (entry_domain_evidence IS NULL OR entry_domain_evidence IN
      ('direct_host', 'embed_ancestor', 'embed_referrer', 'embedded_unresolved'));

-- Retain every existing insert-policy condition, adding only the two new bounds.
DO $policy$
DECLARE existing_check text;
BEGIN
  SELECT pg_get_expr(polwithcheck, polrelid)
    INTO existing_check
    FROM pg_policy
   WHERE polrelid = 'public.careersite_analytics_events'::regclass
     AND polname = 'careersite public insert only';
  IF existing_check IS NULL THEN
    RAISE EXCEPTION 'Expected analytics insertion policy was not found';
  END IF;
  IF position('entry_domain_evidence' in existing_check) = 0 THEN
    EXECUTE format(
      'ALTER POLICY %I ON public.careersite_analytics_events WITH CHECK ((%s) AND
        (entry_domain IS NULL OR entry_domain IN (%L,%L)) AND
        (entry_domain_evidence IS NULL OR entry_domain_evidence IN (%L,%L,%L,%L)) AND
        (entry_domain IS NOT NULL OR entry_domain_evidence IS NULL OR entry_domain_evidence = %L))',
      'careersite public insert only', existing_check,
      'jairribeiro.com', 'jairibeiro-ai.streamlit.app',
      'direct_host', 'embed_ancestor', 'embed_referrer', 'embedded_unresolved',
      'embedded_unresolved'
    );
  END IF;
END
$policy$;

CREATE OR REPLACE FUNCTION public.careersite_entry_domain_report_v1(
  p_token text DEFAULT 'public-readonly-v1',
  p_days integer DEFAULT 30,
  p_window text DEFAULT 'days'
) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $report$
DECLARE
  bounds jsonb;
  result jsonb;
BEGIN
  -- The established reporting RPC supplies the same time-window boundaries
  -- and excludes a caller-defined access-code bypass.
  bounds := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  WITH canonical AS MATERIALIZED (
    SELECT e.id,e.session_id,e.occurred_at,e.entry_domain,e.entry_domain_evidence,
           CASE WHEN e.event_name = 'article_view' THEN 'Editorial' ELSE 'Portfolio page' END AS content_type,
           CASE
             WHEN nullif(btrim(e.attribution_source),'') IS NOT NULL
               OR nullif(btrim(e.utm_source),'') IS NOT NULL THEN 'Tagged'
             WHEN nullif(btrim(e.referrer_host),'') IS NOT NULL
               AND lower(e.referrer_host) NOT IN ('jairribeiro.com','www.jairribeiro.com','jairibeiro-ai.streamlit.app')
               THEN 'External referrer'
             ELSE 'Direct / source unknown'
           END AS source_evidence
      FROM public.careersite_analytics_events e
     WHERE e.occurred_at >= (bounds->>'period_since')::timestamptz
       AND e.occurred_at < (bounds->>'period_until')::timestamptz
       AND (e.event_name = 'article_view'
         OR (e.event_name = 'page_view'
           AND e.article_slug IS NULL AND e.content_kind IS DISTINCT FROM 'article'))
       AND NOT (lower(coalesce(e.attribution_source,''))='application'
         AND lower(coalesce(e.attribution_role,''))='test')
  ), classified AS MATERIALIZED (
    SELECT *,
      CASE
        WHEN entry_domain = 'jairribeiro.com' THEN 'jairribeiro.com'
        WHEN entry_domain = 'jairibeiro-ai.streamlit.app' THEN 'jairibeiro-ai.streamlit.app'
        WHEN entry_domain_evidence = 'embedded_unresolved' THEN 'Unresolved embedded address'
        ELSE 'Not measured (historical)'
      END AS domain_label
    FROM canonical
  ), sessions AS (
    SELECT DISTINCT ON (session_id)
      session_id,domain_label,entry_domain_evidence,source_evidence
    FROM classified ORDER BY session_id,occurred_at,id
  ), domains AS (
    SELECT d.domain_label,d.sort_order,
           (SELECT count(*) FROM classified c WHERE c.domain_label=d.domain_label)::bigint AS views,
           (SELECT count(*) FROM sessions s WHERE s.domain_label=d.domain_label)::bigint AS sessions
    FROM (VALUES
      ('jairribeiro.com',1),
      ('jairibeiro-ai.streamlit.app',2),
      ('Unresolved embedded address',3),
      ('Not measured (historical)',4)
    ) d(domain_label,sort_order)
  ), evidence AS (
    SELECT s.domain_label,s.source_evidence,count(*)::bigint AS sessions
    FROM sessions s GROUP BY 1,2
  ), daily AS (
    SELECT to_char((c.occurred_at AT TIME ZONE 'Europe/Stockholm')::date,'YYYY-MM-DD') AS day,
           c.domain_label, count(*)::bigint AS views
    FROM classified c GROUP BY 1,2
  )
  SELECT pg_catalog.jsonb_build_object(
    'period_since',bounds->'period_since',
    'period_until',bounds->'period_until',
    'total_views',(SELECT count(*) FROM classified),
    'total_sessions',(SELECT count(*) FROM sessions),
    'domains',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(d) ORDER BY d.sort_order) FROM domains d),'[]'::jsonb),
    'source_evidence',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s) ORDER BY s.domain_label,s.source_evidence) FROM evidence s),'[]'::jsonb),
    'daily',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.day,x.domain_label) FROM daily x),'[]'::jsonb)
  ) INTO result;
  RETURN result;
END;
$report$;
REVOKE ALL ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text) TO anon,authenticated,service_role;
COMMENT ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text) IS
'Aggregate-only first observed domain and source-evidence reporting; historical rows remain unmeasured. No raw session IDs or referrers returned.';
