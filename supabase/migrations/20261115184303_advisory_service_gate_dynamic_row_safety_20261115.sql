-- Explicit branching avoids access to fields absent from other service tables.
create or replace function public.portfolio_advisory_check_new_start_v1()
returns trigger language plpgsql security invoker set search_path=''
as $$
declare v_service text; v_enabled boolean;
begin
 if tg_table_name='portfolio_advisory_requests' then
  v_service := new.source_service;
 else
  v_service := tg_argv[0];
 end if;
 select c.is_enabled into v_enabled
 from public.portfolio_advisory_service_visibility c where c.service_key=v_service;
 if v_enabled is distinct from true then
  raise exception 'This Advisory service is temporarily unavailable for new starts.'
   using errcode='42501';
 end if;
 return new;
end; $$;
revoke all on function public.portfolio_advisory_check_new_start_v1()
 from public,anon,authenticated;
