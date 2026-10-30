-- Reusable interview-authority and employer hiring-plan evidence for MTO.
-- Existing owner-only RLS policies remain unchanged. All values are optional.
-- This is a defensive/idempotent source migration; applied live on 2026-10-30.
alter table public.careersite_recruiter_meetings
  add column if not exists interviewer_role text,
  add column if not exists decision_authority text,
  add column if not exists role_evidence_basis text;

alter table public.careersite_recruiting_opportunities
  add column if not exists mto_total_min smallint,
  add column if not exists mto_total_max smallint,
  add column if not exists mto_remaining_min smallint,
  add column if not exists mto_remaining_max smallint,
  add column if not exists mto_source_type text,
  add column if not exists mto_source_note text;

comment on column public.careersite_recruiter_meetings.decision_authority is
  'Role in THIS hiring decision: recruiter, hiring_manager, stakeholder, executive_sponsor, functional_owner, final_decision_maker; NULL when unverified. Functional owner does not prove final approval.';
comment on column public.careersite_recruiting_opportunities.mto_source_type is
  'Only employer_confirmed may override MTO role-based priors. General guidance and conditional planning are nonbinding.';

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname='careersite_mto_total_range'
  ) then
    alter table public.careersite_recruiting_opportunities
      add constraint careersite_mto_total_range
      check (mto_total_min is null or mto_total_max is null
        or (mto_total_min >= 0 and mto_total_max >= mto_total_min));
  end if;
  if not exists (
    select 1 from pg_constraint where conname='careersite_mto_remaining_range'
  ) then
    alter table public.careersite_recruiting_opportunities
      add constraint careersite_mto_remaining_range
      check (mto_remaining_min is null or mto_remaining_max is null
        or (mto_remaining_min >= 0 and mto_remaining_max >= mto_remaining_min));
  end if;
end $$;
