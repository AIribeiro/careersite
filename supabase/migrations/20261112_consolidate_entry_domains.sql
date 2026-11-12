-- Canonical two-domain reporting. Historical and unverified frames are
-- grouped with the Streamlit application only at REPORT time; original rows
-- remain untouched. The assumed portion is exposed as aggregate metadata.
ALTER TABLE public.careersite_analytics_events
  DROP CONSTRAINT IF EXISTS careersite_entry_domain_valid;
ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_entry_domain_valid
  CHECK (entry_domain IS NULL OR entry_domain IN
    ('jairribeiro.com','jairribeiro-ai.streamlit.app'));

DO $policy$
DECLARE original_check text;
DECLARE corrected_check text;
BEGIN
  SELECT pg_get_expr(polwithcheck,polrelid) INTO original_check
  FROM pg_policy
  WHERE polrelid = 'public.careersite_analytics_events'::regclass
    AND polname = 'careersite public insert only';
  IF original_check IS NULL THEN
    RAISE EXCEPTION 'Expected analytics insert policy missing';
  END IF;
  corrected_check := replace(original_check,
    '''jairibeiro-ai.streamlit.app''::text, ', '');
  IF corrected_check = original_check THEN
    RAISE EXCEPTION 'Expected obsolete alias missing in analytics insert policy';
  END IF;
  EXECUTE format('ALTER POLICY %I ON public.careersite_analytics_events WITH CHECK (%s)',
                 'careersite public insert only', corrected_check);
END;
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
  -- Retain the established public aggregate scope, access token and period logic.
  bounds := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);

  WITH canonical AS MATERIALIZED (
    SELECT e.id, e.session_id, e.occurred_at,
           CASE
             WHEN e.entry_domain = 'jairribeiro.com'
                AND e.entry_domain_evidence IN ('direct_host','embed_ancestor','embed_referrer')
               THEN 'jairribeiro.com'
             ELSE 'jairribeiro-ai.streamlit.app'
           END AS domain_label,
           CASE
             WHEN e.entry_domain = 'jairribeiro.com'
               AND e.entry_domain_evidence IN ('direct_host','embed_ancestor','embed_referrer')
               THEN true
             WHEN e.entry_domain = 'jairribeiro-ai.streamlit.app'
               AND e.entry_domain_evidence = 'direct_host'
               THEN true
             ELSE false
           END AS verified_entry,
           CASE
             WHEN nullif(btrim(e.attribution_source),'') IS NOT NULL
               OR nullif(btrim(e.utm_source),'') IS NOT NULL THEN 'Tagged'
             WHEN nullif(btrim(e.referrer_host),'') IS NOT NULL
               AND lower(e.referrer_host) NOT IN
                 ('jairribeiro.com','www.jairribeiro.com',
                  'jairribeiro-ai.streamlit.app','jairibeiro-ai.streamlit.app')
               THEN 'External referrer'
             ELSE 'Direct / source unknown'
           END AS source_evidence
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= (bounds->>'period_since')::timestamptz
      AND e.occurred_at < (bounds->>'period_until')::timestamptz
      AND (e.event_name = 'article_view'
        OR (e.event_name = 'page_view'
          AND e.article_slug IS NULL AND e.content_kind IS DISTINCT FROM 'article'))
      AND NOT (lower(coalesce(e.attribution_source,'')) = 'application'
        AND lower(coalesce(e.attribution_role,'')) = 'test')
  ), sessions AS MATERIALIZED (
    -- Prefer an observed browser domain over an older record in the same tab.
    -- This avoids assigning an otherwise verified visit to the fallback group
    -- solely because the first page event was written before measurement.
    SELECT DISTINCT ON (session_id)
      session_id,domain_label,verified_entry,source_evidence
    FROM canonical
    ORDER BY session_id, verified_entry DESC, occurred_at, id
  ), domains AS (
    SELECT d.domain_label,d.sort_order,
      (SELECT count(*) FROM canonical c WHERE c.domain_label=d.domain_label)::bigint AS views,
      (SELECT count(*) FROM sessions s WHERE s.domain_label=d.domain_label)::bigint AS sessions,
      (SELECT count(*) FROM canonical c
        WHERE c.domain_label=d.domain_label AND c.verified_entry)::bigint AS verified_views,
      (SELECT count(*) FROM sessions s
        WHERE s.domain_label=d.domain_label AND s.verified_entry)::bigint AS verified_sessions,
      (SELECT count(*) FROM canonical c
        WHERE c.domain_label=d.domain_label AND NOT c.verified_entry)::bigint AS assigned_views,
      (SELECT count(*) FROM sessions s
        WHERE s.domain_label=d.domain_label AND NOT s.verified_entry)::bigint AS assigned_sessions
    FROM (VALUES ('jairribeiro.com',1),('jairribeiro-ai.streamlit.app',2))
      d(domain_label,sort_order)
  ), evidence AS (
    SELECT s.domain_label,s.source_evidence,count(*)::bigint AS sessions
    FROM sessions s GROUP BY 1,2
  ), daily AS (
    SELECT to_char((c.occurred_at AT TIME ZONE 'Europe/Stockholm')::date,
                   'YYYY-MM-DD') AS day,
           c.domain_label,count(*)::bigint AS views
    FROM canonical c GROUP BY 1,2
  )
  SELECT pg_catalog.jsonb_build_object(
    'period_since',bounds->'period_since',
    'period_until',bounds->'period_until',
    'total_views',(SELECT count(*) FROM canonical),
    'total_sessions',(SELECT count(*) FROM sessions),
    'domains',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(d)
      ORDER BY d.sort_order) FROM domains d),'[]'::jsonb),
    'source_evidence',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s)
      ORDER BY s.domain_label,s.source_evidence) FROM evidence s),'[]'::jsonb),
    'daily',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x)
      ORDER BY x.day,x.domain_label) FROM daily x),'[]'::jsonb),
    'historical_assignment_policy',
      'unverified traffic consolidated into native streamlit reporting, original evidence preserved'
  ) INTO result;
  RETURN result;
END;
$report$;

REVOKE ALL ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text)
  TO anon,authenticated,service_role;
COMMENT ON FUNCTION public.careersite_entry_domain_report_v1(text,integer,text) IS
'Two reporting addresses. Historical/unresolved sessions are ASSIGNED to native Streamlit in aggregates; raw events are unchanged. Verified and assigned counts remain separate.';
