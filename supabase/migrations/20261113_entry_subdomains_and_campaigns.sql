-- Branded subdomains use the same first-party domain family but are
-- retained as distinct observed hostnames. Never promote an unverified frame
-- or a lookalike hostname into the branded category.
-- Raw historical events remain untouched and continue to report as
-- assigned Streamlit native sessions, with that distinction kept visible.

ALTER TABLE public.careersite_analytics_events
  DROP CONSTRAINT IF EXISTS careersite_entry_domain_valid;
ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_entry_domain_valid
  CHECK (
    entry_domain IS NULL OR entry_domain = 'jairribeiro-ai.streamlit.app'
    OR (
      length(entry_domain) <= 253
      AND entry_domain ~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'
    )
  );

-- Preserve every existing insert-policy requirement. Replace ONLY its
-- entry-domain allowlist; do not broaden event, PII or attribution rules.
DO $policy$
DECLARE
  old_check text;
  old_clause text := $old$((entry_domain IS NULL) OR (entry_domain = ANY (ARRAY['jairribeiro.com'::text, 'jairribeiro-ai.streamlit.app'::text])))$old$;
  new_clause text := $new$((entry_domain IS NULL) OR (entry_domain = 'jairribeiro-ai.streamlit.app'::text) OR ((length(entry_domain) <= 253) AND (entry_domain ~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'::text)))$new$;
BEGIN
  SELECT pg_get_expr(polwithcheck,polrelid) INTO old_check
  FROM pg_policy
  WHERE polrelid='public.careersite_analytics_events'::regclass
    AND polname='careersite public insert only';
  IF old_check IS NULL THEN
    RAISE EXCEPTION 'Analytics insert policy missing';
  ELSIF position(old_clause in old_check) > 0 THEN
    EXECUTE format('ALTER POLICY %I ON public.careersite_analytics_events WITH CHECK (%s)',
                   'careersite public insert only',
                   replace(old_check,old_clause,new_clause));
  ELSIF position(new_clause in old_check) = 0 THEN
    RAISE EXCEPTION 'Unrecognized analytics insert policy; not changing existing checks';
  END IF;
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
  -- Reuse existing public aggregation's validation, periods and test scope.
  bounds := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  WITH canonical AS MATERIALIZED (
    SELECT
      e.id,e.session_id,e.occurred_at,
      CASE WHEN e.entry_domain ~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'
             AND e.entry_domain_evidence IN ('direct_host','embed_ancestor','embed_referrer')
        THEN 'jairribeiro.com'
        ELSE 'jairribeiro-ai.streamlit.app'
      END AS domain_label,
      CASE WHEN e.entry_domain ~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'
             AND e.entry_domain_evidence IN ('direct_host','embed_ancestor','embed_referrer')
        THEN e.entry_domain
        ELSE 'jairribeiro-ai.streamlit.app'
      END AS host_label,
      CASE WHEN e.entry_domain ~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'
             AND e.entry_domain_evidence IN ('direct_host','embed_ancestor','embed_referrer')
             THEN true
           WHEN e.entry_domain = 'jairribeiro-ai.streamlit.app'
             AND e.entry_domain_evidence = 'direct_host' THEN true
           ELSE false
      END AS verified_entry,
      CASE WHEN nullif(btrim(e.attribution_source),'') IS NOT NULL
                  OR nullif(btrim(e.utm_source),'') IS NOT NULL
                  THEN 'Tagged'
           WHEN nullif(btrim(e.referrer_host),'') IS NOT NULL
             AND lower(e.referrer_host) NOT IN
                 ('jairribeiro-ai.streamlit.app','jairibeiro-ai.streamlit.app')
             AND lower(e.referrer_host)
               !~ '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*jairribeiro\.com$'
               THEN 'External referrer'
           ELSE 'Direct / source unknown'
      END AS source_evidence,
      nullif(btrim(e.attribution_source),'') AS attribution_source,
      nullif(btrim(e.utm_source),'') AS utm_source,
      nullif(btrim(e.utm_medium),'') AS utm_medium,
      nullif(btrim(e.utm_campaign),'') AS utm_campaign,
      nullif(btrim(e.utm_content),'') AS utm_content
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= (bounds->>'period_since')::timestamptz
      AND e.occurred_at < (bounds->>'period_until')::timestamptz
      AND (e.event_name = 'article_view'
        OR (e.event_name = 'page_view'
            AND e.article_slug IS NULL
            AND e.content_kind IS DISTINCT FROM 'article'))
      AND NOT (lower(coalesce(e.attribution_source,'')) = 'application'
        AND lower(coalesce(e.attribution_role,'')) = 'test')
  ), sessions AS MATERIALIZED (
    SELECT DISTINCT ON (session_id)
      session_id,domain_label,host_label,verified_entry,source_evidence,
      attribution_source,utm_source,utm_medium,utm_campaign,utm_content
    FROM canonical
    ORDER BY session_id,verified_entry DESC,occurred_at,id
  ), domains AS (
    SELECT d.domain_label,d.sort_order,
      (SELECT count(*) FROM canonical c WHERE c.domain_label=d.domain_label)::bigint AS views,
      (SELECT count(*) FROM sessions s WHERE s.domain_label=d.domain_label)::bigint AS sessions,
      (SELECT count(*) FROM canonical c WHERE c.domain_label=d.domain_label AND c.verified_entry)::bigint AS verified_views,
      (SELECT count(*) FROM sessions s WHERE s.domain_label=d.domain_label AND s.verified_entry)::bigint AS verified_sessions,
      (SELECT count(*) FROM canonical c WHERE c.domain_label=d.domain_label AND NOT c.verified_entry)::bigint AS assigned_views,
      (SELECT count(*) FROM sessions s WHERE s.domain_label=d.domain_label AND NOT s.verified_entry)::bigint AS assigned_sessions
    FROM (VALUES ('jairribeiro.com',1),('jairribeiro-ai.streamlit.app',2))
      d(domain_label,sort_order)
  ), hosts AS (
    SELECT h.host_label,h.domain_label,
      (SELECT count(*) FROM canonical c WHERE c.host_label=h.host_label)::bigint AS views,
      (SELECT count(*) FROM sessions s WHERE s.host_label=h.host_label)::bigint AS sessions,
      (SELECT count(*) FROM canonical c WHERE c.host_label=h.host_label AND c.verified_entry)::bigint AS verified_views,
      (SELECT count(*) FROM canonical c WHERE c.host_label=h.host_label AND NOT c.verified_entry)::bigint AS assigned_views
    FROM (SELECT DISTINCT host_label,domain_label FROM canonical) h
  ), evidence AS (
    SELECT s.domain_label,s.source_evidence,count(*)::bigint AS sessions
    FROM sessions s GROUP BY 1,2
  ), host_sources AS (
    SELECT s.host_label,s.source_evidence,count(*)::bigint AS sessions
    FROM sessions s GROUP BY 1,2
  ), campaigns AS (
    SELECT s.host_label,s.attribution_source,s.utm_source,
           s.utm_medium,s.utm_campaign,s.utm_content,
           count(*)::bigint AS sessions
    FROM sessions s
    WHERE s.source_evidence = 'Tagged'
    GROUP BY 1,2,3,4,5,6
    ORDER BY sessions DESC,s.host_label,s.utm_campaign
    LIMIT 60
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
    'hosts',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(h)
      ORDER BY h.sessions DESC,h.host_label) FROM hosts h),'[]'::jsonb),
    'source_evidence',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s)
      ORDER BY s.domain_label,s.source_evidence) FROM evidence s),'[]'::jsonb),
    'host_source_evidence',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s)
      ORDER BY s.host_label,s.source_evidence) FROM host_sources s),'[]'::jsonb),
    'campaigns',coalesce((SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s)
      ORDER BY s.sessions DESC,s.host_label) FROM campaigns s),'[]'::jsonb),
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
'Aggregate entry hosts: jairribeiro.com (root and arbitrary subdomains, exact host breakdown), and native Streamlit (historical/unresolved assigned). Hosts and tagged campaign dimensions are aggregate only; no raw sessions/referrer URLs returned.';
