# Portfolio Analytics — public Advanced Insights

Updated: 6 November 2026

## Default public experience

The public URL is `/?page=analytics&view=overview`. The four summary cards
are followed immediately by **Advanced Insights**, with twelve directly
clickable, horizontally scrollable tabs. No toggle, owner login or dropdown
is needed. The active tab alone is rendered, using Streamlit's stateful
`st.tabs(on_change="rerun")` API and its `.open` property; switching tabs
does not fetch every reporting RPC.

All tabs are executive-style analytical dashboards: KPI scorecards, visual
rankings, ratio comparisons, evidence-based diagnostic callouts, and measured
denominator notes. **No default raw data tables** are displayed. Counts and
measurement context appear in tooltips and captions.

## Scope and sources

| Public report | Data source | What is measured |
| --- | --- | --- |
| Executive findings | `careersite_analytics_dashboard_v2` | Guarded traffic movements, source ambiguity, timing coverage, device differences, recorded journeys/actions |
| Traffic overview | Same | Session trend, page exploration, recorded-session funnels, top lenses |
| Audience | Same | Devices, browsers, OS, countries, languages, time zones |
| Discovery paths | Same | Broad first-touch channels, landing and exit pages, destinations |
| Engagement | Same | Active-time buckets, hour/weekday distribution, engagement by device |
| Actions & conversions | Same | Event cohorts, CV/contact interactions, exploration depth |
| Channel outcomes | Same | Grouped channel session volume, observed engagement and observed article/CV reach |
| Content & journeys | `careersite_content_intelligence_v2` | Article reading, multi-article sessions, content transitions, section reach, ordered journeys |
| CTA opportunities | Same | Exposure versus click-session counts and high-exposure/zero-recorded-click diagnostics |
| Site performance | Same | Device-level p75 LCP, TTFB, CLS and slow-measurement shares |
| Attention & friction | `careersite_behavior_intelligence` | Aggregated error categories, measured section attention, CTA hover/attention, browser focus-loss context |
| Data quality | Dashboard + content RPC | Timing confirmation, measurement cohort coverage and non-comparable collectors |

Existing overview content signals and the dedicated Explore Content,
Executive Briefings, and Weekly AI views remain unchanged. This feature adds
decision-oriented reporting, not a parallel tracking system.

## Definitions and safe inferences

- **Session**: browser-tab/collector session, not a unique person. Session
  definitions differ across traffic, content and behavior RPCs. Never add their
  totals or use one collector's total as another's denominator.
- **Recorded engagement**: session engagement as reported by that specific
  collector, not verified human attention.
- **Channel**: first-touch source cohorts grouped into LinkedIn, CV distribution,
  Search, Email/newsletter, Other social, Direct/unattributed and Other sources.
  Raw source/role/campaign labels are discarded before rendering.
- **Completed-week comparison**: most recent seven complete Stockholm dates
  versus the preceding seven complete dates, excluding today. Display the
  relative change only with a prior count of at least 20, and only if the
  selected reporting period includes both weeks.
- **CTA click/exposure**: an observed relationship between two instrumentation
  counts. Do not call it an experimental conversion rate; coverage can differ.
- **Reader path**: consecutive *observed* content views within a tab; navigation
  clicks alone do not prove page arrival.
- **Scroll/section reach**: reported only with its measured denominator and
  unavailable when sample is too small. Older content may not have been tracked
  at all.
- **Site performance**: retrospective browser metrics. The p75 view needs at
  least ten measured sessions, while priority alerts need thirty. P75 LCP
  and CLS may differ from up-to-date experience after a deployment.
- **Browser behavior**: only aggregates. Error sessions across categories can
  overlap; focus losses may be normal user multitasking. Hover is not reliable
  on touch devices.
- **Privacy**: no raw IP address, user agent, session ID, visitor identity,
  employer inference, private recruiting records, campaign-role labels or
  owner JWT is rendered. The public route uses `public_analytics_rpc_headers()`
  and only RPCs already granted to `anon`.

## Architecture and performance

- `src/page_public_portfolio_overview.py` shows the four cards, then
  Advanced Insights by default; earlier navigation-route observations are
  visualized as a ranked chart, not a table.
- `src/page_public_legacy_insights.py` is the internally named compatibility
  module. Its public heading is **Advanced Insights**, and twelve stateful
  tabs remain visible on every visit. Only the active tab renders.
- `src/page_public_legacy_intelligence.py` delivers the source, content,
  CTA, performance, attention and measurement dashboard panels. Reusable
  KPI strips, ranked charts and evidence/next-check notes are used instead
  of dataframes.
- `src/portfolio_legacy_signal_model.py` calculates evidence-gated insights
  without access to visitor or recruiting records.
- Browser session aggregates, content observations and behavior observations
  have independent five-minute caches. Content/behavior RPC calls occur
  only when their relevant tab is selected.
- **Refresh advanced insights** invalidates the three report caches.
  No new data collection, database rights or historical event changes.
- Owner-only career reporting remains protected. Do not reveal exact campaign
  or relationship labels in public reporting.

## Validation checklist

1. Open the Analytics overview signed out: four summary cards should be
   followed immediately by **Advanced Insights** tabs. No toggle or dropdown.
2. Switch among all twelve tabs. Each contains KPI/chart/interpretation
   presentation, not `st.dataframe` or `st.table` output.
3. Confirm mobile tab navigation scrolls horizontally and the page renders
   only the selected tab's expensive content/behavior RPC.
4. Check selected periods, empty states, no-data labels and measured
   denominators. In particular, do not present missing observations as zero.
5. Verify source-channel grouping and absence of private job/campaign records.
6. Run `PYTHONPATH=src python -m pytest tests/test_public_legacy_analytics_toggle.py tests/test_portfolio_legacy_signal_model.py`
   in a repository environment with the test dependencies installed.
7. Verify Streamlit Cloud deployment after the latest GitHub commit.
   GitHub commits alone do not confirm that the live application has updated.

### Current observed limitations

The historical dataset contains a substantial direct/unattributed share, some
unconfirmed durations and uneven content measurement onset in September 2026.
The six-destination navigation redesign on 23 October 2026 also changes which
routes should be compared. Prefer complete periods and quote measured
denominators before proposing site changes.
