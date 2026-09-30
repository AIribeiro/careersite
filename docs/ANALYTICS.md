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
