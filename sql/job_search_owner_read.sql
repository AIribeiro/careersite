-- Owner-only read access for the private Job Search Analytics tab.
-- Same signed-in owner identity as the portfolio CMS; no anonymous access.
ALTER TABLE public.job_search_analytics ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON public.job_search_analytics TO authenticated;
CREATE POLICY job_search_owner_read ON public.job_search_analytics
FOR SELECT TO authenticated USING (
 (SELECT auth.uid()) IS NOT NULL
 AND lower(coalesce((SELECT auth.jwt())->>'email','')) = 'jair.ribeiro@outlook.it'
 AND coalesce((SELECT auth.jwt())->>'is_anonymous','false') = 'false'
);
