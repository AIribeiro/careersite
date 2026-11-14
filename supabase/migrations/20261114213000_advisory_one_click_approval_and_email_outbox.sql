
-- Owner approval is an entitlement decision, not an invented engagement transition.
-- Each approval transition gets a private durable transactional-email record.
create table if not exists public.portfolio_advisory_approval_notifications (
    id uuid primary key default gen_random_uuid(),
    request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    service_key text not null check (service_key in ('scorecard','rollout')),
    recipient_email text not null check (char_length(recipient_email) between 3 and 254),
    state text not null default 'pending'
        check (state in ('pending','sending','sent','failed')),
    attempts integer not null default 0 check (attempts >= 0 and attempts <= 25),
    provider_message_id text not null default '',
    error_category text not null default '',
    created_at timestamptz not null default now(),
    last_attempt_at timestamptz,
    sent_at timestamptz,
    updated_at timestamptz not null default now()
);
create index if not exists advisory_approval_notifications_recent
on public.portfolio_advisory_approval_notifications(request_id,service_key,created_at desc);
alter table public.portfolio_advisory_approval_notifications enable row level security;
revoke all on public.portfolio_advisory_approval_notifications from public,anon,authenticated;
grant select on public.portfolio_advisory_approval_notifications to authenticated;
drop policy if exists "Owner sees advisory approval notifications" on public.portfolio_advisory_approval_notifications;
create policy "Owner sees advisory approval notifications"
on public.portfolio_advisory_approval_notifications for select to authenticated
using (
  auth.uid() is not null and
  exists(select 1 from auth.users u
         where u.id=(select auth.uid())
         and u.email_confirmed_at is not null
         and lower(u.email)='jair.ribeiro@outlook.it')
);

create or replace function public.portfolio_advisory_service_owner_action_v2(
    p_request_id uuid, p_service_key text, p_action text)
returns jsonb language plpgsql security definer set search_path = ''
as $$
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
        where request_id=p_request_id for update;
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
            on conflict (request_id) do update
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
$$;
revoke all on function public.portfolio_advisory_service_owner_action_v2(uuid,text,text) from public,anon;
grant execute on function public.portfolio_advisory_service_owner_action_v2(uuid,text,text) to authenticated;

-- Legacy request-owner controls call the same single-step grant/revoke contract.
create or replace function public.portfolio_advisory_scorecard_owner_action_v1(
    p_request_id uuid,p_action text)
returns jsonb language sql security invoker set search_path = ''
as $$ select public.portfolio_advisory_service_owner_action_v2(p_request_id,'scorecard',p_action) $$;
create or replace function public.portfolio_advisory_rollout_owner_action_v1(
    p_request_id uuid,p_action text)
returns jsonb language sql security invoker set search_path = ''
as $$ select public.portfolio_advisory_service_owner_action_v2(p_request_id,'rollout',p_action) $$;
revoke all on function public.portfolio_advisory_scorecard_owner_action_v1(uuid,text) from public,anon;
revoke all on function public.portfolio_advisory_rollout_owner_action_v1(uuid,text) from public,anon;
grant execute on function public.portfolio_advisory_scorecard_owner_action_v1(uuid,text) to authenticated;
grant execute on function public.portfolio_advisory_rollout_owner_action_v1(uuid,text) to authenticated;

-- Claim/ack are owner-gated. Browser never sees provider API credentials.
create or replace function public.portfolio_advisory_email_claim_v1(p_id uuid)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_owner uuid:=auth.uid(); v_row public.portfolio_advisory_approval_notifications%rowtype;
begin
 if v_owner is null or not exists(
  select 1 from auth.users where id=v_owner and email_confirmed_at is not null
  and lower(email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Owner only' using errcode='42501'; end if;
 select * into v_row from public.portfolio_advisory_approval_notifications
 where id=p_id for update;
 if not found then raise exception 'Notification not found' using errcode='22023'; end if;
 if v_row.state='sent' then
   return jsonb_build_object('id',p_id,'state','sent');
 end if;
 if v_row.state='sending' and
    v_row.last_attempt_at>now()-interval '10 minutes' then
   return jsonb_build_object('id',p_id,'state','sending');
 end if;
 if v_row.attempts>=25 then
   raise exception 'Notification retry limit reached' using errcode='22023'; end if;
 update public.portfolio_advisory_approval_notifications
 set state='sending',last_attempt_at=now(),attempts=attempts+1,
     error_category='',updated_at=now()
 where id=p_id;
 return jsonb_build_object('id',p_id,'state','sending','claimed',true,
  'service_key',v_row.service_key,'to',v_row.recipient_email);
end;
$$;
create or replace function public.portfolio_advisory_email_finish_v1(
 p_id uuid,p_sent boolean,p_provider_message_id text default '',
 p_error_category text default '')
returns jsonb language plpgsql security definer set search_path=''
as $$
declare v_owner uuid:=auth.uid(); v_state text;
begin
 if v_owner is null or not exists(
  select 1 from auth.users where id=v_owner and email_confirmed_at is not null
  and lower(email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Owner only' using errcode='42501'; end if;
 if length(coalesce(p_provider_message_id,''))>180 or
    length(coalesce(p_error_category,''))>160 then
   raise exception 'Invalid provider result' using errcode='22023'; end if;
 update public.portfolio_advisory_approval_notifications
 set state=case when p_sent then 'sent' else 'failed' end,
     provider_message_id=case when p_sent then coalesce(p_provider_message_id,'') else '' end,
     error_category=case when p_sent then '' else coalesce(p_error_category,'delivery_error') end,
     sent_at=case when p_sent then now() else sent_at end, updated_at=now()
 where id=p_id and state='sending' returning state into v_state;
 if v_state is null then raise exception 'Notification is not claimed' using errcode='22023'; end if;
 return jsonb_build_object('id',p_id,'state',v_state);
end;
$$;
revoke all on function public.portfolio_advisory_email_claim_v1(uuid) from public,anon;
revoke all on function public.portfolio_advisory_email_finish_v1(uuid,boolean,text,text) from public,anon;
grant execute on function public.portfolio_advisory_email_claim_v1(uuid) to authenticated;
grant execute on function public.portfolio_advisory_email_finish_v1(uuid,boolean,text,text) to authenticated;

-- Client visibility follows owner-approved individual entitlement, not an unrelated CRM stage.
drop policy if exists "Scorecard client reads only individually approved engagement" on public.portfolio_advisory_scorecards;
create policy "Scorecard client reads only individually approved engagement"
on public.portfolio_advisory_scorecards for select to authenticated
using (
 user_id=(select auth.uid()) and status='active'
 and (select public.portfolio_advisory_password_session_v1())
 and exists(select 1 from public.portfolio_advisory_requests r
            where r.id=portfolio_advisory_scorecards.request_id
            and r.user_id=portfolio_advisory_scorecards.user_id
            and r.status not in ('closed','declined'))
 and exists(select 1 from public.portfolio_advisory_profiles p
            where p.user_id=portfolio_advisory_scorecards.user_id
            and p.account_status='active')
);
drop policy if exists "Member reads their individually approved rollout access" on public.portfolio_advisory_rollout_access;
create policy "Member reads their individually approved rollout access"
on public.portfolio_advisory_rollout_access for select to authenticated
using (
 user_id=(select auth.uid()) and status='active'
 and (select public.portfolio_advisory_password_session_v1())
 and exists(select 1 from public.portfolio_advisory_profiles p
            where p.user_id=portfolio_advisory_rollout_access.user_id and p.account_status='active')
 and exists(select 1 from public.portfolio_advisory_requests r
            where r.id=portfolio_advisory_rollout_access.request_id
            and r.user_id=portfolio_advisory_rollout_access.user_id
            and r.status not in ('closed','declined'))
);
drop policy if exists "Member reads own approved rollout assessments" on public.portfolio_advisory_rollout_assessments;
create policy "Member reads own approved rollout assessments"
on public.portfolio_advisory_rollout_assessments for select to authenticated
using (
 user_id=(select auth.uid()) and
 (select public.portfolio_advisory_password_session_v1())
 and exists(select 1 from public.portfolio_advisory_rollout_access a
   join public.portfolio_advisory_requests r on r.id=a.request_id
   join public.portfolio_advisory_profiles p on p.user_id=a.user_id
   where a.id=portfolio_advisory_rollout_assessments.access_id
    and a.user_id=portfolio_advisory_rollout_assessments.user_id
    and a.status='active' and p.account_status='active'
    and r.status not in ('closed','declined'))
);

-- Preserve function contract and replace only the over-restrictive request stage check.
CREATE OR REPLACE FUNCTION public.portfolio_advisory_feedback_submit_v1(p_service_key text, p_stage text, p_request_id uuid, p_scorecard_id uuid, p_rating smallint, p_comment text DEFAULT ''::text, p_followup_answer text DEFAULT ''::text, p_contact_ok boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid; v_id uuid; v_key text;
begin
 v_uid:=auth.uid();
 if v_uid is null or not public.portfolio_advisory_password_session_v1()
 or not exists(
  select 1 from public.portfolio_advisory_profiles p
  where p.user_id=v_uid and p.account_status='active'
 ) then
  raise exception 'Active password-verified Advisory account required' using errcode='42501';
 end if;
 if p_rating is null or p_rating not between 1 and 5
 or char_length(coalesce(p_comment,''))>800
 or char_length(coalesce(p_followup_answer,''))>800 then
  raise exception 'Invalid feedback rating or text length';
 end if;
 if p_service_key='executive_advisory' and p_stage='registration_access'
   and p_request_id is null and p_scorecard_id is null then
   v_key:='registration';
 elsif p_service_key='executive_advisory' and p_stage='personal_advisory'
   and p_request_id is not null and p_scorecard_id is null
   and exists(
     select 1 from public.portfolio_advisory_requests r
     where r.id=p_request_id and r.user_id=v_uid and r.status in ('active','completed')
       and exists(select 1 from public.portfolio_advisory_messages m
                  where m.request_id=r.id and m.sender='advisor')
   ) then
   v_key:=p_request_id::text;
 elsif p_service_key='ai_portfolio_prioritization_scorecard'
   and p_stage in ('assessment_completion','executive_recommendation','report_download')
   and p_request_id is not null and p_scorecard_id is not null
   and exists (
     select 1 from public.portfolio_advisory_scorecards s
     join public.portfolio_advisory_requests r on r.id=s.request_id
     where s.id=p_scorecard_id and s.request_id=p_request_id and s.user_id=v_uid
       and s.status='active' and r.user_id=v_uid and r.status not in ('closed','declined')
   ) then
   v_key:=p_scorecard_id::text;
 else
   raise exception 'Feedback stage is not available for this account or service' using errcode='42501';
 end if;

 insert into public.portfolio_advisory_interaction_feedback(
   user_id,service_key,stage,request_id,scorecard_id,rating,comment,followup_answer,contact_ok
 ) values(
   v_uid,p_service_key,p_stage,p_request_id,p_scorecard_id,p_rating,
   coalesce(p_comment,''),coalesce(p_followup_answer,''),coalesce(p_contact_ok,false)
 )
 on conflict(user_id,service_key,stage,scope_key) do nothing
 returning id into v_id;
 if v_id is null then
   select f.id into v_id from public.portfolio_advisory_interaction_feedback f
   where f.user_id=v_uid and f.service_key=p_service_key and f.stage=p_stage and f.scope_key=v_key;
   return jsonb_build_object('status','already_recorded','id',v_id);
 end if;
 return jsonb_build_object('status','recorded','id',v_id);
end $function$
;

-- Preserve function contract and replace only the over-restrictive request stage check.
CREATE OR REPLACE FUNCTION public.portfolio_advisory_rollout_assess_v1(p_request_id uuid, p_answers jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
 and r.status not in ('closed','declined') and p.account_status='active';
 if v_access_id is null then raise exception 'No active approved rollout entitlement' using errcode='42501'; end if;
 if (select count(*) from public.portfolio_advisory_rollout_assessments x
     where x.user_id=v_uid and x.created_at>now()-interval '24 hours')>=20 then
   raise exception 'Assessment submission limit reached'; end if;
 insert into public.portfolio_advisory_rollout_assessments(access_id,request_id,user_id,answers)
 values(v_access_id,p_request_id,v_uid,p_answers) returning id into v_id;
 insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action,assessment_id)
 values(v_access_id,v_uid,'assess',v_id);
 return jsonb_build_object('id',v_id,'request_id',p_request_id);
end $function$
;

-- Preserve function contract and replace only the over-restrictive request stage check.
CREATE OR REPLACE FUNCTION public.portfolio_advisory_rollout_feedback_submit_v1(p_request_id uuid, p_stage text, p_rating smallint, p_comment text DEFAULT ''::text, p_followup_answer text DEFAULT ''::text, p_contact_ok boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid; v_id uuid;
begin
 v_uid:=auth.uid();
 if v_uid is null or not public.portfolio_advisory_password_session_v1()
 or not exists(select 1 from public.portfolio_advisory_profiles p
   where p.user_id=v_uid and p.account_status='active') then
  raise exception 'Verified active Advisory account required' using errcode='42501';
 end if;
 if p_stage not in ('assessment_completion','executive_recommendation','report_download')
 or p_rating is null or p_rating not between 1 and 5
 or char_length(coalesce(p_comment,''))>800
 or char_length(coalesce(p_followup_answer,''))>800
 or not exists(
  select 1 from public.portfolio_advisory_rollout_access a
  join public.portfolio_advisory_requests r on r.id=a.request_id
  where a.request_id=p_request_id and a.user_id=v_uid and a.status='active'
  and r.status not in ('closed','declined')
 ) then
  raise exception 'Unapproved feedback submission' using errcode='42501';
 end if;
 insert into public.portfolio_advisory_interaction_feedback(
  user_id,service_key,stage,request_id,scorecard_id,rating,comment,followup_answer,contact_ok
 ) values(
  v_uid,'enterprise_ai_rollout_readiness',p_stage,p_request_id,null,p_rating,
  coalesce(p_comment,''),coalesce(p_followup_answer,''),coalesce(p_contact_ok,false)
 ) on conflict(user_id,service_key,stage,scope_key) do nothing
 returning id into v_id;
 if v_id is null then
  select f.id into v_id from public.portfolio_advisory_interaction_feedback f
  where f.user_id=v_uid and f.service_key='enterprise_ai_rollout_readiness'
  and f.stage=p_stage and f.scope_key=p_request_id::text;
  return jsonb_build_object('status','already_recorded','id',v_id);
 end if;
 return jsonb_build_object('status','recorded','id',v_id);
end $function$
;

-- Preserve function contract and replace only the over-restrictive request stage check.
CREATE OR REPLACE FUNCTION public.portfolio_advisory_scorecard_save_v1(p_id uuid, p_payload jsonb, p_expected_revision integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
             and r.status not in ('closed','declined'))
 and exists (select 1 from public.portfolio_advisory_profiles p
             where p.user_id=v_uid and p.account_status='active')
 returning s.revision,s.request_id into v_new_revision,v_request_id;
 if v_new_revision is null then
  raise exception 'Access revoked, session invalid, or this workspace has changed. Reload before saving.' using errcode='42501';
 end if;
 insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action,revision)
 values(p_id,v_uid,'save',v_new_revision);
 return jsonb_build_object('id',p_id,'revision',v_new_revision,'request_id',v_request_id);
end $function$
;
