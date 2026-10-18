
-- Keep the privileged aggregate calculator outside the exposed public schema.
create schema if not exists journey_report_internal;
revoke all on schema journey_report_internal from public;

alter function public.careersite_home_journey_v1(text,integer,text)
  set schema journey_report_internal;

alter function journey_report_internal.careersite_home_journey_v1(text,integer,text)
  rename to home_journey_impl;

revoke all on function journey_report_internal.home_journey_impl(text,integer,text)
  from public,anon,authenticated;

-- A small public invoker wrapper can delegate only the existing public report.
-- The helper schema is not in the Data API's exposed schemas.
grant usage on schema journey_report_internal to anon,authenticated;
grant execute on function journey_report_internal.home_journey_impl(text,integer,text)
  to anon,authenticated;

create function public.careersite_home_journey_v1(
  p_token text,
  p_days integer default 30,
  p_window text default 'days'
) returns jsonb
language sql
security invoker
set search_path = ''
as $function$
  select journey_report_internal.home_journey_impl(p_token,p_days,p_window);
$function$;

revoke all on function public.careersite_home_journey_v1(text,integer,text)
  from public,anon,authenticated;
grant execute on function public.careersite_home_journey_v1(text,integer,text)
  to anon,authenticated;

comment on function public.careersite_home_journey_v1(text,integer,text)
is 'Public invoker wrapper; aggregate only. Internal calculator reuses the existing public token and report-window validation.';
