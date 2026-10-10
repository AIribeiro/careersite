DO $patch$
declare f text;
 old_pred text := $old$      ) as duration_confirmed
    from scoped$old$;
 new_pred text := $new$      ) as duration_confirmed,
      bool_or(event_name in ('email_click','linkedin_click')) as contacted_channel
    from scoped$new$;
 old_json text := $old$    'confirmed_duration_sessions', count(*) filter (where duration_confirmed),$old$;
 new_json text := $new$    'confirmed_duration_sessions', count(*) filter (where duration_confirmed),
    'contact_channel_sessions', count(*) filter (where contacted_channel),$new$;
begin
 select pg_get_functiondef(p.oid) into f
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='careersite_analytics_dashboard_v2';
 if f is null or position(old_pred in f)=0 or position(old_json in f)=0 then
   raise exception 'Dashboard contact counting definition changed';
 end if;
 f:=replace(f,old_pred,new_pred);
 f:=replace(f,old_json,new_json);
 execute f;
end $patch$;
