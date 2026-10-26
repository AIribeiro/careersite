-- Calendar reporting boundaries shared by all portfolio analytics.
CREATE OR REPLACE FUNCTION public.careersite_analytics_dashboard(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_expected_hash text;
  v_reset_at timestamptz;
  v_days integer;
  v_window text;
  v_requested_since timestamptz;
  v_since timestamptz;
  v_until timestamptz := now();
  v_period_label text;
  v_result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  select token_hash, reset_at
    into v_expected_hash, v_reset_at
  from public.careersite_analytics_admin_config
  where singleton = true;

  if coalesce(p_token, '') <> 'public-readonly-v1'
     and (
       v_expected_hash is null
       or encode(digest(coalesce(p_token, ''), 'sha256'), 'hex') <> v_expected_hash
     ) then
    raise exception 'invalid analytics access code' using errcode = '28000';
  end if;

  v_window := lower(coalesce(nullif(trim(p_window), ''), 'days'));
  v_days := greatest(1, least(coalesce(p_days, 30), 3650));

  if v_window = 'last_hour' then
    v_requested_since := now() - interval '1 hour';
    v_period_label := 'Last hour';
  elsif v_window = 'today' then
    v_requested_since := date_trunc('day', now() at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm';
    v_period_label := 'Today';
  elsif v_window in ('this_week','last_week','this_month','last_month','this_year') then
    v_requested_since := date_trunc(
      case when v_window like '%week' then 'week' when v_window like '%month' then 'month' else 'year' end,
      now() at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm';
    if v_window in ('last_week','last_month') then
      v_until := v_requested_since;
      v_requested_since := ((v_requested_since at time zone 'Europe/Stockholm') -
        case when v_window='last_week' then interval '1 week' else interval '1 month' end) at time zone 'Europe/Stockholm';
    end if;
    v_period_label := case v_window when 'this_week' then 'This Week' when 'last_week' then 'Last Week'
      when 'this_month' then 'This Month' when 'last_month' then 'Last Month' else 'This year' end;
  elsif v_window = 'all' then
    select coalesce(min(occurred_at),now()) into v_requested_since from public.careersite_analytics_events;
    v_period_label := 'All';
  elsif v_window = 'days' then
    v_requested_since := now() - make_interval(days => v_days);
    v_period_label := format('Last %s days', v_days);
  else
    raise exception 'invalid analytics reporting window' using errcode = '22023';
  end if;

  v_since := greatest(v_requested_since, coalesce(v_reset_at, v_requested_since));

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < v_until
      and not (
        lower(coalesce(attribution_source, '')) = 'application'
        and lower(coalesce(attribution_role, '')) = 'test'
      )
  ),
  session_rollup as (
    select
      session_id,
      min(occurred_at) as started_at,
      max(occurred_at) as last_seen_at,
      greatest(
        coalesce(max(session_elapsed_ms), 0),
        floor(extract(epoch from (max(occurred_at) - min(occurred_at))) * 1000)::bigint
      ) as elapsed_ms,
      coalesce(max(engaged_ms), 0) as engaged_ms,
      count(*) filter (where event_name='page_view' and article_slug is null and content_kind is distinct from 'article') as page_views,
      count(distinct page) filter (where event_name='page_view' and article_slug is null and content_kind is distinct from 'article') as unique_pages,
      (array_agg(page order by occurred_at) filter (where event_name='page_view' and article_slug is null and content_kind is distinct from 'article'))[1] as landing_page,
      (array_agg(page order by occurred_at desc) filter (where event_name='page_view' and article_slug is null and content_kind is distinct from 'article'))[1] as exit_page,
      min(device_type) filter (where device_type is not null) as device_type,
      min(browser_family) filter (where browser_family is not null) as browser_family,
      min(os_family) filter (where os_family is not null) as os_family,
      min(language) filter (where language is not null) as language,
      min(timezone) filter (where timezone is not null) as timezone,
      min(country_code) filter (where country_code is not null) as country_code,
      min(connection_type) filter (where connection_type is not null) as connection_type,
      min(viewport_width) filter (where viewport_width is not null) as viewport_width,
      min(viewport_height) filter (where viewport_height is not null) as viewport_height,
      min(screen_width) filter (where screen_width is not null) as screen_width,
      min(screen_height) filter (where screen_height is not null) as screen_height,
      min(referrer_host) filter (where referrer_host is not null) as referrer_host,
      coalesce(
        min(attribution_source) filter (where attribution_source is not null),
        min(utm_source) filter (where utm_source is not null),
        'direct/unknown'
      ) as attribution_source,
      min(attribution_role) filter (where attribution_role is not null) as attribution_role,
      bool_or(event_name='page_view' and article_slug is null and content_kind is distinct from 'article' and page='home') as saw_home,
      bool_or(event_name='impact_view') as saw_impact,
      bool_or(event_name='lens_view') as saw_lens,
      bool_or(event_name='cv_download') as downloaded_cv,
      bool_or(event_name='email_click') as clicked_email,
      bool_or(event_name='linkedin_click') as clicked_linkedin,
      bool_or(event_name='article_click') as clicked_article
    from scoped
    group by session_id
  ),
  session_quality as (
    select *,
      (engaged_ms >= 10000 or unique_pages >= 2 or downloaded_cv or clicked_email or clicked_linkedin or clicked_article) as engaged_session,
      (page_views <= 1) as single_page_session
    from session_rollup
  ),
  totals as (
    select jsonb_build_object(
      'events', (select count(*) from scoped),
      'recorded_views', (select count(*) from scoped where event_name='article_view' or (event_name='page_view' and article_slug is null and content_kind is distinct from 'article')),
      'sessions', count(*),
      'home_sessions', count(*) filter (where saw_home),
      'impact_sessions', count(*) filter (where saw_impact),
      'lens_sessions', count(*) filter (where saw_lens),
      'cv_sessions', count(*) filter (where downloaded_cv),
      'email_sessions', count(*) filter (where clicked_email),
      'linkedin_sessions', count(*) filter (where clicked_linkedin),
      'article_sessions', count(*) filter (where clicked_article),
      'engaged_sessions', count(*) filter (where engaged_session),
      'single_page_sessions', count(*) filter (where single_page_session),
      'avg_session_seconds', round(coalesce(avg(elapsed_ms), 0) / 1000.0, 1),
      'avg_engaged_seconds', round(coalesce(avg(engaged_ms), 0) / 1000.0, 1),
      'median_session_seconds', round(coalesce(percentile_cont(0.5) within group (order by elapsed_ms), 0)::numeric / 1000.0, 1),
      'avg_pages_per_session', round(coalesce(avg(page_views), 0), 2)
    ) as data
    from session_quality
  ),
  by_event as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.event_name), '[]'::jsonb) as data
    from (
      select event_name, count(*) as events, count(distinct session_id) as sessions
      from scoped
      where event_name <> 'engagement_ping'
      group by event_name
    ) x
  ),
  by_lens as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.lens), '[]'::jsonb) as data
    from (
      select lens, count(*) as views, count(distinct session_id) as sessions
      from scoped
      where event_name='lens_view' and lens is not null
      group by lens
    ) x
  ),
  by_attribution as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.attribution_source, x.attribution_role), '[]'::jsonb) as data
    from (
      select
        attribution_source,
        attribution_role,
        count(*) as sessions,
        count(*) filter (where saw_home) as home_sessions,
        count(*) filter (where saw_impact) as impact_sessions,
        count(*) filter (where saw_lens) as lens_sessions,
        count(*) filter (where downloaded_cv) as cv_sessions,
        count(*) filter (where clicked_email) as email_sessions,
        count(*) filter (where clicked_linkedin) as linkedin_sessions,
        count(*) filter (where clicked_article) as article_sessions,
        count(*) filter (where engaged_session) as engaged_sessions
      from session_quality
      group by attribution_source, attribution_role
    ) x
  ),
  daily as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.day), '[]'::jsonb) as data
    from (
      select
        (occurred_at at time zone 'Europe/Stockholm')::date as day,
        count(*) filter (where event_name <> 'engagement_ping') as events,
        count(distinct session_id) as sessions,
        count(distinct session_id) filter (where event_name='impact_view') as impact_sessions,
        count(distinct session_id) filter (where event_name='cv_download') as cv_sessions
      from scoped
      group by 1
    ) x
  ),
  by_device as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.device_type), '[]'::jsonb) as data
    from (
      select coalesce(device_type, 'unknown') as device_type,
             count(*) as sessions,
             count(*) filter (where engaged_session) as engaged_sessions,
             round(coalesce(avg(elapsed_ms), 0) / 1000.0, 1) as avg_session_seconds,
             round(coalesce(avg(page_views), 0), 2) as avg_pages
      from session_quality
      group by 1
    ) x
  ),
  by_browser as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.browser_family), '[]'::jsonb) as data
    from (
      select coalesce(browser_family, 'unknown') as browser_family, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_os as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.os_family), '[]'::jsonb) as data
    from (
      select coalesce(os_family, 'unknown') as os_family, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_country as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.country_code), '[]'::jsonb) as data
    from (
      select coalesce(country_code, 'unknown') as country_code, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_language as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.language), '[]'::jsonb) as data
    from (
      select coalesce(language, 'unknown') as language, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_timezone as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.timezone), '[]'::jsonb) as data
    from (
      select coalesce(timezone, 'unknown') as timezone, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_referrer as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.referrer_host), '[]'::jsonb) as data
    from (
      select coalesce(referrer_host, 'direct/unknown') as referrer_host, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_landing as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.landing_page), '[]'::jsonb) as data
    from (
      select coalesce(landing_page, 'unknown') as landing_page, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_exit as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.exit_page), '[]'::jsonb) as data
    from (
      select coalesce(exit_page, 'unknown') as exit_page, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_duration as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sort_order), '[]'::jsonb) as data
    from (
      select duration_bucket, count(*) as sessions, min(sort_order) as sort_order
      from (
        select case
          when elapsed_ms < 10000 then '<10s'
          when elapsed_ms < 30000 then '10–29s'
          when elapsed_ms < 60000 then '30–59s'
          when elapsed_ms < 120000 then '1–2m'
          when elapsed_ms < 300000 then '2–5m'
          else '5m+'
        end as duration_bucket,
        case
          when elapsed_ms < 10000 then 1
          when elapsed_ms < 30000 then 2
          when elapsed_ms < 60000 then 3
          when elapsed_ms < 120000 then 4
          when elapsed_ms < 300000 then 5
          else 6
        end as sort_order
        from session_quality
      ) b
      group by duration_bucket
    ) x
  ),
  by_hour as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.hour), '[]'::jsonb) as data
    from (
      select extract(hour from started_at at time zone 'Europe/Stockholm')::int as hour, count(*) as sessions
      from session_quality group by 1
    ) x
  ),
  by_weekday as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.weekday_index), '[]'::jsonb) as data
    from (
      select extract(isodow from started_at at time zone 'Europe/Stockholm')::int as weekday_index,
             trim(to_char(started_at at time zone 'Europe/Stockholm', 'Day')) as weekday,
             count(*) as sessions
      from session_quality group by 1, 2
    ) x
  )
  select jsonb_build_object(
    'period_window', v_window,
    'period_label', v_period_label,
    'period_days', case when v_window = 'days' then v_days else null end,
    'period_since', v_since,
    'period_until', v_until,
    'requested_since', v_requested_since,
    'reset_at', v_reset_at,
    'generated_at', now(),
    'totals', totals.data,
    'events', by_event.data,
    'lenses', by_lens.data,
    'attribution', by_attribution.data,
    'daily', daily.data,
    'devices', by_device.data,
    'browsers', by_browser.data,
    'operating_systems', by_os.data,
    'countries', by_country.data,
    'languages', by_language.data,
    'timezones', by_timezone.data,
    'referrers', by_referrer.data,
    'landing_pages', by_landing.data,
    'exit_pages', by_exit.data,
    'duration_buckets', by_duration.data,
    'hours', by_hour.data,
    'weekdays', by_weekday.data
  ) into v_result
  from totals, by_event, by_lens, by_attribution, daily, by_device, by_browser, by_os,
       by_country, by_language, by_timezone, by_referrer, by_landing, by_exit,
       by_duration, by_hour, by_weekday;

  return v_result;
end;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_content_intelligence_v2(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text, p_article_metadata jsonb DEFAULT '[]'::jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  base jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  previous_since timestamptz;
  result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (base->>'period_since')::timestamptz;
  report_now := (base->>'period_until')::timestamptz;
  previous_since := since_at - (report_now - since_at);

  WITH article_meta AS MATERIALIZED (
    SELECT
      left(coalesce(x.slug,''),160) AS slug,
      left(coalesce(x.title,''),240) AS title,
      left(coalesce(x.topic,'Uncategorized'),120) AS topic,
      left(coalesce(x.kind,'Article'),80) AS kind,
      x.published_date
    FROM pg_catalog.jsonb_to_recordset(coalesce(p_article_metadata,'[]'::jsonb))
      AS x(slug text,title text,topic text,kind text,published_date date)
    WHERE coalesce(x.slug,'') <> ''
  ),
  current_scoped AS MATERIALIZED (
    SELECT e.*,
      CASE
        WHEN e.content_kind='article' OR (e.article_slug IS NOT NULL AND e.event_name<>'article_click') THEN 'article'
        WHEN e.content_kind='page' THEN 'page'
        WHEN e.page='thinking' THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= since_at
      AND e.occurred_at < report_now
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
  ),
  previous_scoped AS MATERIALIZED (
    SELECT e.*,
      CASE
        WHEN e.content_kind='article' OR (e.article_slug IS NOT NULL AND e.event_name<>'article_click') THEN 'article'
        WHEN e.content_kind='page' THEN 'page'
        WHEN e.page='thinking' THEN 'legacy_thinking'
        ELSE 'page'
      END AS kind
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= previous_since
      AND e.occurred_at < since_at
      AND NOT (
        lower(coalesce(e.attribution_source,''))='application'
        AND lower(coalesce(e.attribution_role,''))='test'
      )
  ),
  views AS MATERIALIZED (
    SELECT c.*,
      CASE WHEN c.event_name='article_view' THEN 'article:'||c.article_slug ELSE c.page END AS content
    FROM current_scoped c
    WHERE c.event_name='article_view'
       OR (c.event_name='page_view' AND c.kind<>'article')
  ),
  previous_views AS MATERIALIZED (
    SELECT c.*,
      CASE WHEN c.event_name='article_view' THEN 'article:'||c.article_slug ELSE c.page END AS content
    FROM previous_scoped c
    WHERE c.event_name='article_view'
       OR (c.event_name='page_view' AND c.kind<>'article')
  ),
  content_sessions AS MATERIALIZED (
    SELECT
      c.kind,
      c.page,
      CASE WHEN c.kind='article' THEN c.article_slug END AS slug,
      c.session_id,
      count(*) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS views,
      min(c.occurred_at) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS opened,
      max(CASE WHEN c.kind='article' THEN c.article_engaged_ms ELSE c.page_engaged_ms END) AS active_ms,
      max(c.scroll_depth) AS depth,
      bool_or(coalesce(c.tracking_version,0)>=3) AS measured,
      bool_or(coalesce(c.tracking_version,0)>=4) AS measured_v4,
      count(*) FILTER (WHERE c.event_name='article_share') AS shares,
      bool_or(c.event_name IN ('cv_download','email_click','linkedin_click')) AS action_on_content
    FROM current_scoped c
    WHERE c.event_name<>'article_click'
    GROUP BY c.kind,c.page,CASE WHEN c.kind='article' THEN c.article_slug END,c.session_id
  ),
  session_last_actions AS MATERIALIZED (
    SELECT session_id,
      max(occurred_at) FILTER (WHERE event_name='cv_download') AS last_cv,
      max(occurred_at) FILTER (WHERE event_name IN ('email_click','linkedin_click')) AS last_contact
    FROM current_scoped GROUP BY session_id
  ),
  session_last_portfolio AS MATERIALIZED (
    SELECT session_id,max(occurred_at) AS last_portfolio
    FROM views WHERE kind='page' AND page<>'thinking' GROUP BY session_id
  ),
  quality_sessions AS MATERIALIZED (
    SELECT c.*,
      coalesce(a.last_cv>=c.opened,false) AS later_cv,
      coalesce(a.last_contact>=c.opened,false) AS later_contact,
      coalesce(p.last_portfolio>c.opened,false) AS later_portfolio
    FROM content_sessions c
    LEFT JOIN session_last_actions a ON a.session_id=c.session_id
    LEFT JOIN session_last_portfolio p ON p.session_id=c.session_id
    WHERE c.views>0
  ),
  performance AS MATERIALIZED (
    SELECT
      q.kind,
      coalesce(q.slug,q.page) AS content,
      count(*) AS sessions,
      sum(q.views) AS views,
      count(*) FILTER (WHERE q.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE q.active_ms>=5000) AS confirmed_sessions,
      round((avg(q.active_ms) FILTER (WHERE q.active_ms>=5000))/1000.0,1) AS avg_active_seconds,
      count(*) FILTER (WHERE q.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE q.depth>=25) AS quarter_sessions,
      count(*) FILTER (WHERE q.depth>=50) AS halfway_sessions,
      count(*) FILTER (WHERE q.depth>=75) AS three_quarter_sessions,
      count(*) FILTER (WHERE q.depth>=90) AS bottom_sessions,
      count(*) FILTER (WHERE q.depth>=90 AND q.active_ms>=30000) AS deep_read_sessions,
      sum(q.shares) AS shares,
      count(*) FILTER (WHERE q.shares>0) AS sharing_sessions,
      count(*) FILTER (WHERE q.action_on_content) AS action_sessions,
      count(*) FILTER (WHERE q.later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE q.later_contact) AS later_contact_sessions,
      count(*) FILTER (WHERE q.later_portfolio) AS later_portfolio_sessions
    FROM quality_sessions q
    GROUP BY q.kind,coalesce(q.slug,q.page)
  ),
  previous_content_sessions AS MATERIALIZED (
    SELECT
      c.kind,
      c.page,
      CASE WHEN c.kind='article' THEN c.article_slug END AS slug,
      c.session_id,
      count(*) FILTER (
        WHERE c.event_name=CASE WHEN c.kind='article' THEN 'article_view' ELSE 'page_view' END
      ) AS views,
      max(CASE WHEN c.kind='article' THEN c.article_engaged_ms ELSE c.page_engaged_ms END) AS active_ms
    FROM previous_scoped c
    WHERE c.event_name<>'article_click'
    GROUP BY c.kind,c.page,CASE WHEN c.kind='article' THEN c.article_slug END,c.session_id
  ),
  previous_performance AS MATERIALIZED (
    SELECT
      p.kind,
      coalesce(p.slug,p.page) AS content,
      count(*) FILTER (WHERE p.views>0) AS sessions,
      coalesce(sum(p.views) FILTER (WHERE p.views>0),0) AS views,
      count(*) FILTER (WHERE p.views>0 AND p.active_ms>=10000) AS engaged_sessions
    FROM previous_content_sessions p
    GROUP BY p.kind,coalesce(p.slug,p.page)
  ),
  period_comparison AS (
    SELECT
      coalesce(c.kind,p.kind) AS kind,
      coalesce(c.content,p.content) AS content,
      coalesce(c.sessions,0) AS current_sessions,
      coalesce(p.sessions,0) AS previous_sessions,
      coalesce(c.views,0) AS current_views,
      coalesce(p.views,0) AS previous_views,
      coalesce(c.engaged_sessions,0) AS current_engaged_sessions,
      coalesce(p.engaged_sessions,0) AS previous_engaged_sessions
    FROM performance c
    FULL OUTER JOIN previous_performance p
      ON p.kind=c.kind AND p.content=c.content
  ),
  ordered_views AS (
    SELECT v.*,
      lead(v.content) OVER (PARTITION BY v.session_id ORDER BY v.occurred_at,v.id) AS next_content
    FROM views v
  ),
  journeys AS (
    SELECT
      o.content AS from_content,
      o.next_content AS to_content,
      count(*) AS transitions,
      count(DISTINCT o.session_id) AS sessions
    FROM ordered_views o
    WHERE o.next_content IS NOT NULL AND o.next_content<>o.content
    GROUP BY o.content,o.next_content
    ORDER BY sessions DESC
    LIMIT 30
  ),
  session_sources AS MATERIALIZED (
    SELECT
      c.session_id,
      (array_agg(coalesce(c.attribution_source,c.utm_source,'direct/unknown') ORDER BY c.occurred_at,c.id))[1] AS channel,
      (array_agg(coalesce(c.utm_campaign,c.attribution_role,'untagged') ORDER BY c.occurred_at,c.id))[1] AS campaign,
      (array_agg(coalesce(c.device_type,'unknown') ORDER BY c.occurred_at,c.id))[1] AS device_type,
      bool_or(c.event_name='cv_download') AS cv,
      bool_or(c.event_name IN ('email_click','linkedin_click')) AS contact,
      bool_or(c.event_name='article_view') AS reader,
      max(c.engaged_ms)>=10000 AS engaged
    FROM current_scoped c
    GROUP BY c.session_id
  ),
  campaigns AS (
    SELECT
      s.channel,s.campaign,
      count(*) AS sessions,
      count(*) FILTER (WHERE s.engaged) AS engaged_sessions,
      count(*) FILTER (WHERE s.reader) AS reader_sessions,
      count(*) FILTER (WHERE s.cv) AS cv_sessions,
      count(*) FILTER (WHERE s.contact) AS contact_sessions
    FROM session_sources s
    GROUP BY s.channel,s.campaign
    ORDER BY sessions DESC
    LIMIT 40
  ),
  entry_exit AS (
    SELECT
      v.session_id,
      (array_agg(v.content ORDER BY v.occurred_at,v.id))[1] AS entry,
      (array_agg(v.content ORDER BY v.occurred_at DESC,v.id DESC))[1] AS last_content,
      count(*) AS views
    FROM views v
    GROUP BY v.session_id
  ),
  entrances AS (
    SELECT e.entry AS content,count(*) AS sessions,count(*) FILTER (WHERE e.views=1) AS single_view_sessions
    FROM entry_exit e
    GROUP BY e.entry
    ORDER BY sessions DESC
  ),
  exits AS (
    SELECT e.last_content AS content,count(*) AS sessions
    FROM entry_exit e
    GROUP BY e.last_content
    ORDER BY sessions DESC
  ),
  article_exposures AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement,
      c.element_label
    FROM current_scoped c
    WHERE c.event_name='element_impression' AND c.element_kind='article_card'
  ),
  article_clicks AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement
    FROM current_scoped c
    WHERE c.event_name='article_card_click'
  ),
  article_card_ctr AS (
    SELECT
      e.element_key,
      e.placement,
      max(e.element_label) AS label,
      count(*) AS exposed_sessions,
      count(*) FILTER (
        WHERE EXISTS(
          SELECT 1 FROM article_clicks c
          WHERE c.session_id=e.session_id AND c.element_key=e.element_key AND c.placement=e.placement
        )
      ) AS click_sessions
    FROM article_exposures e
    GROUP BY e.element_key,e.placement
    ORDER BY exposed_sessions DESC
  ),
  cta_exposures AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement,
      c.element_label
    FROM current_scoped c
    WHERE c.event_name='element_impression' AND c.element_kind='cta'
  ),
  cta_clicks AS MATERIALIZED (
    SELECT DISTINCT
      c.session_id,
      coalesce(c.element_key,'unknown') AS element_key,
      coalesce(c.element_placement,'unknown') AS placement
    FROM current_scoped c
    WHERE c.event_name='cta_click'
  ),
  cta_ctr AS (
    SELECT
      e.element_key,
      e.placement,
      max(e.element_label) AS label,
      count(*) AS exposed_sessions,
      count(*) FILTER (
        WHERE EXISTS(
          SELECT 1 FROM cta_clicks c
          WHERE c.session_id=e.session_id AND c.element_key=e.element_key AND c.placement=e.placement
        )
      ) AS click_sessions
    FROM cta_exposures e
    GROUP BY e.element_key,e.placement
    ORDER BY exposed_sessions DESC
  ),
  page_denominators AS MATERIALIZED (
    SELECT v.page,count(DISTINCT v.session_id) AS page_sessions
    FROM views v
    WHERE v.kind='page'
    GROUP BY v.page
  ),
  section_reach AS (
    SELECT
      s.page,
      coalesce(s.section_key,'unknown') AS section_key,
      max(s.section_label) AS section_label,
      d.page_sessions,
      count(DISTINCT s.session_id) AS reached_sessions
    FROM current_scoped s
    JOIN page_denominators d ON d.page=s.page
    WHERE s.event_name='section_view' AND s.content_kind='page'
    GROUP BY s.page,coalesce(s.section_key,'unknown'),d.page_sessions
    ORDER BY d.page_sessions DESC,reached_sessions DESC
  ),
  article_entry AS MATERIALIZED (
    SELECT c.session_id,min(c.occurred_at) AS article_at
    FROM current_scoped c
    WHERE c.event_name='article_view'
    GROUP BY c.session_id
  ),
  article_to_impact AS MATERIALIZED (
    SELECT a.session_id,a.article_at,min(i.occurred_at) AS impact_at
    FROM article_entry a
    JOIN current_scoped i
      ON i.session_id=a.session_id
     AND i.event_name='page_view'
     AND i.page='impact'
     AND i.occurred_at>a.article_at
    GROUP BY a.session_id,a.article_at
  ),
  article_to_impact_to_cv AS MATERIALIZED (
    SELECT a.session_id,min(c.occurred_at) AS cv_at
    FROM article_to_impact a
    JOIN current_scoped c
      ON c.session_id=a.session_id
     AND c.event_name='cv_download'
     AND c.occurred_at>a.impact_at
    GROUP BY a.session_id
  ),
  ordered_funnel AS (
    SELECT
      (SELECT count(*) FROM article_entry) AS article_sessions,
      (SELECT count(*) FROM article_to_impact) AS article_to_impact_sessions,
      (SELECT count(*) FROM article_to_impact_to_cv) AS article_to_impact_to_cv_sessions
  ),
  reader_article_counts AS MATERIALIZED (
    SELECT c.session_id,count(DISTINCT c.article_slug) AS articles
    FROM current_scoped c
    WHERE c.event_name='article_view' AND c.article_slug IS NOT NULL
    GROUP BY c.session_id
  ),
  multi_article AS (
    SELECT
      count(*) AS reader_sessions,
      count(*) FILTER (WHERE r.articles>=2) AS multi_article_sessions
    FROM reader_article_counts r
  ),
  session_entries AS MATERIALIZED (
    SELECT v.session_id,min(v.occurred_at) AS entry_at
    FROM views v
    GROUP BY v.session_id
  ),
  meaningful_events AS MATERIALIZED (
    SELECT c.session_id,c.occurred_at,
      CASE
        WHEN c.event_name='page_view' AND c.page='impact' AND c.kind='page' THEN 'case_study'
        WHEN c.event_name='cv_download' THEN 'cv'
        WHEN c.event_name IN ('email_click','linkedin_click') THEN 'contact'
        ELSE NULL
      END AS action
    FROM current_scoped c
    WHERE (c.event_name='page_view' AND c.page='impact' AND c.kind='page')
       OR c.event_name IN ('cv_download','email_click','linkedin_click')
  ),
  first_meaningful AS MATERIALIZED (
    SELECT
      e.session_id,
      m.action,
      min(m.occurred_at) AS action_at,
      extract(epoch FROM (min(m.occurred_at)-e.entry_at)) AS seconds_to_action
    FROM session_entries e
    JOIN meaningful_events m
      ON m.session_id=e.session_id AND m.occurred_at>=e.entry_at
    WHERE m.action IS NOT NULL
    GROUP BY e.session_id,m.action,e.entry_at
  ),
  time_to_action AS (
    SELECT
      f.action,
      count(*) AS sessions,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY f.seconds_to_action))::numeric,1) AS median_seconds,
      round(avg(f.seconds_to_action)::numeric,1) AS avg_seconds
    FROM first_meaningful f
    GROUP BY f.action
    ORDER BY f.action
  ),
  topic_performance AS (
    SELECT
      coalesce(m.topic,'Uncategorized') AS topic,
      count(*) AS article_sessions,
      coalesce(sum(q.views),0) AS views,
      count(*) FILTER (WHERE q.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE q.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE q.depth>=75) AS reached_75_sessions,
      count(*) FILTER (WHERE q.depth>=90) AS reached_90_sessions,
      count(*) FILTER (WHERE q.later_portfolio) AS later_portfolio_sessions,
      count(*) FILTER (WHERE q.later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE q.later_contact) AS later_contact_sessions
    FROM quality_sessions q
    LEFT JOIN article_meta m ON m.slug=q.slug
    WHERE q.kind='article'
    GROUP BY coalesce(m.topic,'Uncategorized')
    ORDER BY article_sessions DESC
  ),
  first7_sessions AS MATERIALIZED (
    SELECT
      m.slug,m.title,m.topic,m.kind,m.published_date,
      e.session_id,
      count(*) FILTER (WHERE e.event_name='article_view') AS views,
      max(e.article_engaged_ms) AS active_ms,
      max(e.scroll_depth) AS depth
    FROM article_meta m
    JOIN public.careersite_analytics_events e
      ON e.article_slug=m.slug
     AND m.published_date IS NOT NULL
     AND e.occurred_at >= m.published_date::timestamptz
     AND e.occurred_at < (m.published_date::timestamptz + interval '7 days')
     AND NOT (
       lower(coalesce(e.attribution_source,''))='application'
       AND lower(coalesce(e.attribution_role,''))='test'
     )
    GROUP BY m.slug,m.title,m.topic,m.kind,m.published_date,e.session_id
  ),
  publication_age AS (
    SELECT
      f.slug,max(f.title) AS title,max(f.topic) AS topic,max(f.kind) AS kind,max(f.published_date) AS published_date,
      count(*) FILTER (WHERE f.views>0) AS sessions,
      coalesce(sum(f.views) FILTER (WHERE f.views>0),0) AS views,
      count(*) FILTER (WHERE f.views>0 AND f.active_ms>=10000) AS engaged_sessions,
      count(*) FILTER (WHERE f.views>0 AND f.depth IS NOT NULL) AS depth_measured_sessions,
      count(*) FILTER (WHERE f.views>0 AND f.depth>=75) AS reached_75_sessions
    FROM first7_sessions f
    GROUP BY f.slug
    ORDER BY views DESC
  ),
  performance_session_values AS MATERIALIZED (
    SELECT
      c.session_id,
      coalesce(max(c.device_type) FILTER (WHERE c.device_type IS NOT NULL),'unknown') AS device_type,
      max(c.metric_value) FILTER (WHERE c.metric_name='ttfb_ms') AS ttfb_ms,
      max(c.metric_value) FILTER (WHERE c.metric_name='lcp_ms') AS lcp_ms,
      max(c.metric_value) FILTER (WHERE c.metric_name='cls') AS cls,
      max(c.metric_value) FILTER (WHERE c.metric_name='interaction_ms') AS interaction_ms
    FROM current_scoped c
    WHERE c.event_name='performance_metric'
    GROUP BY c.session_id
  ),
  experience AS (
    SELECT
      p.device_type,
      count(*) AS measured_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.ttfb_ms) FILTER (WHERE p.ttfb_ms IS NOT NULL))::numeric,1) AS p75_ttfb_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.lcp_ms) FILTER (WHERE p.lcp_ms IS NOT NULL))::numeric,1) AS p75_lcp_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.cls) FILTER (WHERE p.cls IS NOT NULL))::numeric,3) AS p75_cls,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY p.interaction_ms) FILTER (WHERE p.interaction_ms IS NOT NULL))::numeric,1) AS p75_interaction_ms,
      count(*) FILTER (WHERE p.lcp_ms>2500) AS slow_lcp_sessions,
      count(*) FILTER (WHERE p.lcp_ms>2500 AND s.engaged) AS slow_lcp_engaged_sessions,
      count(*) FILTER (WHERE p.cls>0.1) AS unstable_cls_sessions,
      count(*) FILTER (WHERE p.interaction_ms>200) AS slow_interaction_sessions
    FROM performance_session_values p
    LEFT JOIN session_sources s ON s.session_id=p.session_id
    GROUP BY p.device_type
    ORDER BY measured_sessions DESC
  )
  SELECT jsonb_build_object(
    'generated_at',now(),'period_until',report_now,
    'period_since',since_at,
    'previous_period_since',previous_since,
    'period_label',base->'period_label',
    'performance',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.sessions DESC) FROM performance p),'[]'::jsonb),
    'period_comparison',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.current_sessions DESC,p.previous_sessions DESC) FROM period_comparison p),'[]'::jsonb),
    'journeys',coalesce((SELECT jsonb_agg(to_jsonb(j)) FROM journeys j),'[]'::jsonb),
    'campaigns',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM campaigns c),'[]'::jsonb),
    'entrances',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM entrances e),'[]'::jsonb),
    'exits',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM exits e),'[]'::jsonb),
    'article_cards',coalesce((SELECT jsonb_agg(to_jsonb(a)) FROM article_card_ctr a),'[]'::jsonb),
    'cta_placements',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM cta_ctr c),'[]'::jsonb),
    'section_reach',coalesce((SELECT jsonb_agg(to_jsonb(s)) FROM section_reach s),'[]'::jsonb),
    'ordered_funnel',coalesce((SELECT to_jsonb(o) FROM ordered_funnel o),'{}'::jsonb),
    'multi_article',coalesce((SELECT to_jsonb(m) FROM multi_article m),'{}'::jsonb),
    'time_to_action',coalesce((SELECT jsonb_agg(to_jsonb(t)) FROM time_to_action t),'[]'::jsonb),
    'topic_performance',coalesce((SELECT jsonb_agg(to_jsonb(t)) FROM topic_performance t),'[]'::jsonb),
    'publication_age',coalesce((SELECT jsonb_agg(to_jsonb(p)) FROM publication_age p),'[]'::jsonb),
    'experience',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM experience x),'[]'::jsonb),
    'quality',jsonb_build_object(
      'last_event_at',(SELECT max(c.occurred_at) FROM current_scoped c),
      'new_measurement_since',(SELECT min(c.occurred_at) FROM current_scoped c WHERE coalesce(c.tracking_version,0)>=3),
      'attention_measurement_since',(SELECT min(c.occurred_at) FROM current_scoped c WHERE coalesce(c.tracking_version,0)>=4),
      'measured_content_sessions',(SELECT count(*) FROM quality_sessions q WHERE q.measured),
      'attention_measured_content_sessions',(SELECT count(*) FROM quality_sessions q WHERE q.measured_v4),
      'content_sessions',(SELECT count(*) FROM quality_sessions),
      'legacy_thinking_views',(SELECT count(*) FROM views v WHERE v.kind='legacy_thinking'),
      'contact_sessions',(SELECT count(*) FROM session_sources s WHERE s.contact),
      'page_sessions',(SELECT count(DISTINCT v.session_id) FROM views v WHERE v.kind='page'),
      'page_views',(SELECT count(*) FROM views v WHERE v.kind='page'),
      'article_sessions',(SELECT count(DISTINCT v.session_id) FROM views v WHERE v.kind='article'),
      'article_views',(SELECT count(*) FROM views v WHERE v.kind='article')
    )
  ) INTO result;

  RETURN result;
END;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_content_intelligence(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE base jsonb; since_at timestamptz; result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

 base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
 since_at := (base->>'period_since')::timestamptz;
 WITH scoped AS MATERIALIZED (
  SELECT *,
   CASE WHEN content_kind='article' OR (article_slug IS NOT NULL AND event_name<>'article_click') THEN 'article'
        WHEN content_kind='page' THEN 'page'
        WHEN page='thinking' THEN 'legacy_thinking' ELSE 'page' END AS kind
  FROM public.careersite_analytics_events
  WHERE occurred_at >= since_at AND occurred_at < (base->>'period_until')::timestamptz
   AND NOT (lower(coalesce(attribution_source,''))='application' AND lower(coalesce(attribution_role,''))='test')
 ), views AS MATERIALIZED (
  SELECT *, CASE WHEN event_name='article_view' THEN 'article:'||article_slug ELSE page END AS content
  FROM scoped WHERE event_name='article_view' OR (event_name='page_view' AND kind<>'article')
 ), content_sessions AS (
  SELECT kind, page, CASE WHEN kind='article' THEN article_slug END AS slug, session_id,
   count(*) FILTER(WHERE event_name=CASE WHEN kind='article' THEN 'article_view' ELSE 'page_view' END) AS views,
   min(occurred_at) FILTER(WHERE event_name=CASE WHEN kind='article' THEN 'article_view' ELSE 'page_view' END) AS opened,
   max(CASE WHEN kind='article' THEN article_engaged_ms ELSE page_engaged_ms END) AS active_ms,
   max(scroll_depth) AS depth,
   bool_or(tracking_version=3) AS measured,
   count(*) FILTER(WHERE event_name='article_share') AS shares,
   bool_or(event_name IN ('cv_download','email_click','linkedin_click')) AS action_on_content
  FROM scoped WHERE event_name<>'article_click'
  GROUP BY kind,page,CASE WHEN kind='article' THEN article_slug END,session_id
 ), quality AS MATERIALIZED (
  SELECT c.*,
   EXISTS(SELECT 1 FROM scoped e WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened AND e.event_name='cv_download') AS later_cv,
   EXISTS(SELECT 1 FROM scoped e WHERE e.session_id=c.session_id AND e.occurred_at>=c.opened AND e.event_name IN ('email_click','linkedin_click')) AS later_contact,
   EXISTS(SELECT 1 FROM views v WHERE v.session_id=c.session_id AND v.occurred_at>c.opened AND v.kind='page' AND v.page<>'thinking') AS later_portfolio
  FROM content_sessions c WHERE views>0
 ), performance AS (
  SELECT kind,coalesce(slug,page) AS content,
   count(*) AS sessions, sum(views) AS views,
   count(*) FILTER(WHERE active_ms>=10000) AS engaged_sessions,
   count(*) FILTER(WHERE active_ms>=5000) AS confirmed_sessions,
   round((avg(active_ms) FILTER(WHERE active_ms>=5000))/1000.0,1) AS avg_active_seconds,
   count(*) FILTER(WHERE depth IS NOT NULL) AS depth_measured_sessions,
   count(*) FILTER(WHERE depth>=50) AS halfway_sessions,
   count(*) FILTER(WHERE depth>=90) AS bottom_sessions,
   count(*) FILTER(WHERE depth>=90 AND active_ms>=30000) AS deep_read_sessions,
   sum(shares) AS shares,
   count(*) FILTER(WHERE shares>0) AS sharing_sessions,
   count(*) FILTER(WHERE action_on_content) AS action_sessions,
   count(*) FILTER(WHERE later_cv) AS later_cv_sessions,
   count(*) FILTER(WHERE later_contact) AS later_contact_sessions,
   count(*) FILTER(WHERE later_portfolio) AS later_portfolio_sessions
  FROM quality GROUP BY kind,coalesce(slug,page)
 ), ordered_views AS (
  SELECT *,lead(content) OVER(PARTITION BY session_id ORDER BY occurred_at,id) AS next_content
  FROM views
 ), journeys AS (
  SELECT content AS from_content,next_content AS to_content,count(*) AS transitions,count(DISTINCT session_id) AS sessions
  FROM ordered_views WHERE next_content IS NOT NULL AND next_content<>content
  GROUP BY content,next_content ORDER BY sessions DESC LIMIT 30
 ), session_sources AS (
  SELECT session_id,
   (array_agg(coalesce(attribution_source,utm_source,'direct/unknown') ORDER BY occurred_at,id))[1] AS channel,
   (array_agg(coalesce(utm_campaign,attribution_role,'untagged') ORDER BY occurred_at,id))[1] AS campaign,
   bool_or(event_name='cv_download') AS cv,
   bool_or(event_name IN ('email_click','linkedin_click')) AS contact,
   bool_or(event_name='article_view') AS reader,
   max(engaged_ms)>=10000 AS engaged
  FROM scoped GROUP BY session_id
 ), campaigns AS (
  SELECT channel,campaign,count(*) AS sessions,count(*) FILTER(WHERE engaged) AS engaged_sessions,
   count(*) FILTER(WHERE reader) AS reader_sessions,count(*) FILTER(WHERE cv) AS cv_sessions,
   count(*) FILTER(WHERE contact) AS contact_sessions
  FROM session_sources GROUP BY channel,campaign ORDER BY sessions DESC LIMIT 40
 ), entry_exit AS (
  SELECT session_id,(array_agg(content ORDER BY occurred_at,id))[1] AS entry,
   (array_agg(content ORDER BY occurred_at DESC,id DESC))[1] AS last_content,
   count(*) AS views FROM views GROUP BY session_id
 ), entrances AS (
  SELECT entry AS content,count(*) AS sessions,count(*) FILTER(WHERE views=1) AS single_view_sessions
  FROM entry_exit GROUP BY entry ORDER BY sessions DESC
 ), exits AS (
  SELECT last_content AS content,count(*) AS sessions FROM entry_exit GROUP BY last_content ORDER BY sessions DESC
 )
 SELECT jsonb_build_object(
  'generated_at',now(),'period_since',since_at,'period_label',base->'period_label',
  'performance',coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY sessions DESC) FROM performance p),'[]'::jsonb),
  'journeys',coalesce((SELECT jsonb_agg(to_jsonb(j)) FROM journeys j),'[]'::jsonb),
  'campaigns',coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM campaigns c),'[]'::jsonb),
  'entrances',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM entrances e),'[]'::jsonb),
  'exits',coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM exits e),'[]'::jsonb),
  'quality',jsonb_build_object(
   'last_event_at',(SELECT max(occurred_at) FROM scoped),
   'new_measurement_since',(SELECT min(occurred_at) FROM scoped WHERE tracking_version=3),
   'measured_content_sessions',(SELECT count(*) FROM quality WHERE measured),
   'content_sessions',(SELECT count(*) FROM quality),
   'legacy_thinking_views',(SELECT count(*) FROM views WHERE kind='legacy_thinking'),
   'contact_sessions',(SELECT count(*) FROM session_sources WHERE contact),
   'page_sessions',(SELECT count(DISTINCT session_id) FROM views WHERE kind='page'),
   'page_views',(SELECT count(*) FROM views WHERE kind='page'),
   'article_sessions',(SELECT count(DISTINCT session_id) FROM views WHERE kind='article'),
   'article_views',(SELECT count(*) FROM views WHERE kind='article'))
 ) INTO result;
 RETURN result;
END; $function$;

CREATE OR REPLACE FUNCTION public.__owner_inner_careersite_hiring_intelligence_v1(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  v_base jsonb;
  v_requested_since timestamptz;
  v_v5_since timestamptz;
  v_quality_since timestamptz;
  v_now timestamptz := pg_catalog.now();
  v_result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  -- Reuse the established token validation and reporting-window logic.
  v_base := public.careersite_analytics_dashboard_v2(p_token, p_days, p_window);
  v_requested_since := (v_base->>'period_since')::timestamptz;
  v_now := (v_base->>'period_until')::timestamptz;

  SELECT pg_catalog.min(e.occurred_at)
  INTO v_v5_since
  FROM public.careersite_analytics_events e
  WHERE coalesce(e.tracking_version, 0) >= 5;

  v_quality_since := greatest(
    v_requested_since,
    coalesce(v_v5_since, v_requested_since)
  );

  WITH quality_ids AS MATERIALIZED (
    SELECT DISTINCT e.session_id
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= v_quality_since
      AND e.occurred_at < v_now
      AND coalesce(e.tracking_version, 0) >= 5
  ),
  scoped AS MATERIALIZED (
    SELECT e.*
    FROM public.careersite_analytics_events e
    JOIN quality_ids q USING (session_id)
    WHERE e.occurred_at >= v_quality_since
      AND e.occurred_at < v_now
  ),
  preview_page_events AS MATERIALIZED (
    SELECT e.id,e.session_id,e.page,e.occurred_at,
      CASE
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) like 'linkedin%' THEN 'LinkedIn'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('facebook','fb','meta') THEN 'Facebook'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('whatsapp','wa') THEN 'WhatsApp'
        WHEN lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) IN ('x','twitter') THEN 'X'
        ELSE lower(coalesce(nullif(trim(e.attribution_source),''),
                            nullif(trim(e.utm_source),''),'direct/unknown')) END AS channel,
      pg_catalog.concat_ws('|',
        coalesce(e.country_code,''),coalesce(e.timezone,''),
        coalesce(e.device_type,''),coalesce(e.browser_family,''),
        coalesce(e.os_family,''),coalesce(e.language,''),
        coalesce(e.viewport_width::text,''),coalesce(e.screen_width::text,'')) AS signature
    FROM scoped e
    WHERE e.event_name='page_view'
      AND e.article_slug IS NULL AND e.content_kind IS DISTINCT FROM 'article'
  ),
  preview_bursts AS MATERIALIZED (
    SELECT DISTINCT a.session_id
    FROM preview_page_events a
    WHERE EXISTS (
       SELECT 1 FROM preview_page_events b JOIN preview_page_events c
         ON c.id<>a.id AND b.id<>a.id AND c.id<>b.id
           AND b.signature=a.signature AND c.signature=a.signature
           AND b.channel=a.channel AND c.channel=a.channel
       WHERE a.page<>b.page AND a.page<>c.page AND b.page<>c.page
         AND a.session_id<>b.session_id AND a.session_id<>c.session_id AND b.session_id<>c.session_id
         AND b.occurred_at BETWEEN a.occurred_at-interval '30 seconds' AND a.occurred_at+interval '30 seconds'
         AND c.occurred_at BETWEEN a.occurred_at-interval '30 seconds' AND a.occurred_at+interval '30 seconds'
    )
  ),
  session_base AS MATERIALIZED (
    SELECT
      e.session_id,
      pg_catalog.min(e.occurred_at) AS first_at,
      pg_catalog.max(coalesce(e.engaged_ms, 0))::bigint AS max_engaged_ms,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view')) AS has_content_view,
      pg_catalog.bool_or(e.event_name = 'first_interaction') AS has_first_interaction,
      pg_catalog.bool_or(e.event_name IN (
        'cv_download','email_click','linkedin_click','cta_click','article_card_click','article_share'
      )) AS has_any_action,
      pg_catalog.bool_or(
        pg_catalog.lower(coalesce(e.attribution_source,'')) = 'application'
        AND pg_catalog.lower(coalesce(e.attribution_role,'')) = 'test'
      ) AS explicit_test,

      pg_catalog.bool_or(
        e.event_name = 'article_card_click'
        OR (e.event_name = 'cta_click' AND coalesce(e.element_key,'') = 'impact')
      ) AS exploration_action,

      pg_catalog.bool_or(
        (e.event_name = 'cta_click'
          AND e.page = 'certifications'
          AND coalesce(e.element_key,'') IN ('linkedin','verify-credential'))
        OR (e.event_name = 'linkedin_click' AND e.page = 'certifications')
      ) AS evidence_verified,

      pg_catalog.bool_or(
        e.event_name = 'cv_download'
        OR e.event_name = 'email_click'
        OR (e.event_name = 'linkedin_click' AND e.page <> 'certifications')
      ) AS hiring_intent,

      pg_catalog.bool_or(
        e.event_name = 'article_view'
        OR (e.event_name IN ('page_view','impact_view') AND e.page IN ('impact','ai-data-governance','certifications'))
        OR (
          e.event_name IN ('section_view','section_attention')
          AND coalesce(e.section_key,'') IN (
            'evidence-of-adoption',
            'adoption-in-practice',
            'selected-leadership-cases',
            'operating-perspective',
            'experience-behind-the-perspective',
            'executive-perspective',
            'executive-definition',
            'leadership-in-practice',
            'leadership-impact',
            'about-credentials',
            'coverage',
            'featured-technical-foundation',
            'recent-credentials'
          )
        )
      ) AS evidence_reached,

      pg_catalog.bool_or(e.event_name IN ('page_view','impact_view') AND e.page = 'impact') AS reached_impact,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view') AND e.page = 'ai-data-governance') AS reached_governance,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view') AND e.page = 'certifications') AS reached_certifications,

      coalesce(
        (pg_catalog.array_agg(e.attribution_source ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.attribution_source IS NOT NULL AND e.attribution_source <> ''))[1],
        (pg_catalog.array_agg(e.utm_source ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.utm_source IS NOT NULL AND e.utm_source <> ''))[1],
        'direct/unknown'
      ) AS source_raw,

      coalesce(
        (pg_catalog.array_agg(e.utm_campaign ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.utm_campaign IS NOT NULL AND e.utm_campaign <> ''))[1],
        (pg_catalog.array_agg(e.attribution_role ORDER BY e.occurred_at,e.id)
          FILTER (WHERE e.attribution_role IS NOT NULL AND e.attribution_role <> ''))[1],
        'untagged'
      ) AS campaign_raw,

      pg_catalog.max(e.country_code) AS country_code,
      pg_catalog.max(e.timezone) AS timezone,
      pg_catalog.max(e.device_type) AS device_type,
      pg_catalog.max(e.browser_family) AS browser_family,
      pg_catalog.max(e.os_family) AS os_family,
      pg_catalog.max(e.language) AS language,
      pg_catalog.max(e.viewport_width) AS viewport_width,
      pg_catalog.max(e.viewport_height) AS viewport_height,
      pg_catalog.max(e.screen_width) AS screen_width,
      pg_catalog.max(e.screen_height) AS screen_height,
      pg_catalog.max(e.hardware_concurrency) AS hardware_concurrency,
      pg_catalog.max(e.device_memory_gb) AS device_memory_gb
    FROM scoped e
    GROUP BY e.session_id
  ),
  signed AS MATERIALIZED (
    SELECT
      s.*,
      pg_catalog.concat_ws(
        '|',
        coalesce(s.country_code,''),
        coalesce(s.timezone,''),
        coalesce(s.device_type,''),
        coalesce(s.browser_family,''),
        coalesce(s.os_family,''),
        coalesce(s.language,''),
        coalesce(s.viewport_width::text,''),
        coalesce(s.viewport_height::text,''),
        coalesce(s.screen_width::text,''),
        coalesce(s.screen_height::text,''),
        coalesce(s.hardware_concurrency::text,''),
        coalesce(s.device_memory_gb::text,'')
      ) AS technical_signature
    FROM session_base s
  ),
  history_ids AS MATERIALIZED (
    SELECT DISTINCT e.session_id
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= v_v5_since
      AND e.occurred_at < v_now
      AND coalesce(e.tracking_version, 0) >= 5
  ),
  history_base AS MATERIALIZED (
    SELECT
      e.session_id,
      pg_catalog.max(coalesce(e.engaged_ms, 0))::bigint AS max_engaged_ms,
      pg_catalog.bool_or(e.event_name IN ('page_view','article_view')) AS has_content_view,
      pg_catalog.bool_or(e.event_name = 'first_interaction') AS has_first_interaction,
      pg_catalog.bool_or(e.event_name IN (
        'cv_download','email_click','linkedin_click','cta_click','article_card_click','article_share'
      )) AS has_any_action,
      pg_catalog.bool_or(
        pg_catalog.lower(coalesce(e.attribution_source,'')) = 'application'
        AND pg_catalog.lower(coalesce(e.attribution_role,'')) = 'test'
      ) AS explicit_test,
      pg_catalog.max(e.country_code) AS country_code,
      pg_catalog.max(e.timezone) AS timezone,
      pg_catalog.max(e.device_type) AS device_type,
      pg_catalog.max(e.browser_family) AS browser_family,
      pg_catalog.max(e.os_family) AS os_family,
      pg_catalog.max(e.language) AS language,
      pg_catalog.max(e.viewport_width) AS viewport_width,
      pg_catalog.max(e.viewport_height) AS viewport_height,
      pg_catalog.max(e.screen_width) AS screen_width,
      pg_catalog.max(e.screen_height) AS screen_height,
      pg_catalog.max(e.hardware_concurrency) AS hardware_concurrency,
      pg_catalog.max(e.device_memory_gb) AS device_memory_gb
    FROM public.careersite_analytics_events e
    JOIN history_ids h USING (session_id)
    WHERE e.occurred_at >= v_v5_since
      AND e.occurred_at < v_now
    GROUP BY e.session_id
  ),
  history_signed AS MATERIALIZED (
    SELECT
      h.*,
      pg_catalog.concat_ws(
        '|',
        coalesce(h.country_code,''),
        coalesce(h.timezone,''),
        coalesce(h.device_type,''),
        coalesce(h.browser_family,''),
        coalesce(h.os_family,''),
        coalesce(h.language,''),
        coalesce(h.viewport_width::text,''),
        coalesce(h.viewport_height::text,''),
        coalesce(h.screen_width::text,''),
        coalesce(h.screen_height::text,''),
        coalesce(h.hardware_concurrency::text,''),
        coalesce(h.device_memory_gb::text,'')
      ) AS technical_signature
    FROM history_base h
  ),
  signature_stats AS MATERIALIZED (
    SELECT
      s.technical_signature,
      pg_catalog.count(*) FILTER (WHERE s.has_content_view AND NOT s.explicit_test) AS valid_sessions,
      pg_catalog.count(*) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test AND s.has_first_interaction
      ) AS interaction_sessions,
      pg_catalog.count(*) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test AND s.has_any_action
      ) AS action_sessions,
      pg_catalog.avg(s.max_engaged_ms) FILTER (
        WHERE s.has_content_view AND NOT s.explicit_test
      ) AS avg_engaged_ms
    FROM history_signed s
    GROUP BY s.technical_signature
  ),
  classified AS MATERIALIZED (
    SELECT
      s.*,
      (
        NOT s.explicit_test
        AND s.has_content_view
        AND (
          (
            coalesce(g.valid_sessions,0) >= 10
            AND coalesce(g.interaction_sessions,0) = 0
            AND coalesce(g.action_sessions,0) = 0
            AND coalesce(g.avg_engaged_ms,0) < 10000
          )
          OR EXISTS (SELECT 1 FROM preview_bursts p WHERE p.session_id=s.session_id)
        )
      ) AS suspected_automation
    FROM signed s
    LEFT JOIN signature_stats g USING (technical_signature)
  ),
  enriched AS MATERIALIZED (
    SELECT
      c.*,
      (NOT c.explicit_test AND c.has_content_view AND NOT c.suspected_automation) AS analysis_eligible,
      (
        NOT c.explicit_test
        AND c.has_content_view
        AND NOT c.suspected_automation
        AND (
          c.max_engaged_ms >= 10000
          OR c.has_first_interaction
          OR c.evidence_verified
          OR c.hiring_intent
        )
      ) AS engaged,
      (
        NOT c.explicit_test
        AND c.has_content_view
        AND NOT c.suspected_automation
        AND c.evidence_reached
        AND (
          c.max_engaged_ms >= 5000
          OR c.evidence_verified
          OR c.hiring_intent
        )
      ) AS evidence_engaged,
      CASE
        WHEN pg_catalog.lower(c.source_raw) LIKE 'linkedin%' THEN 'LinkedIn'
        WHEN pg_catalog.lower(c.source_raw) = 'cv' THEN 'CV'
        WHEN pg_catalog.lower(c.source_raw) IN ('x','twitter') THEN 'X'
        WHEN pg_catalog.lower(c.source_raw) = 'facebook' THEN 'Facebook'
        WHEN pg_catalog.lower(c.source_raw) = 'whatsapp' THEN 'WhatsApp'
        WHEN pg_catalog.lower(c.source_raw) = 'email' THEN 'Email'
        WHEN pg_catalog.lower(c.source_raw) = 'outreach' THEN 'Outreach'
        WHEN pg_catalog.lower(c.source_raw) = 'application' THEN 'Application'
        WHEN pg_catalog.lower(c.source_raw) = 'direct/unknown' THEN 'Unattributed / unknown'
        ELSE 'Other'
      END AS normalized_channel
    FROM classified c
  ),
  quality_summary AS (
    SELECT
      pg_catalog.count(*) AS recorded_sessions,
      pg_catalog.count(*) FILTER (WHERE NOT explicit_test AND has_content_view) AS valid_content_sessions,
      pg_catalog.count(*) FILTER (WHERE explicit_test) AS explicit_test_sessions,
      pg_catalog.count(*) FILTER (WHERE NOT explicit_test AND NOT has_content_view) AS telemetry_only_sessions,
      pg_catalog.count(*) FILTER (WHERE suspected_automation) AS suspected_automation_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible) AS analysis_eligible_sessions,
      pg_catalog.count(*) FILTER (WHERE engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND evidence_reached) AS evidence_reached_sessions,
      pg_catalog.count(*) FILTER (WHERE evidence_engaged) AS evidence_engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND exploration_action) AS exploration_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND hiring_intent) AS hiring_intent_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_impact) AS impact_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_governance) AS governance_sessions,
      pg_catalog.count(*) FILTER (WHERE analysis_eligible AND reached_certifications) AS certification_sessions,
      pg_catalog.round(
        coalesce(
          pg_catalog.avg(max_engaged_ms) FILTER (WHERE analysis_eligible),0
        ) / 1000.0,
        1
      ) AS avg_engaged_seconds,
      pg_catalog.round(
        coalesce(
          (pg_catalog.percentile_cont(0.5) WITHIN GROUP (ORDER BY max_engaged_ms)
            FILTER (WHERE analysis_eligible))::numeric,
          0
        ) / 1000.0,
        1
      ) AS median_engaged_seconds
    FROM enriched
  ),
  quality_breakdown AS (
    SELECT *
    FROM (VALUES
      (1,'Analysis eligible',(SELECT analysis_eligible_sessions FROM quality_summary)),
      (2,'Engaged',(SELECT engaged_sessions FROM quality_summary)),
      (3,'Evidence reached',(SELECT evidence_reached_sessions FROM quality_summary)),
      (4,'Evidence engaged',(SELECT evidence_engaged_sessions FROM quality_summary)),
      (5,'Evidence verified',(SELECT evidence_verified_sessions FROM quality_summary)),
      (6,'Hiring intent',(SELECT hiring_intent_sessions FROM quality_summary))
    ) AS x(sort_order,stage,sessions)
  ),
  excluded_breakdown AS (
    SELECT *
    FROM (VALUES
      (1,'Telemetry only',(SELECT telemetry_only_sessions FROM quality_summary)),
      (2,'Suspected automation',(SELECT suspected_automation_sessions FROM quality_summary)),
      (3,'Explicit test',(SELECT explicit_test_sessions FROM quality_summary))
    ) AS x(sort_order,category,sessions)
  ),
  normalized_channels AS (
    SELECT
      e.normalized_channel AS channel,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_reached) AS evidence_reached_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE e.hiring_intent) AS hiring_intent_sessions,
      pg_catalog.round(pg_catalog.avg(e.max_engaged_ms) / 1000.0,1) AS avg_engaged_seconds
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY e.normalized_channel
    ORDER BY sessions DESC
  ),
  campaigns AS (
    SELECT
      e.normalized_channel AS channel,
      e.source_raw AS source,
      e.campaign_raw AS campaign,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.count(*) FILTER (WHERE e.evidence_verified) AS evidence_verified_sessions,
      pg_catalog.count(*) FILTER (WHERE e.hiring_intent) AS hiring_intent_sessions
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY e.normalized_channel,e.source_raw,e.campaign_raw
    ORDER BY sessions DESC
    LIMIT 40
  ),
  countries AS (
    SELECT
      coalesce(e.country_code,'unknown') AS country_code,
      pg_catalog.count(*) AS sessions
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY coalesce(e.country_code,'unknown')
    ORDER BY sessions DESC
  ),
  devices AS (
    SELECT
      coalesce(e.device_type,'unknown') AS device_type,
      pg_catalog.count(*) AS sessions,
      pg_catalog.count(*) FILTER (WHERE e.engaged) AS engaged_sessions,
      pg_catalog.round(pg_catalog.avg(e.max_engaged_ms) / 1000.0,1) AS avg_engaged_seconds
    FROM enriched e
    WHERE e.analysis_eligible
    GROUP BY coalesce(e.device_type,'unknown')
    ORDER BY sessions DESC
  ),
  action_tiers AS (
    SELECT *
    FROM (VALUES
      (1,'Exploration',(SELECT exploration_sessions FROM quality_summary)),
      (2,'Evidence verification',(SELECT evidence_verified_sessions FROM quality_summary)),
      (3,'Hiring intent',(SELECT hiring_intent_sessions FROM quality_summary))
    ) AS x(sort_order,tier,sessions)
  ),
  automation_meta AS (
    SELECT
      pg_catalog.count(*) AS signatures
    FROM signature_stats
    WHERE valid_sessions >= 10
      AND interaction_sessions = 0
      AND action_sessions = 0
      AND coalesce(avg_engaged_ms,0) < 10000
  )
  SELECT pg_catalog.jsonb_build_object(
    'generated_at', now(),'period_until',v_now,
    'requested_since', v_requested_since,
    'quality_since', v_quality_since,
    'quality_tracking_version', 5,
    'quality_summary', coalesce(
      (SELECT pg_catalog.to_jsonb(q) FROM quality_summary q),
      '{}'::jsonb
    ),
    'quality_funnel', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM quality_breakdown x),
      '[]'::jsonb
    ),
    'excluded_traffic', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM excluded_breakdown x),
      '[]'::jsonb
    ),
    'normalized_channels', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM normalized_channels x),
      '[]'::jsonb
    ),
    'campaigns', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM campaigns x),
      '[]'::jsonb
    ),
    'countries', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM countries x),
      '[]'::jsonb
    ),
    'devices', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sessions DESC) FROM devices x),
      '[]'::jsonb
    ),
    'action_tiers', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(x) ORDER BY x.sort_order) FROM action_tiers x),
      '[]'::jsonb
    ),
    'automation_rule', pg_catalog.jsonb_build_object(
      'minimum_repeated_signature_sessions',10,
      'requires_zero_interaction_sessions',true,
      'requires_zero_action_sessions',true,
      'maximum_signature_average_engaged_ms',10000,
      'suspected_signature_count',(SELECT signatures FROM automation_meta),
      'preview_burst_window_seconds',30,
      'minimum_different_preview_pages',3,
      'suspected_preview_burst_sessions',(SELECT count(*) FROM preview_bursts)
    )
  )
  INTO v_result;

  RETURN v_result;
END;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_analytics_dashboard_v2(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_base jsonb;
  v_since timestamptz;
  v_totals_overlay jsonb;
  v_duration jsonb;
  v_pages jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  -- Reuse the established access-code validation, reset baseline and all
  -- non-duration dimensions from the existing dashboard RPC.
  v_base := public.careersite_analytics_dashboard(p_token, p_days, p_window);
  v_since := (v_base->>'period_since')::timestamptz;

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < (v_base->>'period_until')::timestamptz
      and not (
        lower(coalesce(attribution_source, '')) = 'application'
        and lower(coalesce(attribution_role, '')) = 'test'
      )
  ),
  session_quality as (
    select
      session_id,
      coalesce(max(engaged_ms), 0)::bigint as active_ms,
      (
        count(*) filter (where event_name = 'engagement_ping') > 0
        and coalesce(max(engaged_ms), 0) > 0
      ) as duration_confirmed,
      bool_or(event_name in ('email_click','linkedin_click')) as contacted_channel
    from scoped
    group by session_id
  )
  select jsonb_build_object(
    'confirmed_duration_sessions', count(*) filter (where duration_confirmed),
    'contact_channel_sessions', count(*) filter (where contacted_channel),
    'unconfirmed_duration_sessions', count(*) filter (where not duration_confirmed),
    'avg_active_seconds',
      round(
        coalesce(avg(active_ms) filter (where duration_confirmed), 0) / 1000.0,
        1
      ),
    'median_active_seconds',
      round(
        coalesce(
          percentile_cont(0.5) within group (order by active_ms)
            filter (where duration_confirmed),
          0
        )::numeric / 1000.0,
        1
      ),
    -- Compatibility keys now carry the corrected active-time semantics.
    'avg_session_seconds',
      round(
        coalesce(avg(active_ms) filter (where duration_confirmed), 0) / 1000.0,
        1
      ),
    'median_session_seconds',
      round(
        coalesce(
          percentile_cont(0.5) within group (order by active_ms)
            filter (where duration_confirmed),
          0
        )::numeric / 1000.0,
        1
      ),
    'avg_engaged_seconds',
      round(
        coalesce(avg(active_ms) filter (where duration_confirmed), 0) / 1000.0,
        1
      )
  )
  into v_totals_overlay
  from session_quality;

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < (v_base->>'period_until')::timestamptz
      and not (
        lower(coalesce(attribution_source, '')) = 'application'
        and lower(coalesce(attribution_role, '')) = 'test'
      )
  ),
  session_quality as (
    select
      session_id,
      coalesce(max(engaged_ms), 0)::bigint as active_ms,
      (
        count(*) filter (where event_name = 'engagement_ping') > 0
        and coalesce(max(engaged_ms), 0) > 0
      ) as duration_confirmed,
      bool_or(event_name in ('email_click','linkedin_click')) as contacted_channel
    from scoped
    group by session_id
  ),
  bucketed as (
    select
      case
        when not duration_confirmed then 'Unconfirmed'
        when active_ms < 10000 then '<10s'
        when active_ms < 30000 then '10–29s'
        when active_ms < 60000 then '30–59s'
        when active_ms < 120000 then '1–2m'
        when active_ms < 300000 then '2–5m'
        else '5m+'
      end as duration_bucket,
      case
        when not duration_confirmed then 0
        when active_ms < 10000 then 1
        when active_ms < 30000 then 2
        when active_ms < 60000 then 3
        when active_ms < 120000 then 4
        when active_ms < 300000 then 5
        else 6
      end as sort_order
    from session_quality
  )
  select coalesce(
    jsonb_agg(to_jsonb(x) order by x.sort_order),
    '[]'::jsonb
  )
  into v_duration
  from (
    select duration_bucket, count(*) as sessions, min(sort_order) as sort_order
    from bucketed
    group by duration_bucket
  ) x;

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < (v_base->>'period_until')::timestamptz
      and not (
        lower(coalesce(attribution_source, '')) = 'application'
        and lower(coalesce(attribution_role, '')) = 'test'
      )
      and event_name = 'page_view'
      and article_slug is null
      and content_kind is distinct from 'article'
  ),
  page_catalog(page, page_label, page_family, sort_order) as (
    values
      ('home', 'Home', 'Core', 1),
      ('impact', 'Leadership Impact', 'Core', 2),
      ('thinking', 'Thinking', 'Core', 3),
      ('about', 'About', 'About', 4),
      ('certifications', 'Credentials & Certifications', 'About', 5),
      ('presence', 'Speaking & Thought Leadership', 'About', 6),
      ('enterprise', 'Enterprise AI & Data Leadership', 'Role lenses', 7),
      ('transformation', 'AI Transformation & Adoption', 'Role lenses', 8),
      ('governance', 'AI Governance & Operating Model', 'Role lenses', 9),
      ('consulting', 'Business-Driven AI & Consulting', 'Role lenses', 10),
      ('contact', 'Contact', 'Core', 11),
      ('ai-data-governance', 'AI & Data Governance', 'Core', 12)
  ),
  page_stats as (
    select
      page,
      count(*)::bigint as page_views,
      count(distinct session_id)::bigint as sessions
    from scoped
    group by page
  )
  select coalesce(
    jsonb_agg(to_jsonb(x) order by x.sessions desc, x.page_views desc, x.sort_order),
    '[]'::jsonb
  )
  into v_pages
  from (
    select
      c.page,
      c.page_label,
      c.page_family,
      c.sort_order,
      coalesce(s.page_views, 0)::bigint as page_views,
      coalesce(s.sessions, 0)::bigint as sessions
    from page_catalog c
    left join page_stats s using (page)
  ) x;

  v_base := jsonb_set(
    v_base,
    '{totals}',
    coalesce(v_base->'totals', '{}'::jsonb) || coalesce(v_totals_overlay, '{}'::jsonb),
    true
  );
  v_base := jsonb_set(v_base, '{duration_buckets}', coalesce(v_duration, '[]'::jsonb), true);
  v_base := jsonb_set(v_base, '{pages}', coalesce(v_pages, '[]'::jsonb), true);

  return v_base;
end;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_analytics_articles_v2(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_base jsonb;
  v_since timestamptz;
  v_result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  -- Reuse the corrected dashboard function for access-code validation,
  -- reset-baseline handling and reporting-window semantics.
  v_base := public.careersite_analytics_dashboard_v2(p_token, p_days, p_window);
  v_since := (v_base ->> 'period_since')::timestamptz;

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < (v_base->>'period_until')::timestamptz
      and not (
        lower(coalesce(attribution_source, '')) = 'application'
        and lower(coalesce(attribution_role, '')) = 'test'
      )
      and article_slug is not null
  ),
  article_session as (
    select
      article_slug,
      session_id,
      count(*) filter (where event_name = 'article_click') as open_clicks,
      count(*) filter (where event_name = 'article_view') as views,
      count(*) filter (where event_name = 'article_share') as shares,
      count(*) filter (where event_name = 'engagement_ping') as heartbeats,
      coalesce(max(article_engaged_ms), 0)::bigint as article_engaged_ms,
      coalesce(
        min(attribution_source) filter (where attribution_source is not null),
        min(utm_source) filter (where utm_source is not null),
        'direct/unknown'
      ) as attribution_source
    from scoped
    group by article_slug, session_id
  ),
  article_quality as (
    select *,
      (article_engaged_ms >= 5000) as duration_confirmed,
      (article_engaged_ms >= 10000) as engaged_reader
    from article_session
  ),
  by_article as (
    select coalesce(
      jsonb_agg(to_jsonb(x) order by x.sessions desc, x.views desc, x.article_slug),
      '[]'::jsonb
    ) as data
    from (
      select
        article_slug,
        coalesce(sum(open_clicks), 0)::bigint as open_clicks,
        coalesce(sum(views), 0)::bigint as views,
        count(*) filter (where views > 0)::bigint as sessions,
        coalesce(sum(shares), 0)::bigint as shares,
        count(*) filter (where shares > 0)::bigint as share_sessions,
        count(*) filter (where views > 0 and engaged_reader)::bigint as engaged_sessions,
        count(*) filter (where views > 0 and duration_confirmed)::bigint as confirmed_duration_sessions,
        count(*) filter (where views > 0 and not duration_confirmed)::bigint as unconfirmed_duration_sessions,
        round(
          coalesce(
            avg(article_engaged_ms) filter (where views > 0 and duration_confirmed),
            0
          )::numeric / 1000.0,
          1
        ) as avg_active_seconds,
        round(
          coalesce(
            percentile_cont(0.5) within group (order by article_engaged_ms)
              filter (where views > 0 and duration_confirmed),
            0
          )::numeric / 1000.0,
          1
        ) as median_active_seconds
      from article_quality
      group by article_slug
    ) x
  ),
  by_share_action as (
    select coalesce(
      jsonb_agg(to_jsonb(x) order by x.shares desc, x.article_action),
      '[]'::jsonb
    ) as data
    from (
      select
        coalesce(article_action, 'unknown') as article_action,
        count(*)::bigint as shares,
        count(distinct session_id)::bigint as sessions
      from scoped
      where event_name = 'article_share'
      group by 1
    ) x
  ),
  by_source as (
    select coalesce(
      jsonb_agg(to_jsonb(x) order by x.sessions desc, x.article_slug, x.attribution_source),
      '[]'::jsonb
    ) as data
    from (
      select
        article_slug,
        attribution_source,
        count(*) filter (where views > 0)::bigint as sessions
      from article_quality
      where views > 0
      group by article_slug, attribution_source
    ) x
  ),
  daily as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.day), '[]'::jsonb) as data
    from (
      select
        (occurred_at at time zone 'Europe/Stockholm')::date as day,
        count(*) filter (where event_name = 'article_view')::bigint as views,
        count(distinct session_id) filter (where event_name = 'article_view')::bigint as sessions,
        count(*) filter (where event_name = 'article_share')::bigint as shares
      from scoped
      group by 1
    ) x
  ),
  totals as (
    select jsonb_build_object(
      'views', (select count(*) from scoped where event_name = 'article_view'),
      'sessions', (select count(distinct session_id) from scoped where event_name = 'article_view'),
      'open_clicks', (select count(*) from scoped where event_name = 'article_click'),
      'shares', (select count(*) from scoped where event_name = 'article_share'),
      'share_sessions', (select count(distinct session_id) from scoped where event_name = 'article_share'),
      'engaged_sessions', (
        select count(*) from article_quality where views > 0 and engaged_reader
      ),
      'confirmed_duration_sessions', (
        select count(*) from article_quality where views > 0 and duration_confirmed
      ),
      'unconfirmed_duration_sessions', (
        select count(*) from article_quality where views > 0 and not duration_confirmed
      ),
      'avg_active_seconds', (
        select round(
          coalesce(
            avg(article_engaged_ms) filter (where views > 0 and duration_confirmed),
            0
          )::numeric / 1000.0,
          1
        )
        from article_quality
      ),
      'median_active_seconds', (
        select round(
          coalesce(
            percentile_cont(0.5) within group (order by article_engaged_ms)
              filter (where views > 0 and duration_confirmed),
            0
          )::numeric / 1000.0,
          1
        )
        from article_quality
      )
    ) as data
  )
  select jsonb_build_object(
    'period_label', v_base -> 'period_label',
    'period_since', v_base -> 'period_since',
    'reset_at', v_base -> 'reset_at',
    'generated_at', now(),
    'totals', totals.data,
    'articles', by_article.data,
    'share_actions', by_share_action.data,
    'sources', by_source.data,
    'daily', daily.data
  )
  into v_result
  from totals, by_article, by_share_action, by_source, daily;

  return v_result;
end;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_analytics_articles(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_base jsonb;
  v_since timestamptz;
  v_result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  IF auth.uid() IS NULL
     OR lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
     OR coalesce(auth.jwt()->>'is_anonymous','false') <> 'false' THEN
    RAISE EXCEPTION 'Owner sign-in required' USING ERRCODE = '42501';
  END IF;

  -- Reuse the established dashboard function for access-code validation,
  -- reset-baseline handling and reporting-window semantics.
  v_base := public.careersite_analytics_dashboard(p_token, p_days, p_window);
  v_since := (v_base ->> 'period_since')::timestamptz;

  with scoped as (
    select *
    from public.careersite_analytics_events
    where occurred_at >= v_since and occurred_at < (v_base->>'period_until')::timestamptz
      and article_slug is not null
  ),
  article_session as (
    select
      article_slug,
      session_id,
      count(*) filter (where event_name = 'article_click') as open_clicks,
      count(*) filter (where event_name = 'article_view') as views,
      count(*) filter (where event_name = 'article_share') as shares,
      coalesce(max(article_engaged_ms), 0) as article_engaged_ms,
      coalesce(
        min(attribution_source) filter (where attribution_source is not null),
        min(utm_source) filter (where utm_source is not null),
        'direct/unknown'
      ) as attribution_source
    from scoped
    group by article_slug, session_id
  ),
  by_article as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.views desc, x.article_slug), '[]'::jsonb) as data
    from (
      select
        article_slug,
        coalesce(sum(open_clicks), 0)::bigint as open_clicks,
        coalesce(sum(views), 0)::bigint as views,
        count(*) filter (where views > 0)::bigint as sessions,
        coalesce(sum(shares), 0)::bigint as shares,
        count(*) filter (where shares > 0)::bigint as share_sessions,
        count(*) filter (where views > 0 and article_engaged_ms >= 10000)::bigint as engaged_sessions,
        round(
          coalesce(avg(article_engaged_ms) filter (where views > 0), 0)::numeric / 1000.0,
          1
        ) as avg_active_seconds
      from article_session
      group by article_slug
    ) x
  ),
  by_share_action as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.shares desc, x.article_action), '[]'::jsonb) as data
    from (
      select
        coalesce(article_action, 'unknown') as article_action,
        count(*)::bigint as shares,
        count(distinct session_id)::bigint as sessions
      from scoped
      where event_name = 'article_share'
      group by 1
    ) x
  ),
  by_source as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc, x.article_slug, x.attribution_source), '[]'::jsonb) as data
    from (
      select
        article_slug,
        attribution_source,
        count(*) filter (where views > 0)::bigint as sessions
      from article_session
      where views > 0
      group by article_slug, attribution_source
    ) x
  ),
  daily as (
    select coalesce(jsonb_agg(to_jsonb(x) order by x.day), '[]'::jsonb) as data
    from (
      select
        (occurred_at at time zone 'Europe/Stockholm')::date as day,
        count(*) filter (where event_name = 'article_view')::bigint as views,
        count(distinct session_id) filter (where event_name = 'article_view')::bigint as sessions,
        count(*) filter (where event_name = 'article_share')::bigint as shares
      from scoped
      group by 1
    ) x
  ),
  totals as (
    select jsonb_build_object(
      'views', (select count(*) from scoped where event_name = 'article_view'),
      'sessions', (select count(distinct session_id) from scoped where event_name = 'article_view'),
      'open_clicks', (select count(*) from scoped where event_name = 'article_click'),
      'shares', (select count(*) from scoped where event_name = 'article_share'),
      'share_sessions', (select count(distinct session_id) from scoped where event_name = 'article_share'),
      'engaged_sessions', (select count(*) from article_session where views > 0 and article_engaged_ms >= 10000),
      'avg_active_seconds', (
        select round(coalesce(avg(article_engaged_ms) filter (where views > 0), 0)::numeric / 1000.0, 1)
        from article_session
      )
    ) as data
  )
  select jsonb_build_object(
    'period_label', v_base -> 'period_label',
    'period_since', v_base -> 'period_since',
    'reset_at', v_base -> 'reset_at',
    'generated_at', now(),
    'totals', totals.data,
    'articles', by_article.data,
    'share_actions', by_share_action.data,
    'sources', by_source.data,
    'daily', daily.data
  ) into v_result
  from totals, by_article, by_share_action, by_source, daily;

  return v_result;
end;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_attribution_integrity_v1(p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  result jsonb;
  since_at timestamptz;
  until_at timestamptz := now();
  v_v5_since timestamptz;
begin
  -- Public aggregate-only analytics: owner gate removed intentionally.
  
  select (r->>'period_since')::timestamptz, (r->>'period_until')::timestamptz
  into since_at, until_at
  from (select public.careersite_analytics_dashboard_v2('public-readonly-v1',p_days,p_window) r) bounds;

  select min(occurred_at) into v_v5_since from public.careersite_analytics_events
    where coalesce(tracking_version,0)>=5;

  with raw as materialized (
    select * from public.careersite_analytics_events e
    where e.occurred_at >= since_at and e.occurred_at < until_at
  ),
  normalized as materialized (
    select e.*,
      lower(coalesce(nullif(trim(e.attribution_source),''),
                     nullif(trim(e.utm_source),''),'direct/unknown')) as raw_src,
      lower(regexp_replace(
        coalesce(nullif(trim(e.attribution_source),''),nullif(trim(e.utm_source),''),'direct/unknown'),
        '[?&]role=.*$','','i')) as base_src,
      lower(coalesce(nullif(trim(e.utm_campaign),''),
                     nullif(trim(e.attribution_role),''),
                     substring(e.attribution_source from '[?&]role=([^&]+)'),
                     'untagged')) as campaign_key,
      pg_catalog.concat_ws('|',coalesce(e.country_code,''),coalesce(e.timezone,''),
        coalesce(e.device_type,''),coalesce(e.browser_family,''),coalesce(e.os_family,''),
        coalesce(e.language,''),coalesce(e.viewport_width::text,''),
        coalesce(e.screen_width::text,'')) as client_signature,
      pg_catalog.concat_ws('|',coalesce(e.country_code,''),coalesce(e.timezone,''),
        coalesce(e.device_type,''),coalesce(e.browser_family,''),coalesce(e.os_family,''),
        coalesce(e.language,''),coalesce(e.viewport_width::text,''),
        coalesce(e.viewport_height::text,''),coalesce(e.screen_width::text,''),
        coalesce(e.screen_height::text,''),coalesce(e.hardware_concurrency::text,''),
        coalesce(e.device_memory_gb::text,'')) as technical_signature
    from raw e
  ),
  classified_events as materialized (
    select n.*,
      case
        when base_src='direct/unknown' then 'Unattributed / unknown'
        when base_src in ('thre','threads') then 'Threads' when base_src='cv' then 'CV'
        when base_src like 'linkedin%' then 'LinkedIn'
        when base_src in ('facebook','fb','meta') then 'Facebook'
        when base_src in ('whatsapp','wa') then 'WhatsApp'
        when base_src in ('x','twitter') then 'X'
        when base_src='social' then 'Social / unspecified'
        when base_src in ('chatgpt.com','chatgpt','openai') then 'ChatGPT tagged'
        when base_src='email' then 'Email'
        when base_src='outreach' then 'Outreach'
        when base_src='application' then 'Application'
        else 'Other / unrecognized tag' end as channel,
      (n.event_name='page_view'
        and n.article_slug is null
        and n.content_kind is distinct from 'article') as nav_view,
      (n.event_name='page_view' and
        (n.article_slug is not null or n.content_kind='article')) as article_page_wrapper,
      (n.event_name='article_view') as article_read
    from normalized n
  ),
  page_events as materialized (
    select id,session_id,page,occurred_at,channel,client_signature
    from classified_events
    where nav_view
      and not (base_src='application' and campaign_key='test')
  ),
  preview_bursts as materialized (
    select distinct a.session_id
    from page_events a
    where exists (
      select 1 from page_events b join page_events c
      on c.id<>b.id and c.id<>a.id and b.id<>a.id
        and b.client_signature=a.client_signature
        and c.client_signature=a.client_signature
        and b.channel=a.channel and c.channel=a.channel
      where a.page<>b.page and a.page<>c.page and b.page<>c.page
        and a.session_id<>b.session_id and a.session_id<>c.session_id
        and b.session_id<>c.session_id
        and b.occurred_at between a.occurred_at-interval '30 seconds' and a.occurred_at+interval '30 seconds'
        and c.occurred_at between a.occurred_at-interval '30 seconds' and a.occurred_at+interval '30 seconds'
    )
  ),
  sessions as materialized (
    select
      n.session_id,
      (array_agg(n.channel order by n.occurred_at,n.id))[1] channel,
      (array_agg(n.base_src order by n.occurred_at,n.id))[1] raw_first_source,
      coalesce((array_agg(n.campaign_key order by n.occurred_at,n.id)
        filter(where n.campaign_key<>'untagged'))[1],'untagged') campaign,
      pg_catalog.concat_ws('|',coalesce(max(n.country_code),''),
        coalesce(max(n.timezone),''),coalesce(max(n.device_type),''),
        coalesce(max(n.browser_family),''),coalesce(max(n.os_family),''),
        coalesce(max(n.language),''),coalesce(max(n.viewport_width)::text,''),
        coalesce(max(n.viewport_height)::text,''),coalesce(max(n.screen_width)::text,''),
        coalesce(max(n.screen_height)::text,''),
        coalesce(max(n.hardware_concurrency)::text,''),
        coalesce(max(n.device_memory_gb)::text,'')) signature,
      bool_or(n.nav_view or n.article_read or n.article_page_wrapper) has_content,
      bool_or(n.event_name='first_interaction') has_interaction,
      bool_or(n.event_name in ('cv_download','email_click','linkedin_click','cta_click',
                 'article_card_click','article_share')) has_action,
      bool_or(n.base_src='application' and n.campaign_key='test') explicit_test,
      bool_or(coalesce(n.tracking_version,0)>=5) v5,
      max(coalesce(n.engaged_ms,0)) engaged_ms,
      count(*) filter(where n.nav_view) navigation_page_views,
      count(*) filter(where n.article_read) article_views,
      count(*) filter(where n.article_page_wrapper) duplicate_article_wrappers,
      bool_or(n.utm_source is not null and n.attribution_source is not null
            and lower(trim(n.utm_source))<>lower(trim(n.attribution_source))) conflicting_sources,
      bool_or(n.utm_campaign is not null and n.attribution_role is not null
            and lower(trim(n.utm_campaign))<>lower(trim(n.attribution_role))) conflicting_campaigns,
      bool_or(n.base_src='direct/unknown' and n.referrer_host is not null
            and n.referrer_host<>'') untagged_with_referrer
    from classified_events n group by n.session_id
  ),
  v5_history_ids as materialized (
    select distinct session_id from public.careersite_analytics_events
    where occurred_at>=v_v5_since and occurred_at<until_at
      and coalesce(tracking_version,0)>=5
  ),
  v5_history as materialized (
    select e.session_id,
      bool_or(e.event_name in ('page_view','article_view')) has_content,
      bool_or(e.event_name='first_interaction') interacted,
      bool_or(e.event_name in ('cv_download','email_click','linkedin_click',
             'cta_click','article_card_click','article_share')) acted,
      bool_or(lower(coalesce(e.attribution_source,''))='application'
              and lower(coalesce(e.attribution_role,''))='test') is_test,
      max(coalesce(e.engaged_ms,0)) engaged_ms,
      pg_catalog.concat_ws('|',coalesce(max(e.country_code),''),
        coalesce(max(e.timezone),''),coalesce(max(e.device_type),''),
        coalesce(max(e.browser_family),''),coalesce(max(e.os_family),''),
        coalesce(max(e.language),''),coalesce(max(e.viewport_width)::text,''),
        coalesce(max(e.viewport_height)::text,''),coalesce(max(e.screen_width)::text,''),
        coalesce(max(e.screen_height)::text,''),
        coalesce(max(e.hardware_concurrency)::text,''),
        coalesce(max(e.device_memory_gb)::text,'')) as signature
    from public.careersite_analytics_events e join v5_history_ids h using(session_id)
    where e.occurred_at>=v_v5_since and e.occurred_at<until_at
    group by e.session_id
  ),
  signature_quality as materialized (
    select signature,
      count(*) filter(where has_content and not is_test) source_sessions,
      count(*) filter(where has_content and not is_test and interacted) interacted,
      count(*) filter(where has_content and not is_test and acted) acted,
      avg(engaged_ms) filter(where has_content and not is_test) mean_ms
    from v5_history group by signature
  ),
    assessed as materialized (
    select s.*,
      exists(select 1 from preview_bursts p where p.session_id=s.session_id) flagged_burst,
      (t.source_sessions>=10 and t.interacted=0 and t.acted=0
       and coalesce(t.mean_ms,0)<10000) flagged_signature,
      case
        when s.explicit_test then 'explicit_test'
        when not s.has_content then 'telemetry_only'
        when not s.v5 then 'legacy_ungraded'
        when exists(select 1 from preview_bursts p where p.session_id=s.session_id) then 'suspected_preview_burst'
        when t.source_sessions>=10 and t.interacted=0 and t.acted=0
          and coalesce(t.mean_ms,0)<10000 then 'suspected_automation'
        else 'quality_eligible' end as quality_class
    from sessions s left join signature_quality t using(signature)
  ),
  channels as (
    select channel,
      count(*) filter(where not explicit_test)::int recorded_sessions,
      count(*) filter(where has_content and not explicit_test)::int content_sessions,
      sum(navigation_page_views) filter(where not explicit_test)::int navigation_page_views,
      sum(article_views) filter(where not explicit_test)::int article_views,
      sum(duplicate_article_wrappers) filter(where not explicit_test)::int article_page_wrappers,
      count(*) filter(where quality_class='quality_eligible')::int quality_eligible,
      count(*) filter(where quality_class='legacy_ungraded')::int legacy_ungraded,
      count(*) filter(where quality_class='suspected_preview_burst')::int preview_burst_sessions,
      count(*) filter(where quality_class='suspected_automation')::int other_suspected_automation,
      count(*) filter(where quality_class='telemetry_only')::int telemetry_only,
      count(*) filter(where has_content and not explicit_test and engaged_ms>=10000)::int engaged_10s,
      count(*) filter(where conflicting_sources and not explicit_test)::int source_conflicts,
      count(*) filter(where conflicting_campaigns and not explicit_test)::int campaign_conflicts,
      count(*) filter(where untagged_with_referrer and not explicit_test)::int untagged_referrer
    from assessed group by channel
  ),
  campaign_channels as (
    select channel,campaign,
      count(*)::int content_sessions,
      count(*) filter(where quality_class='quality_eligible')::int quality_eligible,
      count(*) filter(where quality_class in ('suspected_preview_burst','suspected_automation'))::int flagged_sessions,
      count(*) filter(where quality_class='legacy_ungraded')::int legacy_ungraded
    from assessed where has_content and not explicit_test
    group by channel,campaign
  ),
  unexpected as (
    select raw_first_source,
      count(*)::int sessions
    from assessed where channel='Other / unrecognized tag' and not explicit_test
    group by raw_first_source
  )
  select jsonb_build_object(
    'from',since_at,'through',until_at,
    'method','v5-history-session-max-signature-quality-reconciled-v4',
    'overview',jsonb_build_object(
      'recorded_sessions',(select count(*) from assessed),
      'test_sessions',(select count(*) from assessed where explicit_test),
      'content_sessions',(select count(*) from assessed where has_content and not explicit_test),
      'quality_eligible',(select count(*) from assessed where quality_class='quality_eligible'),
      'legacy_ungraded',(select count(*) from assessed where quality_class='legacy_ungraded'),
      'telemetry_only',(select count(*) from assessed where quality_class='telemetry_only'),
      'suspected_preview_bursts',(select count(*) from assessed where quality_class='suspected_preview_burst'),
      'suspected_automation_other',(select count(*) from assessed where quality_class='suspected_automation'),
      'navigation_page_views',(select coalesce(sum(navigation_page_views),0) from assessed where not explicit_test),
      'article_views',(select coalesce(sum(article_views),0) from assessed where not explicit_test),
      'article_page_wrappers',(select coalesce(sum(duplicate_article_wrappers),0) from assessed where not explicit_test),
      'source_conflicts',(select count(*) from assessed where conflicting_sources and not explicit_test),
      'campaign_conflicts',(select count(*) from assessed where conflicting_campaigns and not explicit_test),
      'untagged_with_referrer',(select count(*) from assessed where untagged_with_referrer and not explicit_test)
    ),
    'channels',(select coalesce(jsonb_agg(to_jsonb(x) order by x.content_sessions desc,x.channel),'[]'::jsonb)
       from channels x),
    'campaigns',(select coalesce(jsonb_agg(to_jsonb(x) order by x.content_sessions desc,x.channel,x.campaign),'[]'::jsonb)
       from campaign_channels x),
    'unexpected_tags',(select coalesce(jsonb_agg(to_jsonb(x) order by x.sessions desc),'[]'::jsonb)
       from unexpected x)
  ) into result;
  return result;
end
$function$;

CREATE OR REPLACE FUNCTION public.careersite_cv_attribution_audit_v1(p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  result jsonb;
  since_at timestamptz;
  report_until timestamptz := now();
begin
  -- Public aggregate-only analytics: owner gate removed intentionally.
  
  select (r->>'period_since')::timestamptz, (r->>'period_until')::timestamptz
  into since_at, report_until
  from (select public.careersite_analytics_dashboard_v2('public-readonly-v1',p_days,p_window) r) bounds;

  with scoped as materialized (
    select e.*
    from public.careersite_analytics_events e
    where e.occurred_at>=since_at and e.occurred_at<report_until
      and e.event_name='page_view'
      and not (lower(coalesce(e.attribution_source,''))='application'
               and lower(coalesce(e.attribution_role,''))='test')
  ),
  cv as materialized (
    select e.*,
      pg_catalog.concat_ws('|',
        coalesce(e.country_code,''),coalesce(e.timezone,''),
        coalesce(e.device_type,''),coalesce(e.browser_family,''),
        coalesce(e.os_family,''),coalesce(e.language,''),
        coalesce(e.viewport_width::text,''),coalesce(e.screen_width::text,'')) as signature
    from scoped e
    where lower(trim(coalesce(e.attribution_source,e.utm_source,'')))='cv'
  ),
  flagged as materialized (
    select a.id,a.session_id,a.page,
      exists(
        select 1 from cv b join cv c
        on c.id<>a.id and c.id<>b.id and b.id<>a.id
          and c.signature=a.signature and b.signature=a.signature
        where b.page<>a.page and c.page<>a.page and c.page<>b.page
          and b.session_id<>a.session_id and c.session_id<>a.session_id
          and c.session_id<>b.session_id
          and b.occurred_at between a.occurred_at-interval '30 seconds'
                                and a.occurred_at+interval '30 seconds'
          and c.occurred_at between a.occurred_at-interval '30 seconds'
                                and a.occurred_at+interval '30 seconds'
      ) as suspected_scan
    from cv a
  ),
  overview as (
    select
      (select count(*) from scoped)::int all_page_views,
      (select count(distinct session_id) from scoped)::int page_view_sessions,
      (select count(*) from cv)::int cv_page_views,
      (select count(distinct session_id) from cv)::int cv_sessions,
      (select count(*) from cv where lower(coalesce(utm_source,''))='cv')::int cv_utm_source_same_view,
      (select count(*) from cv where coalesce(nullif(lower(trim(attribution_role)),''), substring(lower(coalesce(attribution_source,'')) from '[?&]role=([^&]+)')) is not null)::int cv_with_role,
      (select count(*) from scoped where coalesce(nullif(lower(trim(attribution_role)),''), substring(lower(coalesce(attribution_source,'')) from '[?&]role=([^&]+)')) is not null)::int role_tagged_views,
      (select count(*) from flagged where suspected_scan)::int suspect_scan_views,
      (select count(distinct session_id) from flagged where suspected_scan)::int suspect_scan_sessions
  ),
  page_breakdown as (
    select f.page, count(*)::int as raw_views,
       count(*) filter(where f.suspected_scan)::int as suspect_scan_views,
       count(*) filter(where not f.suspected_scan)::int as other_views
    from flagged f group by f.page
  ),
  roles as (
    select coalesce(nullif(lower(trim(attribution_role)),''), substring(lower(coalesce(attribution_source,'')) from '[?&]role=([^&]+)')) as role,
      count(*)::int as page_views,
      count(distinct session_id)::int as sessions
    from scoped where coalesce(nullif(lower(trim(attribution_role)),''), substring(lower(coalesce(attribution_source,'')) from '[?&]role=([^&]+)')) is not null
    group by 1
  )
  select jsonb_build_object(
    'since',since_at,'through',report_until,
    'overview',(select to_jsonb(o) from overview o),
    'cv_pages',(select coalesce(jsonb_agg(to_jsonb(p) order by p.raw_views desc,p.page),'[]'::jsonb) from page_breakdown p),
    'roles',(select coalesce(jsonb_agg(to_jsonb(r) order by r.page_views desc,r.role),'[]'::jsonb) from roles r),
    'method','exact-one-view-one-source; correlated-30s-three-page-same-client-burst')
  into result;
  return result;
end
$function$;

CREATE OR REPLACE FUNCTION public.careersite_page_sources(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE base jsonb; result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

 base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
 WITH views AS (
 SELECT id,occurred_at,page,session_id,
 coalesce(nullif(btrim(attribution_source),''),nullif(btrim(utm_source),''),'direct/unknown') AS tag
 FROM public.careersite_analytics_events
 WHERE occurred_at >= (base->>'period_since')::timestamptz AND occurred_at < (base->>'period_until')::timestamptz
 AND event_name='page_view' AND article_slug IS NULL
 AND content_kind IS DISTINCT FROM 'article'
 AND (content_kind='page' OR page IS DISTINCT FROM 'thinking')
 AND page IS NOT NULL
 AND NOT(lower(coalesce(attribution_source,''))='application' AND lower(coalesce(attribution_role,''))='test')
 ), visits AS (
 SELECT DISTINCT ON(page,session_id) page,session_id,tag
 FROM views ORDER BY page,session_id,occurred_at,id
 ), grouped AS (
 SELECT page,lower(tag) AS attribution_source,count(*) AS sessions FROM visits GROUP BY page,lower(tag)
 )
 SELECT jsonb_build_object('sources',coalesce(jsonb_agg(to_jsonb(grouped) ORDER BY sessions DESC,page,attribution_source),'[]'::jsonb),
 'period_since',base->'period_since') INTO result FROM grouped;
 RETURN result;
END;
$function$;

CREATE OR REPLACE FUNCTION public.careersite_weekly_audio_analytics_v1(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  base jsonb;
  since_at timestamptz;
  until_at timestamptz := pg_catalog.now();
  result jsonb;
BEGIN
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  -- Existing owner RPC remains authoritative for time-window interpretation.
  base := public.careersite_analytics_dashboard_v2(p_token, p_days, p_window);
  since_at := (base->>'period_since')::timestamptz;
  until_at := (base->>'period_until')::timestamptz;

  WITH episodes AS MATERIALIZED (
    SELECT
      e.article_slug AS slug,
      e.session_id,
      pg_catalog.bool_or(e.event_name='audio_start') AS started,
      pg_catalog.bool_or(e.event_name='audio_progress' AND e.element_key='25') AS reached_25,
      pg_catalog.bool_or(e.event_name='audio_progress' AND e.element_key='50') AS reached_50,
      pg_catalog.bool_or(e.event_name='audio_progress' AND e.element_key='75') AS reached_75,
      pg_catalog.bool_or(e.event_name='audio_complete') AS completed,
      coalesce(pg_catalog.max(e.attention_ms),0) AS listened_ms
    FROM public.careersite_analytics_events e
    WHERE e.occurred_at >= since_at AND e.occurred_at < until_at
      AND e.event_name IN ('audio_start','audio_progress','audio_complete')
      AND e.page='thinking' AND e.content_kind='article'
      AND e.article_slug ~ '^weekly-ai-[0-9]{4}-[0-9]{2}-[0-9]{2}$'
      AND e.element_placement='thinking:weekly-ai-audio'
      AND NOT (
        pg_catalog.lower(coalesce(e.attribution_source,''))='application'
        AND pg_catalog.lower(coalesce(e.attribution_role,''))='test'
      )
    GROUP BY e.article_slug, e.session_id
  ),
  editions AS (
    SELECT
      slug,
      pg_catalog.count(*) FILTER (WHERE started) AS starts,
      pg_catalog.count(*) FILTER (WHERE reached_25) AS progress_25,
      pg_catalog.count(*) FILTER (WHERE reached_50) AS progress_50,
      pg_catalog.count(*) FILTER (WHERE reached_75) AS progress_75,
      pg_catalog.count(*) FILTER (WHERE completed) AS completions,
      pg_catalog.round(pg_catalog.sum(listened_ms)::numeric / 1000,1) AS estimated_listened_seconds
    FROM episodes
    WHERE started
    GROUP BY slug
  )
  SELECT pg_catalog.jsonb_build_object(
    'period_since', since_at,
    'generated_at', now(),'period_until',until_at,
    'started_sessions', (SELECT pg_catalog.count(DISTINCT session_id) FROM episodes WHERE started),
    'completed_sessions', (SELECT pg_catalog.count(DISTINCT session_id) FROM episodes WHERE started AND completed),
    'edition_starts', (SELECT pg_catalog.count(*) FROM episodes WHERE started),
    'edition_completions', (SELECT pg_catalog.count(*) FROM episodes WHERE started AND completed),
    'estimated_listened_seconds', (SELECT coalesce(pg_catalog.round(pg_catalog.sum(listened_ms)::numeric / 1000,1),0) FROM episodes WHERE started),
    'editions', coalesce(
      (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) ORDER BY e.starts DESC,e.slug DESC) FROM editions e),
      '[]'::jsonb
    )
  ) INTO result;
  
 -- weekly_campaign_breakdown: one first-view attribution per edition/session.
 WITH scoped AS MATERIALIZED (
   SELECT * FROM public.careersite_analytics_events
   WHERE occurred_at >= since_at AND occurred_at < until_at
     AND article_slug ~ '^weekly-ai-[0-9]{4}-[0-9]{2}-[0-9]{2}$'
     AND NOT (lower(coalesce(attribution_source,''))='application'
              AND lower(coalesce(attribution_role,''))='test')
 ), first_views AS (
   SELECT DISTINCT ON (article_slug,session_id)
     article_slug,session_id,occurred_at,
     CASE WHEN lower(coalesce(nullif(trim(attribution_source),''),nullif(trim(utm_source),''),'direct/unknown'))='twitter'
       THEN 'x' ELSE lower(coalesce(nullif(trim(attribution_source),''),nullif(trim(utm_source),''),'direct/unknown')) END channel,
     coalesce(nullif(lower(trim(attribution_role)),''),'untagged') role,
     coalesce(nullif(trim(utm_campaign),''),'untagged') campaign,
     coalesce(nullif(trim(utm_content),''),'unrecorded') content
   FROM scoped WHERE event_name='article_view'
   ORDER BY article_slug,session_id,occurred_at,id
 ), visits AS (
   SELECT f.article_slug,f.session_id,f.channel,f.role,f.campaign,f.content,
     bool_or(coalesce(e.article_engaged_ms,0)>=10000) engaged,
     bool_or(e.event_name='audio_start') audio_started,
     bool_or(e.event_name='article_share') shared
   FROM first_views f JOIN scoped e USING(article_slug,session_id)
   WHERE e.occurred_at >= f.occurred_at
   GROUP BY f.article_slug,f.session_id,f.channel,f.role,f.campaign,f.content
 ), grouped AS (
   SELECT article_slug,channel,role,campaign,content,count(*) reads,
     count(*) FILTER(WHERE engaged) engaged_reads,
     count(*) FILTER(WHERE audio_started) audio_starts,
     count(*) FILTER(WHERE shared) share_sessions
   FROM visits GROUP BY article_slug,channel,role,campaign,content
 )
 SELECT result || jsonb_build_object('campaigns',coalesce(
   (SELECT jsonb_agg(to_jsonb(g) ORDER BY reads DESC,article_slug,channel,campaign,content) FROM grouped g),
   '[]'::jsonb)) INTO result;
 RETURN result;
 
END
$function$;

CREATE OR REPLACE FUNCTION public.careersite_behavior_intelligence(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  base jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  result jsonb;
BEGIN
  -- shared_analytics_owner_guard
  -- Public aggregate-only analytics: owner gate removed intentionally.
  

  base := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (base->>'period_since')::timestamptz;
  report_now := (base->>'period_until')::timestamptz;

  WITH scoped AS NOT MATERIALIZED (
    SELECT *
    FROM public.careersite_analytics_events
    WHERE occurred_at >= since_at
      AND occurred_at < report_now
      AND NOT (
        lower(coalesce(attribution_source,''))='application'
        AND lower(coalesce(attribution_role,''))='test'
      )
  ),
  section_seen AS MATERIALIZED (
    SELECT session_id,page,coalesce(article_slug,'') AS article_slug,
      coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      min(occurred_at) AS first_seen_at
    FROM scoped WHERE event_name IN ('section_view','section_attention')
    GROUP BY session_id,page,coalesce(article_slug,''),coalesce(section_key,'unknown')
  ),
  section_per_session AS MATERIALIZED (
    SELECT s.session_id,s.page,s.article_slug,s.section_key,s.section_label,s.first_seen_at,
      coalesce(sum(a.attention_ms),0) AS attention_ms,
      coalesce(sum(a.exposure_count),0) AS exposure_count,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name='cv_download') AS later_cv,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name IN ('email_click','linkedin_click')) AS later_contact,
      EXISTS (SELECT 1 FROM scoped e WHERE e.session_id=s.session_id AND e.occurred_at>s.first_seen_at AND e.event_name='page_view' AND e.page='impact') AS later_impact
    FROM section_seen s
    LEFT JOIN scoped a ON a.session_id=s.session_id AND a.page=s.page
      AND coalesce(a.article_slug,'')=s.article_slug
      AND coalesce(a.section_key,'unknown')=s.section_key
      AND a.event_name='section_attention'
    GROUP BY s.session_id,s.page,s.article_slug,s.section_key,s.section_label,s.first_seen_at
  ),
  section_attention AS (
    SELECT page,nullif(article_slug,'') AS article_slug,section_key,max(section_label) AS section_label,
      count(*) AS reached_sessions,
      count(*) FILTER (WHERE attention_ms>0) AS measured_attention_sessions,
      round(avg(attention_ms) FILTER (WHERE attention_ms>0)/1000.0,1) AS avg_attention_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS median_attention_seconds,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS p75_attention_seconds,
      count(*) FILTER (WHERE attention_ms>=5000) AS attentive_5s_sessions,
      coalesce(sum(exposure_count),0) AS exposures,
      count(*) FILTER (WHERE later_impact) AS later_impact_sessions,
      count(*) FILTER (WHERE later_cv) AS later_cv_sessions,
      count(*) FILTER (WHERE later_contact) AS later_contact_sessions
    FROM section_per_session
    GROUP BY page,article_slug,section_key
    ORDER BY reached_sessions DESC,measured_attention_sessions DESC
  ),
  element_seen AS MATERIALIZED (
    SELECT session_id,page,coalesce(article_slug,'') AS article_slug,
      coalesce(element_kind,'unknown') AS element_kind,coalesce(element_key,'unknown') AS element_key,
      coalesce(element_placement,'unknown') AS element_placement,max(element_label) AS element_label,
      min(occurred_at) AS first_seen_at
    FROM scoped WHERE event_name IN ('element_impression','element_attention')
    GROUP BY session_id,page,coalesce(article_slug,''),coalesce(element_kind,'unknown'),
      coalesce(element_key,'unknown'),coalesce(element_placement,'unknown')
  ),
  element_per_session AS MATERIALIZED (
    SELECT e.session_id,e.page,e.article_slug,e.element_kind,e.element_key,e.element_placement,e.element_label,e.first_seen_at,
      coalesce(sum(a.attention_ms),0) AS attention_ms,coalesce(sum(a.hover_ms),0) AS hover_ms,
      coalesce(sum(a.exposure_count),0) AS exposure_count,
      EXISTS (
        SELECT 1 FROM scoped c WHERE c.session_id=e.session_id AND c.occurred_at>=e.first_seen_at
          AND (
            (e.element_kind='cta' AND c.event_name='cta_click' AND coalesce(c.element_key,'unknown')=e.element_key AND coalesce(c.element_placement,'unknown')=e.element_placement)
            OR
            (e.element_kind='article_card' AND c.event_name='article_card_click' AND coalesce(c.element_key,'unknown')=e.element_key AND coalesce(c.element_placement,'unknown')=e.element_placement)
          )
      ) AS clicked
    FROM element_seen e
    LEFT JOIN scoped a ON a.session_id=e.session_id AND a.page=e.page
      AND coalesce(a.article_slug,'')=e.article_slug
      AND coalesce(a.element_kind,'unknown')=e.element_kind
      AND coalesce(a.element_key,'unknown')=e.element_key
      AND coalesce(a.element_placement,'unknown')=e.element_placement
      AND a.event_name='element_attention'
    GROUP BY e.session_id,e.page,e.article_slug,e.element_kind,e.element_key,e.element_placement,e.element_label,e.first_seen_at
  ),
  element_attention AS (
    SELECT page,nullif(article_slug,'') AS article_slug,element_kind,element_key,element_placement,max(element_label) AS element_label,
      count(*) AS exposed_sessions,count(*) FILTER (WHERE attention_ms>0) AS measured_attention_sessions,
      round(avg(attention_ms) FILTER (WHERE attention_ms>0)/1000.0,1) AS avg_attention_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY attention_ms) FILTER (WHERE attention_ms>0)/1000.0)::numeric,1) AS median_attention_seconds,
      count(*) FILTER (WHERE attention_ms>=2000) AS attentive_2s_sessions,
      count(*) FILTER (WHERE hover_ms>0) AS hover_sessions,
      round(avg(hover_ms) FILTER (WHERE hover_ms>0)/1000.0,1) AS avg_hover_seconds,
      count(*) FILTER (WHERE clicked) AS click_sessions,coalesce(sum(exposure_count),0) AS exposures
    FROM element_per_session
    GROUP BY page,article_slug,element_kind,element_key,element_placement
    ORDER BY exposed_sessions DESC,click_sessions DESC
  ),
  cta_hesitation AS (
    SELECT page,coalesce(element_key,'unknown') AS element_key,coalesce(element_placement,'unknown') AS element_placement,
      max(element_label) AS element_label,count(DISTINCT session_id) AS sessions,
      round(avg(hesitation_ms)/1000.0,1) AS avg_hesitation_seconds,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY hesitation_ms)/1000.0)::numeric,1) AS median_hesitation_seconds,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY hesitation_ms)/1000.0)::numeric,1) AS p75_hesitation_seconds
    FROM scoped WHERE event_name='cta_hesitation' AND hesitation_ms IS NOT NULL
    GROUP BY page,coalesce(element_key,'unknown'),coalesce(element_placement,'unknown')
    ORDER BY sessions DESC
  ),
  last_regions AS (
    SELECT CASE WHEN content_kind='article' OR article_slug IS NOT NULL THEN 'article' ELSE 'page' END AS kind,
      page,article_slug,coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      count(DISTINCT session_id) AS sessions,round(avg(scroll_depth)::numeric,1) AS avg_scroll_depth,
      round(avg(page_engaged_ms)/1000.0,1) AS avg_visible_seconds,
      round(avg(max_scroll_velocity)::numeric,1) AS avg_max_scroll_velocity,
      round(avg(max_reverse_scroll_velocity)::numeric,1) AS avg_max_reverse_scroll_velocity
    FROM scoped WHERE event_name='scroll_abandonment'
    GROUP BY CASE WHEN content_kind='article' OR article_slug IS NOT NULL THEN 'article' ELSE 'page' END,
      page,article_slug,coalesce(section_key,'unknown')
    ORDER BY sessions DESC
  ),
  ux_signals AS (
    SELECT interaction_type,page,coalesce(section_key,'unknown') AS section_key,max(section_label) AS section_label,
      max(error_type) AS error_type,count(*) AS events,count(DISTINCT session_id) AS sessions
    FROM scoped WHERE event_name='ux_signal'
    GROUP BY interaction_type,page,coalesce(section_key,'unknown')
    ORDER BY sessions DESC,events DESC
  ),
  first_interaction AS (
    SELECT interaction_type,coalesce(device_type,'unknown') AS device_type,count(*) AS sessions,
      round((percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms))::numeric,1) AS median_latency_ms,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY latency_ms))::numeric,1) AS p75_latency_ms
    FROM scoped WHERE event_name='first_interaction' AND latency_ms IS NOT NULL
    GROUP BY interaction_type,coalesce(device_type,'unknown')
    ORDER BY sessions DESC
  ),
  behavior_summary AS (
    SELECT coalesce(device_type,'unknown') AS device_type,count(DISTINCT session_id) AS sessions,
      round(avg(focus_loss_count)::numeric,1) AS avg_focus_losses,round(avg(resize_count)::numeric,1) AS avg_resizes,
      round(avg(orientation_change_count)::numeric,1) AS avg_orientation_changes,
      round(avg(max_scroll_velocity)::numeric,1) AS avg_max_scroll_velocity,
      round(avg(max_reverse_scroll_velocity)::numeric,1) AS avg_max_reverse_scroll_velocity,
      round(avg(hardware_concurrency)::numeric,1) AS avg_logical_cores,
      round(avg(device_memory_gb)::numeric,1) AS avg_device_memory_gb,
      count(*) FILTER (WHERE save_data) AS save_data_sessions
    FROM scoped WHERE event_name='behavior_summary'
    GROUP BY coalesce(device_type,'unknown')
    ORDER BY sessions DESC
  ),
  web_vitals AS (
    SELECT coalesce(device_type,'unknown') AS device_type,
      count(DISTINCT session_id) FILTER (WHERE metric_name='fcp_ms') AS fcp_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY metric_value) FILTER (WHERE metric_name='fcp_ms'))::numeric,1) AS p75_fcp_ms,
      count(DISTINCT session_id) FILTER (WHERE metric_name='inp_ms') AS inp_sessions,
      round((percentile_cont(0.75) WITHIN GROUP (ORDER BY metric_value) FILTER (WHERE metric_name='inp_ms'))::numeric,1) AS p75_inp_ms
    FROM scoped WHERE event_name='performance_metric' AND metric_name IN ('fcp_ms','inp_ms')
    GROUP BY coalesce(device_type,'unknown')
    ORDER BY greatest(
      count(DISTINCT session_id) FILTER (WHERE metric_name='fcp_ms'),
      count(DISTINCT session_id) FILTER (WHERE metric_name='inp_ms')
    ) DESC
  )
  SELECT jsonb_build_object(
    'generated_at',now(),'period_until',report_now,'period_since',since_at,
    'section_attention',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM section_attention x),'[]'::jsonb),
    'element_attention',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM element_attention x),'[]'::jsonb),
    'cta_hesitation',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM cta_hesitation x),'[]'::jsonb),
    'last_regions',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM last_regions x),'[]'::jsonb),
    'ux_signals',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM ux_signals x),'[]'::jsonb),
    'first_interaction',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM first_interaction x),'[]'::jsonb),
    'behavior_summary',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM behavior_summary x),'[]'::jsonb),
    'web_vitals',coalesce((SELECT jsonb_agg(to_jsonb(x)) FROM web_vitals x),'[]'::jsonb),
    'quality',jsonb_build_object(
      'behavior_first_seen',(SELECT min(occurred_at) FROM scoped WHERE coalesce(tracking_version,0)>=5),
      'behavior_events',(SELECT count(*) FROM scoped WHERE event_name IN (
        'section_attention','element_attention','cta_hesitation','scroll_abandonment','ux_signal','first_interaction','behavior_summary'
      )),
      'behavior_sessions',(SELECT count(DISTINCT session_id) FROM scoped WHERE event_name IN (
        'section_attention','element_attention','cta_hesitation','scroll_abandonment','ux_signal','first_interaction','behavior_summary'
      ))
    )
  ) INTO result;

  RETURN result;
END;
$function$;

CREATE OR REPLACE FUNCTION journey_report_internal.home_journey_impl(p_token text, p_days integer DEFAULT 30, p_window text DEFAULT 'days'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  valid_report jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  result jsonb;
begin
  -- Reuse the existing reporting endpoint's token and window validation.
  valid_report := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (valid_report ->> 'period_since')::timestamptz;
  report_now := (valid_report->>'period_until')::timestamptz;
  if since_at is null then
    raise exception 'Unsupported reporting window';
  end if;
  with scoped as materialized (
    select id, session_id, occurred_at, event_name, page, target, element_key,
           device_type, attribution_source
    from public.careersite_analytics_events
    where occurred_at >= since_at and occurred_at < report_now
      and not (
        lower(coalesce(attribution_source,'')) = 'application'
        and lower(coalesce(attribution_role,'')) = 'test'
      )
  ),
  pv as materialized (
    select id, session_id, occurred_at, page, device_type, attribution_source,
           row_number() over(partition by session_id order by occurred_at,id) as rn
    from scoped where event_name = 'page_view'
  ),
  home as materialized (
    select session_id, occurred_at as home_at, device_type, attribution_source
    from pv where rn = 1 and page = 'home'
  ),
  paths as materialized (
    select h.session_id, h.home_at, h.device_type, h.attribution_source,
           next_view.page as destination
    from home h
    left join lateral (
      select p.page
      from pv p
      where p.session_id=h.session_id and p.page <> 'home'
        and p.occurred_at > h.home_at
      order by p.occurred_at,p.id limit 1
    ) next_view on true
  ),
  clicks as materialized (
    select c.session_id,c.occurred_at,c.target,c.element_key,
           exists (
             select 1 from pv p
             where p.session_id = c.session_id and p.page = c.target
               and p.occurred_at > c.occurred_at
               and p.occurred_at <= c.occurred_at + interval '30 minutes'
           ) as confirmed
    from scoped c
    where c.event_name = 'navigation_click' and c.page = 'home'
      and c.target in (
        'impact','thinking','ai-data-governance','about','presence',
        'certifications','contact','enterprise','transformation','governance','consulting'
      )
  )
  select jsonb_build_object(
    'period_since',since_at,
    'period_until',report_now,
    'home_landings',(select count(*) from paths),
    'onward_sessions',(select count(*) from paths where destination is not null),
    'no_recorded_destination',(select count(*) from paths where destination is null),
    'last_7d_home_landings',(select count(*) from paths where home_at >= greatest(since_at,report_now - interval '7 days')),
    'last_7d_onward_sessions',(select count(*) from paths where destination is not null and home_at >= greatest(since_at,report_now - interval '7 days')),
    'navigation_clicks',(select count(*) from clicks),
    'navigation_click_sessions',(select count(distinct session_id) from clicks),
    'confirmed_clicks',(select count(*) from clicks where confirmed),
    'unconfirmed_clicks',(select count(*) from clicks where not confirmed),
    'destinations',(
      select coalesce(jsonb_agg(jsonb_build_object('page',destination,'sessions',sessions)
               order by sessions desc,destination),'[]'::jsonb)
      from (select destination,count(*) sessions from paths where destination is not null group by destination) d
    ),
    'route_selections',(
      select coalesce(jsonb_agg(jsonb_build_object('page',target,'clicks',clicks_count,
               'confirmed',confirmed_count) order by clicks_count desc,target),'[]'::jsonb)
      from (select target,count(*) clicks_count,count(*) filter(where confirmed) confirmed_count
            from clicks group by target) c
    ),
    'device_breakdown',(
      select coalesce(jsonb_agg(jsonb_build_object('device',device,'landings',landings,
               'onward',onward) order by landings desc),'[]'::jsonb)
      from (select coalesce(device_type,'unknown') device, count(*) landings,
                   count(*) filter(where destination is not null) onward
            from paths group by 1) dev
    )
  ) into result;
  return result;
end;
$function$;
