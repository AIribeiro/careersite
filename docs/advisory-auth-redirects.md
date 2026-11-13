# Advisory authentication URLs — production configuration

The application code sends confirmation and recovery redirects to:

`https://advisory.jairribeiro.com/?page=advisory-access`

Premium Reader redirects remain on `https://jairribeiro.com/?page=readers`.
The dedicated `jairribeiro-reader-test.streamlit.app` remains staging-only.

These settings are **not** changed by a PostgreSQL migration or repository commit.
They must be applied separately to the production Supabase Auth service and to
the domain host. Do not claim email redirects are fixed end-to-end until checked.

## Hosted Supabase project

Project: `rnqweoxtynelfirffmlr`

1. Open **Authentication → URL Configuration**:
   https://supabase.com/dashboard/project/rnqweoxtynelfirffmlr/auth/url-configuration
2. Keep the Site URL on a suitable first-party portfolio address, not a
   `streamlit.app` URL (recommended: `https://jairribeiro.com/`).
3. Add the exact allowed Redirect URLs:
   - `https://advisory.jairribeiro.com/?page=advisory-access`
   - `https://jairribeiro.com/?page=readers`
   - Existing first-party Reader article/briefing callback paths already in
     use, and a separate Reader **staging** callback where applicable.
4. In **Authentication → Email Templates**, make **Confirm signup**, **Magic
   link / OTP** and **Reset password** send direct token-hash links using
   `{{ .RedirectTo }}`, **not** `{{ .SiteURL }}` or hardcoded Streamlit
   addresses. Avoid `{{ .ConfirmationURL }}` for these Streamlit server-side
   token exchange screens, since it commonly returns the session in a URL
   fragment which Python cannot access.

   **Confirm signup** and **Magic link / OTP** link:
   ```html
   <a href="{{ .RedirectTo }}&amp;token_hash={{ .TokenHash }}&amp;type=email">Confirm email</a>
   ```

   **Reset password** link:
   ```html
   <a href="{{ .RedirectTo }}&amp;token_hash={{ .TokenHash }}&amp;type=recovery">Reset password</a>
   ```

   The HTML uses escaped `&amp;` delimiters; the browser converts these to
   regular `&` in the clicked URL. The generated redirect target already
   includes `?page=advisory-access` or `?page=readers`.

5. If a custom Send Email Hook is enabled, update its templates/URL builder
   too. The hosted template editor alone does not override an external hook.

## Domain hosting — token propagation must be tested

A masked frame or registrar forwarding rule may not pass the browser's outer
query string to its embedded Streamlit application. A branded address alone
does not establish a working verification callback.

`https://advisory.jairribeiro.com/?page=advisory-access&token_hash=TEST_ONLY_12345678901234567890&type=recovery`
must send the exact `page`, `token_hash` and `type` parameters to the
Streamlit application **without** replacing the visible branded domain with
`streamlit.app` and **without** leaking tokens to external scripts, frames or
logs. Do not test with a real token in a shared screenshot.

Prefer a secure first-party host/proxy with query-preserving routing and proper
SSL. An iframe mask is not a safe assumption for authentication redirects.
If the registrar can only offer masking without query propagation, the
hosting setup needs to change; a code commit alone cannot make that work.

## Two smoke tests

- **New Advisory account**: register with an unused test email, inspect the
  new email **without forwarding it**, verify that its link starts with
  `https://advisory.jairribeiro.com/?page=advisory-access&token_hash=`
  and has `type=email`; clicking it must show the password form. Setting
  the password should activate the Advisory account.
- **Existing account recovery**: click "Forgot your password?", request a
  reset. The new email must target the same Advisory host, with
  `type=recovery`. Clicking it must show "Reset your Advisory password"
  and accept a new password. Subsequent email/password sign-in must succeed.

Old messages already sent are immutable: only newly issued emails reflect the
new Supabase template and redirect settings.
