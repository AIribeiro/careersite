
-- Independent, individually approved analysis requests. Legacy entitlement remains.
create table public.portfolio_advisory_scorecard_analysis_requests (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 anchor_scorecard_id uuid not null references public.portfolio_advisory_scorecards(id) on delete restrict,
 request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
 title text not null check(length(btrim(title)) between 10 and 140),
 decision_context text not null check(length(btrim(decision_context)) between 20 and 1800),
 expected_outcome text not null check(length(btrim(expected_outcome)) between 10 and 800),
 decision_timing text not null check(decision_timing in ('This month','1–3 months','Exploratory')),
 status text not null default 'pending' check(status in ('pending','approved','declined','revoked')),
 decision_note text not null default '' check(length(decision_note)<=1000),
 decided_by uuid references auth.users(id),
 decided_at timestamptz,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create unique index scorecard_one_pending_analysis_per_client
 on public.portfolio_advisory_scorecard_analysis_requests(user_id)
 where status='pending';
create index scorecard_analysis_owner_queue
 on public.portfolio_advisory_scorecard_analysis_requests(status,created_at desc);
create index scorecard_analysis_member_history
 on public.portfolio_advisory_scorecard_analysis_requests(user_id,created_at desc);

alter table public.portfolio_advisory_scorecards
 add column analysis_request_id uuid
 references public.portfolio_advisory_scorecard_analysis_requests(id) on delete restrict;
alter table public.portfolio_advisory_scorecards
 drop constraint portfolio_advisory_scorecards_request_id_key;
create unique index scorecard_legacy_one_entitlement_per_engagement
 on public.portfolio_advisory_scorecards(request_id)
 where analysis_request_id is null;
create unique index scorecard_approved_one_workspace_per_request
 on public.portfolio_advisory_scorecards(analysis_request_id)
 where analysis_request_id is not null;

alter table public.portfolio_advisory_scorecard_analysis_requests enable row level security;
revoke all on public.portfolio_advisory_scorecard_analysis_requests from public,anon,authenticated;
grant select on public.portfolio_advisory_scorecard_analysis_requests to authenticated;
create policy "Member sees own analysis requests only" on public.portfolio_advisory_scorecard_analysis_requests
 for select to authenticated
 using (
   user_id=(select auth.uid())
   and (select public.portfolio_advisory_password_session_v1())
   and exists(select 1 from public.portfolio_advisory_profiles p
              where p.user_id=(select auth.uid()) and p.account_status='active')
 );
create policy "Verified Advisory owner reviews analysis requests" on public.portfolio_advisory_scorecard_analysis_requests
 for select to authenticated
 using (
   exists(select 1 from auth.users u where u.id=(select auth.uid())
          and u.email_confirmed_at is not null
          and lower(u.email)='jair.ribeiro@outlook.it')
 );

create or replace function public.portfolio_advisory_scorecard_analysis_request_v1(
 p_anchor_scorecard_id uuid,p_title text,p_context text,p_outcome text,p_timing text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare
 v_uid uuid:=auth.uid();
 v_request_id uuid;
 v_id uuid;
begin
 if v_uid is null or not public.portfolio_advisory_password_session_v1()
    or not exists(select 1 from public.portfolio_advisory_profiles p
      join auth.users u on u.id=p.user_id where p.user_id=v_uid and p.account_status='active'
      and u.email_confirmed_at is not null) then
    raise exception 'Verified Advisory membership required' using errcode='42501';
 end if;
 if p_title is null or length(btrim(p_title)) not between 10 and 140
    or p_context is null or length(btrim(p_context)) not between 20 and 1800
    or p_outcome is null or length(btrim(p_outcome)) not between 10 and 800
    or p_timing not in ('This month','1–3 months','Exploratory') then
    raise exception 'Complete the analysis request fields' using errcode='22023';
 end if;
 select s.request_id into v_request_id
 from public.portfolio_advisory_scorecards s
 join public.portfolio_advisory_requests r on r.id=s.request_id
 where s.id=p_anchor_scorecard_id and s.user_id=v_uid
   and s.status='active' and r.user_id=v_uid
   and r.status not in ('closed','declined');
 if v_request_id is null then
   raise exception 'Approved Scorecard access required for another analysis'
   using errcode='42501';
 end if;
 insert into public.portfolio_advisory_scorecard_analysis_requests(
   user_id,anchor_scorecard_id,request_id,title,decision_context,
   expected_outcome,decision_timing
 ) values(v_uid,p_anchor_scorecard_id,v_request_id,btrim(p_title),btrim(p_context),
          btrim(p_outcome),p_timing)
 on conflict(user_id) where status='pending' do nothing
 returning id into v_id;
 if v_id is null then
   select id into v_id
   from public.portfolio_advisory_scorecard_analysis_requests
   where user_id=v_uid and status='pending';
   return jsonb_build_object('id',v_id,'status','pending','already_pending',true);
 end if;
 return jsonb_build_object('id',v_id,'status','pending','already_pending',false);
end $fn$;
revoke all on function public.portfolio_advisory_scorecard_analysis_request_v1(uuid,text,text,text,text) from public,anon;
grant execute on function public.portfolio_advisory_scorecard_analysis_request_v1(uuid,text,text,text,text) to authenticated;

create or replace function public.portfolio_advisory_scorecard_analysis_owner_v1(
 p_analysis_id uuid,p_action text,p_note text default ''
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare
 v_owner uuid:=auth.uid();
 v_req public.portfolio_advisory_scorecard_analysis_requests%rowtype;
 v_workspace uuid;
 v_email text;
begin
 if v_owner is null or not exists(
    select 1 from auth.users u where u.id=v_owner
    and u.email_confirmed_at is not null
    and lower(u.email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Owner only' using errcode='42501'; end if;
 if p_action not in ('approve','decline','revoke')
    or length(coalesce(p_note,''))>1000 then
    raise exception 'Invalid analysis action' using errcode='22023'; end if;
 select * into v_req
 from public.portfolio_advisory_scorecard_analysis_requests
 where id=p_analysis_id for update;
 if not found then raise exception 'Analysis request not found'; end if;
 if p_action='approve' and v_req.status='approved' then
   select id into v_workspace from public.portfolio_advisory_scorecards
   where analysis_request_id=p_analysis_id and status='active';
   return jsonb_build_object('id',p_analysis_id,'workspace_id',v_workspace,
                             'status','approved','unchanged',true);
 end if;
 if p_action='revoke' and v_req.status='revoked' then
   return jsonb_build_object('id',p_analysis_id,'status','revoked','unchanged',true);
 end if;
 if p_action in ('approve','decline') and v_req.status<>'pending' then
   raise exception 'Request is no longer pending' using errcode='22023'; end if;
 if p_action='revoke' and v_req.status<>'approved' then
   raise exception 'Only an approved analysis can be revoked' using errcode='22023'; end if;
 if p_action='approve' then
   if not exists(
       select 1 from public.portfolio_advisory_scorecards s
       join public.portfolio_advisory_requests r on r.id=s.request_id
       join public.portfolio_advisory_profiles p on p.user_id=s.user_id
       join auth.users u on u.id=s.user_id
       where s.id=v_req.anchor_scorecard_id
         and s.user_id=v_req.user_id and s.request_id=v_req.request_id
         and s.status='active' and r.user_id=v_req.user_id
         and r.status not in ('closed','declined')
         and p.account_status='active' and u.email_confirmed_at is not null
   ) then raise exception 'The original approved engagement is no longer active';
   end if;
   insert into public.portfolio_advisory_scorecards(
      request_id,user_id,status,approved_by,analysis_request_id,payload
   ) values(
      v_req.request_id,v_req.user_id,'active',v_owner,v_req.id,
      '{"settings":{"weights":[15,20,15,15,15,10,10],"advance":78,"test":62,"capacity_fte_months":12.0,"budget_sek":1200000.0,"max_tests":1},"initiatives":[]}'::jsonb
   ) returning id into v_workspace;
   insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
   values(v_workspace,v_owner,'approve');
   update public.portfolio_advisory_scorecard_analysis_requests
   set status='approved',decided_by=v_owner,decided_at=now(),
       decision_note=coalesce(p_note,''),updated_at=now()
   where id=p_analysis_id;
   -- Existing Supabase-backed notification queue processes approved services.
   select p.email into v_email from public.portfolio_advisory_profiles p
   where p.user_id=v_req.user_id;
   if v_email is not null then
     insert into public.portfolio_advisory_approval_notifications(
       request_id,user_id,service_key,recipient_email
     ) values(v_req.request_id,v_req.user_id,'scorecard',v_email);
   end if;
   return jsonb_build_object('id',p_analysis_id,'workspace_id',v_workspace,
      'status','approved','unchanged',false);
 elsif p_action='decline' then
   update public.portfolio_advisory_scorecard_analysis_requests
   set status='declined',decided_by=v_owner,decided_at=now(),
       decision_note=coalesce(p_note,''),updated_at=now()
   where id=p_analysis_id;
   return jsonb_build_object('id',p_analysis_id,'status','declined');
 else
   update public.portfolio_advisory_scorecards
   set status='revoked',revoked_at=now(),updated_at=now()
   where analysis_request_id=p_analysis_id and status='active'
   returning id into v_workspace;
   if v_workspace is null then raise exception 'Active analysis workspace not found'; end if;
   insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
   values(v_workspace,v_owner,'revoke');
   update public.portfolio_advisory_scorecard_analysis_requests
   set status='revoked',decided_by=v_owner,decided_at=now(),
       decision_note=coalesce(p_note,''),updated_at=now()
   where id=p_analysis_id;
   return jsonb_build_object('id',p_analysis_id,'workspace_id',v_workspace,
      'status','revoked');
 end if;
end $fn$;
revoke all on function public.portfolio_advisory_scorecard_analysis_owner_v1(uuid,text,text) from public,anon;
grant execute on function public.portfolio_advisory_scorecard_analysis_owner_v1(uuid,text,text) to authenticated;

-- Preserve the existing first-entitlement approval and revocation using the legacy-only index.
CREATE OR REPLACE FUNCTION public.portfolio_advisory_service_owner_action_v2(p_request_id uuid, p_service_key text, p_action text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
    v_owner uuid := auth.uid();
    v_uid uuid;
    v_stage text;
    v_email text;
    v_id uuid;
    v_old text;
    v_event_id uuid;
    v_new text;
begin
    if v_owner is null or not exists(
        select 1 from auth.users u
        where u.id=v_owner and u.email_confirmed_at is not null
        and lower(u.email)='jair.ribeiro@outlook.it'
    ) then raise exception 'Owner only' using errcode='42501'; end if;
    if p_service_key not in ('scorecard','rollout')
       or p_action not in ('approve','revoke')
    then raise exception 'Unsupported service action' using errcode='22023'; end if;

    select r.user_id,r.status,p.email into v_uid,v_stage,v_email
    from public.portfolio_advisory_requests r
    join public.portfolio_advisory_profiles p on p.user_id=r.user_id
    join auth.users u on u.id=r.user_id
    where r.id=p_request_id and p.account_status='active'
      and u.email_confirmed_at is not null and lower(u.email)=lower(p.email)
    for update of r;
    if v_uid is null then
        raise exception 'Verified active Advisory member and request required'
        using errcode='22023';
    end if;
    if p_action='approve' and v_stage in ('closed','declined') then
        raise exception 'Reopen the closed request before approving a service'
        using errcode='22023';
    end if;

    if p_service_key='scorecard' then
        select id,status into v_id,v_old
        from public.portfolio_advisory_scorecards
        where request_id=p_request_id and analysis_request_id is null for update;
    else
        select id,status into v_id,v_old
        from public.portfolio_advisory_rollout_access
        where request_id=p_request_id for update;
    end if;

    if p_action='approve' and v_old='active' then
        select n.id into v_event_id
        from public.portfolio_advisory_approval_notifications n
        where n.request_id=p_request_id and n.service_key=p_service_key
        order by n.created_at desc limit 1;
        return jsonb_build_object('id',v_id,'user_id',v_uid,'status','active',
             'unchanged',true,'notification_id',v_event_id);
    end if;

    if p_action='approve' then
        if p_service_key='scorecard' then
            insert into public.portfolio_advisory_scorecards(request_id,user_id,approved_by)
            values(p_request_id,v_uid,v_owner)
            on conflict (request_id) where analysis_request_id is null do update
                set status='active',approved_by=excluded.approved_by,
                    approved_at=now(),revoked_at=null,updated_at=now()
            returning id into v_id;
            insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
            values(v_id,v_owner,'approve');
        else
            insert into public.portfolio_advisory_rollout_access(request_id,user_id,approved_by)
            values(p_request_id,v_uid,v_owner)
            on conflict (request_id) do update
                set status='active',approved_by=excluded.approved_by,
                    approved_at=now(),revoked_at=null,updated_at=now()
            returning id into v_id;
            insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action)
            values(v_id,v_owner,'approve');
        end if;
        insert into public.portfolio_advisory_approval_notifications(
            request_id,user_id,service_key,recipient_email
        ) values(p_request_id,v_uid,p_service_key,v_email)
        returning id into v_event_id;
        v_new:='active';
    else
        if v_id is null then raise exception 'No entitlement to revoke'; end if;
        if v_old='revoked' then
            return jsonb_build_object('id',v_id,'user_id',v_uid,'status','revoked','unchanged',true);
        end if;
        if p_service_key='scorecard' then
            update public.portfolio_advisory_scorecards
            set status='revoked',revoked_at=now(),updated_at=now()
            where id=v_id;
            insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
            values(v_id,v_owner,'revoke');
        else
            update public.portfolio_advisory_rollout_access
            set status='revoked',revoked_at=now(),updated_at=now()
            where id=v_id;
            insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action)
            values(v_id,v_owner,'revoke');
        end if;
        v_new:='revoked';
    end if;
    return jsonb_build_object('id',v_id,'user_id',v_uid,'status',v_new,
            'unchanged',false,'notification_id',v_event_id);
end;
$function$
;
