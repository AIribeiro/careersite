# Articles — latest published issue plus a minimum seven-day Premium period

## Release policy — 12 November 2026

A published Article's full text requires a complimentary Premium Reader account while **either** of the following is true:

1. It is the **newest published editorial Article**, regardless of its age.
2. It is **less than 168 hours (seven days) old**, measured from the original `published_at` timestamp.

The full Article becomes publicly available **only when both** conditions have been cleared: a newer published Article exists **and** seven days have elapsed since this Article's publication.

The rule applies to all five editorial Article kinds in one sequence: Article, Point of view, Decision note, Field note and Framework. Weekly AI and Executive AI Briefings do **not** count as successors to Articles.

### Release examples

- Article A published 1 November, still latest on 20 November: **Premium**, despite being 19 days old.
- Article B published 21 November: A becomes public immediately (A is older than seven days); B is Premium.
- Article C published 23 November: B remains Premium because B is only two days old, even though C is now latest.
- On 28 November, B opens once its full seven days are complete; C remains Premium until its successor appears, even if C is older than seven days.

Neither an edit, an update to `updated_at`, a featured-article selection, a draft, nor publishing a Briefing or Weekly AI can open a Premium Article. No manual unlock job is required. If publication metadata cannot be checked, the access check **fails closed** rather than exposing an Article prematurely.

## Full editorial access matrix

| Format | Registered reader | Anonymous visitor |
|---|---|---|
| **Executive AI Briefings** | Every full Briefing, permanently | Genuine public preview only; full Briefings always require an account |
| **Articles** | Full editions immediately | Public preview while newest or younger than 7 days; otherwise complete content |
| **Weekly AI** | Full latest published edition | Latest issue preview; all earlier editions fully open |

Every format shares the same verified Supabase Auth reader identity, profile, optional mailing consent and personal library. Existing accounts retain their original sign-up channel and do not require re-registration.

## Reader-facing language

The public article preview gives actual editorial value and explains:

> The full article becomes public after its first seven days and once a newer Article has been published.

Do not promise a specific public unlock date for the **latest** Article, because its successor has not been published yet. The Articles tab in My Library identifies the newest Article, another Premium Article still within seven days, and public editions. The Thinking page keeps the benefit-focused Premium Reader section fixed directly under its hero; access rules remain secondary to the editorial value.

## Operational verification

1. An Article remains Premium after seven days when no newer Article has been published.
2. Publishing a newer Article opens a predecessor older than seven days.
3. Publishing another Article within seven days does **not** open the preceding Article early; it opens at the original 168-hour threshold.
4. Direct anonymous Article routes never render full CMS body before both conditions are satisfied. A verified reader immediately sees the full edition through existing password/OTP.
5. Publishing Weekly AI, Executive AI Briefings or a draft cannot act as a newer Article.
6. All Executive AI Briefings, including historical editions, remain Premium indefinitely.
7. Validate production callback redirects, mobile layout, and library state after deploying the merged code.

## Supabase redirect setup

Keep both first-party Article callback patterns in Supabase Authentication → URL Configuration → Redirect URLs:

```text
https://jairribeiro-ai.streamlit.app/?page=thinking&article=*&access=1
https://jairribeiro-reader-test.streamlit.app/?page=thinking&article=*&access=1
```

Verify real email-code/password and emailed-link flows and ensure the email templates use `{{ .RedirectTo }}` / `{{ .TokenHash }}` rather than a default localhost target.

## Existing security boundary

This controls **website rendering**, not the underlying public CMS Data API. The API currently exposes `careersite_articles.content_html` through public reads, and Weekly AI narrated audio can be accessed via public media URLs. Properly restricted publication requires authenticated server-side text and audio delivery, plus a separate API/RLS redesign. Do not describe this as a secure paid paywall or DRM.
