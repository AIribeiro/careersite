-- Advanced browser behavior telemetry, implemented with Streamlit Components v2.
-- Additive: no existing analytics event or reporting endpoint is removed.

ALTER TABLE public.careersite_analytics_events
  ADD COLUMN IF NOT EXISTS attention_ms integer CHECK (attention_ms IS NULL OR (attention_ms >= 0 AND attention_ms <= 86400000)),
  ADD COLUMN IF NOT EXISTS hover_ms integer CHECK (hover_ms IS NULL OR (hover_ms >= 0 AND hover_ms <= 86400000)),
  ADD COLUMN IF NOT EXISTS hesitation_ms integer CHECK (hesitation_ms IS NULL OR (hesitation_ms >= 0 AND hesitation_ms <= 86400000)),
  ADD COLUMN IF NOT EXISTS latency_ms integer CHECK (latency_ms IS NULL OR (latency_ms >= 0 AND latency_ms <= 86400000)),
  ADD COLUMN IF NOT EXISTS exposure_count integer CHECK (exposure_count IS NULL OR (exposure_count >= 0 AND exposure_count <= 10000)),
  ADD COLUMN IF NOT EXISTS interaction_type text CHECK (
    interaction_type IS NULL OR interaction_type IN (
      'pointer','keyboard','scroll','dead_click','rage_click','js_error','promise_rejection'
    )
  ),
  ADD COLUMN IF NOT EXISTS focus_loss_count integer CHECK (focus_loss_count IS NULL OR (focus_loss_count >= 0 AND focus_loss_count <= 10000)),
  ADD COLUMN IF NOT EXISTS resize_count integer CHECK (resize_count IS NULL OR (resize_count >= 0 AND resize_count <= 10000)),
  ADD COLUMN IF NOT EXISTS orientation_change_count integer CHECK (orientation_change_count IS NULL OR (orientation_change_count >= 0 AND orientation_change_count <= 10000)),
  ADD COLUMN IF NOT EXISTS max_scroll_velocity numeric CHECK (max_scroll_velocity IS NULL OR (max_scroll_velocity >= 0 AND max_scroll_velocity <= 1000000)),
  ADD COLUMN IF NOT EXISTS max_reverse_scroll_velocity numeric CHECK (max_reverse_scroll_velocity IS NULL OR (max_reverse_scroll_velocity >= 0 AND max_reverse_scroll_velocity <= 1000000)),
  ADD COLUMN IF NOT EXISTS error_type text CHECK (error_type IS NULL OR char_length(error_type) <= 64),
  ADD COLUMN IF NOT EXISTS hardware_concurrency integer CHECK (hardware_concurrency IS NULL OR (hardware_concurrency >= 1 AND hardware_concurrency <= 256)),
  ADD COLUMN IF NOT EXISTS device_memory_gb numeric CHECK (device_memory_gb IS NULL OR (device_memory_gb > 0 AND device_memory_gb <= 256)),
  ADD COLUMN IF NOT EXISTS save_data boolean,
  ADD COLUMN IF NOT EXISTS orientation text CHECK (orientation IS NULL OR orientation IN ('portrait','landscape','unknown'));

ALTER TABLE public.careersite_analytics_events
  DROP CONSTRAINT IF EXISTS careersite_analytics_events_event_name_check;
ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_analytics_events_event_name_check
  CHECK (event_name IN (
    'page_view','impact_view','lens_view','cv_download','email_click','linkedin_click',
    'article_click','article_view','article_share','engagement_ping',
    'element_impression','article_card_click','cta_click','section_view','performance_metric',
    'section_attention','element_attention','cta_hesitation','scroll_abandonment',
    'ux_signal','first_interaction','behavior_summary'
  ));

ALTER TABLE public.careersite_analytics_events
  DROP CONSTRAINT IF EXISTS careersite_analytics_events_metric_name_check;
ALTER TABLE public.careersite_analytics_events
  ADD CONSTRAINT careersite_analytics_events_metric_name_check
  CHECK (metric_name IS NULL OR metric_name IN (
    'ttfb_ms','fcp_ms','lcp_ms','cls','interaction_ms','inp_ms'
  ));

-- Keep raw analytics insert-only to public browser roles. This also fixes the
-- v4 regression where the table constraint accepted exposure events but the
-- RLS INSERT policy still rejected those event names.
DROP POLICY IF EXISTS "careersite public insert only" ON public.careersite_analytics_events;
CREATE POLICY "careersite public insert only"
ON public.careersite_analytics_events
FOR INSERT
TO anon, authenticated
WITH CHECK (
  event_name IN (
    'page_view','impact_view','lens_view','cv_download','email_click','linkedin_click',
    'article_click','article_view','article_share','engagement_ping',
    'element_impression','article_card_click','cta_click','section_view','performance_metric',
    'section_attention','element_attention','cta_hesitation','scroll_abandonment',
    'ux_signal','first_interaction','behavior_summary'
  )
  AND source IN ('streamlit','lovable')
  AND length(page) BETWEEN 1 AND 64
  AND (lens IS NULL OR length(lens) <= 64)
  AND (target IS NULL OR length(target) <= 500)
  AND (referrer_host IS NULL OR length(referrer_host) <= 255)
  AND (utm_source IS NULL OR length(utm_source) <= 100)
  AND (utm_campaign IS NULL OR length(utm_campaign) <= 100)
  AND (attribution_source IS NULL OR length(attribution_source) <= 100)
  AND (attribution_role IS NULL OR length(attribution_role) <= 120)
  AND (device_type IS NULL OR device_type IN ('desktop','mobile','tablet'))
  AND (browser_family IS NULL OR length(browser_family) <= 32)
  AND (os_family IS NULL OR length(os_family) <= 32)
  AND (language IS NULL OR length(language) <= 35)
  AND (timezone IS NULL OR length(timezone) <= 64)
  AND (viewport_width IS NULL OR viewport_width BETWEEN 1 AND 20000)
  AND (viewport_height IS NULL OR viewport_height BETWEEN 1 AND 20000)
  AND (screen_width IS NULL OR screen_width BETWEEN 1 AND 20000)
  AND (screen_height IS NULL OR screen_height BETWEEN 1 AND 20000)
  AND (connection_type IS NULL OR length(connection_type) <= 20)
  AND (session_elapsed_ms IS NULL OR session_elapsed_ms BETWEEN 0 AND 86400000)
  AND (engaged_ms IS NULL OR engaged_ms BETWEEN 0 AND 86400000)
  AND (country_code IS NULL OR country_code ~ '^[A-Z]{2}$')
  AND (article_slug IS NULL OR length(article_slug) <= 160)
  AND (article_action IS NULL OR length(article_action) <= 32)
  AND (article_engaged_ms IS NULL OR article_engaged_ms BETWEEN 0 AND 86400000)
  AND (content_kind IS NULL OR content_kind IN ('page','article'))
  AND (tracking_version IS NULL OR tracking_version BETWEEN 1 AND 10)
  AND (page_engaged_ms IS NULL OR page_engaged_ms BETWEEN 0 AND 86400000)
  AND (scroll_depth IS NULL OR scroll_depth BETWEEN 0 AND 100)
  AND (element_kind IS NULL OR element_kind IN ('article_card','cta'))
  AND (element_key IS NULL OR length(element_key) <= 160)
  AND (element_label IS NULL OR length(element_label) <= 240)
  AND (element_placement IS NULL OR length(element_placement) <= 160)
  AND (section_key IS NULL OR length(section_key) <= 160)
  AND (section_label IS NULL OR length(section_label) <= 240)
  AND (metric_name IS NULL OR metric_name IN ('ttfb_ms','fcp_ms','lcp_ms','cls','interaction_ms','inp_ms'))
  AND (metric_value IS NULL OR metric_value BETWEEN 0 AND 10000000)
  AND (attention_ms IS NULL OR attention_ms BETWEEN 0 AND 86400000)
  AND (hover_ms IS NULL OR hover_ms BETWEEN 0 AND 86400000)
  AND (hesitation_ms IS NULL OR hesitation_ms BETWEEN 0 AND 86400000)
  AND (latency_ms IS NULL OR latency_ms BETWEEN 0 AND 86400000)
  AND (exposure_count IS NULL OR exposure_count BETWEEN 0 AND 10000)
  AND (interaction_type IS NULL OR interaction_type IN ('pointer','keyboard','scroll','dead_click','rage_click','js_error','promise_rejection'))
  AND (focus_loss_count IS NULL OR focus_loss_count BETWEEN 0 AND 10000)
  AND (resize_count IS NULL OR resize_count BETWEEN 0 AND 10000)
  AND (orientation_change_count IS NULL OR orientation_change_count BETWEEN 0 AND 10000)
  AND (max_scroll_velocity IS NULL OR max_scroll_velocity BETWEEN 0 AND 1000000)
  AND (max_reverse_scroll_velocity IS NULL OR max_reverse_scroll_velocity BETWEEN 0 AND 1000000)
  AND (error_type IS NULL OR length(error_type) <= 64)
  AND (hardware_concurrency IS NULL OR hardware_concurrency BETWEEN 1 AND 256)
  AND (device_memory_gb IS NULL OR (device_memory_gb > 0 AND device_memory_gb <= 256))
  AND (orientation IS NULL OR orientation IN ('portrait','landscape','unknown'))
);

CREATE OR REPLACE FUNCTION public.careersite_behavior_intelligence(
  p_token text,
  p_days integer DEFAULT 30,
  p_window text DEFAULT 'days'
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  base jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  result jsonb;
BEGIN
  base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (base->>'period_since')::timestamptz;

  WITH scoped AS MATERIALIZED (
    SELECT *
    FROM public.careersite_analytics_events
    WHERE occurred_at >= since_at
      AND occurred_at <= report_now
      AND NOT (
        lower(coalesce(attribution_source,''))='application'
        AND lower(coalesce(attribution_role,''))='test'
      )
  ),
  section_seen AS MATERIALIZED (
    SELECT session_id,page,coalesce(article_slug,'') AS article_slug,
      coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      min(occurred_at) AS first_seen_at
    FROM scoped WHERE event_name IN ('section_view','section_attention')
    GROUP BY session_id,page,coalesce(article_slug,''),coalesce(section_key,'unknown')
  ),
  section_per_session AS MATERIALIZED (
    SELECT s.session_id,s.page,s.article_slug,s.section_key,s.section_label,s.first_seen_at,
      coalesce(sum(a.attention_ms),0) AS attention_ms,
      coalesce(sum(a.exposure_count),0) AS exposure_count,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name='cv_download') AS later_cv,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name IN ('email_click','linkedin_click')) AS later_contact,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name='page_view' AND e.page='impact') AS later_impact
    FROM section_seen s
    LEFT JOIN scoped a ON a.session_id=s.session_id AND a.page=s.page
      AND coalesce(a.article_slug,'')=s.article_slug
      AND coalesce(a.section_key,'unknown')=s.section_key
      AND a.event_name='section_attention'
    GROUP BY s.session_id,s.page,s.article_slug,s.section_key,s.section_label,s.first_seen_at
  ),
  section_attention AS (
    SELECT page,nullif(article_slug,'') AS article_slug,section_key,max(section_label) AS section_label,
      count(*) AS reached_sessions,
      count(*) FILTER (WHERE attention_ms>0) AS measured_attention_sessions,
      round(avg(attention_ms) FILTER (WHERE attention_ms>0)/1000.0,1) AS avg_attention_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS median_attention_seconds,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS p75_attention_seconds,
      count(*) FILTER (WHERE attention_ms>=5000) AS attentive_5s_sessions,
      coalesce(sum(exposure_count),0) AS exposures,
      count(*) FILTER (WHERE later_impact) AS later_impact_sessions,
      count(*) FILTER (WHERE later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE later_contact) AS later_contact_sessions
    FROM section_per_session
    GROUP BY page,article_slug,section_key
    ORDER BY reached_sessions DESC,measured_attention_sessions DESC
  ),
  element_seen AS MATERIALIZED (
    SELECT session_id,page,coalesce(article_slug,'') AS article_slug,
      coalesce(element_kind,'unknown') AS element_kind,coalesce(element_key,'unknown') AS element_key,
      coalesce(element_placement,'unknown') AS element_placement,max(element_label) AS element_label,
      min(occurred_at) AS first_seen_at
    FROM scoped WHERE event_name IN ('element_impression','element_attention')
    GROUP BY session_id,page,coalesce(article_slug,''),coalesce(element_kind,'unknown'),
      coalesce(element_key,'unknown'),coalesce(element_placement,'unknown')
  ),
  element_per_session AS MATERIALIZED (
    SELECT e.session_id,e.page,e.article_slug,e.element_kind,e.element_key,e.element_placement,e.element_label,e.first_seen_at,
      coalesce(sum(a.attention_ms),0) AS attention_ms,coalesce(sum(a.hover_ms),0) AS hover_ms,
      coalesce(sum(a.exposure_count),0) AS exposure_count,
      EXISTS (
        SELECT 1 FROM scoped c WHERE c.session_id=e.session_id AND c.occurred_at>=e.first_seen_at
          AND (
            (e.element_kind='cta' AND c.event_name='cta_click' AND coalesce(c.element_key,'unknown')=e.element_key AND coalesce(c.element_placement,'unknown')=e.element_placement)
            OR
            (e.element_kind='article_card' AND c.event_name='article_card_click' AND coalesce(c.element_key,'unknown')=e.element_key AND coalesce(c.element_placement,'unknown')=e.element_placement)
          )
      ) AS clicked
    FROM element_seen e
    LEFT JOIN scoped a ON a.session_id=e.session_id AND a.page=e.page
      AND coalesce(a.article_slug,'')=e.article_slug
      AND coalesce(a.element_kind,'unknown')=e.element_kind
      AND coalesce(a.element_key,'unknown')=e.element_key
      AND coalesce(a.element_placement,'unknown')=e.element_placement
      AND a.event_name='element_attention'
    GROUP BY e.session_id,e.page,e.article_slug,e.element_kind,e.element_key,e.element_placement,e.element_label,e.first_seen_at
  ),
  element_attention AS (
    SELECT page,nullif(article_slug,'') AS article_slug,element_kind,element_key,element_placement,max(element_label) AS element_label,
      count(*) AS exposed_sessions,count(*) FILTER (WHERE attention_ms>0) AS measured_attention_sessions,
      round(avg(attention_ms) FILTER (WHERE attention_ms>0)/1000.0,1) AS avg_attention_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS median_attention_seconds,
      count(*) FILTER (WHERE attention_ms>=2000) AS attentive_2s_sessions,
      count(*) FILTER (WHERE hover_ms>0) AS hover_sessions,
      round(avg(hover_ms) FILTER (WHERE hover_ms>0)/1000.0,1) AS avg_hover_seconds,
      count(*) FILTER (WHERE clicked) AS click_sessions,coalesce(sum(exposure_count),0) AS exposures
    FROM element_per_session
    GROUP BY page,article_slug,element_kind,element_key,element_placement
    ORDER BY exposed_sessions DESC,click_sessions DESC
  ),
  cta_hesitation AS (
    SELECT page,coalesce(element_key,'unknown') AS element_key,coalesce(element_placement,'unknown') AS element_placement,
      max(element_label) AS element_label,count(DISTINCT session_id) AS sessions,
      round(avg(hesitation_ms)/1000.0,1) AS avg_hesitation_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY hesitation_ms)/1000.0)::numeric,1) AS median_hesitation_seconds,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY hesitation_ms)/1000.0)::numeric,1) AS p75_hesitation_seconds
    FROM scoped WHERE event_name='cta_hesitation' AND hesitation_ms IS NOT NULL
    GROUP BY page,coalesce(element_key,'unknown'),coalesce(element_placement,'unknown')
    ORDER BY sessions DESC
  ),
  last_regions AS (
    SELECT CASE WHEN content_kind='article' OR article_slug IS NOT NULL THEN 'article' ELSE 'page' END AS kind,
      page,article_slug,coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      count(DISTINCT session_id) AS sessions,round(avg(scroll_depth)::numeric,1) AS avg_scroll_depth,
      round(avg(page_engaged_ms)/1000.0,1) AS avg_visible_seconds,
      round(avg(max_scroll_velocity)::numeric,1) AS avg_max_scroll_velocity,
      round(avg(max_reverse_scroll_velocity)::numeric,1) AS avg_max_reverse_scroll_velocity
    FROM scoped WHERE event_name='scroll_abandonment'
    GROUP BY CASE WHEN content_kind='article' OR article_slug IS NOT NULL THEN 'article' ELSE 'page' END,
      page,article_slug,coalesce(section_key,'unknown')
    ORDER BY sessions DESC
  ),
  ux_signals AS (
    SELECT interaction_type,page,coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      max(error_type) AS error_type,count(*) AS events,count(DISTINCT session_id) AS sessions
    FROM scoped WHERE event_name='ux_signal'
    GROUP BY interaction_type,page,coalesce(section_key,'unknown')
    ORDER BY sessions DESC,events DESC
  ),
  first_interaction AS (
    SELECT interaction_type,coalesce(device_type,'unknown') AS device_type,count(*) AS sessions,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms))::numeric,1) AS median_latency_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY latency_ms))::numeric,1) AS p75_latency_ms
    FROM scoped WHERE event_name='first_interaction' AND latency_ms IS NOT NULL
    GROUP BY interaction_type,coalesce(device_type,'unknown')
    ORDER BY sessions DESC
  ),
  behavior_summary AS (
    SELECT coalesce(device_type,'unknown') AS device_type,count(DISTINCT session_id) AS sessions,
      round(avg(focus_loss_count)::numeric,1) AS avg_focus_losses,round(avg(resize_count)::numeric,1) AS avg_resizes,
      round(avg(orientation_change_count)::numeric,1) AS avg_orientation_changes,
      round(avg(max_scroll_velocity)::numeric,1) AS avg_max_scroll_velocity,
      round(avg(max_reverse_scroll_velocity)::numeric,1) AS avg_max_reverse_scroll_velocity,
      round(avg(hardware_concurrency)::numeric,1) AS avg_logical_cores,
      round(avg(device_memory_gb)::numeric,1) AS avg_device_memory_gb,
      count(*) FILTER (WHERE save_data) AS save_data_sessions
    FROM scoped WHERE event_name='behavior_summary'
    GROUP BY coalesce(device_type,'unknown')
    ORDER BY sessions DESC
  ),
  web_vitals AS (
    SELECT coalesce(device_type,'unknown') AS device_type,
      count(DISTINCT session_id) FILTER (WHERE metric_name='fcp_ms') AS fcp_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY metric_value) FILTER (WHERE metric_name='fcp_ms'))::numeric,1) AS p75_fcp_ms,
      count(DISTINCT session_id) FILTER (WHERE metric_name='inp_ms') AS inp_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY metric_value) FILTER (WHERE metric_name='inp_ms'))::numeric,1) AS p75_inp_ms
    FROM scoped WHERE event_name='performance_metric' AND metric_name IN ('fcp_ms','inp_ms')
    GROUP BY coalesce(device_type,'unknown')
    ORDER BY greatest(
      count(DISTINCT session_id) FILTER (WHERE metric_name='fcp_ms'),
      count(DISTINCT session_id) FILTER (WHERE metric_name='inp_ms')
    ) DESC
  )
  SELECT jsonb_build_object(
    'generated_at',report_now,'period_since',since_at,
    'section_attention',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM section_attention x),'[]'::jsonb),
    'element_attention',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM element_attention x),'[]'::jsonb),
    'cta_hesitation',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM cta_hesitation x),'[]'::jsonb),
    'last_regions',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM last_regions x),'[]'::jsonb),
    'ux_signals',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM ux_signals x),'[]'::jsonb),
    'first_interaction',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM first_interaction x),'[]'::jsonb),
    'behavior_summary',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM behavior_summary x),'[]'::jsonb),
    'web_vitals',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM web_vitals x),'[]'::jsonb),
    'quality',jsonb_build_object(
      'behavior_first_seen',(SELECT min(occurred_at) FROM scoped WHERE coalesce(tracking_version,0)>=5),
      'behavior_events',(SELECT count(*) FROM scoped WHERE event_name IN (
        'section_attention','element_attention','cta_hesitation','scroll_abandonment','ux_signal','first_interaction','behavior_summary'
      )),
      'behavior_sessions',(SELECT count(DISTINCT session_id) FROM scoped WHERE event_name IN (
        'section_attention','element_attention','cta_hesitation','scroll_abandonment','ux_signal','first_interaction','behavior_summary'
      ))
    )
  ) INTO result;

  RETURN result;
END;
$$;

REVOKE ALL ON FUNCTION public.careersite_behavior_intelligence(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_behavior_intelligence(text,integer,text)
  TO anon,authenticated,service_role;
