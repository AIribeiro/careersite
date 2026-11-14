-- Optional, stage-specific feedback for executive advisory and approved Scorecard clients.
-- The user's assessment, recommendation, and export are NEVER gated by feedback.
create table if not exists public.portfolio_advisory_interaction_feedback (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 service_key text not null check(service_key in ('executive_advisory','ai_portfolio_prioritization_scorecard')),
 stage text not null check(stage in ('registration_access','assessment_completion','executive_recommendation','report_download','personal_advisory')),
 request_id uuid references public.portfolio_advisory_requests(id) on delete cascade,
 scorecard_id uuid references public.portfolio_advisory_scorecards(id) on delete cascade,
 scope_key text generated always as (coalesce(scorecard_id::text,request_id::text,'registration')) stored,
 rating smallint not null check(rating between 1 and 5),
 comment text not null default '' check(char_length(comment)<=800),
 followup_answer text not null default '' check(char_length(followup_answer)<=800),
 contact_ok boolean not null default false,
 owner_status text not null default 'new' check(owner_status in ('new','reviewed','follow_up','resolved')),
 owner_note text not null default '' check(char_length(owner_note)<=1200),
 reviewed_at timestamptz,
 created_at timestamptz not null default now(),
 constraint advisory_feedback_stage_scope check (
  (service_key='executive_advisory' and stage='registration_access' and request_id is null and scorecard_id is null)
  or (service_key='executive_advisory' and stage='personal_advisory' and request_id is not null and scorecard_id is null)
  or (service_key='ai_portfolio_prioritization_scorecard' and stage in ('assessment_completion','executive_recommendation','report_download') and request_id is not null and scorecard_id is not null)
 ),
 unique(user_id,service_key,stage,scope_key)
);
create index if not exists advisory_feedback_service_stage_created_idx on public.portfolio_advisory_interaction_feedback(service_key,stage,created_at desc);
create index if not exists advisory_feedback_attention_idx on public.portfolio_advisory_interaction_feedback(owner_status,rating,created_at desc);

create table if not exists public.portfolio_advisory_interaction_feedback_audit (
 id bigint generated always as identity primary key,
 feedback_id uuid not null references public.portfolio_advisory_interaction_feedback(id) on delete cascade,
 actor_id uuid not null references auth.users(id),
 old_status text not null,
 new_status text not null,
 note text not null default '',
 created_at timestamptz not null default now()
);

alter table public.portfolio_advisory_interaction_feedback enable row level security;
alter table public.portfolio_advisory_interaction_feedback_audit enable row level security;
revoke all on public.portfolio_advisory_interaction_feedback from public,anon,authenticated;
revoke all on public.portfolio_advisory_interaction_feedback_audit from public,anon,authenticated;
grant select on public.portfolio_advisory_interaction_feedback to authenticated;
grant select on public.portfolio_advisory_interaction_feedback_audit to authenticated;

create policy "Advisory feedback: client sees own, owner oversees" on public.portfolio_advisory_interaction_feedback
 for select to authenticated
 using (
   user_id=(select auth.uid())
   or lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it'
 );
create policy "Advisory feedback audit: owner reads" on public.portfolio_advisory_interaction_feedback_audit
 for select to authenticated
 using (lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it');

create or replace function public.portfolio_advisory_feedback_submit_v1(
 p_service_key text, p_stage text, p_request_id uuid, p_scorecard_id uuid,
 p_rating smallint, p_comment text default '', p_followup_answer text default '',
 p_contact_ok boolean default false
) returns jsonb language plpgsql security definer set search_path='' as $function$
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
       and s.status='active' and r.user_id=v_uid and r.status in ('active','completed')
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
end $function$;
revoke all on function public.portfolio_advisory_feedback_submit_v1(text,text,uuid,uuid,smallint,text,text,boolean) from public,anon;
grant execute on function public.portfolio_advisory_feedback_submit_v1(text,text,uuid,uuid,smallint,text,text,boolean) to authenticated;

create or replace function public.portfolio_advisory_feedback_owner_review_v1(
 p_id uuid, p_status text, p_note text default ''
) returns jsonb language plpgsql security definer set search_path='' as $function$
declare v_owner uuid; v_old text; v_note text;
begin
 v_owner:=auth.uid();
 if v_owner is null or not exists(
  select 1 from auth.users u where u.id=v_owner and lower(u.email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Not authorized' using errcode='42501'; end if;
 if p_status not in ('reviewed','follow_up','resolved') or char_length(coalesce(p_note,''))>1200 then
  raise exception 'Invalid feedback review';
 end if;
 select owner_status into v_old from public.portfolio_advisory_interaction_feedback
 where id=p_id for update;
 if v_old is null then raise exception 'Feedback not found'; end if;
 v_note:=coalesce(p_note,'');
 update public.portfolio_advisory_interaction_feedback
 set owner_status=p_status, owner_note=v_note, reviewed_at=now()
 where id=p_id;
 insert into public.portfolio_advisory_interaction_feedback_audit(
  feedback_id,actor_id,old_status,new_status,note
 ) values(p_id,v_owner,v_old,p_status,v_note);
 return jsonb_build_object('status',p_status,'id',p_id);
end $function$;
revoke all on function public.portfolio_advisory_feedback_owner_review_v1(uuid,text,text) from public,anon;
grant execute on function public.portfolio_advisory_feedback_owner_review_v1(uuid,text,text) to authenticated;
