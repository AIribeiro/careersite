-- Private, bounded catalogue for owner role sensitivity; no public access.
create or replace function public.careersite_hiring_role_catalog_v1()
returns jsonb language plpgsql stable security definer
set search_path to ''
as $function$
declare answer jsonb;
begin
  if auth.uid() is distinct from '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
    or pg_catalog.lower(pg_catalog.coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
    or pg_catalog.coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
  then
    raise exception 'Owner sign-in required' using errcode='42501';
  end if;
  select pg_catalog.coalesce(pg_catalog.jsonb_agg(
    pg_catalog.jsonb_build_object(
      'title', s.title, 'company_name', s.company_name,
      'description', s.description,
      'country_code', s.country_code, 'is_active', s.is_active,
      'first_seen_at', s.first_seen_at) order by s.first_seen_at desc
  ), '[]'::jsonb)
  into answer
  from (
    select title, company_name, pg_catalog.left(pg_catalog.coalesce(description,''),2200) as description,
           country_code,is_active,first_seen_at
    from public.jobwise_vacancies
    where country_code='SE' and is_active = true
    order by first_seen_at desc nulls last, vacancy_id desc
    limit 500
  ) s;
  return answer;
end;
$function$;
revoke all on function public.careersite_hiring_role_catalog_v1() from PUBLIC, anon;
grant execute on function public.careersite_hiring_role_catalog_v1() to authenticated;