-- Role-aware service visibility: a hidden service remains fully available to verified admins.
create table if not exists public.portfolio_advisory_user_roles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 role text not null default 'regular' check(role in ('regular','admin')),
 assigned_by uuid references auth.users(id),
 updated_at timestamptz not null default now()
);
create table if not exists public.portfolio_advisory_user_role_audit(
 id bigint generated always as identity primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 previous_role text not null,
 new_role text not null,
 actor_id uuid not null references auth.users(id),
 changed_at timestamptz not null default now()
);
alter table public.portfolio_advisory_user_roles enable row level security;
alter table public.portfolio_advisory_user_role_audit enable row level security;
revoke all on public.portfolio_advisory_user_roles from public,anon,authenticated;
revoke all on public.portfolio_advisory_user_role_audit from public,anon,authenticated;
grant select(user_id,role,updated_at) on public.portfolio_advisory_user_roles to authenticated;
grant select on public.portfolio_advisory_user_role_audit to authenticated;
create policy "Portfolio owner lists advisory roles" on public.portfolio_advisory_user_roles
 for select to authenticated using(
 auth.uid() is not null and lower(coalesce(auth.jwt()->>'email',''))='jair.ribeiro@outlook.it');
create policy "Portfolio owner reads advisory role audit" on public.portfolio_advisory_user_role_audit
 for select to authenticated using(
 auth.uid() is not null and lower(coalesce(auth.jwt()->>'email',''))='jair.ribeiro@outlook.it');
insert into public.portfolio_advisory_user_roles(user_id,role,assigned_by)
select id,'admin',id from auth.users where lower(email)='jair.ribeiro@outlook.it'
and email_confirmed_at is not null
on conflict(user_id) do update set role='admin',updated_at=now();

CREATE OR REPLACE FUNCTION public.portfolio_advisory_check_new_start_v1()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare v_service text; v_enabled boolean;
begin
 if tg_table_name='portfolio_advisory_requests' then
  v_service:=new.source_service;
 else
  v_service:=tg_argv[0];
 end if;
 select c.is_enabled into v_enabled
 from public.portfolio_advisory_service_visibility c where c.service_key=v_service;
 if v_enabled is distinct from true
    and not public.portfolio_advisory_is_admin_v1() then
  raise exception 'This Advisory service is not available.'
   using errcode='42501';
 end if;
 return new;
end; $function$
;

CREATE OR REPLACE FUNCTION public.portfolio_advisory_is_admin_v1()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
 select auth.uid() is not null
 and exists (
  select 1 from auth.users u
  join public.portfolio_advisory_user_roles r on r.user_id=u.id
  where u.id=auth.uid() and u.email_confirmed_at is not null and r.role='admin'
 );
$function$
;

CREATE OR REPLACE FUNCTION public.portfolio_advisory_my_role_v1()
 RETURNS text
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
 select case when public.portfolio_advisory_is_admin_v1() then 'admin' else 'regular' end;
$function$
;
revoke all on function public.portfolio_advisory_is_admin_v1() from public,anon,authenticated;
grant execute on function public.portfolio_advisory_is_admin_v1() to authenticated;
revoke all on function public.portfolio_advisory_my_role_v1() from public,anon,authenticated;
grant execute on function public.portfolio_advisory_my_role_v1() to authenticated;
revoke all on function public.portfolio_advisory_check_new_start_v1() from public,anon,authenticated;
