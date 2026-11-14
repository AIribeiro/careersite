-- Keep advisor-internal satisfaction notes out of member-readable columns.
-- Owner retrieves full rows through a tightly checked authenticated RPC.
revoke all on public.portfolio_advisory_interaction_feedback from authenticated;
grant select (
 id,user_id,service_key,stage,request_id,scorecard_id,
 rating,comment,followup_answer,contact_ok,created_at
) on public.portfolio_advisory_interaction_feedback to authenticated;

create or replace function public.portfolio_advisory_feedback_owner_list_v1(
 p_limit integer default 1000
) returns jsonb language plpgsql security definer set search_path='' as $f$
declare v_uid uuid; v_result jsonb;
begin
 v_uid:=auth.uid();
 if v_uid is null or not exists(
   select 1 from auth.users u
   where u.id=v_uid and lower(u.email)='jair.ribeiro@outlook.it'
 ) then raise exception 'Not authorized' using errcode='42501'; end if;
 select coalesce(jsonb_agg(to_jsonb(x)), '[]'::jsonb) into v_result
 from (
  select id,user_id,service_key,stage,request_id,scorecard_id,rating,
         comment,followup_answer,contact_ok,owner_status,owner_note,
         reviewed_at,created_at
  from public.portfolio_advisory_interaction_feedback
  order by created_at desc limit least(greatest(coalesce(p_limit,1000),1),1000)
 ) x;
 return v_result;
end $f$;
revoke all on function public.portfolio_advisory_feedback_owner_list_v1(integer) from public,anon;
grant execute on function public.portfolio_advisory_feedback_owner_list_v1(integer) to authenticated;
