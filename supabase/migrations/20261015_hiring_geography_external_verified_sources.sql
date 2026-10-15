-- Curated, traceable vacancy-location evidence for cases where the owner's
-- application event lacks location and the linked Jobwise corpus has no match.
-- Never guess role eligibility from office city; this table affects descriptive
-- geographic coverage only, not hiring odds.
CREATE TABLE IF NOT EXISTS public.hiring_geography_external_evidence (
    employer_key text NOT NULL,
    role_key text NOT NULL,
    advertised_location text NOT NULL,
    work_model text,
    country text,
    source_url text NOT NULL,
    source_type text NOT NULL CHECK (source_type IN ('official_employer','verified_job_board')),
    checked_on date NOT NULL,
    source_note text,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (employer_key,role_key,source_url)
);
ALTER TABLE public.hiring_geography_external_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.hiring_geography_external_evidence FROM PUBLIC,anon;
GRANT SELECT ON TABLE public.hiring_geography_external_evidence TO authenticated;
DROP POLICY IF EXISTS hiring_geography_external_owner_read
    ON public.hiring_geography_external_evidence;
CREATE POLICY hiring_geography_external_owner_read
    ON public.hiring_geography_external_evidence FOR SELECT
    TO authenticated USING (
        (SELECT auth.uid()) IS NOT NULL
        AND lower(coalesce((SELECT auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
        AND coalesce((SELECT auth.jwt())->>'is_anonymous','false')='false'
    );
INSERT INTO public.hiring_geography_external_evidence (
    employer_key,role_key,advertised_location,work_model,country,
    source_url,source_type,checked_on,source_note
) VALUES
('cgi','director business-driven ai','Göteborg, Västra Götaland',NULL,'Sweden',
'https://cgi.njoyn.com/corp/xweb/xweb.asp?JobId=J0726-1069&NTKN=c&clid=21001&lang=10&page=JobDetails',
'official_employer',date '2026-10-15','Employer vacancy page; job id J0726-1069'),
('leovegas mobile gaming group','ai strategy and transformation lead','Stockholm, Sweden',
'Hybrid','Sweden',
'https://jobs.ashbyhq.com/leovegasgroup/600e207b-a3b0-43b7-9f38-c1e93623ee21',
'official_employer',date '2026-10-15','Employer ATS role and workplace type'),
('hcltech','client delivery director (husqvarna group)','Jönköping','', 'Sweden',
'https://se.indeed.com/viewjob?jk=40a9e66db521ea64',
'verified_job_board',date '2026-10-15','Job-board posting; location not an employer-confirmed work arrangement')
ON CONFLICT DO NOTHING;
