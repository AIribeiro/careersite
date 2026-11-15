# Member session continuity — production behavior and verification

## Scope

Premium Reader and Executive Advisory use a **single Supabase Auth identity**.
The member's Advisory profile, role-specific password check and service
entitlements stay independent of the Reader account. Reader sign-in alone
never approves a Scorecard or Rollout workspace.

The native Streamlit navigation bridge already keeps authenticated clicks
within the same WebSocket for both branded routes. This release adds a secure
HTTP-only session bridge for full reloads and return visits **when the actual
application origin supports same-origin cookie endpoints**.

## How persistence works

1. The native email-link or password verification completes through Supabase.
2. Python validates the account, saves the session in the active Streamlit
   WebSocket and issues a **45-second, one-use** in-process escrow ticket.
3. A Streamlit V2 component sends the ticket to a same-origin Starlette POST.
   Starlette rechecks the Supabase user and account status, then writes Secure,
   HttpOnly, SameSite=Lax member cookies. Refresh tokens never enter
   JavaScript, URLs, browser storage, or analytics.
4. After browser reload, another same-origin POST uses those cookies to check
   the member and, if required, rotate the refresh token. It returns only a
   separate, one-use restoration ticket. Python redeems that ticket and
   independently verifies access before displaying private Reader data.
5. Advisory account access still requires the existing password-authenticated
   Supabase policy. Each approved service still checks its own entitlement.
6. Sign-out revokes the active Supabase session and clears cookies using the
   same-origin endpoint before another private page is shown.

The cookie lifetime is at most 60 days. Actual account access can end sooner
because of Supabase session expiry, suspension or explicit revocation.

## Branded domain and Streamlit Cloud caveats

If requests genuinely reach Starlette under `jairribeiro.com` or
`advisory.jairribeiro.com`, cookies use `Domain=jairribeiro.com`. Both
branded hosts can then share a single cookie boundary.

If a branded host is only a **masked iframe** of a `streamlit.app` origin,
the response cannot legally install a first-party `jairribeiro.com` cookie.
The cookie remains host-only for the actual Streamlit origin. Safari/iOS and
some mobile privacy settings may block that cookie as third-party. The
application must fail closed to standard sign-in rather than store member
refresh tokens in localStorage as a workaround.

Starlette endpoints must be accessible on the deployment:
`POST /member-auth/attach`, `POST /member-auth/bootstrap`,
`POST /member-auth/logout`. If those endpoints are unreachable through
hosting/masking, persistent reload/return SSO cannot be certified. Use a
real first-party HTTPS reverse proxy/domain for the Streamlit ASGI app rather
than a masked iframe for guaranteed cross-subdomain sessions.

## Required authenticated browser acceptance checks

Use a disposable Reader/Advisory test account and DevTools network/cookies;
never capture real access links or token values in screenshots:

- Desktop: register and verify; move Home → Thinking → Reader → Advisory →
  Reader, including browser Back/Forward. The same identity stays signed in.
- Refresh while on Reader and Advisory, including an assessment in progress.
  Saved server-side assessments remain accessible after a new WebSocket starts.
- Open a second tab for the alternate branded subdomain; confirm the intended
  cookie is sent and the original profile and entitlements are preserved.
- Mobile Safari and Chrome: test navigation and refresh with both native
  browser privacy settings and the existing Spaceship domain mask.
- Allow the access JWT to expire; verify that HTTP refresh rotates the cookie
  and subsequent content access succeeds without password entry.
- Sign out in Reader; revisit Advisory in a new tab and after refresh.
  Neither private workspace may remain authenticated.
- Suspend the Reader membership; confirm both bootstrapping and private
  content deny access. A Reader-only account must never gain Advisory access.
- Intentionally block the HTTP endpoint/cookies; verify a controlled sign-in
  fallback, not a partial or anonymous private experience.

Automated regression tests cover ticket expiry, same-origin POST, cookie
scope/security attributes, refresh rotation, server-side validation and
global sign-out behavior. They do not prove that a registrar's masked iframe
accepts or forwards cookies on real browsers.
