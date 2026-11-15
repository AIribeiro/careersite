-- Preserve existing approvals and histories. Gate only new records.
alter table public.portfolio_advisory_requests
 add column if not exists source_service text not null default 'requests';
do $$
begin
 if not exists(select 1 from pg_constraint
               where conname='portfolio_advisory_requests_source_service_chk') then
  alter table public.portfolio_advisory_requests
   add constraint portfolio_advisory_requests_source_service_chk
   check(source_service in ('requests','rollout','scorecard'));
 end if;
end $$;

create or replace function public.portfolio_advisory_check_new_start_v1()
returns trigger language plpgsql security invoker set search_path=''
as $$
declare v_service text; v_enabled boolean;
begin
 v_service := case when tg_table_name='portfolio_advisory_requests'
                  then new.source_service else tg_argv[0] end;
 select c.is_enabled into v_enabled from public.portfolio_advisory_service_visibility c
 where c.service_key=v_service;
 if v_enabled is distinct from true then
  raise exception 'This Advisory service is temporarily unavailable for new starts.'
   using errcode='42501';
 end if;
 return new;
end;
$$;
revoke all on function public.portfolio_advisory_check_new_start_v1()
 from public,anon,authenticated;

do $$
declare r record;
begin
 for r in select * from (values
   ('portfolio_advisory_requests','requests'),
   ('portfolio_advisory_investment_decisions','decision'),
   ('portfolio_advisory_rollout_assessments','rollout'),
   ('portfolio_advisory_scorecard_analysis_requests','scorecard'),
   ('portfolio_advisory_scorecards','scorecard'),
   ('portfolio_leadership_workshops','workshop')
 ) x(tbl,service_key)
 loop
  execute format('drop trigger if exists advisory_service_new_start_gate on public.%I',r.tbl);
  execute format(
   'create trigger advisory_service_new_start_gate before insert on public.%I for each row execute function public.portfolio_advisory_check_new_start_v1(%L)',
   r.tbl,r.service_key
  );
 end loop;
end $$;
