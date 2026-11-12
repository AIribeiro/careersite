# Weekly AI — current-week complimentary Premium Reader access

## Editorial rule

The **edition covering the current ISO 8601 calendar week in Europe/Stockholm** is the Premium Reader edition. Anonymous visitors see a useful summary derived from the published text and can sign in or register for free to see the full issue. Premium Reader status is calculated from the Weekly AI edition's existing `edition_week()` semantics, not merely its publication timestamp.

At **Monday 00:00 Europe/Stockholm immediately following the covered week**, that edition becomes completely public. This is **not a rolling seven-day lock**. A Friday issue is Premium Friday–Sunday; earlier editions are always open even if the next Friday issue has not been published. The rule handles ISO-year rollover and Stockholm DST transitions, and does not require a scheduled job.

Other membership rules remain unchanged:
- Executive AI Briefings: full content requires registration.
- Articles: first 168 hours after publication require registration, then open to all.
- Weekly AI: current covered calendar week requires registration, then open to all.

## Experience

1. Thinking's fixed Premium Reader section now describes **all three** editorial benefits. Hourly ordering only moves the three editorial collections, never the reader section.
2. Current Weekly AI opens to a credible public summary with the week's editorial question and a bounded extract from the actual published edition. Full story collection, source links, leadership signal and embedded audio player are not in that anonymous HTML.
3. The **same** account works for Weekly AI, Articles and Executive AI Briefings: email verification or password, verified account controls, single session, and profile.
4. The library offers a separate Weekly AI tab with current Premium and earlier open editions, preserving existing Briefings, Articles, Saved, PDFs and Profile tabs.
5. The Weekly AI catalogue and public archive label the current issue **Premium this week** and older weeks **Open access**. The latest featured Weekly AI suppresses its direct audio link during the Premium week and links to its public summary instead.
6. New registrants from Weekly AI have immutable `acquisition_source=weekly_ai` and computed back-office tag `origin:weekly_ai`. Existing profiles are not re-attributed or duplicated. All mailing follows explicit consent and suppression settings.
7. No payment details are requested.

## Authentication callback prerequisites

As with Article access, allowlist your first-party `?page=thinking&article=*&access=1` URL patterns in Supabase Auth Redirect URLs for the production and staging Streamlit hosts. Verify password, email code and emailed-link sign-in on desktop/mobile, including session continuity when navigating to the next article or briefing.

## Release criteria

- Verify **current** Friday and Sunday 23:59 Stockholm access remains Premium.
- Verify Monday 00:00 Stockholm opens last week's full issue without login, including its audio player.
- Verify anonymous current-week rendered HTML has no full CMS article body and no `<audio>` or media URL.
- Verify registered access to the selected issue and all previously open weeks without additional registration.
- Verify the original public archive, automatic Thinking section ranking and Briefings/Articles access rules still work.
- Verify new registration source and consent remain separate.
- Confirm live deployment independently; code merge and CI do not prove that external masked-domain routes or email links are correct.

## Security boundary

This extends the website's **presentation-level member gate**, as used by Articles and Briefings. The underlying Supabase CMS Data API currently returns full `content_html` through public reads, and Weekly AI MP3 files are available from public repository/CDN media URLs. The public preview does not link to the current narration, but this does **not** prevent direct access to those public files. Real restricted publication would require private content storage and a backend authorization-controlled delivery path for both text and audio, plus a review of social/indexer flows. Do not market this as encryption, DRM or a paywall.
