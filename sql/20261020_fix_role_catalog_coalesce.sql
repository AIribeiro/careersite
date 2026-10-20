-- Repair PostgreSQL special expression qualification in owner-only role catalogue.
-- Preserve security-definer owner guards and existing grants.
CREATE OR REPLACE FUNCTION public.careersite_hiring_role_catalog_v1()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare answer jsonb;
begin
  if auth.uid() is distinct from '210ec7a4-6b03-4720-99d9-091ea6cbf975'::uuid
    or pg_catalog.lower(coalesce(auth.jwt()->>'email','')) <> 'jair.ribeiro@outlook.it'
    or coalesce(auth.jwt()->>'is_anonymous','false') <> 'false'
  then
    raise exception 'Owner sign-in required' using errcode='42501';
  end if;
  select coalesce(pg_catalog.jsonb_agg(
    pg_catalog.jsonb_build_object(
      'title', s.title, 'company_name', s.company_name,
      'description', s.description,
      'country_code', s.country_code, 'is_active', s.is_active,
      'first_seen_at', s.first_seen_at) order by s.first_seen_at desc
  ), '[]'::jsonb)
  into answer
  from (
    select title, company_name, pg_catalog.left(coalesce(description,''),2200) as description,
           country_code,is_active,first_seen_at
    from public.jobwise_vacancies
    where country_code='SE' and is_active = true
    order by first_seen_at desc nulls last, vacancy_id desc
    limit 500
  ) s;
  return answer;
end;
$function$;

REVOKE ALL ON FUNCTION public.careersite_hiring_role_catalog_v1() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.careersite_hiring_role_catalog_v1() TO authenticated;
