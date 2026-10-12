-- Defensive hardening: anonymous visitors may read published articles under
-- RLS, but must never have table-level CMS mutation privileges.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON public.careersite_articles FROM anon;

-- The public Analytics feature must not expose private recruitment rows,
-- regardless of RLS or RPC ownership configuration.
REVOKE SELECT, INSERT, UPDATE, DELETE
ON public.job_search_analytics FROM anon;
REVOKE SELECT, INSERT, UPDATE, DELETE
ON public.job_market_insights FROM anon;
