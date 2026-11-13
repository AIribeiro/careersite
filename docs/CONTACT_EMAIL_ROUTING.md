# Portfolio contact and service email routing

Updated: 2026-11-13. Public-facing addresses belong to the `jairribeiro.com` domain. The old Outlook address is **not** a public contact address.

## Published in the portfolio

| Address | Purpose | Current website treatment |
| --- | --- | --- |
| `jair@jairribeiro.com` | Executive personal identity, professional and speaking correspondence | Canonical `site_assets.EMAIL`, Contact page, site footer, canonical CV |
| `advisory@jairribeiro.com` | Executive AI/Data advisory and scoped business inquiries | Public Advisory page and Contact pathways |
| `readers@jairribeiro.com` | Premium Reader access, account questions, downloadable resources | Reader sign-in, account support, library footer, Contact pathways |
| `privacy@jairribeiro.com` | Data-subject rights, GDPR inquiries and privacy concerns | Public Privacy page and Reader account guidance |
| `info@jairribeiro.com` | General informational mailbox | Retained as an alias; not displayed as a competing reader-support address |
| `contact@jairribeiro.com` | General inquiry alias | Retained as a fallback; the public Contact page uses specific routes |
| `no-reply@jairribeiro.com` | Automated account verification and other transactional mail | **Address reserved; sender is not configured by this code change** |
| `admin@jairribeiro.com` | Internal owner alerts and operations | **Address reserved; not used as the current Supabase administrator login** |

Address constants live in `src/site_assets.py`.

## Authentication: preserve the current owner identity

The owner CMS and privileged session checks still use the verified Supabase account address in `src/site_cms.py` and `src/site_owner_tickets.py`. The address is a security **identity check**, not public contact copy. Do not replace it with `admin@` or `jair@` until the existing Supabase Auth user has been migrated, verified and all related checks can be updated together.

Suggested controlled migration when ready:

1. Verify the `admin@` mailbox can receive verification and recovery messages.
2. Migrate the established Supabase Auth owner identity using the provider's supported flow, preserving the user ID, authorizations and recovery path; do not create a new privileged account by changing a literal in code.
3. Confirm a valid new owner session and refresh token, including cookie escrow and CMS/Analytics access.
4. Change both owner identity checks in one reviewed commit, then test sign-in, refresh, sign-out and recovery before retiring the old address.
5. Keep `admin@` private; no public page should disclose the administrative login identity.

## Transactional email sender configuration — external step required

Supabase Auth controls the actual From identity for signup and sign-in messages. A Python constant or visible site label cannot configure the sending mailbox. To use `no-reply@jairribeiro.com`:

1. Choose an authenticated SMTP/email provider and verify that it supports this sender and the domain.
2. Publish the provider's prescribed SPF and DKIM records. Add an appropriate DMARC policy and review delivery and alignment. Do not commit SMTP credentials to GitHub.
3. Configure the sender identity in the Supabase Auth Email/SMTP settings for the actual reader project; retain the existing reader callback and token-template variables.
4. Set a reply-to address that is staffed (prefer `readers@jairribeiro.com` for account messages), where supported.
5. Test confirmation email, magic-link/OTP, expired code, sending errors, spam placement and reply handling before declaring the sender live.

**Do not enable editorial campaigns simply because transactional mail works.** The reader campaign workspace currently stores drafts only. Editorial mail requires separately verified sender identity, explicit subscriber consent, unsubscribe/suppression controls, bounce/complaint management and a reviewed sending flow.

## Privacy operations

The public Privacy page provides user-visible information and a contact route for rights requests. It does not automatically execute access, export or erasure requests. Maintain a controlled request log, verify requester identity where needed, and confirm operational retention/deletion schedules and processor/transfer details before treating the notice as a legally reviewed final policy. Do not expose reader records or privileged keys through public website components.

## Deployment checks

- Confirm `/?page=advisory` and `/?page=privacy` render on the branded domain and the original Streamlit origin.
- Check desktop/mobile navigation, site and Contact footers, and the Reader Library after sign-in.
- Test `mailto:` destinations for `jair@`, `advisory@`, `readers@` and `privacy@`.
- Confirm `/sitemap.xml`, search metadata and `/llms.txt` link to the new public pages.
- Verify the PDF CV exposes the branded personal email and the old Outlook address remains limited to privileged identity checks.
