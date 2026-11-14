
-- Individually approved, private AI Portfolio Scorecard workspaces.
-- No public, reader-only or unapproved advisory-account access.
create table if not exists public.portfolio_advisory_scorecards (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null unique references public.portfolio_advisory_requests(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'active' check (status in ('active','revoked')),
  payload jsonb not null default '{"initiatives":[],"settings":{"weights":[15,20,15,15,15,10,10],"advance":78,"test":62,"capacity_fte_months":12,"budget_sek":1200000}}'::jsonb
    check (jsonb_typeof(payload)='object'),
  revision integer not null default 0 check(revision>=0),
  approved_by uuid not null references auth.users(id),
  approved_at timestamptz not null default now(),
  revoked_at timestamptz,
  updated_at timestamptz not null default now()
);
create index if not exists scorecards_user_status_idx
on public.portfolio_advisory_scorecards(user_id,status);
create table if not exists public.portfolio_advisory_scorecard_audit (
 id bigint generated always as identity primary key,
 scorecard_id uuid not null references public.portfolio_advisory_scorecards(id) on delete cascade,
 actor_id uuid not null,
 action text not null check(action in ('approve','revoke','save')),
 revision integer,
 created_at timestamptz not null default now()
);

alter table public.portfolio_advisory_scorecards enable row level security;
alter table public.portfolio_advisory_scorecard_audit enable row level security;

revoke all on public.portfolio_advisory_scorecards from public,anon,authenticated;
revoke all on public.portfolio_advisory_scorecard_audit from public,anon,authenticated;
grant select on public.portfolio_advisory_scorecards to authenticated;
grant select on public.portfolio_advisory_scorecard_audit to authenticated;

create policy "Scorecard client reads only individually approved engagement"
 on public.portfolio_advisory_scorecards for select to authenticated
 using (
  user_id=(select auth.uid()) and status='active'
  and (select public.portfolio_advisory_password_session_v1())
  and exists (
   select 1 from public.portfolio_advisory_requests r
   where r.id=request_id and r.user_id=user_id and r.status in ('active','completed')
  )
  and exists(
   select 1 from public.portfolio_advisory_profiles p
   where p.user_id=user_id and p.account_status='active'
  )
 );
create policy "Scorecard owner reads for client support"
 on public.portfolio_advisory_scorecards for select to authenticated
 using (
  lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it'
 );
create policy "Scorecard audit owner reads only"
 on public.portfolio_advisory_scorecard_audit for select to authenticated
 using (
  lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it'
 );

create or replace function public.portfolio_advisory_scorecard_owner_action_v1(
 p_request_id uuid, p_action text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_uid uuid; v_owner uuid; v_id uuid; v_status text;
begin
 v_owner:=auth.uid();
 if v_owner is null or not exists(
  select 1 from auth.users u where u.id=v_owner and lower(u.email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Not authorized' using errcode='42501'; end if;
 if p_action not in ('approve','revoke') then raise exception 'Unsupported action'; end if;
 select r.user_id, r.status into v_uid,v_status
 from public.portfolio_advisory_requests r where r.id=p_request_id;
 if v_uid is null then raise exception 'Advisory request not found'; end if;
 if p_action='approve' then
  if v_status <> 'active' then
   raise exception 'Only an active, agreed Advisory engagement can receive this service';
  end if;
  insert into public.portfolio_advisory_scorecards(request_id,user_id,approved_by)
  values(p_request_id,v_uid,v_owner)
  on conflict(request_id) do update set
   status='active',approved_by=excluded.approved_by,approved_at=now(),
   revoked_at=null,updated_at=now()
  returning id,status into v_id,v_status;
 else
  update public.portfolio_advisory_scorecards
  set status='revoked',revoked_at=now(),updated_at=now()
  where request_id=p_request_id returning id,status into v_id,v_status;
  if v_id is null then raise exception 'No scorecard access exists for request'; end if;
 end if;
 insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
 values(v_id,v_owner,p_action);
 return jsonb_build_object('id',v_id,'status',v_status,'user_id',v_uid);
end $$;
revoke all on function public.portfolio_advisory_scorecard_owner_action_v1(uuid,text) from public,anon;
grant execute on function public.portfolio_advisory_scorecard_owner_action_v1(uuid,text) to authenticated;

create or replace function public.portfolio_advisory_scorecard_save_v1(
 p_id uuid,p_payload jsonb,p_expected_revision integer
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_uid uuid; v_new_revision integer; v_request_id uuid;
begin
 v_uid:=auth.uid();
 if v_uid is null or not public.portfolio_advisory_password_session_v1() then
  raise exception 'Verified advisory session required' using errcode='42501';
 end if;
 if p_payload is null or jsonb_typeof(p_payload)<>'object'
 or not (p_payload ? 'initiatives')
 or jsonb_typeof(p_payload->'initiatives')<>'array'
 or jsonb_array_length(p_payload->'initiatives')>30
 or length(p_payload::text)>150000
 or p_expected_revision is null or p_expected_revision<0 then
  raise exception 'Invalid scorecard payload';
 end if;
 update public.portfolio_advisory_scorecards s
 set payload=p_payload,revision=revision+1,updated_at=now()
 where s.id=p_id and s.user_id=v_uid and s.status='active'
 and s.revision=p_expected_revision
 and exists (select 1 from public.portfolio_advisory_requests r
             where r.id=s.request_id and r.user_id=v_uid
             and r.status in ('active','completed'))
 and exists (select 1 from public.portfolio_advisory_profiles p
             where p.user_id=v_uid and p.account_status='active')
 returning s.revision,s.request_id into v_new_revision,v_request_id;
 if v_new_revision is null then
  raise exception 'Access revoked, session invalid, or this workspace has changed. Reload before saving.' using errcode='42501';
 end if;
 insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action,revision)
 values(p_id,v_uid,'save',v_new_revision);
 return jsonb_build_object('id',p_id,'revision',v_new_revision,'request_id',v_request_id);
end $$;
revoke all on function public.portfolio_advisory_scorecard_save_v1(uuid,jsonb,integer) from public,anon;
grant execute on function public.portfolio_advisory_scorecard_save_v1(uuid,jsonb,integer) to authenticated;
