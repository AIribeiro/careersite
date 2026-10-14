-- Canonicalize only the two confirmed aliases; campaign/role tags stay intact.
CREATE OR REPLACE FUNCTION public.careersite_normalize_threads_event()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
  IF lower(btrim(NEW.attribution_source)) IN ('thre','threads') THEN
    NEW.attribution_source := 'Threads';
  END IF;
  IF lower(btrim(NEW.utm_source)) IN ('thre','threads') THEN
    NEW.utm_source := 'Threads';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_normalize_threads_event() FROM PUBLIC;
CREATE OR REPLACE TRIGGER careersite_normalize_threads_event
BEFORE INSERT OR UPDATE OF attribution_source,utm_source
ON public.careersite_analytics_events FOR EACH ROW
EXECUTE FUNCTION public.careersite_normalize_threads_event();

-- Recompute downstream views from the same events, not summed session totals.
UPDATE public.careersite_analytics_events
SET attribution_source = CASE WHEN lower(btrim(attribution_source)) IN ('thre','threads')
    THEN 'Threads' ELSE attribution_source END,
    utm_source = CASE WHEN lower(btrim(utm_source)) IN ('thre','threads')
    THEN 'Threads' ELSE utm_source END
WHERE (lower(btrim(attribution_source)) IN ('thre','threads') AND attribution_source <> 'Threads')
   OR (lower(btrim(utm_source)) IN ('thre','threads') AND utm_source <> 'Threads');

-- Preserve the deployed quality model and its grants; add one explicit channel.
DO $$
DECLARE definition text;
BEGIN
  SELECT pg_get_functiondef('public.careersite_attribution_integrity_v1(integer,text)'::regprocedure)
    INTO definition;
  IF strpos(definition, 'then ''Threads''') = 0 THEN
    IF strpos(definition, 'when base_src=''cv'' then ''CV''') = 0 THEN
      RAISE EXCEPTION 'Attribution model changed; review before applying';
    END IF;
    definition := replace(definition, 'when base_src=''cv'' then ''CV''',
      'when base_src in (''thre'',''threads'') then ''Threads'' when base_src=''cv'' then ''CV''');
    EXECUTE definition;
  END IF;
END;
$$;
