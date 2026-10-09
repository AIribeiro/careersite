-- Owner-only, quality-screened action sessions for 28d vs preceding 28d.
-- No visitor identities, raw sessions, or event payloads leave the database.
CREATE OR REPLACE FUNCTION public.careersite_hiring_predictor_actions_v1()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_end date := (pg_catalog.now() AT TIME ZONE 'Europe/Stockholm')::date;
    v_result jsonb;
BEGIN
    IF auth.uid() IS NULL
      OR pg_catalog.lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
      OR coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
    THEN
        RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE='42501';
    END IF;

    WITH recent_events AS MATERIALIZED (
        SELECT e.*
        FROM public.careersite_analytics_events e
        WHERE (e.occurred_at AT TIME ZONE 'Europe/Stockholm')::date
              BETWEEN v_end - 55 AND v_end
    ), sessions AS MATERIALIZED (
        SELECT e.session_id,
               (pg_catalog.min(e.occurred_at) AT TIME ZONE 'Europe/Stockholm')::date AS d,
               pg_catalog.bool_or(coalesce(e.tracking_version,0) >= 5) AS has_v5,
               pg_catalog.bool_or(e.event_name IN ('page_view','article_view')) AS has_content,
               pg_catalog.bool_or(e.event_name='first_interaction') AS interacted,
               pg_catalog.bool_or(e.event_name IN (
                    'cv_download','email_click','linkedin_click','cta_click','article_card_click','article_share'
               )) AS acted,
               pg_catalog.bool_or(
                   pg_catalog.lower(coalesce(e.attribution_source,''))='application'
                   AND pg_catalog.lower(coalesce(e.attribution_role,''))='test'
               ) AS explicit_test,
               pg_catalog.bool_or(e.event_name='cv_download') AS cv_download,
               pg_catalog.bool_or(e.event_name='email_click' OR
                                   (e.event_name='linkedin_click' AND e.page <> 'certifications')) AS contact_click,
               pg_catalog.max(coalesce(e.engaged_ms,0)) AS active_ms,
               pg_catalog.concat_ws('|',coalesce(pg_catalog.max(e.country_code),''),
                   coalesce(pg_catalog.max(e.timezone),''),
                   coalesce(pg_catalog.max(e.device_type),''),
                   coalesce(pg_catalog.max(e.browser_family),''),
                   coalesce(pg_catalog.max(e.os_family),''),
                   coalesce(pg_catalog.max(e.language),''),
                   coalesce(pg_catalog.max(e.viewport_width)::text,''),
                   coalesce(pg_catalog.max(e.viewport_height)::text,''),
                   coalesce(pg_catalog.max(e.screen_width)::text,''),
                   coalesce(pg_catalog.max(e.screen_height)::text,''),
                   coalesce(pg_catalog.max(e.hardware_concurrency)::text,''),
                   coalesce(pg_catalog.max(e.device_memory_gb)::text,'')) AS technical_signature
        FROM recent_events e
        GROUP BY e.session_id
    ), signatures AS MATERIALIZED (
        SELECT technical_signature,
               pg_catalog.count(*) FILTER (WHERE has_v5 AND has_content AND NOT explicit_test) AS valid_sessions,
               pg_catalog.count(*) FILTER (WHERE has_v5 AND has_content AND NOT explicit_test AND interacted) AS interactions,
               pg_catalog.count(*) FILTER (WHERE has_v5 AND has_content AND NOT explicit_test AND acted) AS actions,
               pg_catalog.avg(active_ms) FILTER (WHERE has_v5 AND has_content AND NOT explicit_test) AS mean_ms
        FROM sessions
        GROUP BY technical_signature
    ), qualified AS (
        SELECT s.*
        FROM sessions s JOIN signatures t USING (technical_signature)
        WHERE s.has_v5 AND s.has_content AND NOT s.explicit_test
          AND NOT (t.valid_sessions >= 10 AND t.interactions = 0
                   AND t.actions = 0 AND coalesce(t.mean_ms,0) < 10000)
    )
    SELECT pg_catalog.jsonb_build_object(
        'quality_checked', true,
        'includes_partial_today', true,
        'recent_from', (v_end - 27)::text,
        'previous_from', (v_end - 55)::text,
        'through', v_end::text,
        'cv_download_sessions', pg_catalog.jsonb_build_object(
            'recent', pg_catalog.count(*) FILTER (WHERE d >= v_end-27 AND cv_download),
            'previous', pg_catalog.count(*) FILTER (WHERE d < v_end-27 AND cv_download)
        ),
        'contact_click_sessions', pg_catalog.jsonb_build_object(
            'recent', pg_catalog.count(*) FILTER (WHERE d >= v_end-27 AND contact_click),
            'previous', pg_catalog.count(*) FILTER (WHERE d < v_end-27 AND contact_click)
        )
    ) INTO v_result FROM qualified;
    RETURN v_result;
END; $$;
REVOKE ALL ON FUNCTION public.careersite_hiring_predictor_actions_v1() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_predictor_actions_v1() TO authenticated;
