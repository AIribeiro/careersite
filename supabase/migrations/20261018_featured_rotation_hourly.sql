-- Hourly database reconciliation is sufficient for the featured-article rule.
-- Publishing still triggers an immediate database sync, and public page render
-- selects the highlight using the 24-hour deadline and current readership.
-- The job is a fallback for keeping the persisted featured flag up to date.
DO $$
DECLARE v_id bigint;
BEGIN
  SELECT jobid INTO v_id
  FROM cron.job
  WHERE jobname = 'careersite-featured-rotation';
  IF v_id IS NULL THEN
    RAISE EXCEPTION 'Expected existing featured rotation job not found';
  END IF;
  PERFORM cron.alter_job(v_id, schedule := '0 * * * *');
END;
$$;
