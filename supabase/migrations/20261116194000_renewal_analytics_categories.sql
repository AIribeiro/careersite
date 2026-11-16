-- Additive privacy-limited recommendation category for owner reporting.
alter table public.portfolio_advisory_renewal_events
 add column if not exists recommendation text;
alter table public.portfolio_advisory_renewal_events
 add constraint renewal_event_recommendation_check
 check (recommendation is null or recommendation in ('RENEW','REPLACE','TEST','STOP','HOLD','COMPLETE INPUTS'));
comment on column public.portfolio_advisory_renewal_events.recommendation is
 'Model action category only; no private financial amounts, project names or scenario contents.';
