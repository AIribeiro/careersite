-- Supabase authenticated roles cannot directly SELECT auth.users inside a standard RLS policy.
-- Signed JWT email is read-only; privileged write RPC separately checks verified auth.users.
drop policy if exists "Owner reads service availability audit"
 on public.portfolio_advisory_service_visibility_audit;
create policy "Owner reads service availability audit"
 on public.portfolio_advisory_service_visibility_audit
 for select to authenticated
 using (
  auth.uid() is not null
  and lower(coalesce(auth.jwt() ->> 'email',''))='jair.ribeiro@outlook.it'
 );
