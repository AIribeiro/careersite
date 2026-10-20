-- Applied to AIribeiro's DB on 2026-10-20.
-- Add-only shadow history: no change to primary hiring forecast snapshots.
create table if not exists public.careersite_hiring_market_shadow_history (
    id bigint generated always as identity primary key,
    owner_user_id uuid not null default auth.uid(),
    forecast_day date not null,
    baseline_model_version text not null,
    shadow_model_version text not null default 'market-shadow-v1-context-only',
    baseline_offer_central date,
    baseline_start_central date,
    shadow_offer_central date,
    shadow_start_central date,
    outlook text not null,
    scoring_status text not null default 'context_only',
    source_signature text not null,
    evidence jsonb not null,
    created_at timestamptz not null default now(),
    constraint careersite_shadow_status_check check (scoring_status='context_only'),
    constraint careersite_shadow_version_check check (shadow_model_version='market-shadow-v1-context-only'),
    constraint careersite_shadow_unique unique(
        owner_user_id, forecast_day, baseline_model_version, source_signature)
);
comment on table public.careersite_hiring_market_shadow_history is
'Owner-only, append-only contextual hiring market shadow evaluations. No scoring weights, no probability adjustments; historical hiring forecasts are unchanged.';
create index if not exists careersite_shadow_history_owner_time
on public.careersite_hiring_market_shadow_history
(owner_user_id, forecast_day desc, id desc);
alter table public.careersite_hiring_market_shadow_history enable row level security;
revoke all on public.careersite_hiring_market_shadow_history from public, anon, authenticated;
grant select, insert on public.careersite_hiring_market_shadow_history to authenticated;
create policy careersite_market_shadow_owner_select
on public.careersite_hiring_market_shadow_history for select to authenticated
using (
  owner_user_id = (select auth.uid())
  and lower(coalesce((select auth.jwt())->>'email','')) = 'jair.ribeiro@outlook.it'
  and coalesce((select auth.jwt())->>'is_anonymous','false') = 'false'
);
create policy careersite_market_shadow_owner_insert
on public.careersite_hiring_market_shadow_history for insert to authenticated
with check (
  owner_user_id = (select auth.uid())
  and lower(coalesce((select auth.jwt())->>'email','')) = 'jair.ribeiro@outlook.it'
  and coalesce((select auth.jwt())->>'is_anonymous','false') = 'false'
);
