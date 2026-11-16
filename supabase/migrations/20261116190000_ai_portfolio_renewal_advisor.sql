-- Additive, member-owned renewal case workspace; no changes to legacy Advisory records.
insert into public.portfolio_advisory_service_visibility(service_key,display_name,is_enabled)
values ('renewal','AI Portfolio Renewal Advisor',false)
on conflict (service_key) do nothing;
-- Start disabled; release gate is opened only after checks.

create table if not exists public.portfolio_advisory_renewal_assessments (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references auth.users(id) on delete cascade,
 initiative text not null default 'Untitled renewal decision',
 status text not null default 'draft' check(status in ('draft','ready','analyzed','decision_recorded','review_due','archived')),
 inputs jsonb not null default '{}'::jsonb,
 analysis jsonb not null default '{}'::jsonb,
 model_version text not null default 'renewal-v1.0.0',
 revision integer not null default 1 check(revision between 1 and 100000),
 synthetic boolean not null default false,
 next_review date,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(id,owner_id),
 check(jsonb_typeof(inputs)='object' and jsonb_typeof(analysis)='object'),
 check(length(initiative) between 1 and 200)
);
create index if not exists renewal_assessments_owner_recent on public.portfolio_advisory_renewal_assessments(owner_id,updated_at desc);
create index if not exists renewal_assessments_review on public.portfolio_advisory_renewal_assessments(owner_id,next_review) where status in ('analyzed','decision_recorded','review_due');

create table if not exists public.portfolio_advisory_renewal_versions (
 id bigint generated always as identity primary key,
 assessment_id uuid not null,
 owner_id uuid not null,
 revision integer not null,
 event text not null check(event in ('created','changed')),
 snapshot jsonb not null,
 model_version text not null,
 recorded_at timestamptz not null default now(),
 foreign key (assessment_id,owner_id) references public.portfolio_advisory_renewal_assessments(id,owner_id) on delete cascade,
 unique(assessment_id,revision)
);
create index if not exists renewal_versions_owner_recent on public.portfolio_advisory_renewal_versions(owner_id,assessment_id,revision desc);

create table if not exists public.portfolio_advisory_renewal_scenarios (
 id uuid primary key default gen_random_uuid(),
 assessment_id uuid not null,
 owner_id uuid not null,
 label text not null check(length(label) between 1 and 120),
 changes jsonb not null check(jsonb_typeof(changes)='object'),
 inputs jsonb not null check(jsonb_typeof(inputs)='object'),
 analysis jsonb not null check(jsonb_typeof(analysis)='object'),
 model_version text not null,
 base_revision integer not null,
 synthetic boolean not null default false,
 created_at timestamptz not null default now(),
 foreign key (assessment_id,owner_id) references public.portfolio_advisory_renewal_assessments(id,owner_id) on delete cascade
);
create index if not exists renewal_scenarios_owner_recent on public.portfolio_advisory_renewal_scenarios(owner_id,assessment_id,created_at desc);

create table if not exists public.portfolio_advisory_renewal_decisions (
 id uuid primary key default gen_random_uuid(),
 assessment_id uuid not null,
 owner_id uuid not null,
 authorized_action text not null check(authorized_action in ('RENEW','REPLACE','TEST','STOP','HOLD')),
 recommendation_at_signoff text not null,
 rationale text not null check(length(rationale) between 12 and 4000),
 authorized_by text not null check(length(authorized_by) between 2 and 200),
 next_review date not null,
 supporting_revision integer not null,
 synthetic boolean not null default false,
 recorded_at timestamptz not null default now(),
 foreign key (assessment_id,owner_id) references public.portfolio_advisory_renewal_assessments(id,owner_id) on delete cascade
);
create index if not exists renewal_decisions_owner_recent on public.portfolio_advisory_renewal_decisions(owner_id,assessment_id,recorded_at desc);

-- Privacy-minimal telemetry; do not write assessment payloads or business amounts.
create table if not exists public.portfolio_advisory_renewal_events (
 id bigint generated always as identity primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 assessment_id uuid,
 event text not null check(event in ('service_start','draft_saved','analyzed','scenario_saved','decision_recorded','pdf_download','excel_download','review_revisit','reopened','error')),
 synthetic boolean not null default false,
 recorded_at timestamptz not null default now()
);
create index if not exists renewal_events_aggregate on public.portfolio_advisory_renewal_events(event,recorded_at) where synthetic=false;
create index if not exists renewal_events_member on public.portfolio_advisory_renewal_events(user_id,recorded_at desc);

-- Trigger is not a callable public API; it preserves the exact pre/post-edit history.
create or replace function public.portfolio_renewal_version_audit_trigger()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_op='INSERT' then
  insert into public.portfolio_advisory_renewal_versions
   (assessment_id,owner_id,revision,event,snapshot,model_version)
  values(new.id,new.owner_id,new.revision,'created',to_jsonb(new),new.model_version);
  return new;
 end if;
 if new.owner_id<>old.owner_id or new.id<>old.id or new.synthetic<>old.synthetic
    or new.created_at<>old.created_at then
  raise exception 'Case identity and provenance are immutable' using errcode='42501';
 end if;
 new.revision:=old.revision+1;
 new.updated_at:=now();
 insert into public.portfolio_advisory_renewal_versions
   (assessment_id,owner_id,revision,event,snapshot,model_version)
 values(new.id,new.owner_id,new.revision,'changed',to_jsonb(new),new.model_version);
 return new;
end $$;
revoke all on function public.portfolio_renewal_version_audit_trigger() from public,anon,authenticated;
drop trigger if exists portfolio_renewal_version_insert on public.portfolio_advisory_renewal_assessments;
create trigger portfolio_renewal_version_insert after insert on public.portfolio_advisory_renewal_assessments
for each row execute function public.portfolio_renewal_version_audit_trigger();
drop trigger if exists portfolio_renewal_version_update on public.portfolio_advisory_renewal_assessments;
create trigger portfolio_renewal_version_update before update on public.portfolio_advisory_renewal_assessments
for each row execute function public.portfolio_renewal_version_audit_trigger();

-- Must consult the same trusted role catalogue as the established Advisory workspace.
create or replace function public.portfolio_renewal_service_allowed()
returns boolean language sql stable security invoker set search_path='' as $$
 select (select auth.uid()) is not null and (
  exists(select 1 from public.portfolio_advisory_service_visibility where service_key='renewal' and is_enabled)
  or exists(select 1 from public.portfolio_advisory_user_roles where user_id=(select auth.uid()) and role='admin')
 )
$$;
revoke all on function public.portfolio_renewal_service_allowed() from public,anon;
grant execute on function public.portfolio_renewal_service_allowed() to authenticated;

-- RLS enforced on every object including telemetry and history.
alter table public.portfolio_advisory_renewal_assessments enable row level security;
alter table public.portfolio_advisory_renewal_versions enable row level security;
alter table public.portfolio_advisory_renewal_scenarios enable row level security;
alter table public.portfolio_advisory_renewal_decisions enable row level security;
alter table public.portfolio_advisory_renewal_events enable row level security;
revoke all on public.portfolio_advisory_renewal_assessments,public.portfolio_advisory_renewal_versions,
 public.portfolio_advisory_renewal_scenarios,public.portfolio_advisory_renewal_decisions,
 public.portfolio_advisory_renewal_events from anon,authenticated;
grant select,insert,update,delete on public.portfolio_advisory_renewal_assessments to authenticated;
grant select on public.portfolio_advisory_renewal_versions to authenticated;
grant select,insert on public.portfolio_advisory_renewal_scenarios,public.portfolio_advisory_renewal_decisions to authenticated;
grant select,insert on public.portfolio_advisory_renewal_events to authenticated;
grant usage,select on sequence public.portfolio_advisory_renewal_events_id_seq to authenticated;
grant usage,select on sequence public.portfolio_advisory_renewal_versions_id_seq to authenticated;

create policy renewal_owner_read on public.portfolio_advisory_renewal_assessments
 for select to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_owner_create on public.portfolio_advisory_renewal_assessments
 for insert to authenticated with check(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_owner_change on public.portfolio_advisory_renewal_assessments
 for update to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed())
 with check(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_owner_erase on public.portfolio_advisory_renewal_assessments
 for delete to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());

create policy renewal_versions_read on public.portfolio_advisory_renewal_versions
 for select to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_scenarios_read on public.portfolio_advisory_renewal_scenarios
 for select to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_scenarios_add on public.portfolio_advisory_renewal_scenarios
 for insert to authenticated with check(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_decisions_read on public.portfolio_advisory_renewal_decisions
 for select to authenticated using(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_decisions_add on public.portfolio_advisory_renewal_decisions
 for insert to authenticated with check(owner_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());

create policy renewal_events_add on public.portfolio_advisory_renewal_events
 for insert to authenticated with check(user_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_events_member_read on public.portfolio_advisory_renewal_events
 for select to authenticated using(user_id=(select auth.uid()) and public.portfolio_renewal_service_allowed());
create policy renewal_events_admin_read on public.portfolio_advisory_renewal_events
 for select to authenticated using(exists(
  select 1 from public.portfolio_advisory_user_roles r where r.user_id=(select auth.uid()) and r.role='admin'
 ));

comment on table public.portfolio_advisory_renewal_assessments is
 'Member-owned AI Portfolio Renewal Challenge cases. Original context, deterministic analysis and version preserved. Never publish proprietary inputs.';
comment on table public.portfolio_advisory_renewal_events is
 'Privacy-minimal advisory engagement events; business context and financial values are prohibited.';
