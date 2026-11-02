-- Extend the deployed function without replacing other report revisions or grants.
do $migration$
declare
  definition text := pg_get_functiondef('public.careersite_analytics_dashboard(text,integer,text)'::regprocedure);
  marker text := '  elsif v_window = ''today'' then';
begin
  if strpos(definition, 'elsif v_window = ''yesterday'' then') > 0 then return; end if;
  if strpos(definition, marker) = 0 then raise exception 'Reporting window definition changed'; end if;
  execute replace(definition, marker, $branch$  elsif v_window = 'yesterday' then
    v_until := date_trunc('day', now() at time zone 'Europe/Stockholm') at time zone 'Europe/Stockholm';
    v_requested_since := ((v_until at time zone 'Europe/Stockholm') - interval '1 day') at time zone 'Europe/Stockholm';
    v_period_label := 'Yesterday';
$branch$ || marker);
end
$migration$;
