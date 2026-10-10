-- Audited attribution is a classification of events, not a destructive rewrite.
-- Source tags, role labels and UTM source are separate dimensions of ONE view.
create or replace function public.careersite_cv_attribution_audit_v1(
  p_days integer default 30,
  p_window text default 'days'
) returns jsonb
language plpgsql security definer set search_path=''
as $fn$
declare
  result jsonb;
  since_at timestamptz;
  report_until timestamptz := now();
begin
  if auth.uid() is null
     or lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
     or coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
  then
    raise exception 'Owner sign-in required' using errcode='42501';
  end if;
  if p_days is null or p_days < 1 or p_days > 365
     or p_window not in ('days','today','last_hour')
  then
    raise exception 'Unsupported analytics reporting window' using errcode='22023';
  end if;
  since_at := case p_window
    when 'today' then date_trunc('day',report_until at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm'
    when 'last_hour' then report_until-interval '1 hour'
    else report_until-make_interval(days=>p_days) end;

  with scoped as materialized (
    select e.*
    from public.careersite_analytics_events e
    where e.occurred_at>=since_at and e.occurred_at<=report_until
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
      (select count(*) from cv where nullif(trim(coalesce(attribution_role,'')),'') is not null)::int cv_with_role,
      (select count(*) from scoped where nullif(trim(coalesce(attribution_role,'')),'') is not null)::int role_tagged_views,
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
    select lower(trim(attribution_role)) as role,
      count(*)::int as page_views,
      count(distinct session_id)::int as sessions
    from scoped where nullif(trim(coalesce(attribution_role,'')),'') is not null
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
$fn$;

revoke all on function public.careersite_cv_attribution_audit_v1(integer,text) from PUBLIC,anon;
grant execute on function public.careersite_cv_attribution_audit_v1(integer,text) to authenticated;
