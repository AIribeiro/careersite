
-- One-session rollout decision advisor and contextual client satisfaction.
-- Member/owner access is inherited from the verified, password-authenticated Advisory account.
create table if not exists public.portfolio_advisory_rollout_access (
 id uuid primary key default gen_random_uuid(),
 request_id uuid not null unique references public.portfolio_advisory_requests(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 status text not null default 'active' check (status in ('active','revoked')),
 approved_by uuid not null references auth.users(id),
 approved_at timestamptz not null default now(),
 revoked_at timestamptz,
 updated_at timestamptz not null default now()
);
create index if not exists rollout_access_user_idx on public.portfolio_advisory_rollout_access(user_id,status);

create table if not exists public.portfolio_advisory_rollout_assessments (
 id uuid primary key default gen_random_uuid(),
 access_id uuid not null references public.portfolio_advisory_rollout_access(id) on delete cascade,
 request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 answers jsonb not null check (jsonb_typeof(answers)='object' and length(answers::text)<=16000),
 model_version text not null default 'rollout-v1',
 created_at timestamptz not null default now()
);
create index if not exists rollout_assessments_user_created_idx
 on public.portfolio_advisory_rollout_assessments(user_id,created_at desc);

create table if not exists public.portfolio_advisory_rollout_audit (
 id bigint generated always as identity primary key,
 access_id uuid not null references public.portfolio_advisory_rollout_access(id) on delete cascade,
 actor_id uuid not null,
 action text not null check(action in ('approve','revoke','assess')),
 assessment_id uuid,
 created_at timestamptz not null default now()
);

create table if not exists public.portfolio_advisory_feedback (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 request_id uuid references public.portfolio_advisory_requests(id) on delete set null,
 service_key text not null check(service_key in ('advisory','scorecard','rollout')),
 stage text not null check(stage in ('onboarding','conversation','assessment','recommendation','download','decision')),
 interaction_key text not null check(length(interaction_key) between 1 and 80),
 rating integer not null check(rating between 1 and 5),
 comment text not null default '' check(length(comment)<=1000),
 created_at timestamptz not null default now(),
 unique(user_id,service_key,stage,interaction_key),
 check(
  (service_key='advisory' and stage in ('onboarding','conversation'))
  or (service_key='scorecard' and stage='decision')
  or (service_key='rollout' and stage in ('assessment','recommendation','download'))
 )
);
create index if not exists advisory_feedback_stage_idx
 on public.portfolio_advisory_feedback(service_key,stage,created_at desc);

alter table public.portfolio_advisory_rollout_access enable row level security;
alter table public.portfolio_advisory_rollout_assessments enable row level security;
alter table public.portfolio_advisory_rollout_audit enable row level security;
alter table public.portfolio_advisory_feedback enable row level security;
revoke all on public.portfolio_advisory_rollout_access from public,anon,authenticated;
revoke all on public.portfolio_advisory_rollout_assessments from public,anon,authenticated;
revoke all on public.portfolio_advisory_rollout_audit from public,anon,authenticated;
revoke all on public.portfolio_advisory_feedback from public,anon,authenticated;
grant select on public.portfolio_advisory_rollout_access to authenticated;
grant select on public.portfolio_advisory_rollout_assessments to authenticated;
grant select on public.portfolio_advisory_rollout_audit to authenticated;
grant select,insert on public.portfolio_advisory_feedback to authenticated;

create policy "Member reads their individually approved rollout access"
 on public.portfolio_advisory_rollout_access for select to authenticated
 using (
  user_id=(select auth.uid()) and status='active'
  and (select public.portfolio_advisory_password_session_v1())
  and exists(select 1 from public.portfolio_advisory_profiles p
    where p.user_id=portfolio_advisory_rollout_access.user_id and p.account_status='active')
  and exists(select 1 from public.portfolio_advisory_requests r
    where r.id=request_id and r.user_id=portfolio_advisory_rollout_access.user_id
      and r.status in ('active','completed'))
 );
create policy "Owner reads rollout access" on public.portfolio_advisory_rollout_access
 for select to authenticated
 using(lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it');
create policy "Member reads own approved rollout assessments"
 on public.portfolio_advisory_rollout_assessments for select to authenticated
 using(
  user_id=(select auth.uid()) and (select public.portfolio_advisory_password_session_v1())
  and exists(select 1 from public.portfolio_advisory_rollout_access a
    join public.portfolio_advisory_requests r on r.id=a.request_id
    where a.id=access_id and a.user_id=portfolio_advisory_rollout_assessments.user_id
    and a.status='active' and r.status in ('active','completed'))
 );
create policy "Owner reads rollout assessments" on public.portfolio_advisory_rollout_assessments
 for select to authenticated
 using(lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it');
create policy "Owner reads rollout audit" on public.portfolio_advisory_rollout_audit
 for select to authenticated
 using(lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it');

create policy "Member reads their feedback" on public.portfolio_advisory_feedback
 for select to authenticated using(
  user_id=(select auth.uid()) and (select public.portfolio_advisory_password_session_v1())
 );
create policy "Owner reads feedback" on public.portfolio_advisory_feedback
 for select to authenticated
 using(lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it');
create policy "Verified Advisory client submits contextual feedback"
 on public.portfolio_advisory_feedback for insert to authenticated
 with check(
  user_id=(select auth.uid())
  and (select public.portfolio_advisory_password_session_v1())
  and exists(select 1 from public.portfolio_advisory_profiles p
    where p.user_id=(select auth.uid()) and p.account_status='active')
  and (
   (service_key='advisory' and stage='onboarding' and request_id is null)
   or (service_key='advisory' and stage='conversation'
    and exists(select 1 from public.portfolio_advisory_requests r
      where r.id=request_id and r.user_id=(select auth.uid())))
   or (service_key='scorecard' and stage='decision'
    and exists(select 1 from public.portfolio_advisory_scorecards s
      where s.request_id=portfolio_advisory_feedback.request_id
       and s.user_id=(select auth.uid()) and s.status='active'))
   or (service_key='rollout' and stage in ('assessment','recommendation','download')
    and exists(select 1 from public.portfolio_advisory_rollout_access a
      where a.request_id=portfolio_advisory_feedback.request_id
       and a.user_id=(select auth.uid()) and a.status='active'))
  )
 );

create or replace function public.portfolio_advisory_rollout_owner_action_v1(
 p_request_id uuid,p_action text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_uid uuid; v_owner uuid; v_id uuid; v_status text;
begin
 v_owner:=auth.uid();
 if v_owner is null or not exists(
  select 1 from auth.users u where u.id=v_owner
  and lower(u.email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Not authorized' using errcode='42501'; end if;
 if p_action not in ('approve','revoke') then raise exception 'Unsupported action'; end if;
 select r.user_id,r.status into v_uid,v_status
 from public.portfolio_advisory_requests r where r.id=p_request_id;
 if v_uid is null then raise exception 'Advisory request not found'; end if;
 if p_action='approve' then
  if v_status <> 'active' then raise exception 'An agreed active Advisory engagement is required'; end if;
  insert into public.portfolio_advisory_rollout_access(request_id,user_id,approved_by)
  values(p_request_id,v_uid,v_owner)
  on conflict(request_id) do update set status='active',approved_by=excluded.approved_by,
   approved_at=now(),revoked_at=null,updated_at=now()
  returning id,status into v_id,v_status;
 else
  update public.portfolio_advisory_rollout_access
  set status='revoked',revoked_at=now(),updated_at=now()
  where request_id=p_request_id returning id,status into v_id,v_status;
  if v_id is null then raise exception 'No rollout entitlement exists'; end if;
 end if;
 insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action)
 values(v_id,v_owner,p_action);
 return jsonb_build_object('id',v_id,'status',v_status);
end $$;
revoke all on function public.portfolio_advisory_rollout_owner_action_v1(uuid,text) from public,anon;
grant execute on function public.portfolio_advisory_rollout_owner_action_v1(uuid,text) to authenticated;

create or replace function public.portfolio_advisory_rollout_assess_v1(
 p_request_id uuid,p_answers jsonb
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_uid uuid; v_access_id uuid; v_id uuid;
begin
 v_uid:=auth.uid();
 if v_uid is null or not public.portfolio_advisory_password_session_v1() then
  raise exception 'Verified Advisory session required' using errcode='42501'; end if;
 if p_answers is null or jsonb_typeof(p_answers)<>'object'
 or length(p_answers::text)>16000
 or jsonb_typeof(p_answers->'responses')<>'object'
 or (select count(*) from jsonb_object_keys(p_answers->'responses')) <> 18
 or exists(select 1 from jsonb_each_text(p_answers->'responses') kv
   where kv.value not in ('0','1','2','3'))
 then raise exception 'Invalid rollout assessment inputs'; end if;
 select a.id into v_access_id from public.portfolio_advisory_rollout_access a
 join public.portfolio_advisory_requests r on r.id=a.request_id
 join public.portfolio_advisory_profiles p on p.user_id=a.user_id
 where a.request_id=p_request_id and a.user_id=v_uid and a.status='active'
 and r.status in ('active','completed') and p.account_status='active';
 if v_access_id is null then raise exception 'No active approved rollout entitlement' using errcode='42501'; end if;
 if (select count(*) from public.portfolio_advisory_rollout_assessments x
     where x.user_id=v_uid and x.created_at>now()-interval '24 hours')>=20 then
   raise exception 'Assessment submission limit reached'; end if;
 insert into public.portfolio_advisory_rollout_assessments(access_id,request_id,user_id,answers)
 values(v_access_id,p_request_id,v_uid,p_answers) returning id into v_id;
 insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action,assessment_id)
 values(v_access_id,v_uid,'assess',v_id);
 return jsonb_build_object('id',v_id,'request_id',p_request_id);
end $$;
revoke all on function public.portfolio_advisory_rollout_assess_v1(uuid,jsonb) from public,anon;
grant execute on function public.portfolio_advisory_rollout_assess_v1(uuid,jsonb) to authenticated;
