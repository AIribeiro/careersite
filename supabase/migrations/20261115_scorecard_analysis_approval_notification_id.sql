CREATE OR REPLACE FUNCTION public.portfolio_advisory_scorecard_analysis_owner_v1(p_analysis_id uuid, p_action text, p_note text DEFAULT ''::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 v_owner uuid:=auth.uid();
 v_req public.portfolio_advisory_scorecard_analysis_requests%rowtype;
 v_workspace uuid;
 v_email text;
 v_notification_id uuid;
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
     ) values(v_req.request_id,v_req.user_id,'scorecard',v_email)
     returning id into v_notification_id;
   end if;
   return jsonb_build_object('id',p_analysis_id,'workspace_id',v_workspace,
      'status','approved','unchanged',false,'notification_id',v_notification_id);
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
end $function$
;
