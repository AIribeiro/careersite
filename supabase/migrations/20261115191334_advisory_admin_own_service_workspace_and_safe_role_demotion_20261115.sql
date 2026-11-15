-- Private self-owned service workspaces for admins, without bypassing client RLS.
-- Admin-created entitlements are revoked on demotion; other client approvals are preserved.
create table if not exists public.portfolio_advisory_admin_workspace_grants(
 user_id uuid not null references auth.users(id) on delete cascade,
 service_key text not null check(service_key in ('scorecard','rollout')),
 request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
 entitlement_id uuid not null,
 created_at timestamptz not null default now(),
 revoked_at timestamptz,
 primary key(user_id,service_key)
);
alter table public.portfolio_advisory_admin_workspace_grants enable row level security;
revoke all on public.portfolio_advisory_admin_workspace_grants from public,anon,authenticated;
CREATE OR REPLACE FUNCTION public.portfolio_advisory_admin_ensure_workspace_v1(p_service_key text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid:=auth.uid(); v_request uuid; v_entitlement uuid; v_status text; v_existing uuid;
begin
 if p_service_key not in ('scorecard','rollout') or p_service_key is null then
   raise exception 'Unsupported administrator service' using errcode='22023';
 end if;
 if v_uid is null or not public.portfolio_advisory_is_admin_v1()
    or not public.portfolio_advisory_password_session_v1()
    or not exists(select 1 from public.portfolio_advisory_profiles p where p.user_id=v_uid and p.account_status='active') then
   raise exception 'Verified active Advisory admin required' using errcode='42501';
 end if;
 perform 1 from public.portfolio_advisory_profiles p
 where p.user_id=v_uid and p.account_status='active' for update;
 if p_service_key='scorecard' then
  select s.id,s.request_id into v_entitlement,v_request
  from public.portfolio_advisory_scorecards s
  join public.portfolio_advisory_requests r on r.id=s.request_id
  where s.user_id=v_uid and s.status='active'
    and r.status not in ('closed','declined')
  order by s.approved_at desc limit 1;
 else
  select a.id,a.request_id into v_entitlement,v_request
  from public.portfolio_advisory_rollout_access a
  join public.portfolio_advisory_requests r on r.id=a.request_id
  where a.user_id=v_uid and a.status='active'
    and r.status not in ('closed','declined')
  order by a.approved_at desc limit 1;
 end if;
 if v_entitlement is not null then
  return jsonb_build_object('status','existing','service_key',p_service_key);
 end if;
 -- Reuse an existing authorized admin-only grant where it was previously revoked.
 select g.entitlement_id,g.request_id into v_existing,v_request
 from public.portfolio_advisory_admin_workspace_grants g
 join public.portfolio_advisory_requests r on r.id=g.request_id
 where g.user_id=v_uid and g.service_key=p_service_key
   and r.status not in ('closed','declined');
 if v_existing is not null then
  if p_service_key='scorecard' then
   update public.portfolio_advisory_scorecards s
   set status='active',revoked_at=null,updated_at=now()
   where s.id=v_existing and s.user_id=v_uid returning s.id into v_entitlement;
  else
   update public.portfolio_advisory_rollout_access a
   set status='active',revoked_at=null,updated_at=now()
   where a.id=v_existing and a.user_id=v_uid returning a.id into v_entitlement;
  end if;
  if v_entitlement is not null then
   update public.portfolio_advisory_admin_workspace_grants g
   set revoked_at=null where g.user_id=v_uid and g.service_key=p_service_key;
   return jsonb_build_object('status','restored','service_key',p_service_key);
  end if;
 end if;
 -- Existing open personal requests are reused; no duplicate active request is made.
 select r.id into v_request from public.portfolio_advisory_requests r
 where r.user_id=v_uid and r.status not in ('closed','declined')
 order by r.created_at desc limit 1;
 if v_request is null then
   insert into public.portfolio_advisory_requests(
    user_id,title,desired_outcome,business_context,decision_timing,contact_preference,status,source_service)
   values(
    v_uid,
    case when p_service_key='scorecard'
      then 'AI Portfolio Prioritization Scorecard — access request'
      else 'Enterprise AI Rollout Readiness Advisor — access request' end,
    'Internal Advisory admin workspace for ongoing service evaluation.',
    'Administrator-owned decision workspace. Not an external client engagement.',
    'Exploratory','Email','active',p_service_key)
   returning id into v_request;
 end if;
 if p_service_key='scorecard' then
   -- A manually revoked entitlement on this request remains owner-controlled.
   if exists(select 1 from public.portfolio_advisory_scorecards s
             where s.request_id=v_request and s.analysis_request_id is null) then
     raise exception 'An existing Scorecard entitlement requires owner review' using errcode='42501';
   end if;
   insert into public.portfolio_advisory_scorecards(
    request_id,user_id,status,approved_by)
   values(v_request,v_uid,'active',v_uid)
   returning id into v_entitlement;
 else
   if exists(select 1 from public.portfolio_advisory_rollout_access a
             where a.request_id=v_request) then
     raise exception 'An existing Rollout entitlement requires owner review' using errcode='42501';
   end if;
   insert into public.portfolio_advisory_rollout_access(
    request_id,user_id,status,approved_by)
   values(v_request,v_uid,'active',v_uid)
   returning id into v_entitlement;
 end if;
 insert into public.portfolio_advisory_admin_workspace_grants(
  user_id,service_key,request_id,entitlement_id,revoked_at)
 values(v_uid,p_service_key,v_request,v_entitlement,null)
 on conflict(user_id,service_key) do update set
  request_id=excluded.request_id,
  entitlement_id=excluded.entitlement_id,
  revoked_at=null,created_at=now();
 return jsonb_build_object('status','created','service_key',p_service_key);
end; $function$
;

CREATE OR REPLACE FUNCTION public.portfolio_advisory_revoke_admin_workspaces_v1(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
 if auth.uid() is null or not exists(
  select 1 from auth.users u where u.id=auth.uid()
    and u.email_confirmed_at is not null
    and lower(u.email)='jair.ribeiro@outlook.it'
 ) then
  raise exception 'Portfolio owner authorization required' using errcode='42501';
 end if;
 update public.portfolio_advisory_scorecards s set
   status='revoked',revoked_at=now(),updated_at=now()
 from public.portfolio_advisory_admin_workspace_grants g
 where g.user_id=p_user_id and g.service_key='scorecard'
   and s.id=g.entitlement_id and s.user_id=p_user_id and s.status='active';
 update public.portfolio_advisory_rollout_access a set
   status='revoked',revoked_at=now(),updated_at=now()
 from public.portfolio_advisory_admin_workspace_grants g
 where g.user_id=p_user_id and g.service_key='rollout'
   and a.id=g.entitlement_id and a.user_id=p_user_id and a.status='active';
 update public.portfolio_advisory_admin_workspace_grants g set revoked_at=now()
 where g.user_id=p_user_id and g.revoked_at is null;
end; $function$
;

CREATE OR REPLACE FUNCTION public.portfolio_advisory_set_user_role_v1(p_user_id uuid, p_role text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_actor uuid:=auth.uid(); v_previous text; v_email text;
begin
 if v_actor is null or not exists(
  select 1 from auth.users u where u.id=v_actor
   and u.email_confirmed_at is not null
   and lower(u.email)='jair.ribeiro@outlook.it'
 ) then
  raise exception 'Portfolio owner authorization required' using errcode='42501';
 end if;
 if p_user_id is null or p_role is null or p_role not in ('regular','admin') then
  raise exception 'Valid user and role required' using errcode='22023';
 end if;
 select lower(email) into v_email from auth.users
 where id=p_user_id and email_confirmed_at is not null;
 if v_email is null or not exists(
  select 1 from public.portfolio_advisory_profiles p where p.user_id=p_user_id
  union all select 1 from public.portfolio_reader_profiles r where r.user_id=p_user_id
 ) then
  raise exception 'A verified portfolio account is required' using errcode='22023';
 end if;
 if v_email='jair.ribeiro@outlook.it' and p_role<>'admin' then
  raise exception 'The portfolio owner must remain an admin' using errcode='42501';
 end if;
 select role into v_previous from public.portfolio_advisory_user_roles
 where user_id=p_user_id for update;
 v_previous:=coalesce(v_previous,'regular');
 insert into public.portfolio_advisory_user_roles(user_id,role,assigned_by,updated_at)
 values(p_user_id,p_role,v_actor,now())
 on conflict(user_id) do update set
  role=excluded.role,assigned_by=excluded.assigned_by,updated_at=excluded.updated_at;
 if v_previous is distinct from p_role then
  if p_role='regular' then
    perform public.portfolio_advisory_revoke_admin_workspaces_v1(p_user_id);
  end if;
  insert into public.portfolio_advisory_user_role_audit(user_id,previous_role,new_role,actor_id)
  values(p_user_id,v_previous,p_role,v_actor);
 end if;
 return jsonb_build_object('user_id',p_user_id,'role',p_role,'changed',v_previous is distinct from p_role);
end; $function$
;
revoke all on function public.portfolio_advisory_admin_ensure_workspace_v1(text) from public,anon,authenticated;
grant execute on function public.portfolio_advisory_admin_ensure_workspace_v1(text) to authenticated;
revoke all on function public.portfolio_advisory_revoke_admin_workspaces_v1(uuid) from public,anon,authenticated;
revoke all on function public.portfolio_advisory_set_user_role_v1(uuid,text) from public,anon,authenticated;
grant execute on function public.portfolio_advisory_set_user_role_v1(uuid,text) to authenticated;
