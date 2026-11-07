-- Correct portfolio reach accounting without changing existing event collection.
-- The reporting RPC already maintains canonical "views" that exclude parallel
-- article-page page_view records where an article_view represents the open.
-- Site sessions are deduplicated across page/article view events; content views
-- are the canonical view-event count. Preserve the existing security context,
-- return type, grants and all other reporting fields.
DO $migration$
DECLARE
    original_definition text;
    updated_definition text;
    needle text := $needle$'page_views',(SELECT count(*) FROM views v WHERE v.kind='page'),$needle$;
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO original_definition
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname = 'careersite_content_intelligence_v2';

    IF original_definition IS NULL THEN
        RAISE EXCEPTION 'Missing public.careersite_content_intelligence_v2';
    END IF;

    IF strpos(original_definition, $needle$'site_sessions',$needle$) > 0 THEN
        RETURN; -- Already deployed.
    END IF;

    IF strpos(original_definition, needle) = 0 THEN
        RAISE EXCEPTION 'The content RPC quality section has changed; review before patching';
    END IF;

    updated_definition := replace(
        original_definition,
        needle,
        $replacement$'page_views',(SELECT count(*) FROM views v WHERE v.kind='page'),
      'site_sessions',(SELECT count(DISTINCT v.session_id) FROM views v),
      'site_views',(SELECT count(*) FROM views v),$replacement$
    );
    EXECUTE updated_definition;
END
$migration$;
