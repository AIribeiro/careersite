-- Applied to Supabase project rnqweoxtynelfirffmlr on 2026-11-09.
-- Ranking signal for Thinking sections. View counts, never visitor/session counts.
-- Calendar boundaries follow Europe/Stockholm (including DST), not browser locale.
-- Tie breakers, in order: last hour, today, yesterday, this week,
-- last week, this month, last month, this year.
CREATE OR REPLACE FUNCTION public.careersite_thinking_rank_windows_v2()
RETURNS TABLE (
  section_key text,
  last_hour bigint,
  today bigint,
  yesterday bigint,
  this_week bigint,
  last_week bigint,
  this_month bigint,
  last_month bigint,
  this_year bigint,
  as_of timestamptz
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $function$
  WITH clock AS (
    SELECT
      now() AS checked_at,
      timezone('Europe/Stockholm', now()) AS local_clock,
      coalesce(
        (SELECT c.reset_at FROM public.careersite_analytics_admin_config AS c LIMIT 1),
        '-infinity'::timestamptz
      ) AS reset_at
  ),
  periods AS (
    SELECT
      c.checked_at,
      c.reset_at,
      c.checked_at - interval '60 minutes' AS hour_start,
      date_trunc('day', c.local_clock) AT TIME ZONE 'Europe/Stockholm' AS today_start,
      (date_trunc('day', c.local_clock) - interval '1 day') AT TIME ZONE 'Europe/Stockholm' AS yesterday_start,
      date_trunc('week', c.local_clock) AT TIME ZONE 'Europe/Stockholm' AS week_start,
      (date_trunc('week', c.local_clock) - interval '1 week') AT TIME ZONE 'Europe/Stockholm' AS last_week_start,
      date_trunc('month', c.local_clock) AT TIME ZONE 'Europe/Stockholm' AS month_start,
      (date_trunc('month', c.local_clock) - interval '1 month') AT TIME ZONE 'Europe/Stockholm' AS last_month_start,
      date_trunc('year', c.local_clock) AT TIME ZONE 'Europe/Stockholm' AS year_start
    FROM clock AS c
  ),
  totals AS (
    SELECT
      CASE
        WHEN a.kind = 'Weekly Brief' OR a.category = 'Weekly AI' THEN 'weekly_ai'
        WHEN a.kind = 'Executive Briefing' THEN 'briefings'
        ELSE 'articles'
      END AS section_key,
      count(*) FILTER (WHERE e.occurred_at >= p.hour_start)::bigint AS last_hour,
      count(*) FILTER (WHERE e.occurred_at >= p.today_start)::bigint AS today,
      count(*) FILTER (
        WHERE e.occurred_at >= p.yesterday_start AND e.occurred_at < p.today_start
      )::bigint AS yesterday,
      count(*) FILTER (WHERE e.occurred_at >= p.week_start)::bigint AS this_week,
      count(*) FILTER (
        WHERE e.occurred_at >= p.last_week_start AND e.occurred_at < p.week_start
      )::bigint AS last_week,
      count(*) FILTER (WHERE e.occurred_at >= p.month_start)::bigint AS this_month,
      count(*) FILTER (
        WHERE e.occurred_at >= p.last_month_start AND e.occurred_at < p.month_start
      )::bigint AS last_month,
      count(*) FILTER (WHERE e.occurred_at >= p.year_start)::bigint AS this_year
    FROM public.careersite_analytics_events AS e
    JOIN public.careersite_articles AS a
      ON a.slug = e.article_slug AND a.status = 'published'
    CROSS JOIN periods AS p
    WHERE e.event_name = 'article_view'
      AND e.page IN ('thinking', 'briefing')
      AND e.occurred_at >= p.reset_at
      AND e.occurred_at >= least(
        p.hour_start, p.yesterday_start, p.last_week_start,
        p.last_month_start, p.year_start
      )
      AND e.occurred_at <= p.checked_at
    GROUP BY 1
  )
  SELECT
    sections.section_key,
    coalesce(t.last_hour, 0)::bigint,
    coalesce(t.today, 0)::bigint,
    coalesce(t.yesterday, 0)::bigint,
    coalesce(t.this_week, 0)::bigint,
    coalesce(t.last_week, 0)::bigint,
    coalesce(t.this_month, 0)::bigint,
    coalesce(t.last_month, 0)::bigint,
    coalesce(t.this_year, 0)::bigint,
    p.checked_at AS as_of
  FROM (
    VALUES ('weekly_ai'::text), ('briefings'::text), ('articles'::text)
  ) AS sections(section_key)
  CROSS JOIN periods AS p
  LEFT JOIN totals AS t ON t.section_key = sections.section_key;
$function$;

-- Intentionally public: only three aggregate rows, no user-supplied arguments,
-- slugs, sessions, identifying details, or raw event records.
REVOKE ALL ON FUNCTION public.careersite_thinking_rank_windows_v2() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.careersite_thinking_rank_windows_v2()
  TO anon, authenticated, service_role;