-- Read-only client activity timeline, restricted to the client's active
-- approved Scorecard and verified password-authenticated Advisory session.
-- The existing owner policy remains unchanged.
create policy "Scorecard member reads own approved audit"
 on public.portfolio_advisory_scorecard_audit
 for select to authenticated
 using (
   (select public.portfolio_advisory_password_session_v1())
   and exists (
     select 1
     from public.portfolio_advisory_scorecards s
     join public.portfolio_advisory_requests r on r.id=s.request_id
     join public.portfolio_advisory_profiles p on p.user_id=s.user_id
     where s.id=portfolio_advisory_scorecard_audit.scorecard_id
       and s.user_id=(select auth.uid())
       and s.status='active'
       and r.user_id=s.user_id
       and r.status not in ('closed','declined')
       and p.account_status='active'
   )
 );
