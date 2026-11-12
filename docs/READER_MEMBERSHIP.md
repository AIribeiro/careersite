# Executive AI Briefings — registered reader membership

Status: feature branch in review, Supabase reader tables/policies already applied. Do not merge until auth callback and transactional email are verified.

## Editorial contract
- Full public briefing stays readable and indexed.
- Approved A4 infographic PDFs require free verified reader sign-in; one account for all editions.
- Name/email registration is separate from the optional, unchecked newsletter box.
- No newsletter sending automation and no paid membership yet.
- Existing owner CMS account stays independent.

## Streamlit Community Cloud route prefix
Cloud proxies custom Starlette routes through **`/~/+/`**. The actual Starlette route declarations remain unprefixed because the proxy strips the prefix, but browser-visible form actions, fetch calls, link targets, redirect Location headers and Supabase callback URLs **must** use `/~/+/`. For example, registration is at `https://jairribeiro-reader-test.streamlit.app/~/+/readers/login` and the POST endpoint is `/~/+/readers/request`. Root URLs `/readers/login` or `/readers/request` do not serve the custom routes and must never be linked from the frontend.

The staged callback is `https://jairribeiro-reader-test.streamlit.app/~/+/readers/confirm` (and `?next=*` for briefing links). The production callback will be `https://jairribeiro-ai.streamlit.app/~/+/readers/confirm` (and `?next=*`). Preserve the original non-prefixed redirect allowlist entries for backward compatibility but add these exact new entries in Supabase Authentication > URL Configuration.

For the separate test deployment, add a **root-level Streamlit secret** `PORTFOLIO_READER_CALLBACK_ORIGIN = "https://jairribeiro-reader-test.streamlit.app"`. The application assembles the Cloud route prefix; do not include `/~/+/` in this secret. Keep the default production callback on the canonical Streamlit origin.

## Routes
- /readers/login?next=slug — first-time registration
- /readers/signin — returning reader
- /readers/request — OTP email link (POST)
- /readers/confirm — email-link callback
- /readers/session — token exchange / HttpOnly cookie (POST)
- /readers/library — available download collection
- /readers/preferences — name and editorial subscription choice
- /readers/privacy — reader-specific notice
- /readers/signout — session revoke (POST)
- /readers/download/slug.pdf — verified user, published article, approved PDF
- /readers-admin — owner-only reader directory
- /readers-admin/export.csv — owner-only CSV export

Legacy /briefing-artwork/slug/download.pdf, /briefing-ai-roi/infographic.pdf and
/briefing-ai-authority/infographic.pdf redirect to the reader route. SVG/WebP image views remain public.

## Mandatory go-live checklist
1. Supabase Authentication > URL Configuration: allow `https://jairribeiro-ai.streamlit.app/~/+/readers/confirm` and `https://jairribeiro-ai.streamlit.app/~/+/readers/confirm?next=*`; for the staging app, add the matching `jairribeiro-reader-test.streamlit.app` URLs.
2. Configure custom transactional SMTP for public account verification, sender domain SPF/DKIM/DMARC and monitor delivery/rate limits. Built-in shared email service is too limited.
3. Confirm magic-link implicit callback contains a refresh_token URL fragment and email verification is enabled. Adapt code if your Supabase Auth project uses PKCE or a different email template.
4. Check Streamlit env Supabase URL and publishable key. Do not expose service-role credentials.
5. Test new reader, returning reader, consent opt-in and opt-out, existing reader preferences, signup email replay/expiry, and downloads. Start at `/~/+/readers/login`, confirm form POST stays under `/~/+/readers/request`, and confirm redirect, email callback, session POST and PDF downloads preserve `/~/+/`.
6. Test anonymous PDF requests redirect to registration; authenticated PDF requests return real application/pdf bytes; stale/invalid editions fail closed.
7. Test owner CMS sign-in still works and reader admin directory / CSV work. Test ordinary readers cannot see other users or owner directory.
8. Confirm privacy notice: controller, contact, lawful bases, processor countries, data retention, deletion and data subject access. No marketing without opt-in.
9. Review the tests and CI, remove draft status, merge, then monitor first production events.

## Database
Already applied:
- portfolio_free_briefings_readers_v1: reader profiles, downloads and consent audit (RLS self-only for authenticated readers).
- portfolio_reader_owner_catalog_v1: signed owner-only SELECT on profiles/downloads/consent audit.

The reader catalog is currently read-only. It records completed authenticated HTTP download requests, rather than anonymous clicks. No external email campaigns are enabled.

## Limits and future monetization
The PDFs are still included in the public GitHub repository. Registration therefore provides an orderly audience relationship and download flow but is **not copy protection**: raw files can be found without creating an account. For future premium paywalled downloads, place the assets in a private bucket and enforce server-side entitlement before returning short-lived signed URLs. Removing a file from current GitHub source does not erase earlier public commits.

Registration code is not yet live until this PR is merged. Production SMTP and auth redirect settings are outside the available connector controls and require manual configuration.
