# Privacy-conscious website analytics

The site uses a first-party behavioral analytics layer to understand hiring-site usage without heatmaps, session replay, advertising identifiers, raw IP storage or persistent cross-session visitor tracking.

## What is measured

The event taxonomy is intentionally small:

- `page_view`
- `impact_view`
- `lens_view`
- `cv_download`
- `email_click`
- `linkedin_click`
- `article_click`
- `engagement_ping`

`engagement_ping` is a lightweight session-quality event used to keep active/visible time current. It is excluded from the visible event-activity table so it does not inflate behavioral actions.

Alongside events, the application stores coarse session context that is useful for site decisions:

- device class: desktop, mobile or tablet;
- browser family and operating-system family, derived in the browser without storing the raw user-agent string;
- browser language and IANA timezone;
- viewport and screen dimensions;
- effective connection class when the browser exposes it;
- elapsed session time and active visible/engaged time;
- external referrer hostname when available;
- source/role attribution from campaign links;
- a two-letter country code only when the hosting/API infrastructure supplies a trusted coarse country header.

The reporting layer derives additional metrics from those fields, including pages per session, landing and exit pages, engagement rate, single-page sessions, duration bands, hour-of-day and day-of-week patterns.

## Privacy model

The application does **not** write analytics cookies and does not use `localStorage` for analytics. A random UUID is kept in browser `sessionStorage` only for the lifetime of the current tab/session. The same per-tab storage holds the session start time, accumulated engaged time and optional job-search attribution.

The application-owned event table does not store raw IP addresses, raw user-agent strings, names, email addresses or free-form visitor input. Country is not obtained through a third-party IP lookup. If the API infrastructure does not provide a recognized country header, country remains unknown.

This makes it possible to measure a Home → Leadership Impact → CV-download journey and session quality without creating a durable visitor profile across visits.

## Job-search attribution links

The preferred parameters are:

- `source` — the job-search activity that generated the visit;
- `role` — optional mandate/application label.

Recommended source labels:

- `linkedin`
- `email`
- `cv`
- `outreach`
- `application`

`email` is intentionally separate from `outreach`. Use `source=email` for links placed in ordinary email signatures, email footers, direct email introductions, or other email-originated traffic when the goal is to measure email as the channel. Use `source=outreach` for deliberate recruiter/network outreach campaigns where the activity itself is what should be measured.

Examples:

```text
https://jairribeiro-ai.streamlit.app/?source=linkedin
```

```text
https://jairribeiro-ai.streamlit.app/?source=email
```

```text
https://jairribeiro-ai.streamlit.app/?source=cv
```

```text
https://jairribeiro-ai.streamlit.app/?source=outreach
```

```text
https://jairribeiro-ai.streamlit.app/?source=application&role=ai-transformation
```

Attribution identifies a job-search activity, not a person. Avoid putting recruiter names, company contact names, email addresses or other personal identifiers in these parameters.

Legacy `utm_source`, `src` and `utm_campaign` parameters remain accepted for compatibility. When `source` is present it is the preferred hiring-attribution label.

## Campaign source classification (October 2026)

Not all sessions can be attributed. Missing source parameters, direct navigation,
bookmarks, stripped referrers, in-app browsers, and redirects can produce
`direct/unknown` observations. **Never assign such sessions to LinkedIn,
WhatsApp, search, or any other channel without evidence.** Historical raw
analytics are preserved.

The CMS now includes an authenticated **Distribution links** generator. Use it
for deliberate portfolio sharing, including articles, Daily Quotes, WEEKLY AI,
CV links and introductions. It preserves destination routes and creates:

- `source` and `utm_source` — canonical channel (`linkedin`, `threads`,
  `x`, `facebook`, `whatsapp`, `email`, `cv`, `outreach`, `application`);
- `utm_medium` — channel class (`social`, `messaging`, `email`, etc.);
- `utm_campaign` — publication or distribution series (e.g. `dailyquote`,
  `weekly_ai_2026_w42`, `thinking`);
- `utm_content` — the selected article slug when available.

The built-in CMS article sharing links for LinkedIn, X and email now use the
same tagged URLs. Copying a permanent article URL **does not** imply a known
future distribution channel and therefore remains untagged. Static social
preview bridges retain their existing source-specific links.

Report *tagged first-touch coverage* in subsequent periods, not the share
of historical sessions that can be guessed into new buckets. Compare
equivalent time windows and avoid treating a higher tagged fraction alone as
proof of increased real readership.

## Forward attribution coverage (activated 16 October 2026)

The event store records the optional `utm_medium` field, bounded to 32
lowercase letters, digits, underscores or hyphens. Both normal page views
and article reads capture the field when a visitor follows a tagged URL and
retain it only within the existing browser-tab session.

The authenticated **Analytics → Private analytics → Attribution quality**
dashboard uses an owner-only aggregate RPC and a database activation
timestamp. Historical events are not edited or backfilled. Only sessions
whose first observed event occurred on or after the activation timestamp
are eligible; one session is counted once, at its first recorded page or
article view. Explicit test sessions and telemetry-only sessions are
excluded.

The dashboard separates mutually exclusive source evidence:

- **Explicitly tagged** — a channel was declared in the URL;
- **Referrer-only** — no explicit tag, but an external referrer hostname exists;
- **Unknown** — neither source evidence type exists.

**Identifiable coverage** equals (explicitly tagged + referrer-only) /
eligible new content sessions. **Tagged medium completeness** equals
explicitly tagged first-content sessions with `utm_medium` divided by
all explicitly tagged first-content sessions. Campaign completeness uses
the same denominator with `utm_campaign`. Daily trends use the configured
Europe/Stockholm reporting date. Small cohorts receive an explicit caveat;
missing data is not silently turned into a zero-based growth rate.

The existing CMS link builder already produces channel, medium and
campaign tags for deliberate distribution. Search, bookmarked, referrer-
stripped and otherwise unattributed visits are never assigned to channels
without verification. The owner-only reporting RPC has no raw-row or
session-ID output, and public visitors cannot execute it.

## Shared event store

Both the Streamlit implementation and the Lovable implementation use the same Supabase table:

`public.careersite_analytics_events`

The browser uses a Supabase **publishable** client key. The enforcement boundary is Row Level Security:

- anonymous/public clients may `INSERT` only valid whitelisted events and bounded analytics fields;
- anonymous/public clients cannot `SELECT`, `UPDATE` or `DELETE` analytics data;
- reporting is performed through controlled database access rather than exposing raw analytics publicly.

The database also enriches inserts with a coarse country code if a recognized infrastructure country header is present. It does not persist the request IP address.

Reporting structures include:

- `public.careersite_analytics_daily` — daily event/session counts including attribution dimensions;
- `public.careersite_session_funnel` — per-session funnel flags plus source/role attribution;
- `public.careersite_analytics_dashboard(...)` — access-code-protected aggregate reporting used by the hidden Streamlit dashboard.

Raw event rows are not exposed through the dashboard.

## Streamlit implementation

`src/site_analytics.py` injects a small browser client after each public page is rendered. It:

1. records `page_view` for every valid public page;
2. records `impact_view` when Leadership Impact is reached;
3. records `lens_view` when one of the four role lenses is reached;
4. maps CV, email, LinkedIn and article actions into the corresponding conversion events;
5. captures `source` and optional `role` from attributed entry links;
6. derives coarse device/browser/OS context without retaining the raw user-agent;
7. records language, timezone, viewport/screen dimensions and browser connection class when available;
8. accumulates active visible time in the current tab and sends periodic `engagement_ping` updates;
9. persists analytics state only within the current tab/session;
10. suppresses immediate duplicate view events caused by Streamlit reruns;
11. preserves the existing `hq-conversion` browser event for local debugging/future integrations.

Internal Home → Impact and Home → lens clicks are not stored as separate click events. The destination view plus the ephemeral session ID provides a cleaner funnel signal without duplicate measurement.

## Private analytics dashboard

The Streamlit deployment includes a hidden reporting route:

```text
https://jairribeiro-ai.streamlit.app/?page=analytics
```

It is intentionally absent from public navigation and marked `noindex,nofollow,noarchive`.

The dashboard uses a fixed public-readonly aggregate token. Raw analytics rows remain inaccessible to anonymous clients; the reporting RPC returns aggregates only and is the read boundary for the hidden dashboard.

The dashboard shows:

- measured sessions and engagement rate;
- average and median session duration;
- average active/engaged time;
- pages per session and single-page sessions;
- Home → Leadership Impact → role-lens → CV/contact funnel behavior;
- device class, browser family and operating-system family;
- country when infrastructure data is available, plus browser language and timezone;
- referrers, source/role attribution, landing pages and exit pages;
- session-duration distribution;
- daily activity, hour-of-day and weekday patterns;
- role-lens usage and conversion event activity;
- an attribution-link builder for LinkedIn, email, CV, outreach and application sources.

An engaged session is defined as at least 10 seconds of active visible time, two or more pages, or a conversion action such as a CV download or outbound professional/contact click.

## Audience quality and hiring evidence

Tracking version 5 adds a reporting-quality layer on top of the raw event store. Raw rows are retained unchanged; classification is applied only when analytics are aggregated.

The quality model separates:

- **Recorded v5 sessions** — all tab-session IDs that emitted v5 telemetry in the selected window.
- **Valid content view** — non-test sessions with at least one content view before automation filtering.
- **Telemetry only** — sessions with no valid content view. These are measurement-invalid for audience/behavior interpretation and can occur when a background telemetry lifecycle outlives the content-view lifecycle.
- **Suspected automation** — a deliberately narrow repeated-signature cohort heuristic: at least 10 sessions with the same coarse technical signature, zero recorded interactions, zero recorded actions and cohort average active time below 10 seconds.
- **Explicit test** — deliberately tagged traffic such as `?source=application&role=test`.
- **Analysis eligible** — valid content-view sessions after explicit tests and suspected-automation cohorts are excluded.

The automation label is a reporting heuristic, not proof that an individual session is a bot. Signature evidence is evaluated across the full v5 history and then applied to the selected reporting window, preventing a known synthetic cohort from being re-admitted simply because only a few of its sessions occurred in the last hour. The implementation does not create a durable visitor fingerprint: the signature is built from already-collected coarse session fields and is used only in aggregate reporting.

Hiring behavior is also separated by intent:

1. **Exploration** — internal evidence-seeking actions such as opening Leadership Impact or an article card.
2. **Evidence verification** — explicit credential verification or opening the external LinkedIn credential record.
3. **Hiring intent** — CV download, email action or LinkedIn profile exit outside the credential-verification context.

The dashboard presents an evidence progression of **Analysis eligible → Evidence reached → Evidence engaged → Evidence verified → Hiring intent**. General engagement is shown separately because a visitor can reach a specialist evidence page quickly without first crossing a 10-second engagement threshold.

Source labels that begin with `linkedin` (for example `linkedin` and `linkedin_launch`) roll up to the parent channel **LinkedIn** for decision-making. The original source/campaign values are retained beneath that roll-up for diagnostics.

The aggregate implementation is `public.careersite_hiring_intelligence_v1(...)`, versioned in `sql/analytics_hiring_intelligence_v1.sql`.

## Internal production checks versus real audience (November 2026)

The site runs a Playwright headless Chromium production smoke test on qualifying pushes to the main branch. This is useful for finding broken public routes, missing assets and navigation regressions. It is **not reader activity**.

- Browser QA passes `source=internal_qa&role=smoke` on each real page navigation. The collector retains its events for diagnosis.
- A coarse `browser_automation` boolean records `navigator.webdriver === true` without persisting a raw user agent, IP address or cross-session identity.
- Earlier internal smoke runs with the exact documented navigation sequence are marked by `public.careersite_internal_qa_sessions_v1`; repeated US/UTC/Linux/Chrome sessions with one page view, no actions and <=10 seconds active time are **suspected automation**, not definitively identified visitors.
- Audience, article, library, lifetime, popularity and engagement reporting read from `public.careersite_reporting_events_v1`. This view excludes the internal QA tags, identified historical QA sessions and high-confidence automation signals, while the event table remains untouched.
- The aggregate-only `public.careersite_traffic_quality_audit_v1` reports **recorded**, **internal QA**, **suspected automation** and **unclassified** sessions. Unclassified traffic is *not* a verified-human count; undetected bots remain possible.
- The two evidence tables are RLS-protected and unavailable for anonymous direct reads. The reporting view is `security_invoker=true` and not directly exposed to readers.

These categories are intentionally conservative and will change as better server-side verification becomes available. The source-tag distinction is for analytics quality, not authentication or security access control. Site QA must not be disabled simply to improve a traffic chart.

## Reliable Year and lifetime portfolio overview (14 November 2026)

The public **Visits & reads** overview uses `careersite_portfolio_overview_fast_v1`
for **This year** and **All**. This dedicated SQL aggregate counts canonical
`page_view` and `article_view` events from
`careersite_reporting_events_v1`, retaining internal-QA and suspected-automation
exclusions and the reporting reset baseline. It returns page/article/legacy
Thinking view totals, distinct site/content sessions and per-content ranking
rows. It does **not** run the detailed behavioral telemetry analysis.

The heavier `careersite_content_intelligence_v2` remains available under
**Explore content**, where attention, source and journey detail is relevant.
That report is cached for 120 seconds to reduce simultaneous broad-window
queries. The overview's `Refresh insights` action explicitly clears
the caches.

The dedicated report was reconciled against the established Year aggregation
for site views, page views, article views, legacy Thinking views and
site/content session totals. Do not substitute unfiltered raw event counts
or legacy `careersite_content_intelligence` as a fallback: the legacy query
can be costly on broad windows.

## Collector integrity controls

When a 30-minute session timeout creates a new session on the same open document, the document-level view guard is cleared so the new session can record its own `page_view`. This prevents background behavior summaries from becoming telemetry-only sessions simply because the document remained open.

Repeated JavaScript errors and unhandled promise rejections are deduplicated by page/context, error type and section within the current telemetry context. This keeps a single looping browser error from dominating the UX-signal counts.

## Lovable implementation contract

Lovable should use the same endpoint, table, event taxonomy, attribution parameters, session semantics and privacy rules, with deployment `source='lovable'`. The implementation may be idiomatic TypeScript/React, but the measurement semantics should remain comparable to Streamlit.

## Questions the data should answer

- Did the site receive visits from links used in hiring outreach?
- Which channels and role-specific links generated deeper investigation?
- Are visitors primarily mobile, tablet or desktop?
- Which browser/OS combinations account for meaningful traffic?
- Where is traffic coming from at a coarse country/timezone/language level?
- How long do sessions last, and how much of that time is actively engaged?
- How many pages are viewed per session, and which pages tend to be entry and exit points?
- What proportion of Home sessions reach Leadership Impact or a role lens?
- What proportion of sessions download the CV or click contact/professional links?
- Which days and hours show the most activity?
- Do selected application links produce stronger engagement than generic LinkedIn/CV traffic?

The site intentionally does not implement heatmaps, session recordings, advertising pixels, raw-IP retention, raw-user-agent retention or durable visitor fingerprinting.

## Executive Briefings editorial analytics (2 November 2026)

Portfolio Analytics now has **four** overview cards: **Portfolio visits**, **Articles**, **Weekly AI**, and **Executive Briefings**, all controlled by the same reporting-period selector (including Yesterday). Both the anonymous Explore content focus and the authenticated owner Portfolio Analytics > Content & readers focus offer a dedicated **Executive Briefings** report. No new database table, tracking event, visitor ID or cookie is created.

The published Content Studio catalogue determines the classifications:

- **Portfolio visits** are existing page-view events, including the `briefings` library. The library is a *page*, not an extra article.
- **Articles** exclude published `Weekly Brief` / `Weekly AI` and `Executive Briefing` entries.
- **Weekly AI** only counts published verified weekly issues.
- **Executive Briefings** only count published CMS entries with `kind='Executive Briefing'`; newly published briefings appear without hardcoded slugs. Unpublished drafts never appear as published content. If the CMS catalogue is unavailable, the three classified reading categories display unavailable values, not guessed zeros.

Each reading category reuses the `careersite_content_intelligence_v2` first-party `article_view` rows, classified by slug. **Articles + Weekly AI + Executive Briefings = the same existing article-view total**, if the catalog and per-content report reconcile. Reading one briefing and one article in a browser session produces one item-session in each category; it does not establish two distinct users. Library page views already belong to the portfolio-page total and must not be added to reading views or site visitors.

The Executive Briefings detail uses existing per-content aggregates and instrumented `briefings-library` / `home-executive-briefings` section reach and briefing-card exposures/clicks. Its four primary measures are library visits, published-briefing item-session reads, engaged-read rate (active ≥10 seconds) and *subsequent within-session contact actions*, where the last is **not** evidence of a causal conversion. The detail also shows card exposure-based CTR, item views, measured read depth, shares, later CV actions, a comparative readership chart and a link to each individual published briefing. Scroll rates use only observed depth denominators; average confirmed time may be unavailable. Direct visitors can bypass the library; discovery and readership are *not* a linear funnel.

All measures respect the current reporting window, established test-traffic and attribution exclusions. Historic periods cannot retroactively acquire card impressions that were not instrumented. The dashboard does not identify people or infer recruiter interest. If reporting is unreachable, display an explicit unavailable state rather than claiming no traffic.

## Entry address, subdomains and campaign attribution (13 November 2026)

The entry-address report has two **top-level reporting families**:

- `jairribeiro.com` covers the root domain and every verified branded
  subdomain (`www.jairribeiro.com`, `go.jairribeiro.com`,
  `readers.jairribeiro.com`, future `*.jairribeiro.com` addresses).
  The browser records the **exact** hostname in `entry_domain`, and the
  dashboard lists each verified branded hostname beneath the family total.
  Each visit counts **once** in the branded total; the hostname split is
  a breakdown, not an extra set of visits.
- `jairribeiro-ai.streamlit.app` covers the verified native Streamlit
  address and all historical or unresolved events *assigned* to the native
  reporting group. Exact hostname is never inferred from old data; the
  RPC exposes `assigned_views`, `assigned_sessions`,
  `verified_views` and `verified_sessions` separately.

Hostname checks use exact suffix boundaries, not substring matching.
`go.jairribeiro.com.evil.tld` and `eviljairribeiro.com` are not treated
as branded. Insert-side RLS and table constraints permit only the canonical
Streamlit native hostname or valid `*.jairribeiro.com` hostnames,
up to DNS hostname length limits. Old event records are not rewritten.

The browser collector uses the real top-level hostname for direct visits,
and the highest available verified branded iframe ancestor origin or
the iframe's embedding referrer when masked. Neither is guaranteed on all
browsers: frames that hide their parent remain unresolved. The wrapper
host is **not** an external acquisition referrer.

The entry-domain RPC includes a per-host session/view breakdown, per-host
tagged/direct/external-source session counts, and a capped aggregate campaign
table. It reports `source` and `utm_source` **as separate declared
signals**. For example:

```text
https://go.jairribeiro.com/?page=briefing&article=ai-governance-explained-to-executives&source=linkedin&utm_medium=social&utm_campaign=masked_test_20261113&utm_content=ai-governance-explained-to-executives&utm_source=chatgpt.com
```

Given those parameters *reaching the browser collector*, the recorded
`entry_domain` is `go.jairribeiro.com` (when verified by host/ancestor
or referrer), `attribution_source` is `linkedin`,
`utm_source` is `chatgpt.com`, `utm_medium` is `social`, and the
campaign/content remain as supplied. The host contributes to the
`jairribeiro.com` family total.

The iframe URL remains the primary source of campaign parameters. If it
does not contain them, the collector can recover known marketing tags
from the embedding referrer **only when** the browser exposes the full
verified branded referrer URL. Standard cross-origin referrer policies
often return only the origin, and `ancestorOrigins` never contains query
parameters. If a domain-masking service discards the campaign query from
the iframe URL and hides the full wrapper referrer, those parameters
**cannot be recovered** through Streamlit's frame; attribution stays
unknown rather than invented. Ensure the masking provider forwards all
URL parameters or use native custom-domain hosting.

The report is aggregate-only: it returns no raw session identifiers,
visitor identities, browser IPs or raw referrer URLs. It reuses existing
reporting periods, canonical content-view rules, and test exclusions.
