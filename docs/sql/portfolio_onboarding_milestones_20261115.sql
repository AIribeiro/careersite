-- Minimal owner-visible milestones; no content, typed answer, source URL, IP,
-- device fingerprint, article slug, e-mail, or unstructured event properties.
-- One record per member and first useful action; deletion cascades with Auth.
create table if not exists public.portfolio_onboarding_milestones (
  user_id uuid not null references auth.users(id) on delete cascade,
  journey text not null check (journey in ('reader', 'advisory')),
  milestone text not null,
  occurred_at timestamptz not null default now(),
  elapsed_seconds integer not null default 0
    check (elapsed_seconds between 0 and 315360000),
  constraint portfolio_onboarding_milestone_combination check (
    (journey = 'reader' and milestone = 'first_full_read')
    or (journey = 'advisory' and milestone in
       ('first_assessment', 'first_personal_request'))
  ),
  primary key (user_id, journey, milestone)
);

-- Populate elapsed time on the server, against the actual verified membership
-- creation date. Never accept client-provided elapsed time or timestamps.
create or replace function public.portfolio_onboarding_stamp_first_v1()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  registered_at timestamptz;
begin
  if auth.uid() is null or new.user_id is distinct from auth.uid() then
    raise exception 'Unverified onboarding identity';
  end if;
  if new.journey = 'reader' then
    select p.created_at into registered_at
      from public.portfolio_reader_profiles p where p.user_id = auth.uid();
  elsif new.journey = 'advisory' then
    select p.created_at into registered_at
      from public.portfolio_advisory_profiles p where p.user_id = auth.uid()
        and p.account_status = 'active'
        and public.portfolio_advisory_password_session_v1();
  end if;
  if registered_at is null then
    raise exception 'Membership required before an onboarding milestone';
  end if;
  new.occurred_at := now();
  new.elapsed_seconds := least(
    315360000,
    greatest(0, floor(extract(epoch from now() - registered_at))::integer)
  );
  return new;
end;
$$;

drop trigger if exists portfolio_onboarding_stamp_before_insert on public.portfolio_onboarding_milestones;
create trigger portfolio_onboarding_stamp_before_insert
before insert on public.portfolio_onboarding_milestones
for each row execute function public.portfolio_onboarding_stamp_first_v1();

alter table public.portfolio_onboarding_milestones enable row level security;

create policy onboarding_member_read_own
on public.portfolio_onboarding_milestones for select to authenticated
using (user_id = (select auth.uid()));

create policy onboarding_member_insert_own
on public.portfolio_onboarding_milestones for insert to authenticated
with check (
  user_id = (select auth.uid()) and
  (select auth.jwt() ->> 'is_anonymous') is distinct from 'true'
);

-- Same verified owner boundary used by existing private Reader management.
-- Members cannot select anyone else's milestone, and nobody can UPDATE or
-- DELETE a milestone through the public Data API.
create policy onboarding_owner_read_aggregate
on public.portfolio_onboarding_milestones for select to authenticated
using (
  lower(coalesce((select auth.jwt() ->> 'email'), ''))
  = 'jair.ribeiro@outlook.it'
);

revoke all on public.portfolio_onboarding_milestones from anon, public;
grant select, insert on public.portfolio_onboarding_milestones to authenticated;
revoke all on function public.portfolio_onboarding_stamp_first_v1() from public, anon;
grant execute on function public.portfolio_onboarding_stamp_first_v1() to authenticated;

create index if not exists portfolio_onboarding_milestones_date_idx
on public.portfolio_onboarding_milestones (occurred_at desc, journey, milestone);
