# Weekly AI — latest published edition is Premium

## Corrected publication rule (12 November 2026)

The **newest published Weekly AI edition**, rather than the edition corresponding to the current ISO calendar week, is the complimentary Premium Reader issue. It remains available in full only to authenticated readers until a newer Weekly AI edition is **actually published**. As soon as a newer edition is published, the previous edition becomes public.

This is editorial release-based access, **not** a rolling seven-day expiry and **not** a Monday calendar unlock. The rule works during gaps in the publishing calendar, delayed Friday releases, year changes and week-number transitions. No scheduled unlock job is needed. Drafts and unpublished editions do not release the latest published issue. A metadata lookup outage fails closed for the requested published Weekly AI edition.

### Verified example

On 12 November 2026 (Stockholm, ISO week 46), the latest published Weekly AI in the CMS was **Week 45** (`weekly-ai-2026-11-06`, published 6 November 2026). No Week 46 edition was published. Therefore:

- **Week 45:** Premium Reader full edition (public summary)
- **Week 44 and earlier:** fully open without sign-in
- **When a Week 46 issue is actually published:** Week 45 becomes fully public and Week 46 becomes Premium

A delayed, skipped, or unpublished new edition must never open the current latest issue merely because Monday arrived.

## Other editorial access rules

- **Executive AI Briefings:** Full content requires the complimentary verified reader account.
- **Articles:** Registered-reader access during the first 168 hours after publication; then publicly open.
- **Weekly AI:** Latest **published** issue Premium; all earlier published issues publicly open.

## Reader experience

- Public preview exposes a bounded executive summary, never the full Weekly AI HTML or embedded media controls. It says access will open **when the next issue is published**, never promises Monday.
- Existing email verification and password sign-in unlock the complete latest issue with the same account and session as Briefings and Articles.
- The Weekly AI archive, Thinking featured card and My Library tab label the **Latest edition · Premium Reader** and older editions **Open access**.
- The featured current Premium issue does not advertise a direct audio link in the public HTML. Audio is available in the authenticated full-issue reader when supplied.
- New-account source attribution remains `origin:weekly_ai`; existing readers retain their original sign-up attribution, and mailing consent remains optional.
- The Premium Reader explanation below the Thinking hero stays fixed and focuses on executive value; only the three editorial collections are dynamically reordered.

## Acceptance tests

1. On 12 November 2026 with Week 45 published and Week 46 absent, Week 45 is Premium, Week 44 open.
2. On subsequent days with no newly published edition, Week 45 **remains Premium**.
3. Once Week 46 is published, Week 45 automatically becomes open and Week 46 Premium.
4. Drafts, year/week boundaries or outages never incorrectly expose the most recent live full text.
5. Anonymous HTML does not include restricted editorial body or audio player; registered readers access full issue.
6. Reader account, metadata labels and prior Article/Briefing rules remain unchanged.
7. Check live deployment and actual password/email-link return navigation after merging.

## Access security boundary

This is a **website presentation gate**, matching the site's current Article/Briefing approach. Full text remains obtainable via the public CMS Data API; narrated MP3 files also remain publicly downloadable from repository/CDN paths. Actual private content delivery requires restricted backend APIs and storage for both body and audio. Do not describe this as DRM or a true paywall.
