-- Safe owner invitation for existing library members, separate from service approvals.
create or replace function public.portfolio_advisory_owner_invite_reader_v1(p_user_id uuid)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
    v_actor uuid := auth.uid();
    v_email text;
begin
    if v_actor is null or not exists (
        select 1 from auth.users u where u.id = v_actor
         and u.email_confirmed_at is not null
         and lower(u.email) = 'jair.ribeiro@outlook.it'
    ) then
        raise exception 'Owner authorization required' using errcode = '42501';
    end if;
    if p_user_id is null then
        raise exception 'Reader identity required' using errcode = '22023';
    end if;
    select lower(r.email) into v_email
    from public.portfolio_reader_profiles r
    join auth.users u on u.id = r.user_id
    left join public.portfolio_reader_admin_controls c on c.user_id = r.user_id
    where r.user_id = p_user_id
      and u.email_confirmed_at is not null
      and lower(u.email) = lower(r.email)
      and coalesce(c.account_status, 'active') = 'active';
    if v_email is null then
        raise exception 'No active verified reader for this identity' using errcode = '22023';
    end if;
    if exists (select 1 from public.portfolio_advisory_profiles where user_id = p_user_id) then
        return jsonb_build_object('user_id', p_user_id, 'status', 'already_member');
    end if;
    if exists (select 1 from public.portfolio_advisory_intents where user_id = p_user_id) then
        return jsonb_build_object('user_id', p_user_id, 'status', 'already_invited');
    end if;
    insert into public.portfolio_advisory_intents(user_id, email, source)
    values (p_user_id, v_email, 'owner_reconciled');
    insert into public.portfolio_advisory_admin_audit(user_id, actor_id, action, detail)
    values (p_user_id, v_actor, 'invite_reader',
        'Owner invited verified library member to complete Advisory onboarding');
    return jsonb_build_object('user_id', p_user_id, 'status', 'invited');
end;
$$;
revoke all on function public.portfolio_advisory_owner_invite_reader_v1(uuid) from public, anon;
grant execute on function public.portfolio_advisory_owner_invite_reader_v1(uuid) to authenticated;

-- Members may update professional details but not change their own access status.
revoke update on table public.portfolio_advisory_profiles from authenticated;
grant update (
    first_name, last_name, organization, role_title, decision_context,
    advisory_focus, decision_horizon, updated_at
) on public.portfolio_advisory_profiles to authenticated;

-- Match both the client and the underlying request on Scorecard permissions.
drop policy if exists "Scorecard client reads only individually approved engagement"
on public.portfolio_advisory_scorecards;
create policy "Scorecard client reads only individually approved engagement"
on public.portfolio_advisory_scorecards for select to authenticated
using (
    user_id = (select auth.uid())
    and status = 'active'
    and (select public.portfolio_advisory_password_session_v1())
    and exists (
        select 1 from public.portfolio_advisory_requests r
        where r.id = portfolio_advisory_scorecards.request_id
          and r.user_id = portfolio_advisory_scorecards.user_id
          and r.status in ('active', 'completed')
    )
    and exists (
        select 1 from public.portfolio_advisory_profiles p
        where p.user_id = portfolio_advisory_scorecards.user_id
          and p.account_status = 'active'
    )
);
