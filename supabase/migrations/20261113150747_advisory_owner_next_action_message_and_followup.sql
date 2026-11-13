CREATE OR REPLACE FUNCTION public.portfolio_advisory_request_owner_action_v1(p_request_id uuid, p_action text, p_message text DEFAULT NULL::text, p_next_step text DEFAULT NULL::text, p_follow_up date DEFAULT NULL::date)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
 if p_action='reply' and length(btrim(coalesce(p_message,'')))<2 then raise exception 'Reply text is required'; end if;
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
  follow_up_on=case when p_action='plan' or p_follow_up is not null then p_follow_up else follow_up_on end,
  last_owner_at=case when p_action<>'plan' then now() else last_owner_at end,
  updated_at=now() where id=p_request_id;
 if length(btrim(coalesce(p_message,'')))>=2 then
  insert into public.portfolio_advisory_messages(request_id,user_id,sender,body)
  values(p_request_id,v_request.user_id,'advisor',p_message);
 end if;
 insert into public.portfolio_advisory_request_audit(request_id,actor_id,action,old_status,new_status)
 values(p_request_id,v_actor,p_action,v_request.status,v_target);
 return jsonb_build_object('id',p_request_id,'status',v_target,'action',p_action);
end;
$function$
