-- Advisory service requests and two-way exchanges: membership != engagement.
create table if not exists public.portfolio_advisory_requests (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 title text not null check(length(btrim(title)) between 8 and 160),
 desired_outcome text not null check(length(btrim(desired_outcome)) between 20 and 2000),
 business_context text not null default '' check(length(business_context)<=3000),
 decision_timing text not null default 'Exploratory' check(decision_timing in ('Within 30 days','1–3 months','3–6 months','Exploratory')),
 contact_preference text not null default 'Email' check(contact_preference in ('Email','Video call')),
 status text not null default 'submitted' check(status in ('submitted','reviewing','awaiting_client','discovery','proposal','active','completed','closed','declined')),
 next_step text not null default '' check(length(next_step)<=1000),
 follow_up_on date,
 last_client_at timestamptz not null default now(),
 last_owner_at timestamptz,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create unique index if not exists advisory_one_open_request_per_member on public.portfolio_advisory_requests(user_id)
 where status in ('submitted','reviewing','awaiting_client','discovery','proposal','active');
create index if not exists advisory_requests_queue_idx on public.portfolio_advisory_requests(status,updated_at desc);
create table if not exists public.portfolio_advisory_messages (
 id bigint generated always as identity primary key,
 request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 sender text not null check(sender in ('client','advisor')),
 body text not null check(length(btrim(body)) between 2 and 4000),
 created_at timestamptz not null default now()
);
create index if not exists advisory_messages_thread_idx on public.portfolio_advisory_messages(request_id,created_at,id);
create table if not exists public.portfolio_advisory_request_audit (
 id bigint generated always as identity primary key,
 request_id uuid not null references public.portfolio_advisory_requests(id) on delete cascade,
 actor_id uuid references auth.users(id),
 action text not null, old_status text, new_status text, created_at timestamptz not null default now()
);
alter table public.portfolio_advisory_requests enable row level security;
alter table public.portfolio_advisory_messages enable row level security;
alter table public.portfolio_advisory_request_audit enable row level security;
revoke all on public.portfolio_advisory_requests,public.portfolio_advisory_messages,public.portfolio_advisory_request_audit from public,anon,authenticated;
grant select on public.portfolio_advisory_requests,public.portfolio_advisory_messages,public.portfolio_advisory_request_audit to authenticated;
grant insert(user_id,title,desired_outcome,business_context,decision_timing,contact_preference) on public.portfolio_advisory_requests to authenticated;
grant insert(request_id,user_id,sender,body) on public.portfolio_advisory_messages to authenticated;
grant usage on sequence public.portfolio_advisory_messages_id_seq to authenticated;
create policy "Advisory requests member and owner read" on public.portfolio_advisory_requests for select to authenticated
 using (user_id=(select auth.uid()) or lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it');
create policy "Active advisory member submits request" on public.portfolio_advisory_requests for insert to authenticated
 with check (user_id=(select auth.uid()) and status='submitted'
 and (select public.portfolio_advisory_password_session_v1())
 and exists(select 1 from public.portfolio_advisory_profiles p where p.user_id=(select auth.uid()) and p.account_status='active'));
create policy "Advisory messages member and owner read" on public.portfolio_advisory_messages for select to authenticated
 using (user_id=(select auth.uid()) or lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it');
create policy "Active member replies own open request" on public.portfolio_advisory_messages for insert to authenticated
 with check (user_id=(select auth.uid()) and sender='client'
 and (select public.portfolio_advisory_password_session_v1())
 and exists(select 1 from public.portfolio_advisory_requests r
 join public.portfolio_advisory_profiles p on p.user_id=r.user_id
 where r.id=request_id and r.user_id=(select auth.uid())
   and p.account_status='active' and r.status not in ('completed','closed','declined')));
create policy "Advisory owner audit read" on public.portfolio_advisory_request_audit for select to authenticated
 using (lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it');
create or replace function public.portfolio_advisory_message_stamp_v1()
returns trigger language plpgsql security definer set search_path=''
as $$
declare before_status text;
begin
 if new.sender='client' then
   select status into before_status from public.portfolio_advisory_requests where id=new.request_id;
   update public.portfolio_advisory_requests
   set last_client_at=now(),updated_at=now(),status=case when status='awaiting_client' then 'reviewing' else status end
   where id=new.request_id;
   if before_status='awaiting_client' then
     insert into public.portfolio_advisory_request_audit(request_id,actor_id,action,old_status,new_status)
     values(new.request_id,new.user_id,'client_replied','awaiting_client','reviewing');
   end if;
 else
   update public.portfolio_advisory_requests set last_owner_at=now(),updated_at=now() where id=new.request_id;
 end if;
 return new;
end;
$$;
revoke all on function public.portfolio_advisory_message_stamp_v1() from public,anon,authenticated;
drop trigger if exists trg_advisory_message_stamp on public.portfolio_advisory_messages;
create trigger trg_advisory_message_stamp after insert on public.portfolio_advisory_messages
 for each row execute function public.portfolio_advisory_message_stamp_v1();
create or replace function public.portfolio_advisory_request_owner_action_v1(
 p_request_id uuid,p_action text,p_message text default null,p_next_step text default null,p_follow_up date default null
) returns jsonb
language plpgsql security definer set search_path=''
as $$
declare
 v_actor uuid:=auth.uid();
 v_owner_email text;
 v_request public.portfolio_advisory_requests%rowtype;
 v_target text;
 v_next text;
begin
 if v_actor is null then raise exception 'Unauthorized'; end if;
 select lower(email) into v_owner_email from auth.users where id=v_actor and email_confirmed_at is not null;
 if v_owner_email is distinct from 'jair.ribeiro@outlook.it' then raise exception 'Owner only'; end if;
 select * into v_request from public.portfolio_advisory_requests where id=p_request_id for update;
 if not found then raise exception 'Request not found'; end if;
 if p_action not in ('review','ask_client','invite_discovery','proposal','start','complete','close','decline','reply','plan') then raise exception 'Unsupported action'; end if;
 if length(coalesce(p_message,''))>4000 or length(coalesce(p_next_step,''))>1000 then raise exception 'Message exceeds limit'; end if;
 if p_action in ('ask_client','invite_discovery','proposal','start','complete','decline')
   and length(btrim(coalesce(p_message,'')))<10 then raise exception 'Client-facing message is required'; end if;
 if v_request.status in ('closed','declined') and p_action not in ('plan', 'reply') then raise exception 'Request closed'; end if;
 if p_action='start' and v_request.status not in ('discovery','proposal') then raise exception 'Complete discovery or proposal before starting'; end if;
 if p_action='complete' and v_request.status<>'active' then raise exception 'Only active engagements can complete'; end if;
 v_target:=case p_action
   when 'review' then 'reviewing'
   when 'ask_client' then 'awaiting_client'
   when 'invite_discovery' then 'discovery'
   when 'proposal' then 'proposal'
   when 'start' then 'active'
   when 'complete' then 'completed'
   when 'close' then 'closed'
   when 'decline' then 'declined'
   else v_request.status end;
 v_next:=case
   when p_next_step is not null then p_next_step
   when p_action='review' then 'Your request is being reviewed.'
   when p_action='ask_client' then 'Please respond to the question below.'
   when p_action='invite_discovery' then 'Review the proposed conversation and reply to confirm.'
   when p_action='proposal' then 'Review the proposed scope and respond.'
   when p_action='start' then 'Follow the agreed workplan and milestones.'
   when p_action='complete' then 'Review the final summary and any follow-up.'
   when p_action in ('close','decline') then 'No further action is required.'
   else v_request.next_step end;
 update public.portfolio_advisory_requests set status=v_target,next_step=v_next,
  follow_up_on=case when p_action='plan' then p_follow_up else follow_up_on end,
  last_owner_at=case when p_action<>'plan' then now() else last_owner_at end,
  updated_at=now() where id=p_request_id;
 if p_action<>'plan' and length(btrim(coalesce(p_message,'')))>=2 then
  insert into public.portfolio_advisory_messages(request_id,user_id,sender,body)
  values(p_request_id,v_request.user_id,'advisor',p_message);
 end if;
 insert into public.portfolio_advisory_request_audit(request_id,actor_id,action,old_status,new_status)
 values(p_request_id,v_actor,p_action,v_request.status,v_target);
 return jsonb_build_object('id',p_request_id,'status',v_target,'action',p_action);
end;
$$;
revoke all on function public.portfolio_advisory_request_owner_action_v1(uuid,text,text,text,date) from public,anon;
grant execute on function public.portfolio_advisory_request_owner_action_v1(uuid,text,text,text,date) to authenticated;
