# Articles — Seven-day registered-reader early access

Status: feature branch; not a production rollout until CI, staging authentication and Supabase redirect allowlist are verified.

## Editorial policy

- Published **Articles** (including Point of view, Decision note, Field note and Framework) show a substantive, original-text **executive summary** to visitors who have not signed in.
- The full article is available at no cost to registered readers throughout the first **168 hours** after `published_at`. Readers use the same Supabase Auth identity, password or OTP, active-account controls and Streamlit reader session as Executive AI Briefings.
- At `published_at + interval '7 days'`, the full article is **automatically open to everyone**, without sign-in or a scheduled job. The rule is calculated at render time in UTC. `updated_at` and edits do not restart the period.
- Executive AI Briefings retain the existing always-registered-access model. Weekly AI is unaffected.
- Articles with missing/invalid `published_at` conservatively show the executive summary until corrected.
- Previously published Articles from more than seven days ago remain fully public; no existing URLs, link attribution or historical analytics IDs change.
- No synthetic statistics or unsupported claims in previews: paragraphs are drawn from the published editorial copy, bounded before the full argument or references. For a very short article, editors should verify that the summary does not exhaust the piece.

## Unified account, reader library, tracking

- One `auth.users` record and one `portfolio_reader_profiles` row per person, whether they arrive via a Briefing or an Article. An existing account can use either channel without another registration.
- At first registration, `acquisition_source` is `articles` or `briefings`, read from new-account metadata and retained on the existing profile. Legacy `briefing_pdf` values are treated as Briefings.
- The owner back office displays computed internal `origin:articles` / `origin:briefings` labels and filters. **These are original signup channels, not evidence of all subsequently viewed content** and they do not alter mailing consent or preferences.
- Editorial marketing emails remain strictly optional; sign-up never implicitly opts readers in.
- Reader library now has an **Articles** tab beside Briefings, Saved, PDFs and Profile, with early-access and public status.
- Registered-reader counts in Public Analytics continue to count unique verified profiles, never one account per content format.

## Authentication redirect setup (required before merging)

Add both patterns to **Supabase Authentication → URL Configuration → Redirect URLs**. Retain existing reader and briefing URL patterns:

```text
https://jairribeiro-ai.streamlit.app/?page=thinking&article=*&access=1
https://jairribeiro-reader-test.streamlit.app/?page=thinking&article=*&access=1
```

New-account and returning-reader email codes work in the existing browser tab. Clicking a magic link from a new tab must pass the Supabase redirect allowlist to return to the selected Article. Verify the actual email templates still use `{{ .RedirectTo }}` / `{{ .TokenHash }}` and do not fall back to `localhost:3000`.

## Acceptance checks

1. Anonymous visits to a new Article show meaningful original executive summary, public metadata and access panel; *no full CMS HTML appears in the rendered Streamlit document*.
2. New registration from Article records one profile with `acquisition_source=articles`; a pre-existing Briefings account signs in and sees that full Article without another user row or lost existing origin.
3. Password and emailed OTP both unlock the *selected* Article and preserve same-WebSocket navigation to other Articles and Briefings.
4. At precisely `published_at + 168h`, anonymous Article readers get full text; changing `updated_at` does not restart the lock. Compare UTC and Stockholm around daylight-saving transitions.
5. Weekly AI and Executive Briefings access policies do not change.
6. The owner directory filters signup origin; marketing list still respects explicit prior consent. Public Analytics counts unique registered people.
7. Mobile UI, modal dismiss, back navigation, direct article permalinks, sitemap and social previews remain correct.
8. Validate an actual clicked link on both staging and production callback origin before publishing.

## Known security boundary

Like the existing Executive AI Briefings preview system, **this is a server-rendered presentation gate, not end-to-end content authorization**. Full `careersite_articles.content_html` may still be retrievable through the current publicly accessible CMS Data API or indexers. Do not describe it as secure DRM, paid/private distribution or a protected publisher paywall. A genuinely restricted publishing channel requires a separate anonymous CMS read policy/RLS, a metadata-only public query and an authenticated full-content fetch mechanism with a careful migration of existing Briefings, crawlers, analytics and authoring.
