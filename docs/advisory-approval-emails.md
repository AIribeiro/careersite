# Advisory service approvals and client notifications

Owner workspace: `https://jairribeiro.com/?page=analytics&workspace=advisory`

## One-click approval
In **Requests & replies** or **Access & invitations**, select a real, open Advisory request and click **Approve access & email client** under the requested service. This immediately grants the individual Scorecard or Rollout entitlement without changing the advisory relationship stage. Closed or declined requests must first be reopened.

Approvals are recorded in the corresponding service audit and in the private `portfolio_advisory_approval_notifications` table. A new approval after revocation creates a new email event. Repeating approval on an already active entitlement does not send a duplicate notice. Revocation preserves earlier client reports and immediately blocks further access.

## One-time email provider setup

The site application must have **one** server-only transactional email credential. Configure in the deployed Streamlit app **Settings → Secrets** (or an equivalent protected runtime environment); **never** put the credential in GitHub, code, a URL, or the browser.

Preferred:

```toml
RESEND_API_KEY = "<private Resend API key>"
```

Supported SMTP alternative (with verified `jairribeiro.com` sender domain):

```toml
RESEND_SMTP_PASSWORD = "<private Resend SMTP API key>"
```

Optional SMTP overrides are `RESEND_SMTP_USERNAME`, `RESEND_SMTP_HOST`, `RESEND_SMTP_PORT`, and generic `SMTP_USERNAME`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_PASSWORD`. The default SMTP username is `resend`, host `smtp.resend.com`, port `465`. The sender is `advisory@jairribeiro.com`; the reply-to address is the same.

The Resend API uses an `Idempotency-Key` header per database notification. The response state **sent** means the mail provider accepted the email request; it is not proof that it reached the recipient's inbox. SMTP acceptance is labeled similarly. These are transactional emails only; Reader marketing consent is not changed.

If no mail credentials are available, the service grant still works but the panel **explicitly says the email was not sent**, records a retryable failed notification, and exposes **Retry approval email** after configuration. Retrying does not create a new access grant. Never claim client delivery based on a queued record.

## Operations
- **Service approved / provider accepted:** permission active, notification `sent`, provider ID retained.
- **Service approved / mail failed:** permission active, notification `failed`, use Retry.
- **Service approved / sending:** permission active, notification temporarily `sending`; claim is leased to one sender for 10 minutes.
- **Service revoked:** permission disabled, previous saved work remains.
- **Request closed / declined:** new approval is blocked; existing service access is also blocked by client RLS.

Admin RPCs check the verified owner identity against Supabase Auth. Public and anonymous roles cannot call the privileged approval or email-claim functions. The notification table is owner-private via RLS. Never include a client's business decision details in the access email.

## Verification
Regression: `python -m unittest discover -s tests -p 'test_advisory_one_click_approval.py' -v`; full owner regression is run by `.github/workflows/advisory-owner-operations.yml`. Confirm a provider accepted one real approval email before treating production email delivery as operational.
