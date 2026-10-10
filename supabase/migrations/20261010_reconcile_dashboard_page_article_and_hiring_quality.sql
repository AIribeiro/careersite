-- Make existing dashboard metrics use the same content grain and bot screen
-- as the owner-only attribution audit, without mutating historical events.
DO $patch$
declare f text;
        old_logic text := $old$event_name='page_view'$old$;
        new_logic text := $new$event_name='page_view' and article_slug is null and content_kind is distinct from 'article'$new$;
begin
 select pg_get_functiondef(p.oid) into f
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='careersite_analytics_dashboard';
 if f is null or (length(f)-length(replace(f,old_logic,'')))/length(old_logic)<4 then
   raise exception 'Baseline analytics page-view definition changed; refusing unsafe patch';
 end if;
 f:=replace(f,old_logic,new_logic);
 execute f;
end $patch$;

DO $patch$
declare f text;
        old_clause text := $old$      and event_name = 'page_view'
  ),
  page_catalog$old$;
        replacement text := $new$      and event_name = 'page_view'
      and article_slug is null
      and content_kind is distinct from 'article'
  ),
  page_catalog$new$;
begin
 select pg_get_functiondef(p.oid) into f
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='careersite_analytics_dashboard_v2';
 if f is null or position(old_clause in f)=0 then
    raise exception 'Analytics v2 page catalogue changed; refusing unsafe patch';
 end if;
 f:=replace(f,old_clause,replacement);
 execute f;
end $patch$;

DO $patch$
declare f text;
        insertion_anchor text := $old$  session_base AS MATERIALIZED ($old$;
        extra_ctes text := $new$  preview_page_events AS MATERIALIZED (
    SELECT e.id,e.session_id,e.page,e.occurred_at,
      CASE
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) like 'linkedin%' THEN 'LinkedIn'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('facebook','fb','meta') THEN 'Facebook'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('whatsapp','wa') THEN 'WhatsApp'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('x','twitter') THEN 'X'
        ELSE lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) END AS channel,
      pg_catalog.concat_ws('|',
        coalesce(e.country_code,''),coalesce(e.timezone,''),
        coalesce(e.device_type,''),coalesce(e.browser_family,''),
        coalesce(e.os_family,''),coalesce(e.language,''),
        coalesce(e.viewport_width::text,''),coalesce(e.screen_width::text,'')) AS signature
    FROM scoped e
    WHERE e.event_name='page_view'
      AND e.article_slug IS NULL AND e.content_kind IS DISTINCT FROM 'article'
  ),
  preview_bursts AS MATERIALIZED (
    SELECT DISTINCT a.session_id
    FROM preview_page_events a
    WHERE EXISTS (
       SELECT 1 FROM preview_page_events b JOIN preview_page_events c
         ON c.id<>a.id AND b.id<>a.id AND c.id<>b.id
           AND b.signature=a.signature AND c.signature=a.signature
           AND b.channel=a.channel AND c.channel=a.channel
       WHERE a.page<>b.page AND a.page<>c.page AND b.page<>c.page
         AND a.session_id<>b.session_id AND a.session_id<>c.session_id AND b.session_id<>c.session_id
         AND b.occurred_at BETWEEN a.occurred_at-interval '30 seconds' AND a.occurred_at+interval '30 seconds'
         AND c.occurred_at BETWEEN a.occurred_at-interval '30 seconds' AND a.occurred_at+interval '30 seconds'
    )
  ),
  session_base AS MATERIALIZED ($new$;
        old_class text := $old$        AND coalesce(g.valid_sessions,0) >= 10
        AND coalesce(g.interaction_sessions,0) = 0
        AND coalesce(g.action_sessions,0) = 0
        AND coalesce(g.avg_engaged_ms,0) < 10000
      ) AS suspected_automation$old$;
        new_class text := $new$        AND (
          (
            coalesce(g.valid_sessions,0) >= 10
            AND coalesce(g.interaction_sessions,0) = 0
            AND coalesce(g.action_sessions,0) = 0
            AND coalesce(g.avg_engaged_ms,0) < 10000
          )
          OR EXISTS (SELECT 1 FROM preview_bursts p WHERE p.session_id=s.session_id)
        )
      ) AS suspected_automation$new$;
begin
 select pg_get_functiondef(p.oid) into f
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='careersite_hiring_intelligence_v1';
 if f is null or position(insertion_anchor in f)=0 or position(old_class in f)=0 then
   raise exception 'Hiring quality function changed; refusing unsafe patch';
 end if;
 f:=replace(f,insertion_anchor,extra_ctes);
 f:=replace(f,old_class,new_class);
 f:=replace(f,
   $old$WHEN pg_catalog.lower(c.source_raw) = 'direct/unknown' THEN 'Direct / unknown'$old$,
   $new$WHEN pg_catalog.lower(c.source_raw) = 'direct/unknown' THEN 'Unattributed / unknown'$new$);
 f:=replace(f,
   $old$'suspected_signature_count',(SELECT signatures FROM automation_meta)$old$,
   $new$'suspected_signature_count',(SELECT signatures FROM automation_meta),
      'preview_burst_window_seconds',30,
      'minimum_different_preview_pages',3,
      'suspected_preview_burst_sessions',(SELECT count(*) FROM preview_bursts)$new$);
 execute f;
end $patch$;
