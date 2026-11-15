-- Audited owner-controlled Advisory service catalogue; all existing services start enabled.
create table if not exists public.portfolio_advisory_service_visibility (
  service_key text primary key check (service_key in ('requests','decision','rollout','scorecard','workshop')),
  display_name text not null,
  is_enabled boolean not null default true,
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id)
);
insert into public.portfolio_advisory_service_visibility(service_key,display_name,is_enabled)
values
 ('requests','Personal executive advisory',true),
 ('decision','AI Investment Decision Advisor',true),
 ('rollout','Enterprise AI Rollout Readiness Advisor',true),
 ('scorecard','AI Portfolio Prioritization Scorecard',true),
 ('workshop','Executive AI Leadership Workshop',true)
on conflict (service_key) do nothing;
alter table public.portfolio_advisory_service_visibility enable row level security;
create policy "Advisory public reads service availability"
on public.portfolio_advisory_service_visibility for select to anon,authenticated using(true);
revoke all on public.portfolio_advisory_service_visibility from public,anon,authenticated;
grant select(service_key,display_name,is_enabled)
 on public.portfolio_advisory_service_visibility to anon,authenticated;

create table if not exists public.portfolio_advisory_service_visibility_audit (
 id bigint generated always as identity primary key,
 service_key text not null references public.portfolio_advisory_service_visibility(service_key),
 previous_enabled boolean not null,
 current_enabled boolean not null,
 actor_id uuid not null references auth.users(id),
 changed_at timestamptz not null default now()
);
alter table public.portfolio_advisory_service_visibility_audit enable row level security;
revoke all on public.portfolio_advisory_service_visibility_audit from public,anon,authenticated;
grant select on public.portfolio_advisory_service_visibility_audit to authenticated;
create policy "Owner reads service availability audit"
on public.portfolio_advisory_service_visibility_audit for select to authenticated using (
 auth.uid() is not null and exists (
  select 1 from auth.users u where u.id=auth.uid()
   and u.email_confirmed_at is not null
   and lower(u.email)='jair.ribeiro@outlook.it'
 )
);

create or replace function public.portfolio_advisory_set_service_visibility_v1(
 p_service_key text, p_enabled boolean
) returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_actor uuid := auth.uid(); v_previous boolean;
begin
 if v_actor is null or not exists(
  select 1 from auth.users u where u.id=v_actor
   and u.email_confirmed_at is not null
   and lower(u.email)='jair.ribeiro@outlook.it'
 ) then
   raise exception 'Owner authorization required' using errcode='42501';
 end if;
 if p_service_key is null or p_enabled is null then
   raise exception 'Service and availability are required' using errcode='22023';
 end if;
 select is_enabled into v_previous
 from public.portfolio_advisory_service_visibility
 where service_key=p_service_key for update;
 if not found then
   raise exception 'Unknown advisory service' using errcode='22023';
 end if;
 if v_previous is distinct from p_enabled then
   update public.portfolio_advisory_service_visibility
     set is_enabled=p_enabled,updated_at=now(),updated_by=v_actor
   where service_key=p_service_key;
   insert into public.portfolio_advisory_service_visibility_audit
     (service_key,previous_enabled,current_enabled,actor_id)
   values(p_service_key,v_previous,p_enabled,v_actor);
 end if;
 return jsonb_build_object('service_key',p_service_key,
   'is_enabled',p_enabled,'changed',v_previous is distinct from p_enabled);
end;
$$;
revoke all on function public.portfolio_advisory_set_service_visibility_v1(text,boolean)
 from public,anon,authenticated;
grant execute on function public.portfolio_advisory_set_service_visibility_v1(text,boolean)
 to authenticated;
