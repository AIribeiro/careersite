-- Preserve consistent audience-filtered attribution audit measures.
DO $$
DECLARE f record; definition text; changed integer:=0;
BEGIN
 FOR f IN SELECT p.oid,p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='public' AND p.proname IN (
   'careersite_attribution_coverage_v1','careersite_attribution_integrity_v1',
   'careersite_cv_attribution_audit_v1'
  )
 LOOP
  definition:=pg_get_functiondef(f.oid);
  IF position('public.careersite_analytics_events' IN definition)=0
   THEN RAISE EXCEPTION 'Expected raw analytics source missing in %',f.proname;
  END IF;
  EXECUTE replace(definition,'public.careersite_analytics_events','public.careersite_reporting_events_v1');
  changed:=changed+1;
 END LOOP;
 IF changed<>3 THEN RAISE EXCEPTION 'Expected three attribution read paths, got %',changed; END IF;
END $$;
