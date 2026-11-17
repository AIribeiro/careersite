-- Market Signals Advisory 2.0: immutable, edition-bound executive research.
-- Source points and original November edition are never altered by this migration.
create table if not exists public.portfolio_market_signal_editorial_v2 (
    edition_slug text not null references public.portfolio_market_signal_editions(slug),
    analysis_version text not null,
    analysis jsonb not null,
    is_published boolean not null default false,
    published_at timestamptz,
    created_at timestamptz not null default now(),
    primary key (edition_slug, analysis_version),
    constraint market_editorial_v2_object check (jsonb_typeof(analysis)='object'),
    constraint market_editorial_v2_bound check ((analysis->>'edition_slug')=edition_slug),
    constraint market_editorial_v2_publish check (not is_published or published_at is not null)
);
create unique index if not exists market_editorial_one_published_per_edition
    on public.portfolio_market_signal_editorial_v2 (edition_slug) where is_published;
alter table public.portfolio_market_signal_editorial_v2 enable row level security;
revoke all on public.portfolio_market_signal_editorial_v2 from anon, authenticated;
grant select on public.portfolio_market_signal_editorial_v2 to authenticated;

create policy market_editorial_v2_verified_member_read
on public.portfolio_market_signal_editorial_v2 for select to authenticated
using (
 is_published
 and exists (
     select 1 from public.portfolio_advisory_profiles p
     where p.user_id=(select auth.uid()) and p.account_status='active'
 )
 and (
     exists (select 1 from public.portfolio_advisory_service_visibility v
             where v.service_key='market-signals' and v.is_enabled)
     or (select public.portfolio_advisory_is_admin_v1())
 )
);
create policy market_editorial_v2_admin_review_read
on public.portfolio_market_signal_editorial_v2 for select to authenticated
using ((select public.portfolio_advisory_is_admin_v1()));

create or replace function public.portfolio_market_editorial_immutable_v2()
returns trigger language plpgsql security invoker set search_path=public
as $$
begin
 if old.is_published then
    raise exception 'Published executive editions are immutable; create a new edition.'
      using errcode='23514';
 end if;
 return case when TG_OP='DELETE' then old else new end;
end;
$$;
revoke execute on function public.portfolio_market_editorial_immutable_v2() from public, anon, authenticated;
create trigger market_editorial_v2_immutable
before update or delete on public.portfolio_market_signal_editorial_v2
for each row execute function public.portfolio_market_editorial_immutable_v2();
