-- Full attribution reconciliation: one first-touch source and campaign per session,
-- distinct source/role dimensions, one content event per content load.
-- Owner only; output strictly aggregate, no session IDs or fingerprints.
create or replace function public.careersite_attribution_integrity_v1(
  p_days integer default 30, p_window text default 'days'
) returns jsonb
language plpgsql security definer set search_path=''
as $fn$
declare
  result jsonb;
  since_at timestamptz;
  until_at timestamptz := now();
  v_v5_since timestamptz;
begin
  if auth.uid() is null or lower(coalesce(auth.jwt()->>'email',''))<>'jair.ribeiro@outlook.it'
    or coalesce(auth.jwt()->>'is_anonymous','false')<>'false' then
    raise exception 'Owner sign-in required' using errcode='42501';
  end if;
  if p_days is null or p_days<1 or p_days>365
    or p_window not in ('days','today','last_hour') then
    raise exception 'Unsupported reporting window' using errcode='22023';
  end if;
  since_at := case p_window
    when 'today' then date_trunc('day',until_at at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm'
    when 'last_hour' then until_at-interval '1 hour'
    else until_at-make_interval(days=>p_days) end;

  select min(occurred_at) into v_v5_since from public.careersite_analytics_events
    where coalesce(tracking_version,0)>=5;

  with raw as materialized (
    select * from public.careersite_analytics_events e
    where e.occurred_at between since_at and until_at
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
        when base_src='cv' then 'CV'
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
    where occurred_at>=v_v5_since and occurred_at<=until_at
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
    where e.occurred_at>=v_v5_since and e.occurred_at<=until_at
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
$fn$;
revoke all on function public.careersite_attribution_integrity_v1(integer,text) from PUBLIC,anon;
grant execute on function public.careersite_attribution_integrity_v1(integer,text) to authenticated;
