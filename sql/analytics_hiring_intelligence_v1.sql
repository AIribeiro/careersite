-- Hiring-evidence and audience-quality reporting layer.
-- Raw analytics events remain unchanged; classification happens only at query time.
-- Tracking v5 is the first cohort used because earlier tracking versions do not
-- provide comparable behavior/session semantics.
--
-- Suspected automation is deliberately conservative: repeated exact technical
-- signature (>=10 valid sessions), zero recorded interactions, zero recorded
-- actions, and cohort average active time below 10 seconds.
-- This is a reporting heuristic, not proof that an individual session is a bot.

CREATE OR REPLACE FUNCTION public.careersite_hiring_intelligence_v1(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  v_base jsonb;
  v_requested_since timestamptz;
  v_v5_since timestamptz;
  v_quality_since timestamptz;
  v_now timestamptz := pg_catalog.now();
  v_result jsonb;
BEGIN
  -- Reuse the established token validation and reporting-window logic.
  v_base := public.careersite_analytics_dashboard_v2(p_token, p_days, p_window);
  v_requested_since := (v_base->>'period_since')::timestamptz;

  SELECT pg_catalog.min(e.occurred_at)
  INTO v_v5_since
  FROM public.careersite_analytics_events e
  WHERE coalesce(e.tracking_version, 0) >= 5;

  v_quality_since := greatest(
    v_requested_since,
    coalesce(v_v5_since, v_requested_since)
  );

  WITH quality_ids AS MATERIALIZED (
    SELECT DISTINCT e.session_id
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= v_quality_since
      AND e.occurred_at <= v_now
      AND coalesce(e.tracking_version, 0) >= 5
  ),
  scoped AS MATERIALIZED (
    SELECT e.*
    FROM public.careersite_analytics_events e
    JOIN quality_ids q USING (session_id)
    WHERE e.occurred_at >= v_quality_since
      AND e.occurred_at <= v_now
  ),
  session_base AS MATERIALIZED (
    SELECT
      e.session_id,
      pg_catalog.min(e.occurred_at) AS first_at,
      pg_catalog.max(coalesce(e.engaged_ms, 0))::bigint AS max_engaged_ms,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view')) AS has_content_view,
      pg_catalog.bool_or(e.event_name = 'first_interaction') AS has_first_interaction,
      pg_catalog.bool_or(e.event_name IN (
        'cv_download','email_click','linkedin_click','cta_click','article_card_click','article_share'
      )) AS has_any_action,
      pg_catalog.bool_or(
        pg_catalog.lower(coalesce(e.attribution_source,'')) = 'application'
        AND pg_catalog.lower(coalesce(e.attribution_role,'')) = 'test'
      ) AS explicit_test,

      pg_catalog.bool_or(
        e.event_name = 'article_card_click'
        OR (e.event_name = 'cta_click' AND coalesce(e.element_key,'') = 'impact')
      ) AS exploration_action,

      pg_catalog.bool_or(
        (e.event_name = 'cta_click'
          AND e.page = 'certifications'
          AND coalesce(e.element_key,'') IN ('linkedin','verify-credential'))
        OR (e.event_name = 'linkedin_click' AND e.page = 'certifications')
      ) AS evidence_verified,

      pg_catalog.bool_or(
        e.event_name = 'cv_download'
        OR e.event_name = 'email_click'
        OR (e.event_name = 'linkedin_click' AND e.page <> 'certifications')
      ) AS hiring_intent,

      pg_catalog.bool_or(
        e.event_name = 'article_view'
        OR (e.event_name IN ('page_view','impact_view') AND e.page IN ('impact','ai-data-governance','certifications'))
        OR (
          e.event_name IN ('section_view','section_attention')
          AND coalesce(e.section_key,'') IN (
            'evidence-of-adoption',
            'adoption-in-practice',
            'selected-leadership-cases',
            'operating-perspective',
            'experience-behind-the-perspective',
            'executive-perspective',
            'executive-definition',
            'leadership-in-practice',
            'leadership-impact',
            'about-credentials',
            'coverage',
            'featured-technical-foundation',
            'recent-credentials'
          )
        )
      ) AS evidence_reached,

      pg_catalog.bool_or(e.event_name IN ('page_view','impact_view') AND e.page = 'impact') AS reached_impact,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view') AND e.page = 'ai-data-governance') AS reached_governance,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view') AND e.page = 'certifications') AS reached_certifications,

      coalesce(
        (pg_catalog.array_agg(e.attribution_source ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.attribution_source IS NOT NULL AND e.attribution_source <> ''))[1],
        (pg_catalog.array_agg(e.utm_source ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.utm_source IS NOT NULL AND e.utm_source <> ''))[1],
        'direct/unknown'
      ) AS source_raw,

      coalesce(
        (pg_catalog.array_agg(e.utm_campaign ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.utm_campaign IS NOT NULL AND e.utm_campaign <> ''))[1],
        (pg_catalog.array_agg(e.attribution_role ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.attribution_role IS NOT NULL AND e.attribution_role <> ''))[1],
        'untagged'
      ) AS campaign_raw,

      pg_catalog.max(e.country_code) AS country_code,
      pg_catalog.max(e.timezone) AS timezone,
      pg_catalog.max(e.device_type) AS device_type,
      pg_catalog.max(e.browser_family) AS browser_family,
      pg_catalog.max(e.os_family) AS os_family,
      pg_catalog.max(e.language) AS language,
      pg_catalog.max(e.viewport_width) AS viewport_width,
      pg_catalog.max(e.viewport_height) AS viewport_height,
      pg_catalog.max(e.screen_width) AS screen_width,
      pg_catalog.max(e.screen_height) AS screen_height,
      pg_catalog.max(e.hardware_concurrency) AS hardware_concurrency,
      pg_catalog.max(e.device_memory_gb) AS device_memory_gb
    FROM scoped e
    GROUP BY e.session_id
  ),
  signed AS MATERIALIZED (
    SELECT
      s.*,
      pg_catalog.concat_ws(
        '|',
        coalesce(s.country_code,''),
        coalesce(s.timezone,''),
        coalesce(s.device_type,''),
        coalesce(s.browser_family,''),
        coalesce(s.os_family,''),
        coalesce(s.language,''),
        coalesce(s.viewport_width::text,''),
        coalesce(s.viewport_height::text,''),
        coalesce(s.screen_width::text,''),
        coalesce(s.screen_height::text,''),
        coalesce(s.hardware_concurrency::text,''),
        coalesce(s.device_memory_gb::text,'')
      ) AS technical_signature
    FROM session_base s
  ),
  signature_stats AS MATERIALIZED (
    SELECT
      s.technical_signature,
      pg_catalog.count(*) FILTER (WHERE s.has_content_view AND NOT s.explicit_test) AS valid_sessions,
      pg_catalog.count(*) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test AND s.has_first_interaction
      ) AS interaction_sessions,
      pg_catalog.count(*) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test AND s.has_any_action
      ) AS action_sessions,
      pg_catalog.avg(s.max_engaged_ms) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test
      ) AS avg_engaged_ms
    FROM signed s
    GROUP BY s.technical_signature
  ),
  classified AS MATERIALIZED (
    SELECT
      s.*,
      (
        NOT s.explicit_test
        AND s.has_content_view
        AND coalesce(g.valid_sessions,0) >= 10
        AND coalesce(g.interaction_sessions,0) = 0
        AND coalesce(g.action_sessions,0) = 0
        AND coalesce(g.avg_engaged_ms,0) < 10000
      ) AS suspected_automation
    FROM signed s
    LEFT JOIN signature_stats g USING (technical_signature)
  ),
  enriched AS MATERIALIZED (
    SELECT
      c.*,
      (NOT c.explicit_test AND c.has_content_view AND NOT c.suspected_automation) AS analysis_eligible,
      (
        NOT c.explicit_test
        AND c.has_content_view
        AND NOT c.suspected_automation
        AND (
          c.max_engaged_ms >= 10000
          OR c.has_first_interaction
          OR c.evidence_verified
          OR c.hiring_intent
        )
      ) AS engaged,
      (
        NOT c.explicit_test
        AND c.has_content_view
        AND NOT c.suspected_automation
        AND c.evidence_reached
        AND (
          c.max_engaged_ms >= 5000
          OR c.evidence_verified
          OR c.hiring_intent
        )
      ) AS evidence_engaged,
      CASE
        WHEN pg_catalog.lower(c.source_raw) LIKE 'linkedin%' THEN 'LinkedIn'
        WHEN pg_catalog.lower(c.source_raw) = 'cv' THEN 'CV'
        WHEN pg_catalog.lower(c.source_raw) IN ('x','twitter') THEN 'X'
        WHEN pg_catalog.lower(c.source_raw) = 'facebook' THEN 'Facebook'
        WHEN pg_catalog.lower(c.source_raw) = 'whatsapp' THEN 'WhatsApp'
        WHEN pg_catalog.lower(c.source_raw) = 'email' THEN 'Email'
        WHEN pg_catalog.lower(c.source_raw) = 'outreach' THEN 'Outreach'
        WHEN pg_catalog.lower(c.source_raw) = 'application' THEN 'Application'
        WHEN pg_catalog.lower(c.source_raw) = 'direct/unknown' THEN 'Direct / unknown'
        ELSE 'Other'
      END AS normalized_channel
    FROM classified c
  ),
  quality_summary AS (
    SELECT
      pg_catalog.count(*) AS recorded_sessions,
      pg_catalog.count(*) FILTER (WHERE explicit_test) AS explicit_test_sessions,
      pg_catalog.count(*) FILTER (WHERE NOT explicit_test AND NOT has_content_view) AS telemetry_only_sessions,
      pg_catalog.count(*) FILTER (WHERE suspected_automation) AS suspected_automation_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible) AS analysis_eligible_sessions,
      pg_catalog.count(*) FILTER (WHERE engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND evidence_reached) AS evidence_reached_sessions,
      pg_catalog.count(*) FILTER (WHERE evidence_engaged) AS evidence_engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND exploration_action) AS exploration_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND hiring_intent) AS hiring_intent_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_impact) AS impact_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_governance) AS governance_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_certifications) AS certification_sessions,
      pg_catalog.round(
        coalesce(
          pg_catalog.avg(max_engaged_ms) FILTER (WHERE analysis_eligible),0
        ) / 1000.0,
        1
      ) AS avg_engaged_seconds,
      pg_catalog.round(
        coalesce(
          (pg_catalog.percentile_cont(0.5) WITHIN GROUP (ORDER BY max_engaged_ms)
            FILTER (WHERE analysis_eligible))::numeric,
          0
        ) / 1000.0,
        1
      ) AS median_engaged_seconds
    FROM enriched
  ),
  quality_breakdown AS (
    SELECT *
    FROM (VALUES
      (1,'Analysis eligible',(SELECT analysis_eligible_sessions FROM quality_summary)),
      (2,'Engaged',(SELECT engaged_sessions FROM quality_summary)),
      (3,'Evidence reached',(SELECT evidence_reached_sessions FROM quality_summary)),
      (4,'Evidence engaged',(SELECT evidence_engaged_sessions FROM quality_summary)),
      (5,'Evidence verified',(SELECT evidence_verified_sessions FROM quality_summary)),
      (6,'Hiring intent',(SELECT hiring_intent_sessions FROM quality_summary))
    ) AS x(sort_order,stage,sessions)
  ),
  excluded_breakdown AS (
    SELECT *
    FROM (VALUES
      (1,'Telemetry only',(SELECT telemetry_only_sessions FROM quality_summary)),
      (2,'Suspected automation',(SELECT suspected_automation_sessions FROM quality_summary)),
      (3,'Explicit test',(SELECT explicit_test_sessions FROM quality_summary))
    ) AS x(sort_order,category,sessions)
  ),
  normalized_channels AS (
    SELECT
      e.normalized_channel AS channel,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_reached) AS evidence_reached_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE e.hiring_intent) AS hiring_intent_sessions,
      pg_catalog.round(pg_catalog.avg(e.max_engaged_ms) / 1000.0,1) AS avg_engaged_seconds
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY e.normalized_channel
    ORDER BY sessions DESC
  ),
  campaigns AS (
    SELECT
      e.normalized_channel AS channel,
      e.source_raw AS source,
      e.campaign_raw AS campaign,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE e.hiring_intent) AS hiring_intent_sessions
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY e.normalized_channel,e.source_raw,e.campaign_raw
    ORDER BY sessions DESC
    LIMIT 40
  ),
  countries AS (
    SELECT
      coalesce(e.country_code,'unknown') AS country_code,
      pg_catalog.count(*) AS sessions
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY coalesce(e.country_code,'unknown')
    ORDER BY sessions DESC
  ),
  devices AS (
    SELECT
      coalesce(e.device_type,'unknown') AS device_type,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.round(pg_catalog.avg(e.max_engaged_ms) / 1000.0,1) AS avg_engaged_seconds
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY coalesce(e.device_type,'unknown')
    ORDER BY sessions DESC
  ),
  action_tiers AS (
    SELECT *
    FROM (VALUES
      (1,'Exploration',(SELECT exploration_sessions FROM quality_summary)),
      (2,'Evidence verification',(SELECT evidence_verified_sessions FROM quality_summary)),
      (3,'Hiring intent',(SELECT hiring_intent_sessions FROM quality_summary))
    ) AS x(sort_order,tier,sessions)
  ),
  automation_meta AS (
    SELECT
      pg_catalog.count(*) AS signatures
    FROM signature_stats
    WHERE valid_sessions >= 10
      AND interaction_sessions = 0
      AND action_sessions = 0
      AND coalesce(avg_engaged_ms,0) < 10000
  )
  SELECT pg_catalog.jsonb_build_object(
    'generated_at', v_now,
    'requested_since', v_requested_since,
    'quality_since', v_quality_since,
    'quality_tracking_version', 5,
    'quality_summary', coalesce(
      (SELECT pg_catalog.to_jsonb(q) FROM quality_summary q),
      '{}'::jsonb
    ),
    'quality_funnel', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM quality_breakdown x),
      '[]'::jsonb
    ),
    'excluded_traffic', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM excluded_breakdown x),
      '[]'::jsonb
    ),
    'normalized_channels', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM normalized_channels x),
      '[]'::jsonb
    ),
    'campaigns', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM campaigns x),
      '[]'::jsonb
    ),
    'countries', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM countries x),
      '[]'::jsonb
    ),
    'devices', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM devices x),
      '[]'::jsonb
    ),
    'action_tiers', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM action_tiers x),
      '[]'::jsonb
    ),
    'automation_rule', pg_catalog.jsonb_build_object(
      'minimum_repeated_signature_sessions',10,
      'requires_zero_interaction_sessions',true,
      'requires_zero_action_sessions',true,
      'maximum_signature_average_engaged_ms',10000,
      'suspected_signature_count',(SELECT signatures FROM automation_meta)
    )
  )
  INTO v_result;

  RETURN v_result;
END;
$function$
;

REVOKE ALL ON FUNCTION public.careersite_hiring_intelligence_v1(text,integer,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_intelligence_v1(text,integer,text)
  TO anon, authenticated, service_role;
