-- Specialized approval requests inherit their own availability, not personal-advisory status.
alter table public.portfolio_advisory_requests
 add constraint portfolio_advisory_request_source_title_guard
 check (
   source_service='requests'
   or (source_service='rollout'
       and title='Enterprise AI Rollout Readiness Advisor — access request')
   or (source_service='scorecard'
       and title='AI Portfolio Prioritization Scorecard — access request')
 );
grant insert(source_service) on public.portfolio_advisory_requests to authenticated;
