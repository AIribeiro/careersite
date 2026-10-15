-- Supabase default privileges can grant UPDATE/DELETE/TRUNCATE to
-- authenticated on newly created tables. Remove those explicitly so daily
-- forecast evidence is immutable even if a policy is accidentally broadened.
REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
ON TABLE public.careersite_hiring_forecast_history FROM authenticated;
GRANT SELECT,INSERT ON TABLE public.careersite_hiring_forecast_history TO authenticated;
