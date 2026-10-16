-- Move recruitment outcomes, market evidence and forecasts behind owner auth.
-- Keep original data-returning functions intact under private names, with
-- their public EXECUTE grants revoked. Public-name wrappers verify the
-- authenticated Supabase owner JWT before returning the unchanged report.
--
-- The owner identity matches the existing CMS and timing-table update policy.
DO $hiring_acl$
DECLARE
    f record;
    original_signature text;
    full_arguments text;
    inner_name text;
    call_arguments text;
BEGIN
    FOR f IN
        SELECT p.oid, p.proname, pg_get_function_identity_arguments(p.oid) AS identity_args,
               pg_get_function_arguments(p.oid) AS definition_args
        FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.proname IN (
            'careersite_public_job_summary_v1',
            'careersite_public_market_summary_v1',
            'careersite_public_market_history_v1',
            'careersite_public_hiring_inputs_v1',
            'careersite_public_conversion_quality_v1',
            'careersite_public_pipeline_health_v1',
            'careersite_public_rejection_summary_v1',
            'careersite_hiring_intelligence_v1'
          )
        ORDER BY p.proname
    LOOP
        original_signature := f.identity_args;
        full_arguments := f.definition_args;
        inner_name := '__owner_inner_' || f.proname;
        call_arguments := CASE f.proname
            WHEN 'careersite_public_job_summary_v1' THEN 'p_days'
            WHEN 'careersite_hiring_intelligence_v1' THEN 'p_token, p_days, p_window'
            ELSE ''
        END;

        EXECUTE format(
            'ALTER FUNCTION public.%I(%s) RENAME TO %I',
            f.proname, original_signature, inner_name
        );
        EXECUTE format(
            'REVOKE EXECUTE ON FUNCTION public.%I(%s) FROM PUBLIC, anon, authenticated',
            inner_name, original_signature
        );

        EXECUTE format($wrapper$
            CREATE FUNCTION public.%I(%s)
            RETURNS jsonb
            LANGUAGE plpgsql SECURITY DEFINER
            SET search_path TO ''
            AS $owner_only$
            BEGIN
                IF coalesce(auth.jwt() ->> 'role', '') <> 'service_role'
                   AND (
                     auth.uid() IS DISTINCT FROM '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
                     OR lower(coalesce(auth.jwt() ->> 'email','')) <> 'jair.ribeiro@outlook.it'
                     OR coalesce(auth.jwt() ->> 'is_anonymous','false') <> 'false'
                   )
                THEN
                    RAISE EXCEPTION 'Owner authentication is required'
                        USING ERRCODE = '42501';
                END IF;
                RETURN public.%I(%s);
            END;
            $owner_only$;
        $wrapper$, f.proname, full_arguments, inner_name, call_arguments);

        EXECUTE format(
            'REVOKE EXECUTE ON FUNCTION public.%I(%s) FROM PUBLIC, anon',
            f.proname, original_signature
        );
        EXECUTE format(
            'GRANT EXECUTE ON FUNCTION public.%I(%s) TO authenticated, service_role',
            f.proname, original_signature
        );
    END LOOP;
END;
$hiring_acl$;

-- The previously anonymous date-only hiring projection is also private.
-- Updating this row still uses its pre-existing owner-write policies.
DROP POLICY IF EXISTS public_hiring_timing_read
  ON public.careersite_public_hiring_timing_v2;
DROP POLICY IF EXISTS public_hiring_timing_owner_select
  ON public.careersite_public_hiring_timing_v2;
CREATE POLICY public_hiring_timing_owner_select
  ON public.careersite_public_hiring_timing_v2
  FOR SELECT TO authenticated
  USING (
    (SELECT auth.uid()) = '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
    AND lower(coalesce(auth.jwt() ->> 'email', '')) = 'jair.ribeiro@outlook.it'
    AND coalesce(auth.jwt() ->> 'is_anonymous','false') = 'false'
  );
REVOKE SELECT ON public.careersite_public_hiring_timing_v2 FROM PUBLIC, anon;
GRANT SELECT ON public.careersite_public_hiring_timing_v2 TO authenticated, service_role;
