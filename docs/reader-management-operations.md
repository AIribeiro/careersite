# Reader Management · Owner operations

## Access
Sign in as the portfolio owner on `/?page=analytics` and select **Reader Management**.
This workspace is not available to anonymous visitors. Every private read uses
the signed-in owner's Supabase access token and owner-only row-level security.
The application verifies the owner's identity again when entering the workspace.

## Reader directory
- Search registered readers by first name, email or internal tags.
- Inspect verified profile, registration source, PDF download events, saved
  briefings and the reader's editorial consent history.
- Save owner-only notes and tags. These are not reader consent and are not
  exported to the editorial mailing list.
- Suspend or reinstate complete-briefing access, or suppress/restore a reader
  from mailing exports. These actions require typed-email confirmation and are
  recorded in the owner action audit. A suspension blocks the app's verified
  reader access check; it is not deletion of the Supabase Auth identity.
- Export a filtered directory CSV or an individual reader's data snapshot.
  Review private notes before responding to an access request.
- Identity deletion and data erasure require a separate, authorized Supabase
  Auth and retention workflow. This interface does **not** claim to erase data.

## Mailing list
Membership is not marketing permission. A reader is eligible for an editorial
mailing export only if all conditions are true:
1. The reader explicitly selected editorial updates.
2. A consent timestamp and notice version were recorded.
3. The account is active.
4. Internal mailing suppression is off.

Filters include internal tags and name/email search. Exports are CSV with
spreadsheet formula protection and contain only eligible recipients. Recheck
the current consent state and suppression list before any send.

## Campaign drafts
The **Campaign drafts** tab stores subject, plain-text body, target tag and
draft/archive status in `portfolio_reader_mail_drafts`. No recipient email
addresses are stored with a draft. A live eligible audience count is displayed
for the selected tag.

Drafts do not send, schedule or queue messages. Before outbound sending is
added, require sender-domain verification, unsubscribe links, bounce and
complaint processing, rate limiting, consent revalidation at send time,
delivery logs and an explicit owner review/confirmation.

## Public Analytics
The **Registered Readers** card uses
`careersite_registered_reader_counts_v1`, a public **aggregate-only** RPC.
The reporting period matches the existing Portfolio Analytics filter, using
the canonical Stockholm-aware period boundaries.

The selected-period headline means **new verified reader profiles created
within that period**, not cumulative accounts at its end. The lifetime figure
counts all currently registered profiles. It does not count anonymous visits,
downloads, unverified email attempts or newsletter subscriptions. No email
addresses, names, tags or mailing preferences are exposed by the RPC.

Use **Refresh insights** to clear the card's 90-second cache. If the service is
unavailable, show an unavailable state rather than inventing a zero.

## Storage and security
- `portfolio_reader_profiles`: verified reader identity and consent state.
- `portfolio_reader_downloads`: PDF request history.
- `portfolio_reader_saved_briefings`: saved reading list.
- `portfolio_reader_consent_events`: reader consent history.
- `portfolio_reader_admin_controls`: owner-only access status, suppression,
  tags and notes.
- `portfolio_reader_admin_audit`: owner action audit.
- `portfolio_reader_mail_drafts`: owner-only unsent campaign drafts.

All private administrative tables have RLS enabled, no anonymous SELECT/UPDATE
grants and owner-only policies. Administrative mutations use the validated
`portfolio_reader_admin_action_v1` RPC. Never expose privileged API keys,
access tokens or private reader data in public HTML or analytics.

## Validation
GitHub Actions: **Reader management and public registration KPI** and
**Reader management and registration analytics**. Tests cover consent rules,
owner authorization, CSV formula protection, account controls, public KPI
contracts and a mocked Streamlit back-office render. Supabase checks verify
the aggregate RPC for all nine reporting periods and the private table grants.

Known limit: private tables are paginated up to 10,000 rows in this version.
When the cap is reached, the UI warns that totals or exports may be incomplete;
a server-side cursor export should replace the cap before scaling further.
