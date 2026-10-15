-- One LinkedIn source, with campaign and role evidence retained separately.
CREATE OR REPLACE FUNCTION public.careersite_normalize_linkedin_event()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE tag text;
BEGIN
  tag := lower(btrim(NEW.attribution_source));
  IF tag IN ('linkedin','linkedin_launch','linkedin?role=dailyquote') THEN
    IF tag = 'linkedin_launch' AND nullif(btrim(NEW.utm_campaign),'') IS NULL THEN
      NEW.utm_campaign := 'linkedin_launch';
    END IF;
    IF tag = 'linkedin?role=dailyquote' AND nullif(btrim(NEW.attribution_role),'') IS NULL THEN
      NEW.attribution_role := 'dailyquote';
    END IF;
    NEW.attribution_source := 'LinkedIn';
  END IF;
  tag := lower(btrim(NEW.utm_source));
  IF tag IN ('linkedin','linkedin_launch','linkedin?role=dailyquote') THEN
    IF tag = 'linkedin_launch' AND nullif(btrim(NEW.utm_campaign),'') IS NULL THEN
      NEW.utm_campaign := 'linkedin_launch';
    END IF;
    IF tag = 'linkedin?role=dailyquote' AND nullif(btrim(NEW.attribution_role),'') IS NULL THEN
      NEW.attribution_role := 'dailyquote';
    END IF;
    NEW.utm_source := 'LinkedIn';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.careersite_normalize_linkedin_event() FROM PUBLIC;
CREATE OR REPLACE TRIGGER careersite_normalize_linkedin_event
BEFORE INSERT OR UPDATE OF attribution_source,utm_source
ON public.careersite_analytics_events FOR EACH ROW
EXECUTE FUNCTION public.careersite_normalize_linkedin_event();

-- Invoke the same rule for history; no events or session IDs are added/deleted.
UPDATE public.careersite_analytics_events SET attribution_source=attribution_source
WHERE (lower(btrim(attribution_source)) IN ('linkedin','linkedin_launch','linkedin?role=dailyquote')
       AND attribution_source IS DISTINCT FROM 'LinkedIn')
   OR (lower(btrim(utm_source)) IN ('linkedin','linkedin_launch','linkedin?role=dailyquote')
       AND utm_source IS DISTINCT FROM 'LinkedIn');
