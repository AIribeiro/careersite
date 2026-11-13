-- Applied to rnqweoxtynelfirffmlr on 2026-11-13 (migration 20261113112423).
-- Advisory activation requires a verified email plus password authentication.
-- Reader OTP sessions must not read, create or update Advisory profiles.
create or replace function public.portfolio_advisory_password_session_v1()
returns boolean language sql stable security invoker set search_path = ''
as $function$
  select coalesce(
    (select exists(
      select 1 from jsonb_array_elements(
        case when jsonb_typeof((select auth.jwt()) -> 'amr') = 'array'
          then (select auth.jwt()) -> 'amr' else '[]'::jsonb end
      ) as method
      where method ->> 'method' = 'password'
    )), false
  )
$function$;
revoke all on function public.portfolio_advisory_password_session_v1() from public,anon;
grant execute on function public.portfolio_advisory_password_session_v1() to authenticated;
drop policy if exists "Advisory member can view own access" on public.portfolio_advisory_profiles;
create policy "Advisory member can view own access" on public.portfolio_advisory_profiles
 for select to authenticated
 using ((select auth.uid()) = user_id and (select public.portfolio_advisory_password_session_v1()));
drop policy if exists "Verified member can register own advisory access" on public.portfolio_advisory_profiles;
create policy "Verified member can register own advisory access" on public.portfolio_advisory_profiles
 for insert to authenticated
 with check (
  (select auth.uid()) = user_id
  and lower(email) = lower((select auth.jwt() ->> 'email'))
  and ((select auth.jwt() ->> 'is_anonymous') is distinct from 'true')
  and (select public.portfolio_advisory_password_session_v1())
  and account_status = 'active' and engagement_status = 'inquiry'
 );
drop policy if exists "Advisory member can update own context" on public.portfolio_advisory_profiles;
create policy "Advisory member can update own context" on public.portfolio_advisory_profiles
 for update to authenticated
 using ((select auth.uid()) = user_id and (select public.portfolio_advisory_password_session_v1()))
 with check (
  (select auth.uid()) = user_id
  and lower(email) = lower((select auth.jwt() ->> 'email'))
  and (select public.portfolio_advisory_password_session_v1())
 );
