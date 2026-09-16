# Privacy-conscious website analytics

The site uses a deliberately small first-party behavioral analytics layer so hiring behavior can be evaluated without heatmaps, session replay, advertising identifiers or persistent visitor tracking.

## What is measured

Only these seven events are stored:

- `page_view`
- `impact_view`
- `lens_view`
- `cv_download`
- `email_click`
- `linkedin_click`
- `article_click`

No raw `data-hq-event` name is stored. Existing UI event tags are mapped into this reduced taxonomy.

## Privacy model

The application does **not** write analytics cookies and does not use `localStorage` for analytics. A random UUID is kept in browser `sessionStorage` only for the lifetime of the current tab/session. That makes it possible to answer questions such as Home → Leadership Impact → CV download without creating a durable cross-session profile.

The application-owned event table does not contain IP addresses, user-agent strings, names, email addresses or free-form visitor input.

Job-search attribution also lives only for the current browser tab/session. When an attributed landing URL is opened, the source and optional role are copied into `sessionStorage` so subsequent internal navigation and conversion events keep the same attribution even after the query string changes.

## Job-search attribution links

The preferred parameters are:

- `source` — the job-search activity that generated the visit;
- `role` — optional mandate/application label.

Recommended source labels:

- `linkedin`
- `cv`
- `outreach`
- `application`

Examples:

```text
https://jairribeiro-ai.streamlit.app/?source=linkedin
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

External referrer hostname is also retained when available.

## Shared event store

Both the Streamlit implementation and the Lovable implementation use the same Supabase table:

`public.careersite_analytics_events`

The browser uses a Supabase **publishable** client key. The enforcement boundary is Row Level Security:

- anonymous/public clients may `INSERT` valid whitelisted events;
- anonymous/public clients cannot `SELECT`, `UPDATE` or `DELETE` analytics data;
- reporting is performed through controlled database access rather than exposing raw analytics publicly.

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
4. maps CV, email, LinkedIn and article actions into the four corresponding click/download events;
5. captures `source` and optional `role` from attributed entry links;
6. persists attribution only within the current tab/session;
7. suppresses immediate duplicate view events caused by Streamlit reruns;
8. preserves the existing `hq-conversion` browser event for local debugging/future integrations.

Internal Home → Impact and Home → lens clicks are not stored as separate click events. The destination view plus the ephemeral session ID provides a cleaner funnel signal without duplicate measurement.

## Private analytics dashboard

The Streamlit deployment includes a hidden reporting route:

```text
https://jairribeiro-ai.streamlit.app/?page=analytics
```

It is intentionally absent from public navigation and marked `noindex,nofollow,noarchive`.

The dashboard requires a separate analytics access code. Authentication is enforced by the database reporting function; the public repository does not contain the access code or raw analytics read credentials.

The dashboard shows:

- total measured sessions;
- Home → Leadership Impact progression;
- role-lens usage;
- CV-download conversion;
- event activity;
- source/role attribution performance;
- daily trends;
- a simple attribution-link builder.

## Lovable implementation contract

Lovable must use the same endpoint, table, taxonomy, attribution parameters, privacy rules and per-tab session behavior, with deployment `source='lovable'`. The implementation may be idiomatic TypeScript/React, but the measurement semantics must remain identical to Streamlit so the two deployments are comparable.

## Questions the data should answer

- Did the site receive visits from links used in hiring outreach?
- Which job-search activity generated deeper investigation?
- Which role lenses were actually opened?
- What proportion of Home sessions reached Leadership Impact?
- What proportion of sessions downloaded the CV?
- Do selected application links produce stronger engagement than generic LinkedIn/CV traffic?
- Which articles and outbound professional links were used?

The site intentionally does not implement heatmaps, session recordings, advertising pixels or broad product-analytics instrumentation.
