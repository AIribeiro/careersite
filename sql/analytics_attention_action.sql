-- Attention-to-action analytics upgrade.
-- Additive: established events and careersite_content_intelligence() remain available.
ALTER TABLE public.careersite_analytics_events
  ADD COLUMN IF NOT EXISTS element_kind text CHECK (element_kind IS NULL OR element_kind IN ('article_card','cta')),
  ADD COLUMN IF NOT EXISTS element_key text CHECK (element_key IS NULL OR char_length(element_key) <= 160),
  ADD COLUMN IF NOT EXISTS element_label text CHECK (element_label IS NULL OR char_length(element_label) <= 240),
  ADD COLUMN IF NOT EXISTS element_placement text CHECK (element_placement IS NULL OR char_length(element_placement) <= 160),
  ADD COLUMN IF NOT EXISTS section_key text CHECK (section_key IS NULL OR char_length(section_key) <= 160),
  ADD COLUMN IF NOT EXISTS section_label text CHECK (section_label IS NULL OR char_length(section_label) <= 240),
  ADD COLUMN IF NOT EXISTS metric_name text CHECK (metric_name IS NULL OR metric_name IN ('ttfb_ms','lcp_ms','cls','interaction_ms')),
  ADD COLUMN IF NOT EXISTS metric_value numeric CHECK (metric_value IS NULL OR (metric_value >= 0 AND metric_value <= 10000000));

ALTER TABLE public.careersite_analytics_events
  DROP CONSTRAINT IF EXISTS careersite_analytics_events_event_name_check;
ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_analytics_events_event_name_check
  CHECK (event_name IN (
    'page_view','impact_view','lens_view','cv_download','email_click','linkedin_click',
    'article_click','article_view','article_share','engagement_ping',
    'element_impression','article_card_click','cta_click','section_view','performance_metric'
  ));

CREATE OR REPLACE FUNCTION public.careersite_content_intelligence_v2(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text, p_article_metadata jsonb DEFAULT '[]'::jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  base jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  previous_since timestamptz;
  result jsonb;
BEGIN
  base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (base->>'period_since')::timestamptz;
  previous_since := since_at - (report_now - since_at);

  WITH article_meta AS MATERIALIZED (
    SELECT
      left(coalesce(x.slug,''),160) AS slug,
      left(coalesce(x.title,''),240) AS title,
      left(coalesce(x.topic,'Uncategorized'),120) AS topic,
      left(coalesce(x.kind,'Article'),80) AS kind,
      x.published_date
    FROM pg_catalog.jsonb_to_recordset(coalesce(p_article_metadata,'[]'::jsonb))
      AS x(slug text,title text,topic text,kind text,published_date date)
    WHERE coalesce(x.slug,'') <> ''
  ),
  current_scoped AS MATERIALIZED (
    SELECT e.*,
      CASE
        WHEN e.content_kind='article' OR (e.article_slug IS NOT NULL AND e.event_name<>'article_click') THEN 'article'
        WHEN e.content_kind='page' THEN 'page'
        WHEN e.page='thinking' THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= since_at
      AND e.occurred_at <= report_now
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
  ),
  previous_scoped AS MATERIALIZED (
    SELECT e.*,
      CASE
        WHEN e.content_kind='article' OR (e.article_slug IS NOT NULL AND e.event_name<>'article_click') THEN 'article'
        WHEN e.content_kind='page' THEN 'page'
        WHEN e.page='thinking' THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= previous_since
      AND e.occurred_at < since_at
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
  ),
  views AS MATERIALIZED (
    SELECT c.*,
      CASE WHEN c.event_name='article_view' THEN 'article:'||c.article_slug ELSE c.page END AS content
    FROM current_scoped c
    WHERE c.event_name='article_view'
       OR (c.event_name='page_view' AND c.kind<>'article')
  ),
  previous_views AS MATERIALIZED (
    SELECT c.*,
      CASE WHEN c.event_name='article_view' THEN 'article:'||c.article_slug ELSE c.page END AS content
    FROM previous_scoped c
    WHERE c.event_name='article_view'
       OR (c.event_name='page_view' AND c.kind<>'article')
  ),
  content_sessions AS MATERIALIZED (
    SELECT
      c.kind,
      c.page,
      CASE WHEN c.kind='article' THEN c.article_slug END AS slug,
      c.session_id,
      count(*) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS views,
      min(c.occurred_at) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS opened,
      max(CASE WHEN c.kind='article' THEN c.article_engaged_ms ELSE c.page_engaged_ms END) AS active_ms,
      max(c.scroll_depth) AS depth,
      bool_or(coalesce(c.tracking_version,0)>=3) AS measured,
      bool_or(coalesce(c.tracking_version,0)>=4) AS measured_v4,
      count(*) FILTER (WHERE c.event_name='article_share') AS shares,
      bool_or(c.event_name IN ('cv_download','email_click','linkedin_click')) AS action_on_content
    FROM current_scoped c
    WHERE c.event_name<>'article_click'
    GROUP BY c.kind,c.page,CASE WHEN c.kind='article' THEN c.article_slug END,c.session_id
  ),
  quality_sessions AS MATERIALIZED (
    SELECT c.*,
      EXISTS(
        SELECT 1 FROM current_scoped e
        WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened AND e.event_name='cv_download'
      ) AS later_cv,
      EXISTS(
        SELECT 1 FROM current_scoped e
        WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened
          AND e.event_name IN ('email_click','linkedin_click')
      ) AS later_contact,
      EXISTS(
        SELECT 1 FROM views v
        WHERE v.session_id=c.session_id AND v.occurred_at>c.opened AND v.kind='page' AND v.page<>'thinking'
      ) AS later_portfolio
    FROM content_sessions c
    WHERE c.views>0
  ),
  performance AS MATERIALIZED (
    SELECT
      q.kind,
      coalesce(q.slug,q.page) AS content,
      count(*) AS sessions,
      sum(q.views) AS views,
      count(*) FILTER (WHERE q.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE q.active_ms>=5000) AS confirmed_sessions,
      round((avg(q.active_ms) FILTER (WHERE q.active_ms>=5000))/1000.0,1) AS avg_active_seconds,
      count(*) FILTER (WHERE q.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE q.depth>=25) AS quarter_sessions,
      count(*) FILTER (WHERE q.depth>=50) AS halfway_sessions,
      count(*) FILTER (WHERE q.depth>=75) AS three_quarter_sessions,
      count(*) FILTER (WHERE q.depth>=90) AS bottom_sessions,
      count(*) FILTER (WHERE q.depth>=90 AND q.active_ms>=30000) AS deep_read_sessions,
      sum(q.shares) AS shares,
      count(*) FILTER (WHERE q.shares>0) AS sharing_sessions,
      count(*) FILTER (WHERE q.action_on_content) AS action_sessions,
      count(*) FILTER (WHERE q.later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE q.later_contact) AS later_contact_sessions,
      count(*) FILTER (WHERE q.later_portfolio) AS later_portfolio_sessions
    FROM quality_sessions q
    GROUP BY q.kind,coalesce(q.slug,q.page)
  ),
  previous_content_sessions AS MATERIALIZED (
    SELECT
      c.kind,
      c.page,
      CASE WHEN c.kind='article' THEN c.article_slug END AS slug,
      c.session_id,
      count(*) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS views,
      max(CASE WHEN c.kind='article' THEN c.article_engaged_ms ELSE c.page_engaged_ms END) AS active_ms
    FROM previous_scoped c
    WHERE c.event_name<>'article_click'
    GROUP BY c.kind,c.page,CASE WHEN c.kind='article' THEN c.article_slug END,c.session_id
  ),
  previous_performance AS MATERIALIZED (
    SELECT
      p.kind,
      coalesce(p.slug,p.page) AS content,
      count(*) FILTER (WHERE p.views>0) AS sessions,
      coalesce(sum(p.views) FILTER (WHERE p.views>0),0) AS views,
      count(*) FILTER (WHERE p.views>0 AND p.active_ms>=10000) AS engaged_sessions
    FROM previous_content_sessions p
    GROUP BY p.kind,coalesce(p.slug,p.page)
  ),
  period_comparison AS (
    SELECT
      coalesce(c.kind,p.kind) AS kind,
      coalesce(c.content,p.content) AS content,
      coalesce(c.sessions,0) AS current_sessions,
      coalesce(p.sessions,0) AS previous_sessions,
      coalesce(c.views,0) AS current_views,
      coalesce(p.views,0) AS previous_views,
      coalesce(c.engaged_sessions,0) AS current_engaged_sessions,
      coalesce(p.engaged_sessions,0) AS previous_engaged_sessions
    FROM performance c
    FULL OUTER JOIN previous_performance p
      ON p.kind=c.kind AND p.content=c.content
  ),
  ordered_views AS (
    SELECT v.*,
      lead(v.content) OVER (PARTITION BY v.session_id ORDER BY v.occurred_at,v.id) AS next_content
    FROM views v
  ),
  journeys AS (
    SELECT
      o.content AS from_content,
      o.next_content AS to_content,
      count(*) AS transitions,
      count(DISTINCT o.session_id) AS sessions
    FROM ordered_views o
    WHERE o.next_content IS NOT NULL AND o.next_content<>o.content
    GROUP BY o.content,o.next_content
    ORDER BY sessions DESC
    LIMIT 30
  ),
  session_sources AS MATERIALIZED (
    SELECT
      c.session_id,
      (array_agg(coalesce(c.attribution_source,c.utm_source,'direct/unknown') ORDER BY c.occurred_at,c.id))[1] AS channel,
      (array_agg(coalesce(c.utm_campaign,c.attribution_role,'untagged') ORDER BY c.occurred_at,c.id))[1] AS campaign,
      (array_agg(coalesce(c.device_type,'unknown') ORDER BY c.occurred_at,c.id))[1] AS device_type,
      bool_or(c.event_name='cv_download') AS cv,
      bool_or(c.event_name IN ('email_click','linkedin_click')) AS contact,
      bool_or(c.event_name='article_view') AS reader,
      max(c.engaged_ms)>=10000 AS engaged
    FROM current_scoped c
    GROUP BY c.session_id
  ),
  campaigns AS (
    SELECT
      s.channel,s.campaign,
      count(*) AS sessions,
      count(*) FILTER (WHERE s.engaged) AS engaged_sessions,
      count(*) FILTER (WHERE s.reader) AS reader_sessions,
      count(*) FILTER (WHERE s.cv) AS cv_sessions,
      count(*) FILTER (WHERE s.contact) AS contact_sessions
    FROM session_sources s
    GROUP BY s.channel,s.campaign
    ORDER BY sessions DESC
    LIMIT 40
  ),
  entry_exit AS (
    SELECT
      v.session_id,
      (array_agg(v.content ORDER BY v.occurred_at,v.id))[1] AS entry,
      (array_agg(v.content ORDER BY v.occurred_at DESC,v.id DESC))[1] AS last_content,
      count(*) AS views
    FROM views v
    GROUP BY v.session_id
  ),
  entrances AS (
    SELECT e.entry AS content,count(*) AS sessions,count(*) FILTER (WHERE e.views=1) AS single_view_sessions
    FROM entry_exit e
    GROUP BY e.entry
    ORDER BY sessions DESC
  ),
  exits AS (
    SELECT e.last_content AS content,count(*) AS sessions
    FROM entry_exit e
    GROUP BY e.last_content
    ORDER BY sessions DESC
  ),
  article_exposures AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement,
      c.element_label
    FROM current_scoped c
    WHERE c.event_name='element_impression' AND c.element_kind='article_card'
  ),
  article_clicks AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement
    FROM current_scoped c
    WHERE c.event_name='article_card_click'
  ),
  article_card_ctr AS (
    SELECT
      e.element_key,
      e.placement,
      max(e.element_label) AS label,
      count(*) AS exposed_sessions,
      count(*) FILTER (
        WHERE EXISTS(
          SELECT 1 FROM article_clicks c
          WHERE c.session_id=e.session_id AND c.element_key=e.element_key AND c.placement=e.placement
        )
      ) AS click_sessions
    FROM article_exposures e
    GROUP BY e.element_key,e.placement
    ORDER BY exposed_sessions DESC
  ),
  cta_exposures AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement,
      c.element_label
    FROM current_scoped c
    WHERE c.event_name='element_impression' AND c.element_kind='cta'
  ),
  cta_clicks AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement
    FROM current_scoped c
    WHERE c.event_name='cta_click'
  ),
  cta_ctr AS (
    SELECT
      e.element_key,
      e.placement,
      max(e.element_label) AS label,
      count(*) AS exposed_sessions,
      count(*) FILTER (
        WHERE EXISTS(
          SELECT 1 FROM cta_clicks c
          WHERE c.session_id=e.session_id AND c.element_key=e.element_key AND c.placement=e.placement
        )
      ) AS click_sessions
    FROM cta_exposures e
    GROUP BY e.element_key,e.placement
    ORDER BY exposed_sessions DESC
  ),
  page_denominators AS MATERIALIZED (
    SELECT v.page,count(DISTINCT v.session_id) AS page_sessions
    FROM views v
    WHERE v.kind='page'
    GROUP BY v.page
  ),
  section_reach AS (
    SELECT
      s.page,
      coalesce(s.section_key,'unknown') AS section_key,
      max(s.section_label) AS section_label,
      d.page_sessions,
      count(DISTINCT s.session_id) AS reached_sessions
    FROM current_scoped s
    JOIN page_denominators d ON d.page=s.page
    WHERE s.event_name='section_view' AND s.content_kind='page'
    GROUP BY s.page,coalesce(s.section_key,'unknown'),d.page_sessions
    ORDER BY d.page_sessions DESC,reached_sessions DESC
  ),
  article_entry AS MATERIALIZED (
    SELECT c.session_id,min(c.occurred_at) AS article_at
    FROM current_scoped c
    WHERE c.event_name='article_view'
    GROUP BY c.session_id
  ),
  article_to_impact AS MATERIALIZED (
    SELECT a.session_id,a.article_at,min(i.occurred_at) AS impact_at
    FROM article_entry a
    JOIN current_scoped i
      ON i.session_id=a.session_id
     AND i.event_name='page_view'
     AND i.page='impact'
     AND i.occurred_at>a.article_at
    GROUP BY a.session_id,a.article_at
  ),
  article_to_impact_to_cv AS MATERIALIZED (
    SELECT a.session_id,min(c.occurred_at) AS cv_at
    FROM article_to_impact a
    JOIN current_scoped c
      ON c.session_id=a.session_id
     AND c.event_name='cv_download'
     AND c.occurred_at>a.impact_at
    GROUP BY a.session_id
  ),
  ordered_funnel AS (
    SELECT
      (SELECT count(*) FROM article_entry) AS article_sessions,
      (SELECT count(*) FROM article_to_impact) AS article_to_impact_sessions,
      (SELECT count(*) FROM article_to_impact_to_cv) AS article_to_impact_to_cv_sessions
  ),
  reader_article_counts AS MATERIALIZED (
    SELECT c.session_id,count(DISTINCT c.article_slug) AS articles
    FROM current_scoped c
    WHERE c.event_name='article_view' AND c.article_slug IS NOT NULL
    GROUP BY c.session_id
  ),
  multi_article AS (
    SELECT
      count(*) AS reader_sessions,
      count(*) FILTER (WHERE r.articles>=2) AS multi_article_sessions
    FROM reader_article_counts r
  ),
  session_entries AS MATERIALIZED (
    SELECT v.session_id,min(v.occurred_at) AS entry_at
    FROM views v
    GROUP BY v.session_id
  ),
  meaningful_events AS MATERIALIZED (
    SELECT c.session_id,c.occurred_at,
      CASE
        WHEN c.event_name='page_view' AND c.page='impact' AND c.kind='page' THEN 'case_study'
        WHEN c.event_name='cv_download' THEN 'cv'
        WHEN c.event_name IN ('email_click','linkedin_click') THEN 'contact'
        ELSE NULL
      END AS action
    FROM current_scoped c
    WHERE (c.event_name='page_view' AND c.page='impact' AND c.kind='page')
       OR c.event_name IN ('cv_download','email_click','linkedin_click')
  ),
  first_meaningful AS MATERIALIZED (
    SELECT
      e.session_id,
      m.action,
      min(m.occurred_at) AS action_at,
      extract(epoch FROM (min(m.occurred_at)-e.entry_at)) AS seconds_to_action
    FROM session_entries e
    JOIN meaningful_events m
      ON m.session_id=e.session_id AND m.occurred_at>=e.entry_at
    WHERE m.action IS NOT NULL
    GROUP BY e.session_id,m.action,e.entry_at
  ),
  time_to_action AS (
    SELECT
      f.action,
      count(*) AS sessions,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY f.seconds_to_action))::numeric,1) AS median_seconds,
      round(avg(f.seconds_to_action)::numeric,1) AS avg_seconds
    FROM first_meaningful f
    GROUP BY f.action
    ORDER BY f.action
  ),
  topic_performance AS (
    SELECT
      coalesce(m.topic,'Uncategorized') AS topic,
      count(*) AS article_sessions,
      coalesce(sum(q.views),0) AS views,
      count(*) FILTER (WHERE q.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE q.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE q.depth>=75) AS reached_75_sessions,
      count(*) FILTER (WHERE q.depth>=90) AS reached_90_sessions,
      count(*) FILTER (WHERE q.later_portfolio) AS later_portfolio_sessions,
      count(*) FILTER (WHERE q.later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE q.later_contact) AS later_contact_sessions
    FROM quality_sessions q
    LEFT JOIN article_meta m ON m.slug=q.slug
    WHERE q.kind='article'
    GROUP BY coalesce(m.topic,'Uncategorized')
    ORDER BY article_sessions DESC
  ),
  first7_sessions AS MATERIALIZED (
    SELECT
      m.slug,m.title,m.topic,m.kind,m.published_date,
      e.session_id,
      count(*) FILTER (WHERE e.event_name='article_view') AS views,
      max(e.article_engaged_ms) AS active_ms,
      max(e.scroll_depth) AS depth
    FROM article_meta m
    JOIN public.careersite_analytics_events e
      ON e.article_slug=m.slug
     AND m.published_date IS NOT NULL
     AND e.occurred_at >= m.published_date::timestamptz
     AND e.occurred_at < (m.published_date::timestamptz + interval '7 days')
     AND NOT (
       lower(coalesce(e.attribution_source,''))='application'
       AND lower(coalesce(e.attribution_role,''))='test'
     )
    GROUP BY m.slug,m.title,m.topic,m.kind,m.published_date,e.session_id
  ),
  publication_age AS (
    SELECT
      f.slug,max(f.title) AS title,max(f.topic) AS topic,max(f.kind) AS kind,max(f.published_date) AS published_date,
      count(*) FILTER (WHERE f.views>0) AS sessions,
      coalesce(sum(f.views) FILTER (WHERE f.views>0),0) AS views,
      count(*) FILTER (WHERE f.views>0 AND f.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE f.views>0 AND f.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE f.views>0 AND f.depth>=75) AS reached_75_sessions
    FROM first7_sessions f
    GROUP BY f.slug
    ORDER BY views DESC
  ),
  performance_session_values AS MATERIALIZED (
    SELECT
      c.session_id,
      coalesce(max(c.device_type) FILTER (WHERE c.device_type IS NOT NULL),'unknown') AS device_type,
      max(c.metric_value) FILTER (WHERE c.metric_name='ttfb_ms') AS ttfb_ms,
      max(c.metric_value) FILTER (WHERE c.metric_name='lcp_ms') AS lcp_ms,
      max(c.metric_value) FILTER (WHERE c.metric_name='cls') AS cls,
      max(c.metric_value) FILTER (WHERE c.metric_name='interaction_ms') AS interaction_ms
    FROM current_scoped c
    WHERE c.event_name='performance_metric'
    GROUP BY c.session_id
  ),
  experience AS (
    SELECT
      p.device_type,
      count(*) AS measured_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.ttfb_ms) FILTER (WHERE p.ttfb_ms IS NOT NULL))::numeric,1) AS p75_ttfb_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.lcp_ms) FILTER (WHERE p.lcp_ms IS NOT NULL))::numeric,1) AS p75_lcp_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.cls) FILTER (WHERE p.cls IS NOT NULL))::numeric,3) AS p75_cls,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.interaction_ms) FILTER (WHERE p.interaction_ms IS NOT NULL))::numeric,1) AS p75_interaction_ms,
      count(*) FILTER (WHERE p.lcp_ms>2500) AS slow_lcp_sessions,
      count(*) FILTER (WHERE p.lcp_ms>2500 AND s.engaged) AS slow_lcp_engaged_sessions,
      count(*) FILTER (WHERE p.cls>0.1) AS unstable_cls_sessions,
      count(*) FILTER (WHERE p.interaction_ms>200) AS slow_interaction_sessions
    FROM performance_session_values p
    LEFT JOIN session_sources s ON s.session_id=p.session_id
    GROUP BY p.device_type
    ORDER BY measured_sessions DESC
  )
  SELECT jsonb_build_object(
    'generated_at',report_now,
    'period_since',since_at,
    'previous_period_since',previous_since,
    'period_label',base->'period_label',
    'performance',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.sessions DESC) FROM performance p),'[]'::jsonb),
    'period_comparison',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.current_sessions DESC,p.previous_sessions DESC) FROM period_comparison p),'[]'::jsonb),
    'journeys',coalesce((SELECT jsonb_agg(to_jsonb(j)) FROM journeys j),'[]'::jsonb),
    'campaigns',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM campaigns c),'[]'::jsonb),
    'entrances',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM entrances e),'[]'::jsonb),
    'exits',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM exits e),'[]'::jsonb),
    'article_cards',coalesce((SELECT jsonb_agg(to_jsonb(a)) FROM article_card_ctr a),'[]'::jsonb),
    'cta_placements',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM cta_ctr c),'[]'::jsonb),
    'section_reach',coalesce((SELECT jsonb_agg(to_jsonb(s)) FROM section_reach s),'[]'::jsonb),
    'ordered_funnel',coalesce((SELECT to_jsonb(o) FROM ordered_funnel o),'{}'::jsonb),
    'multi_article',coalesce((SELECT to_jsonb(m) FROM multi_article m),'{}'::jsonb),
    'time_to_action',coalesce((SELECT jsonb_agg(to_jsonb(t)) FROM time_to_action t),'[]'::jsonb),
    'topic_performance',coalesce((SELECT jsonb_agg(to_jsonb(t)) FROM topic_performance t),'[]'::jsonb),
    'publication_age',coalesce((SELECT jsonb_agg(to_jsonb(p)) FROM publication_age p),'[]'::jsonb),
    'experience',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM experience x),'[]'::jsonb),
    'quality',jsonb_build_object(
      'last_event_at',(SELECT max(c.occurred_at) FROM current_scoped c),
      'new_measurement_since',(SELECT min(c.occurred_at) FROM current_scoped c WHERE coalesce(c.tracking_version,0)>=3),
      'attention_measurement_since',(SELECT min(c.occurred_at) FROM current_scoped c WHERE coalesce(c.tracking_version,0)>=4),
      'measured_content_sessions',(SELECT count(*) FROM quality_sessions q WHERE q.measured),
      'attention_measured_content_sessions',(SELECT count(*) FROM quality_sessions q WHERE q.measured_v4),
      'content_sessions',(SELECT count(*) FROM quality_sessions),
      'legacy_thinking_views',(SELECT count(*) FROM views v WHERE v.kind='legacy_thinking'),
      'contact_sessions',(SELECT count(*) FROM session_sources s WHERE s.contact),
      'page_sessions',(SELECT count(DISTINCT v.session_id) FROM views v WHERE v.kind='page'),
      'page_views',(SELECT count(*) FROM views v WHERE v.kind='page'),
      'article_sessions',(SELECT count(DISTINCT v.session_id) FROM views v WHERE v.kind='article'),
      'article_views',(SELECT count(*) FROM views v WHERE v.kind='article')
    )
  ) INTO result;

  RETURN result;
END;
$function$
;

REVOKE ALL ON FUNCTION public.careersite_content_intelligence_v2(text,integer,text,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_content_intelligence_v2(text,integer,text,jsonb)
  TO anon,authenticated,service_role;
