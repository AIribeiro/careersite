DO $patch$
declare f text;
old_text text := $old$      ('contact', 'Contact', 'Core', 11)$old$;
new_text text := $new$      ('contact', 'Contact', 'Core', 11),
      ('ai-data-governance', 'AI & Data Governance', 'Core', 12)$new$;
begin
 select pg_get_functiondef(p.oid) into f
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='careersite_analytics_dashboard_v2';
 if f is null or position(old_text in f)=0 then
   raise exception 'Could not safely extend navigation page catalogue';
 end if;
 execute replace(f,old_text,new_text);
end $patch$;
