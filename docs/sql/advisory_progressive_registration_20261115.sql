-- Progressive Advisory registration, November 2026.
--
-- The existing check forced last name, organization, role and a decision description
-- during sign-up, even for members using the already included no-approval
-- Investment Decision Advisor. Collect that context when a specific advisory
-- request needs it. The password-session RLS policies stay unchanged.
--
-- First name remains mandatory; email remains a NOT NULL field tied to verified
-- Auth identity through the existing insert RLS policy.
--
-- Migration applied separately to the managed Supabase project.

alter table public.portfolio_advisory_profiles
    drop constraint if exists advisory_registration_minimum_check;

alter table public.portfolio_advisory_profiles
    add constraint advisory_registration_minimum_check
    check (length(btrim(first_name)) >= 1);
