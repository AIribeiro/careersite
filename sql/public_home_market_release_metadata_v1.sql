-- Exposes only the timestamp and fixed public labels of the latest
-- PUBLISHED Swedish AI & Data Market Review for the What's New banner.
-- A routine data revision is not a new edition; only publication qualifies.
-- No draft material, confidential evidence, client data or private reports.
CREATE OR REPLACE FUNCTION public.portfolio_public_market_release_timestamp_v1()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT jsonb_build_object(
    'type', 'New market review',
    'title', 'Swedish AI & Data Market Review',
    'description', 'The latest published Swedish AI & Data Market Review is available, including the Executive and Jobseeker Editions.',
    'date', e.published_at,
    'href', '?page=advisory-market-signals',
    'cta', 'Read the latest review'
  )
  FROM public.portfolio_market_signal_editions AS e
  WHERE e.status = 'published' AND e.published_at IS NOT NULL
  ORDER BY e.published_at DESC
  LIMIT 1;
$$;
REVOKE ALL ON FUNCTION public.portfolio_public_market_release_timestamp_v1() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.portfolio_public_market_release_timestamp_v1() TO anon, authenticated;
