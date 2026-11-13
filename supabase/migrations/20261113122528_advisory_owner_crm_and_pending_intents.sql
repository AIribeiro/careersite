
create table if not exists public.portfolio_advisory_intents (
 user_id uuid primary key references auth.users(id) on delete cascade,
 email text not null,
 source text not null default 'self_signup' check (source in ('self_signup','owner_reconciled')),
 created_at timestamptz not null default now()
);
alter table public.portfolio_advisory_intents enable row level security;
revoke all on public.portfolio_advisory_intents from anon, authenticated;
grant select,insert on public.portfolio_advisory_intents to authenticated;
drop policy if exists "Advisory intent owner review" on public.portfolio_advisory_intents;
create policy "Advisory intent owner review" on public.portfolio_advisory_intents
 for select to authenticated using (
   user_id=(select auth.uid())
   or lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it'
 );
drop policy if exists "Own verified advisory intent" on public.portfolio_advisory_intents;
create policy "Own verified advisory intent" on public.portfolio_advisory_intents
 for insert to authenticated with check (
   user_id=(select auth.uid())
   and lower(email)=lower((select auth.jwt()->>'email'))
   and source='self_signup'
   and (select auth.jwt()->>'is_anonymous') is distinct from 'true'
 );
drop policy if exists "Advisory owner views memberships" on public.portfolio_advisory_profiles;
create policy "Advisory owner views memberships" on public.portfolio_advisory_profiles
 for select to authenticated using (
   lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it'
 );
create table if not exists public.portfolio_advisory_admin_records (
 user_id uuid primary key references auth.users(id) on delete cascade,
 relationship_stage text not null default 'inquiry'
   check (relationship_stage in ('inquiry','discovery','proposal','engaged','closed')),
 internal_notes text not null default '' check(length(internal_notes)<=10000),
 next_action text not null default '' check(length(next_action)<=2000),
 follow_up_on date,
 updated_at timestamptz not null default now(),
 updated_by uuid references auth.users(id)
);
alter table public.portfolio_advisory_admin_records enable row level security;
revoke all on public.portfolio_advisory_admin_records from anon,authenticated;
grant select on public.portfolio_advisory_admin_records to authenticated;
drop policy if exists "Advisory owner reads management" on public.portfolio_advisory_admin_records;
create policy "Advisory owner reads management" on public.portfolio_advisory_admin_records
 for select to authenticated using (lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it');
create table if not exists public.portfolio_advisory_admin_audit (
 id bigint generated always as identity primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 actor_id uuid not null references auth.users(id),
 action text not null,
 detail text not null default '',
 created_at timestamptz not null default now()
);
alter table public.portfolio_advisory_admin_audit enable row level security;
revoke all on public.portfolio_advisory_admin_audit from anon,authenticated;
grant select on public.portfolio_advisory_admin_audit to authenticated;
drop policy if exists "Advisory owner reads audit" on public.portfolio_advisory_admin_audit;
create policy "Advisory owner reads audit" on public.portfolio_advisory_admin_audit
 for select to authenticated using (lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it');

create or replace function public.portfolio_advisory_owner_action_v1(
 p_user_id uuid, p_action text, p_value text default null, p_date date default null
) returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare v_actor uuid := auth.uid();
        v_email text;
        v_row public.portfolio_advisory_admin_records%rowtype;
begin
 if v_actor is null then raise exception 'Unauthorized'; end if;
 select lower(u.email) into v_email from auth.users u where u.id=v_actor;
 if v_email is distinct from 'jair.ribeiro@outlook.it' then
   raise exception 'Unauthorized';
 end if;
 if not exists (select 1 from public.portfolio_advisory_intents where user_id=p_user_id)
    and not exists (select 1 from public.portfolio_advisory_profiles where user_id=p_user_id) then
   raise exception 'Unknown advisory relationship';
 end if;
 if p_action not in ('stage','note','next_action','follow_up','suspend','reinstate') then
   raise exception 'Unsupported action';
 end if;
 insert into public.portfolio_advisory_admin_records(user_id,updated_by)
 values(p_user_id,v_actor)
 on conflict (user_id) do nothing;
 if p_action='stage' then
   if p_value not in ('inquiry','discovery','proposal','engaged','closed') then
     raise exception 'Invalid relationship stage';
   end if;
   update public.portfolio_advisory_admin_records
     set relationship_stage=p_value,updated_at=now(),updated_by=v_actor where user_id=p_user_id;
 elsif p_action='note' then
   if length(coalesce(p_value,'')) > 10000 then raise exception 'Note too long'; end if;
   update public.portfolio_advisory_admin_records
     set internal_notes=coalesce(p_value,''),updated_at=now(),updated_by=v_actor where user_id=p_user_id;
 elsif p_action='next_action' then
   if length(coalesce(p_value,'')) > 2000 then raise exception 'Next action too long'; end if;
   update public.portfolio_advisory_admin_records
     set next_action=coalesce(p_value,''),updated_at=now(),updated_by=v_actor where user_id=p_user_id;
 elsif p_action='follow_up' then
   update public.portfolio_advisory_admin_records
     set follow_up_on=p_date,updated_at=now(),updated_by=v_actor where user_id=p_user_id;
 else
   update public.portfolio_advisory_profiles set
     account_status=case when p_action='suspend' then 'suspended' else 'active' end,
     updated_at=now() where user_id=p_user_id;
   if not found then raise exception 'Advisory profile not completed'; end if;
 end if;
 insert into public.portfolio_advisory_admin_audit(user_id,actor_id,action,detail)
 values(p_user_id,v_actor,p_action,
   case when p_action='note' then '[private note updated]'
   when p_action='next_action' then '[next action updated]'
   when p_action='follow_up' then coalesce(p_date::text,'cleared')
   else coalesce(p_value,'') end);
 select * into v_row from public.portfolio_advisory_admin_records where user_id=p_user_id;
 return jsonb_build_object('user_id',p_user_id,'action',p_action,'stage',v_row.relationship_stage);
end;
$$;
revoke all on function public.portfolio_advisory_owner_action_v1(uuid,text,text,date) from public,anon;
grant execute on function public.portfolio_advisory_owner_action_v1(uuid,text,text,date) to authenticated;

-- Reconcile a reported Advisory signup as an *incomplete* relationship only.
-- This does not create a verified Advisory membership or a paid engagement.
insert into public.portfolio_advisory_intents(user_id,email,source)
 select id,lower(email),'owner_reconciled' from auth.users
 where lower(email)='jair.ribeiro@outlook.it' and email_confirmed_at is not null
 on conflict(user_id) do nothing;
