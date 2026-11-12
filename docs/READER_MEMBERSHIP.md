# Executive AI Briefings — verified reader membership

Status (12 November 2026): **production integration candidate — pending final rollout checks**. Supabase reader tables and per-user RLS policies are deployed. The registration and download experience now uses **native Streamlit widgets** because Streamlit Community Cloud returned HTTP 500 for custom Starlette HTML POST requests even when no data was submitted. Streamlit Cloud startup logs also rejected the old `server.useStarlette` option and reported that the `streamlit[starlette]` package extra does not exist; both were removed.

## Staging URL

Use **https://jairribeiro-reader-test.streamlit.app/?page=readers** for the integrated reader route. The staging root now correctly shows the complete portfolio.

**Normal portfolio entrypoint restored:** `app.py` launches `main.py`, not the isolated reader-only app. The integrated reader route is `/?page=readers`, and `reader_test.py` remains an optional standalone local/CI test harness. Verify that staging `/` shows Home and staging `/?page=readers` shows the native reader with the portfolio navigation, footer and contextual briefing links.

Do not test `/readers/login`, `/~/+/readers/login`, or `/readers/request` for registration. Those legacy ASGI GET/POST paths were abandoned as a sign-in mechanism. Native Streamlit `st.form` posts through Streamlit's regular widget connection and sends Auth requests to Supabase from Python, so Community Cloud does not have to process a custom HTTP POST.

## Streamlit test app configuration

Repository: `AIribeiro/careersite`  
Branch: `feature/verified-briefings-readers-20261111`  
Entry point: `app.py`  
Streamlit secret at the **root** of the TOML:

```toml
PORTFOLIO_READER_CALLBACK_ORIGIN = "https://jairribeiro-reader-test.streamlit.app"
```

Keep existing Supabase URL and publishable key settings from the production app. No service role or Supabase secret key is required in the browser. Never print or send these secret values to a third party.

## Supabase Auth email configuration — mandatory for automatic sign-in

In [Supabase Auth Email Templates](https://supabase.com/dashboard/project/rnqweoxtynelfirffmlr/auth/templates), update **both** authentication templates **Confirm signup** and **Magic Link / OTP** to link to the Streamlit reader page instead of the obsolete /readers/confirm route. The critical template expression is:

```html
<p><a href="{{ .RedirectTo }}&amp;token_hash={{ .TokenHash }}&amp;type=email">
  Verify my email and open the reader library
</a></p>
<p>Or enter this one-time code in the reader page: <strong>{{ .Token }}</strong></p>
```

`{{ .RedirectTo }}` is provided by the Python app as `https://jairribeiro-reader-test.streamlit.app/?page=readers` on staging or `https://jairribeiro-ai.streamlit.app/?page=readers` after production release. The `&amp;` above is for HTML: it is parsed as `&` in the resulting link.

The user can click the link or manually enter the OTP code. Both flows call Supabase Auth `/auth/v1/verify` from Python and validate `/auth/v1/user`. The one-time token hash is removed from Streamlit query parameters before the private session is shown. Confirm the Supabase Email provider and custom SMTP via Resend are enabled and functional before the first test.

In [Supabase Authentication URL Configuration](https://supabase.com/dashboard/project/rnqweoxtynelfirffmlr/auth/url-configuration), allow:

- `https://jairribeiro-reader-test.streamlit.app/?page=readers`
- `https://jairribeiro-ai.streamlit.app/?page=readers`

Keep existing allowlist entries until migration is verified.

## Troubleshooting: confirmation goes to localhost:3000

The SMTP delivery path can work while the login fails: on 12 November 2026,
Supabase confirmed a reader identity, but the default email link redirected to
`http://localhost:3000`. That is Supabase's undeployed default Site URL,
not a Streamlit login, and it does not restore the verified reader's browser
session. A second click may report an expired or invalid one-time link.

**Project-wide URL Configuration** in
https://supabase.com/dashboard/project/rnqweoxtynelfirffmlr/auth/url-configuration:

1. Set **Site URL** to `https://jairribeiro-ai.streamlit.app/` (the permanent
   portfolio host, not `http://localhost:3000`). This project-wide setting
   affects any other Auth flow relying on the default Site URL; review them.
2. Add **Redirect URLs**:
   - `https://jairribeiro-reader-test.streamlit.app/?page=readers`
   - `https://jairribeiro-ai.streamlit.app/?page=readers`
3. Keep existing URLs needed by other live Auth flows. The standalone `reader_test.py` launcher explicitly pins its staging callback;
   the deployed integrated `main.py` instead reads the root-level Streamlit
   secret `PORTFOLIO_READER_CALLBACK_ORIGIN` on staging and defaults to the
   production portfolio origin if omitted. Ensure the staging Cloud secret is
   configured, and the app calls `POST /auth/v1/otp?redirect_to=` with its
   percent-encoded reader URL.

In **Authentication → Email Templates** configure **both** *Confirm signup* and
*Magic Link / OTP* to **not** use `{{ .SiteURL }}` or
`{{ .ConfirmationURL }}` as the final direct application destination.
For the native Streamlit verification contract, use the same content in both:

```html
<h2>Your Executive AI Briefings access</h2>
<p>Use this one-time code on the reader registration page:</p>
<p style="font-size:24px;font-weight:700">{{ .Token }}</p>
<p>Or verify with the secure link:</p>
<p><a href="{{ .RedirectTo }}&amp;token_hash={{ .TokenHash }}&amp;type=email">Open my reader library</a></p>
<p>If you did not request this, you can ignore this message.</p>
```

`{{ .Token }}` is the six-digit code and supports code entry without clicking
a link. `{{ .RedirectTo }}` is the allowlisted staging/production reader URL
that the application requests. `{{ .TokenHash }}` can be exchanged with the
Supabase Auth Verify OTP endpoint. The HTML `&amp;` is required within the
attribute because the base redirect already includes `?page=readers`.

**Staging retest:** Since the first confirmation may already have been
consumed, choose *I already have an account* at
https://jairribeiro-reader-test.streamlit.app/?page=readers and request a fresh email.
Then use the displayed six-digit code (simplest) or follow the updated link.
Never post a live code, token hash, session key or full magic link into a chat.
The final test is that the verified user's actual Streamlit session opens the
PDF library, not merely that Supabase has a confirmed user row.

## Reader experience and OTP policy (12 November 2026)

The native reader flow now reuses **actual** `site_components.nav` and
`site_components.footer` under `site_styles.CSS` and `site_image_styles.IMAGE_CSS`
instead of presenting an isolated utility page. Its editorial hero, breadcrumb,
brand identity, color palette, form and download surfaces, mobile spacing and
footer live in `src/site_reader_shell.py`. Streamlit retains the genuine
`st.form`, verification controls and `st.download_button` that worked on Cloud.
The same shell is called from `main.py?page=readers` and from the staging
`reader_test.py`. The staging launcher runs `layout="wide"`; navigation links
return to the real portfolio because the dedicated test app is intentionally
not a general page dispatcher. On the eventual production route they are
relative navigation links within the same application.

The query verification token is consumed **before** header or image markup can
load: single-use secrets must not be exposed as URL-referrer information.
Any success/error notice is displayed inside the styled reader content after
token consumption.

**OTP length:** The user requested four decimal digits. The Supabase Auth
email OTP generator/validator only supports **6–10 digits**, with 6 by default
(official CLI config and Auth server). An on-screen 4-digit truncation would
always fail legitimate verification. Implementing a separate 4-digit code
store/exchange would materially weaken brute-force resistance and require a
new purpose-built, rate-limited and audited authentication service, outside
this staging feature. Keep the **native six-digit code** and functioning
one-click link; do not introduce an insecure faux-four-digit OTP or disable
email confirmation. A shorter code is an unresolved product request, not an
implemented feature.

The temporary `app.py` staging entrypoint override has been removed. Merge
only after relevant reader tests, QA on desktop/mobile, authenticated PDF
retrieval and production redirect configuration are checked.

## Reader contract

- Full public briefing remains readable without sign-in.
- PDF downloads require verified email authentication.
- First name and email are required; the editorial email checkbox is optional and **unchecked**.
- Registration is not newsletter consent. Only consented subscribers may receive editorial mail.
- A verified user may access all approved A4 PDFs through the native reader library; selecting a title prepares a matching PDF and provides a native Streamlit download button.
- Download requests are recorded in `portfolio_reader_downloads` under the authenticated reader's user ID; the profile and editorial choice live in `portfolio_reader_profiles`, with consent changes in `portfolio_reader_consent_events`.
- RLS policies restrict ordinary readers to their own profile and events; the private owner directory is separate.
- The native Streamlit session is currently scoped to the active browser session. Opening a fresh session requires signing in again; this is appropriate for staging but must be reviewed for the final reader experience.
- A public GitHub-hosted PDF is not copy protection. Premium paid distribution will require private storage.

## Required smoke tests before merging

1. Open staging root `/` and confirm the normal portfolio Home. Open `/?page=readers` and confirm the native **Take the briefings with you** page inside shared site navigation, with the original footer and no legacy HTTP POST errors.
2. In Supabase check SMTP and configure both email templates. Register using a **new email address you control**, leaving optional editorial permission unchecked. Click "Send my secure access email". You should see "Check your inbox" instead of an HTTP 500 page.
3. Open the email's link, or enter its one-time code in the original tab. The browser should render the reader library after Supabase confirms the token.
4. Choose a published Executive AI Briefing, click "Prepare PDF" and then "Download A4 infographic". Confirm a real PDF downloads.
5. Verify an entry exists in `portfolio_reader_profiles`, a PDF event in `portfolio_reader_downloads`, and no accidental newsletter subscription. Repeat the test with consent explicitly checked and then revoked in preferences.
6. Test returning reader access, expired/invalid code, failed SMTP handling, sign-out and multiple sessions.
7. Verify that other ordinary readers cannot view one another's records. Review the owner directory and CSV.
8. Complete privacy notice details (controller, contact, retention, deletion rights, appropriate legal bases and processors), review CI, and merge only after successful staging tests.

The previous Starlette routes are **not** authoritative for new sign-in. Native Streamlit `/?page=readers` is the supported reader entry point. Keep incomplete checks and release blockers explicit in the PR; never treat unrelated CI failures as passing.
