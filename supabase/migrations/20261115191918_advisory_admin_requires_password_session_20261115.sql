-- Admin visibility and new-start bypass require a password-authenticated JWT,
-- never email confirmation alone or mutable profile metadata.
create or replace function public.portfolio_advisory_is_admin_v1()
returns boolean language sql stable security definer set search_path=''
as $$
 select auth.uid() is not null
 and public.portfolio_advisory_password_session_v1()
 and exists (
  select 1 from auth.users u
  join public.portfolio_advisory_user_roles r on r.user_id=u.id
  where u.id=auth.uid() and u.email_confirmed_at is not null and r.role='admin'
 );
$$;
revoke all on function public.portfolio_advisory_is_admin_v1() from public,anon,authenticated;
grant execute on function public.portfolio_advisory_is_admin_v1() to authenticated;
