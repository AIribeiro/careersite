# Executive AI Briefings — verified reader membership

Status (12 November 2026): **staging only — do not merge or enable public registration yet**. Supabase reader tables and per-user RLS policies are deployed. The registration and download experience now uses **native Streamlit widgets** because Streamlit Community Cloud returned HTTP 500 for custom Starlette HTML POST requests even when no data was submitted. Streamlit Cloud startup logs also rejected the old `server.useStarlette` option and reported that the `streamlit[starlette]` package extra does not exist; both were removed.

## Staging URL

Use **https://jairribeiro-reader-test.streamlit.app/** (no query parameters required).

**Temporary staging launch switch:** The existing Cloud deployment was created with `app.py` as its entrypoint. Streamlit Cloud does not support editing that entry file in Settings. On this draft PR branch alone, `app.py` now launches `reader_test.py`, bypassing the portfolio Home dispatcher. **Before merging PR #54, revert `App("reader_test.py")` to `App("main.py")` and verify that the production reader route `/?page=readers` works.** Keeping the staging override at merge would replace the public portfolio Home page with the signup portal.

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

1. Open the test app root `/` directly after Streamlit Cloud refreshes the branch. Confirm the first visible page is the native **Take the briefings with you** registration form, not the portfolio Home page, and there are no legacy HTTP 500 errors.
2. In Supabase check SMTP and configure both email templates. Register using a **new email address you control**, leaving optional editorial permission unchecked. Click "Send my secure access email". You should see "Check your inbox" instead of an HTTP 500 page.
3. Open the email's link, or enter its one-time code in the original tab. The browser should render the reader library after Supabase confirms the token.
4. Choose a published Executive AI Briefing, click "Prepare PDF" and then "Download A4 infographic". Confirm a real PDF downloads.
5. Verify an entry exists in `portfolio_reader_profiles`, a PDF event in `portfolio_reader_downloads`, and no accidental newsletter subscription. Repeat the test with consent explicitly checked and then revoked in preferences.
6. Test returning reader access, expired/invalid code, failed SMTP handling, sign-out and multiple sessions.
7. Verify that other ordinary readers cannot view one another's records. Review the owner directory and CSV.
8. Complete privacy notice details (controller, contact, retention, deletion rights, appropriate legal bases and processors), review CI, and merge only after successful staging tests.

The previous Starlette routes are **not** authoritative for new sign-in. Native Streamlit `/?page=readers` is the only supported reader entry point in this branch. Do not merge PR #54 or use public registrations until the above checks pass.
