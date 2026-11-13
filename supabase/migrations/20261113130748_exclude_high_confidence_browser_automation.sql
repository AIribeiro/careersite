-- Store a coarse webdriver signal; retain raw event data unchanged otherwise.
ALTER TABLE public.careersite_analytics_events
 ADD COLUMN IF NOT EXISTS browser_automation boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS public.careersite_suspected_automation_sessions_v1 (
 session_id uuid PRIMARY KEY,
 reason text NOT NULL CHECK(reason='short_repeated_browser_signature'),
 classified_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.careersite_suspected_automation_sessions_v1 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.careersite_suspected_automation_sessions_v1 FROM PUBLIC,anon,authenticated;

WITH sessions AS (
 SELECT e.session_id,
  (min(e.occurred_at) AT TIME ZONE 'Europe/Stockholm')::date AS local_day,
  count(*) FILTER(WHERE e.event_name='page_view') AS page_views,
  count(*) FILTER(WHERE e.event_name IN
   ('first_interaction','navigation_click','article_click','cv_download','email_click','linkedin_click','article_share')) AS actions,
  coalesce(max(e.engaged_ms),0) AS engaged_ms,
  extract(epoch FROM max(e.occurred_at)-min(e.occurred_at)) AS duration_seconds,
  max(e.browser_family) FILTER(WHERE e.browser_family IS NOT NULL) AS browser,
  max(e.os_family) FILTER(WHERE e.os_family IS NOT NULL) AS operating_system,
  max(e.timezone) FILTER(WHERE e.timezone IS NOT NULL) AS tz,
  max(e.country_code) FILTER(WHERE e.country_code IS NOT NULL) AS country
 FROM public.careersite_analytics_events e
 WHERE e.occurred_at >= timestamptz '2026-11-01 00:00:00+01'
 GROUP BY e.session_id
), candidates AS (
 SELECT * FROM sessions WHERE browser='Chrome' AND operating_system='Linux'
  AND tz='UTC' AND country='US' AND page_views=1 AND actions=0
  AND engaged_ms<=10000 AND duration_seconds<=45
), days_with_cohort AS (
 SELECT local_day FROM candidates GROUP BY local_day HAVING count(*)>=10
)
INSERT INTO public.careersite_suspected_automation_sessions_v1(session_id,reason)
SELECT c.session_id,'short_repeated_browser_signature'
FROM candidates c JOIN days_with_cohort d USING(local_day)
ON CONFLICT(session_id) DO NOTHING;

CREATE OR REPLACE VIEW public.careersite_reporting_events_v1
WITH (security_invoker=true) AS
SELECT e.* FROM public.careersite_analytics_events AS e
WHERE NOT EXISTS (
 SELECT 1 FROM public.careersite_internal_qa_sessions_v1 AS qa
 WHERE qa.session_id=e.session_id
)
AND NOT EXISTS (
 SELECT 1 FROM public.careersite_suspected_automation_sessions_v1 AS bot
 WHERE bot.session_id=e.session_id
)
AND NOT coalesce(e.browser_automation,false)
AND NOT (
 lower(coalesce(e.attribution_source,''))='internal_qa'
 AND lower(coalesce(e.attribution_role,''))='smoke'
);
REVOKE ALL ON public.careersite_reporting_events_v1 FROM PUBLIC,anon,authenticated;
NOTIFY pgrst, 'reload schema';
