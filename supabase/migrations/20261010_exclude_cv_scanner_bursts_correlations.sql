-- Daily, owner-only portfolio signals for longitudinal job search analysis.
-- Aggregates contain no session IDs, IP addresses, identifying fingerprints,
-- visitor-level paths, recruiter identity, or linked job/employer data.
create or replace function public.careersite_portfolio_signals_daily_v1(
    p_days integer default 365,
    p_through date default null
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $fn$
declare
    v_first timestamptz;
    v_end date := least(coalesce(p_through, (now() at time zone 'Europe/Stockholm')::date - 1),
                        (now() at time zone 'Europe/Stockholm')::date - 1);
    v_start date;
    v_result jsonb;
begin
    if auth.uid() is null
       or lower(coalesce(auth.jwt()->>'email', '')) <> 'jair.ribeiro@outlook.it'
       or coalesce(auth.jwt()->>'is_anonymous', 'false') <> 'false'
    then
        raise exception 'Owner sign-in required' using errcode='42501';
    end if;
    if p_days is null or p_days < 7 or p_days > 730 then
        raise exception 'Invalid reporting horizon' using errcode='22023';
    end if;

    select min(occurred_at) into v_first
    from public.careersite_analytics_events where tracking_version >= 5;

    v_start := greatest(
        v_end - (p_days - 1),
        coalesce((v_first at time zone 'Europe/Stockholm')::date, v_end + 1)
    );

    with eligible_raw as materialized (
        select e.*
        from public.careersite_analytics_events e
        where e.occurred_at >= v_first
          and (e.occurred_at at time zone 'Europe/Stockholm')::date <= v_end
    ),
    sessions as materialized (
        select
            e.session_id,
            (min(e.occurred_at) at time zone 'Europe/Stockholm')::date as d,
            bool_or(coalesce(e.tracking_version,0)>=5) as has_v5,
            bool_or(e.event_name in ('page_view','article_view')) as has_content,
            bool_or(e.event_name='first_interaction') as interacted,
            bool_or(e.event_name in ('cv_download','email_click','linkedin_click',
                                     'cta_click','article_card_click','article_share')) as acted,
            bool_or(lower(coalesce(e.attribution_source,''))='application'
                    and lower(coalesce(e.attribution_role,''))='test') as explicit_test,
            max(coalesce(e.engaged_ms,0)) as active_ms,
            bool_or(e.event_name='article_view') as read_article,
            bool_or(e.event_name in ('cv_download','email_click','linkedin_click')) as hiring_action,
            bool_or(e.event_name in ('page_view','impact_view') and e.page='impact') as impact,
            bool_or(e.event_name='page_view' and e.page='certifications') as certifications,
            bool_or(e.event_name in ('page_view','article_view')
                    and e.page='ai-data-governance') as governance,
            count(distinct e.page) filter(where e.event_name in ('page_view','article_view')) as pages,
            coalesce((array_agg(e.attribution_source order by e.occurred_at,e.id)
                filter(where e.attribution_source is not null and e.attribution_source<>''))[1],
                (array_agg(e.utm_source order by e.occurred_at,e.id)
                filter(where e.utm_source is not null and e.utm_source<>''))[1],
                'direct/unknown') as raw_source,
            pg_catalog.concat_ws('|',coalesce(max(e.country_code),''),
                coalesce(max(e.timezone),''),coalesce(max(e.device_type),''),
                coalesce(max(e.browser_family),''),coalesce(max(e.os_family),''),
                coalesce(max(e.language),''),coalesce(max(e.viewport_width)::text,''),
                coalesce(max(e.viewport_height)::text,''),coalesce(max(e.screen_width)::text,''),
                coalesce(max(e.screen_height)::text,''),coalesce(max(e.hardware_concurrency)::text,''),
                coalesce(max(e.device_memory_gb)::text,'')) as technical_signature
        from eligible_raw e
        group by e.session_id
    ),
    signature_stats as materialized (
        select technical_signature,
            count(*) filter(where has_v5 and has_content and not explicit_test) as valid_sessions,
            count(*) filter(where has_v5 and has_content and not explicit_test and interacted) as interaction_sessions,
            count(*) filter(where has_v5 and has_content and not explicit_test and acted) as action_sessions,
            avg(active_ms) filter(where has_v5 and has_content and not explicit_test) as mean_ms
        from sessions group by technical_signature
    ),
    cv_views as materialized (
        select e.session_id,e.page,e.occurred_at,
          pg_catalog.concat_ws('|',coalesce(e.country_code,''),coalesce(e.timezone,''),
            coalesce(e.device_type,''),coalesce(e.browser_family,''),
            coalesce(e.os_family,''),coalesce(e.language,''),
            coalesce(e.viewport_width::text,''),coalesce(e.screen_width::text,'')) as cv_signature,
          e.id
        from eligible_raw e
        where e.event_name='page_view'
          and lower(trim(coalesce(nullif(e.attribution_source,''),e.utm_source,'')))='cv'
    ),
    suspected_cv_batches as materialized (
        select distinct a.session_id
        from cv_views a
        where exists(
          select 1 from cv_views b join cv_views c
            on c.id<>a.id and c.id<>b.id and b.id<>a.id
              and c.cv_signature=a.cv_signature and b.cv_signature=a.cv_signature
          where a.page<>b.page and a.page<>c.page and b.page<>c.page
            and a.session_id<>b.session_id and a.session_id<>c.session_id
            and b.session_id<>c.session_id
            and b.occurred_at between a.occurred_at-interval '30 seconds'
                                  and a.occurred_at+interval '30 seconds'
            and c.occurred_at between a.occurred_at-interval '30 seconds'
                                  and a.occurred_at+interval '30 seconds'
        )
    ),
    qualified as materialized (
        select s.*
        from sessions s join signature_stats t using(technical_signature)
        where s.has_v5 and s.has_content and not s.explicit_test and s.d between v_start and v_end
            and not (
                t.valid_sessions >= 10 and t.interaction_sessions = 0
                and t.action_sessions = 0 and coalesce(t.mean_ms,0) < 10000
            )
            -- Correlated three-page independent-session batches are often
            -- CV/ATS link previews; preserve raw views, exclude from inference.
            and not exists(select 1 from suspected_cv_batches b where b.session_id=s.session_id)
    ),
    day_signals as (
        select q.d, count(*)::int as sessions,
            count(*) filter(where q.active_ms>=10000)::int as engaged_10s,
            count(*) filter(where q.read_article)::int as article_readers,
            count(*) filter(where q.impact)::int as impact_visitors,
            count(*) filter(where q.certifications)::int as certification_visitors,
            count(*) filter(where q.governance)::int as governance_visitors,
            count(*) filter(where q.pages>=2)::int as multi_page_visitors,
            count(*) filter(where q.hiring_action)::int as hiring_actions,
            count(*) filter(where lower(q.raw_source)='cv')::int as cv_link_visitors,
            count(*) filter(where lower(q.raw_source) like 'linkedin%')::int as linkedin_visitors,
            count(*) filter(where lower(q.raw_source) in ('x','facebook','whatsapp','social'))::int as social_visitors
        from qualified q group by q.d
    ),
    pages as (
        select q.d, left(lower(trim(e.page)),80) as name,
            count(distinct q.session_id)::int as sessions
        from qualified q join eligible_raw e on e.session_id=q.session_id
        where e.event_name in ('page_view','article_view')
          and e.page is not null and e.page <> ''
        group by q.d, left(lower(trim(e.page)),80)
    ),
    sources as (
        select q.d,
          case when lower(q.raw_source) similar to '[a-z0-9][a-z0-9_.+%-]{0,47}'
                  then lower(q.raw_source) else 'other/invalid' end as name,
          count(*)::int as sessions
        from qualified q group by 1,2
    )
    select jsonb_build_object(
        'tracking_since',v_first,
        'first_day',v_start,
        'through',v_end,
        'quality_method','v5-content-non-test-signature-and-cv-scan-screen-v2',
        'daily',(select coalesce(jsonb_agg(to_jsonb(x) order by x.d),'[]'::jsonb)
                 from day_signals x),
        'pages',(select coalesce(jsonb_agg(to_jsonb(x) order by x.d,x.name),'[]'::jsonb)
                 from pages x),
        'sources',(select coalesce(jsonb_agg(to_jsonb(x) order by x.d,x.name),'[]'::jsonb)
                 from sources x)
    ) into v_result;
    return v_result;
end;
$fn$;

revoke all on function public.careersite_portfolio_signals_daily_v1(integer,date) from public, anon;
grant execute on function public.careersite_portfolio_signals_daily_v1(integer,date) to authenticated;
