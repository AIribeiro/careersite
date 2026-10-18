
-- Home journey monitoring: count explicit internal navigation choices and confirmed arrivals.
-- Existing event rows and analytics definitions are retained; this adds an event type.
alter table public.careersite_analytics_events
  drop constraint careersite_analytics_events_event_name_check;
alter table public.careersite_analytics_events
  add constraint careersite_analytics_events_event_name_check check (
    event_name = any (array[
      'page_view','impact_view','lens_view','cv_download','email_click',
      'linkedin_click','article_click','article_view','article_share',
      'engagement_ping','element_impression','article_card_click','cta_click',
      'navigation_click','section_view','performance_metric','section_attention',
      'element_attention','cta_hesitation','scroll_abandonment','ux_signal',
      'first_interaction','behavior_summary','audio_start','audio_progress',
      'audio_complete'
    ]::text[])
  );

create or replace function public.careersite_home_journey_v1(
  p_token text,
  p_days integer default 30,
  p_window text default 'days'
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  valid_report jsonb;
  since_at timestamptz;
  report_now timestamptz := now();
  result jsonb;
begin
  -- Reuse the existing reporting endpoint's token and window validation.
  valid_report := public.careersite_analytics_dashboard_v2(p_token,p_days,p_window);
  since_at := (valid_report ->> 'period_since')::timestamptz;
  if since_at is null then
    raise exception 'Unsupported reporting window';
  end if;
  with scoped as materialized (
    select id, session_id, occurred_at, event_name, page, target, element_key,
           device_type, attribution_source
    from public.careersite_analytics_events
    where occurred_at >= since_at and occurred_at <= report_now
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

revoke all on function public.careersite_home_journey_v1(text,integer,text) from public, anon, authenticated;
grant execute on function public.careersite_home_journey_v1(text,integer,text) to anon,authenticated;
comment on function public.careersite_home_journey_v1(text,integer,text)
is 'Public aggregate-only home journey report. No session IDs or visitor details returned; uses existing public token and window guard.';
