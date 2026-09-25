# Content intelligence release

Two bookmarkable reporting pages are available through the top menu:

- `?page=analytics&view=pages`: portfolio page views and existing site reports.
- `?page=analytics&view=articles`: article views and existing reading/share reports.

The additive database script is `sql/analytics_content_intelligence.sql`.
Apply it before deploying the browser collectors. Existing events and reporting
functions are retained. The aggregate endpoint follows the existing public
read-only reporting contract; the dashboard is unlisted, not authenticated.
Anonymous clients cannot read raw event records. No persistent visitor identity
is introduced.

## Added measurements

- Content/session visible time, with timing confirmed at five seconds.
- Maximum content exposure (scroll depth), sampled during visible activity.
- Halfway and bottom reach; deep-reading proxy: 30 seconds plus 90% exposure.
- Consecutive content transitions, first and last observed content.
- CV and contact actions observed after content opens in the same session.
- Source/campaign cohorts with readership, engagement and action rates.
- Aggregate CSV export and measurement coverage/freshness.

Views are separated using explicit content type on new events. Historical
Thinking page views cannot reliably be separated into index and article visits;
they remain in the established reports and are disclosed separately. New depth
and page-time fields are not backfilled. Missing depth displays as unavailable.

Article reading rates use article-session visits as their denominator. Contact
intent in the new overview deduplicates email and LinkedIn within a session.
Legacy stage reach is labeled as independent reach, not an ordered funnel.
Ranking charts select the top rows by the metric actually shown.

## Interpretation

Sessions are browser-tab sessions, not people. Visible time does not prove
attention, scroll does not prove comprehension, and share clicks do not prove
publication. Later actions indicate sequence, not causal attribution. Last
observed content is not a confirmed exit. Report boundaries can truncate journeys
and cumulative session timing may include time accrued before the boundary.

## Validation and rollback

Run `python -m unittest discover -s tests -q`. Tests cover dashboard route
separation, missing measurement labels, CSV safety, and executed browser code
for duplicate suppression, visible time, depth retention and share exclusion.
Database inserts and article-to-portfolio-to-CV fixtures were tested inside
rolled-back transactions. Revert the application commit to roll back the UI;
the additive columns and aggregate RPC may safely remain.


## Attention → action layer

The next additive layer starts with tracking version 4 and keeps all earlier reports.

- Article-card CTR uses card-visible sessions as the denominator.
- CTA CTR is split by placement and uses CTA-visible sessions as the denominator.
- Section reach uses page-viewing sessions as the denominator.
- Article reading progression now reports 25%, 50%, 75% and 90% exposure.
- Ordered Article → Leadership Impact → CV progression is separate from independent stage reach.
- Multi-article reading, time to first meaningful action, topic performance, equal-duration period comparison and first-seven-day publication performance are reported.
- Browser-side TTFB, LCP, CLS and maximum observed interaction duration are grouped by device so technical experience can be compared with engagement.
- Every displayed rate includes the underlying counts.

The additive database script is `sql/analytics_attention_action.sql`. It creates the v2 aggregate RPC while leaving the established aggregate RPC in place. Article metadata is supplied by the dashboard for aggregate topic/publication-age analysis; it is not used to create visitor profiles.

Exposure uses browser `IntersectionObserver`: sections count at 15% visibility and cards/CTAs at 50% visibility, once per anonymous tab session and placement. Performance measurements are document-level; Streamlit rerenders can share one browser navigation timing. Technical correlations are descriptive, not causal.


## Components-v2 behavior telemetry

Tracking version 5 adds an invisible Streamlit Components-v2 collector on public portfolio routes. It runs in the main app document and writes through the existing first-party analytics client.

New measurements:

- Visible dwell time by page section and article subheading region.
- Visible attention and hover time for article cards and CTAs.
- CTA hesitation from first visible exposure to click.
- Last observed reading region, scroll depth and coarse scroll-speed summaries.
- First-interaction latency by interaction type and device.
- Potential dead-click and rage-click signals without storing click coordinates.
- Browser JavaScript/rejected-promise error types without error messages or stack traces.
- FCP and an INP estimate from supported PerformanceEventTiming interaction IDs.
- Focus-loss, resize, orientation-change and coarse device-capability summaries.
- Section-assisted Impact, CV and contact sequences.

Privacy remains session-scoped: no cookies, persistent visitor IDs, cursor recordings, raw coordinates, form values or free-text capture are added. Click coordinates are used only transiently in browser memory to detect repeated clicks in the same small area.

The additive database script is `sql/analytics_behavior_telemetry_v5.sql`. It also repairs the v4 RLS INSERT-policy mismatch that could reject exposure/section/performance event names even though the table constraint accepted them.

Interpretation limits remain important: visible dwell is not proof of attention, hover is not intent, dead/rage clicks are diagnostic signals rather than confirmed frustration, and downstream actions are sequential associations rather than causal attribution.
