
drop index if exists public.advisory_one_open_request_per_member;
create unique index advisory_one_open_request_per_member
 on public.portfolio_advisory_requests(user_id)
 where status in ('submitted','reviewing','awaiting_client','discovery','proposal','active','completed');
drop policy if exists "Active member replies own open request" on public.portfolio_advisory_messages;
create policy "Active member replies own open request"
 on public.portfolio_advisory_messages for insert to authenticated
 with check (
 user_id=(select auth.uid()) and sender='client'
 and (select public.portfolio_advisory_password_session_v1())
 and exists(
  select 1 from public.portfolio_advisory_requests r
  join public.portfolio_advisory_profiles p on p.user_id=r.user_id
  where r.id=request_id and r.user_id=(select auth.uid())
    and p.account_status='active' and r.status not in ('closed','declined')
 )
);
