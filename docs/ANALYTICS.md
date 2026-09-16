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

The application-owned event table does not contain IP addresses, user-agent strings, names, email addresses or free-form user input. Optional attribution is limited to:

- external referrer hostname;
- `utm_source` (or the shorter `src` parameter);
- `utm_campaign`.

This allows links sent in hiring workflows to be tagged without identifying the visitor personally. For example:

```text
?utm_source=linkedin&utm_campaign=volvo-dpo
```

or:

```text
?src=executive-search
```

## Shared event store

Both the Streamlit implementation and the Lovable implementation use the same Supabase table:

`public.careersite_analytics_events`

The browser uses a Supabase **publishable** client key. The enforcement boundary is Row Level Security:

- anonymous/public clients may `INSERT` valid whitelisted events;
- anonymous/public clients cannot `SELECT`, `UPDATE` or `DELETE` analytics data;
- reporting is performed through privileged database access rather than exposing analytics publicly.

Two private reporting views are maintained:

- `public.careersite_analytics_daily` — daily event/session counts by source, page and lens;
- `public.careersite_session_funnel` — per-session funnel flags for Home, Impact, lenses, CV download and outbound actions.

## Streamlit implementation

`src/site_analytics.py` injects a small browser client after the page is rendered. It:

1. records `page_view` for every valid page;
2. records `impact_view` when Leadership Impact is reached;
3. records `lens_view` when one of the four role lenses is reached;
4. maps CV, email, LinkedIn and article actions into the four corresponding click/download events;
5. suppresses immediate duplicate view events caused by Streamlit reruns;
6. preserves the existing `hq-conversion` browser event for local debugging/future integrations.

Internal Home → Impact and Home → lens clicks are not stored as separate click events. The destination view plus the ephemeral session ID provides a cleaner funnel signal without duplicate measurement.

## Lovable implementation contract

Lovable must use the same endpoint, table, taxonomy, privacy rules and per-tab session behavior, with `source='lovable'`. The implementation may be idiomatic TypeScript/React, but the measurement semantics must remain identical to Streamlit so the two deployments are comparable.

## Questions the data should answer

- Did the site receive visits from links used in hiring outreach?
- Which role lenses were actually opened?
- What proportion of Home sessions reached Leadership Impact?
- What proportion of sessions downloaded the CV?
- Which articles and outbound professional links were used?

The site intentionally does not implement heatmaps, session recordings, advertising pixels or broad product-analytics instrumentation.
