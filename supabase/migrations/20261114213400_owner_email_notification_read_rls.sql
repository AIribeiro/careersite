-- Authorization policies execute as authenticated clients and cannot read auth.users.
-- Server-side owner RPCs continue to validate the verified identity in auth.users.
drop policy if exists "Owner sees advisory approval notifications"
on public.portfolio_advisory_approval_notifications;
create policy "Owner sees advisory approval notifications"
on public.portfolio_advisory_approval_notifications
for select to authenticated
using (
    (select auth.uid()) is not null
    and lower(coalesce((select auth.jwt()->>'email'),'')) = 'jair.ribeiro@outlook.it'
);