drop policy if exists "Verified Advisory owner reviews analysis requests"
 on public.portfolio_advisory_scorecard_analysis_requests;
create policy "Verified Advisory owner reviews analysis requests"
 on public.portfolio_advisory_scorecard_analysis_requests
 for select to authenticated
 using (
   lower(coalesce((select auth.jwt()->>'email'),''))='jair.ribeiro@outlook.it'
 );
