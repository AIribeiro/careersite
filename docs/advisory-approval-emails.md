# Advisory service approval and Supabase Auth email access

Owner workspace: https://jairribeiro.com/?page=analytics&workspace=advisory

## Current approval process

Select an existing Advisory request under **Requests & replies** or **Access & invitations** and click **Approve access & send Supabase email**. This immediately grants the selected service without changing the private relationship stage. The service must be attached to an open request and a verified, active Advisory member.

The approval generates a private row in `portfolio_advisory_approval_notifications`. Client access uses the existing password-verified Advisory account and per-service permission. Repeated approval on an already-active grant does not create a duplicate notification. Revocation preserves client reports and blocks access.

## What email is actually sent

Both Library and Advisory signups use Supabase Auth `POST /auth/v1/otp`, with their preconfigured authentication mail templates. Password recovery uses `POST /auth/v1/recover`. The approval workflow now invokes **that same Supabase Auth OTP/magic-link endpoint** for the *existing verified* Advisory account, with `create_user: false` and the same configured Advisory callback:

`https://advisory.jairribeiro.com/?page=advisory-access`

The email is an **account access / sign-in email** issued by Supabase Auth. It is **not a custom service-approval email**, because Supabase Auth does not expose a general-purpose transactional email endpoint. The recipient sees the exact approved Scorecard or Rollout service on their Advisory account after password sign-in. Do not describe the Auth email as a custom "Scorecard approved" email or promise an approval-specific subject.

There is **no separate Resend/SMTP credential required in Streamlit**, and the previous warning demanding `RESEND_API_KEY` has been removed. Supabase Auth uses whatever email configuration already supports Library and Advisory registration. The existing Auth sender/template and rate limits apply.

## Auditable delivery state

- `sent`: Supabase Auth accepted the request to send its sign-in email; **inbox delivery is not verified**.
- `failed`: Supabase Auth rejected the request, or request transport failed. The service entitlement remains active; owner can retry from the same screen.
- `sending`: a send attempt has already been claimed and is not retried concurrently.
- `pending`: the grant was approved, but sending has not yet been attempted.

A single approval event is re-used for retries. Supabase Auth can rate-limit repeated OTP requests; do not automatically retry in a tight loop. The private email queue never contains an auth token or password. Auth builds the short-lived magic link securely. There is no change to Reader editorial consent.

## If a service-specific branded email is needed

A custom message with its own subject and service name requires a **separate transactional sender**, usually Supabase Edge Functions invoking a mail provider through server-side credentials. Even when deployed on Supabase, this is not provided by the Auth OTP endpoint. Do not reuse password recovery or a misleading login template to simulate an approval-specific message.

## Verification

Run `python -m unittest discover -s tests -p 'test_advisory_one_click_approval.py' -v` and the owner regression workflow. Use the same verified account as the existing registration smoke test; inspect the saved notification and Supabase Auth logs after trying a retry. Until a live attempt, status is only deployment-ready, not delivery-confirmed.
