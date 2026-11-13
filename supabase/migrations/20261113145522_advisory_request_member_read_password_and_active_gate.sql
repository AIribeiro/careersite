
drop policy if exists "Advisory requests member and owner read" on public.portfolio_advisory_requests;
create policy "Advisory requests member and owner read" on public.portfolio_advisory_requests
for select to authenticated using (
  lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it'
  or (user_id=(select auth.uid())
      and (select public.portfolio_advisory_password_session_v1())
      and exists(select 1 from public.portfolio_advisory_profiles p
                 where p.user_id=(select auth.uid()) and p.account_status='active'))
);
drop policy if exists "Advisory messages member and owner read" on public.portfolio_advisory_messages;
create policy "Advisory messages member and owner read" on public.portfolio_advisory_messages
for select to authenticated using (
  lower((select auth.jwt()->>'email'))='jair.ribeiro@outlook.it'
  or (user_id=(select auth.uid())
      and (select public.portfolio_advisory_password_session_v1())
      and exists(select 1 from public.portfolio_advisory_profiles p
                 where p.user_id=(select auth.uid()) and p.account_status='active'))
);
