# Reader and Advisory onboarding — contextual value and measurement

## Design contract

A new member should never need to decipher an entire service catalog before
finding one useful outcome. The editorial path leads to an actual published
perspective, not a synthetic sample. The executive path leads to an appropriate
decision service, not a suggestion that implies approval, objective verification
or a guaranteed business result.

**Reader priority (deterministic):** an explicitly selected current topic,
an incoming verified published edition slug, the user's voluntarily saved
editorial interests, then the latest published Executive AI Briefing.
The reason for the suggestion is displayed. If the selected topic has no actual
published match, report that rather than fabricate an edition. The topic selector
is optional and does not update member profile or mailing consent.

**Advisory priority (deterministic):** previously supplied decision context,
saved advisory focus, or a clear default single-opportunity starting point.
Members can change their decision type immediately. The four explicit routes
are one AI investment decision (included), competing portfolio decisions
(Scorecard, individually approved), rollout readiness (individually approved),
and a privately reviewed personal request (not guaranteed). Stored context is
used locally in Python to select a route; it is never copied to analytics.

## Before / after editorial framing

Reader: move from a short preview or topic to the complete, actually published
argument with supporting evidence and executive discussion questions.

Advisory: move from an uncertain question to the **appropriate route** for an
evidence-led recommendation and next actions. Access authorization,
independent validation and actual business outcomes remain separate concerns.

Avoid social-pressure tactics, fictional testimonials, fabricated demo clients,
false confidence scores, arbitrary urgency and promises of guaranteed engagement.

## Conversion and first-value measurement

Source of registration truth:
- `portfolio_reader_profiles.created_at` for verified Reader membership.
- `portfolio_advisory_profiles.created_at` and `account_status='active'`
  for Advisory registration.

First-use milestones, recorded only after confirmed actions:
- `reader / first_full_read`: clicking a verified member's complete published
  edition (an open, **not** proof of reading or understanding).
- `advisory / first_assessment`: first server-persisted Investment or Rollout
  assessment, or first saved nonempty Scorecard with a successfully generated
  executive report. No form starts, demos, empty Scorecards or access requests.
- `advisory / first_personal_request`: first successfully saved personal
  request. This is **not** counted as an assessment, a selected pro-bono
  engagement or a received advisory recommendation.

Each milestone can exist only once per verified member and event. Postgres
computes timestamps and seconds since that journey's registration. Client
timing, visit identities, article slugs, IP addresses, device properties,
assessment answers, financial assumptions, private business descriptions
and free-text metadata are not stored in this table.

The owner-only **Reader Management → Onboarding outcomes** tab presents
aggregates: verified registrations, number of first complete opens, first
saved assessments, first requests, and median registration-to-first-outcome
duration. These are not global assessment totals or evidence of adoption.
Measurement only begins from this deployment; historical first-use activity
cannot be reconstructed. Account deletion cascades to its milestones.
Privacy notice describes this use, and writing a milestone is not required
to access a publication or assessment.

## Security / release gates

- No personalization rule changes Supabase authentication, password AMR,
  Reader membership status or service entitlements.
- Supabase RLS: members read/insert only their own rows, owner can read the
  bounded table through the existing verified owner identity; no user UPDATE
  or DELETE API permissions. The trigger uses SECURITY INVOKER.
- A failed milestone write never blocks editorial or executive output.
- All personalized suggestions are based on actual published records or
  existing service definitions; advice displays its reason.
- Verify small-screen selector wrapping and responsive before/after cards.
- Test new member with selected article, returning member with interests,
  no matching topic, Reader-only member opening Advisory, self-service Advisor,
  unapproved Scorecard, approved Rollout, one completed assessment and sign-out.
- Verify the owner dashboard with no events, both journeys represented,
  repeat opens and second-account isolation.
- Existing unrelated repository CI failures must not be mistaken for pass.
  Production domain/browser acceptance remains a distinct validation gate.
