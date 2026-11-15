CREATE OR REPLACE FUNCTION public.portfolio_advisory_service_owner_action_v2(p_request_id uuid, p_service_key text, p_action text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
    v_owner uuid := auth.uid();
    v_uid uuid;
    v_stage text;
    v_email text;
    v_id uuid;
    v_old text;
    v_event_id uuid;
    v_new text;
begin
    if v_owner is null or not exists(
        select 1 from auth.users u
        where u.id=v_owner and u.email_confirmed_at is not null
        and lower(u.email)='jair.ribeiro@outlook.it'
    ) then raise exception 'Owner only' using errcode='42501'; end if;
    if p_service_key not in ('scorecard','rollout')
       or p_action not in ('approve','revoke')
    then raise exception 'Unsupported service action' using errcode='22023'; end if;

    select r.user_id,r.status,p.email into v_uid,v_stage,v_email
    from public.portfolio_advisory_requests r
    join public.portfolio_advisory_profiles p on p.user_id=r.user_id
    join auth.users u on u.id=r.user_id
    where r.id=p_request_id and p.account_status='active'
      and u.email_confirmed_at is not null and lower(u.email)=lower(p.email)
    for update of r;
    if v_uid is null then
        raise exception 'Verified active Advisory member and request required'
        using errcode='22023';
    end if;
    if p_action='approve' and v_stage in ('closed','declined') then
        raise exception 'Reopen the closed request before approving a service'
        using errcode='22023';
    end if;

    if p_service_key='scorecard' then
        select id,status into v_id,v_old
        from public.portfolio_advisory_scorecards
        where request_id=p_request_id and analysis_request_id is null for update;
    else
        select id,status into v_id,v_old
        from public.portfolio_advisory_rollout_access
        where request_id=p_request_id for update;
    end if;

    if p_action='approve' and v_old='active' then
        select n.id into v_event_id
        from public.portfolio_advisory_approval_notifications n
        where n.request_id=p_request_id and n.service_key=p_service_key
        order by n.created_at desc limit 1;
        return jsonb_build_object('id',v_id,'user_id',v_uid,'status','active',
             'unchanged',true,'notification_id',v_event_id);
    end if;

    if p_action='approve' then
        if p_service_key='scorecard' then
            insert into public.portfolio_advisory_scorecards(request_id,user_id,approved_by)
            values(p_request_id,v_uid,v_owner)
            on conflict (request_id) where analysis_request_id is null do update
                set status='active',approved_by=excluded.approved_by,
                    approved_at=now(),revoked_at=null,updated_at=now()
            returning id into v_id;
            insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
            values(v_id,v_owner,'approve');
        else
            insert into public.portfolio_advisory_rollout_access(request_id,user_id,approved_by)
            values(p_request_id,v_uid,v_owner)
            on conflict (request_id) do update
                set status='active',approved_by=excluded.approved_by,
                    approved_at=now(),revoked_at=null,updated_at=now()
            returning id into v_id;
            insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action)
            values(v_id,v_owner,'approve');
        end if;
        insert into public.portfolio_advisory_approval_notifications(
            request_id,user_id,service_key,recipient_email
        ) values(p_request_id,v_uid,p_service_key,v_email)
        returning id into v_event_id;
        v_new:='active';
    else
        if v_id is null then raise exception 'No entitlement to revoke'; end if;
        if v_old='revoked' and p_service_key='rollout' then
            return jsonb_build_object('id',v_id,'user_id',v_uid,'status','revoked','unchanged',true);
        end if;
        if p_service_key='scorecard' then
            -- Revoking the original service entitlement must also revoke every
            -- additional analysis. Otherwise the client could continue accessing
            -- a separately approved workspace after service access was withdrawn.
            with affected as (
                update public.portfolio_advisory_scorecards
                set status='revoked',revoked_at=now(),updated_at=now()
                where request_id=p_request_id and status='active'
                returning id
            )
            insert into public.portfolio_advisory_scorecard_audit(scorecard_id,actor_id,action)
            select affected.id,v_owner,'revoke' from affected;
            update public.portfolio_advisory_scorecard_analysis_requests
            set status='revoked',decided_by=v_owner,decided_at=now(),
                decision_note='Original Scorecard service access was revoked.',
                updated_at=now()
            where request_id=p_request_id and status='approved';
        else
            update public.portfolio_advisory_rollout_access
            set status='revoked',revoked_at=now(),updated_at=now()
            where id=v_id;
            insert into public.portfolio_advisory_rollout_audit(access_id,actor_id,action)
            values(v_id,v_owner,'revoke');
        end if;
        v_new:='revoked';
    end if;
    return jsonb_build_object('id',v_id,'user_id',v_uid,'status',v_new,
            'unchanged',false,'notification_id',v_event_id);
end;
$function$
;
