# Portfolio Analytics — public legacy insights and expanded intelligence

Updated: 6 November 2026

## Public access

The public URL remains `/?page=analytics&view=overview`. The four overview
cards come first. A native **Show legacy visitor analytics** toggle appears
immediately beneath them for anonymous and authenticated users. It is off on
first render to protect site performance. Selecting the toggle reveals twelve directly clickable horizontal
**Streamlit tabs**, scrolling sideways on smaller screens. Tabs use
`on_change="rerun"` and their `.open` state to render only the selected
report, not all twelve panels on every interaction. No owner login, CMS
access or hiring pipeline permissions are required to read the aggregate
portfolio reports.

## Scope and sources

| Public report | Data source | What is measured |
| --- | --- | --- |
| Executive findings | `careersite_analytics_dashboard_v2` | Guarded traffic movements, source ambiguity, timing coverage, device differences, recorded journeys/actions |
| Traffic overview | Same | Session trend, page exploration, legacy funnels, top lenses |
| Audience | Same | Devices, browsers, OS, countries, languages, time zones |
| Discovery paths | Same | Broad first-touch channels, landing and exit pages, destinations |
| Engagement | Same | Active-time buckets, hour/weekday distribution, engagement by device |
| Actions & conversions | Same | Event cohorts, CV/contact interactions, exploration depth |
| Channel outcomes | Same | Grouped channel session volume, observed engagement and legacy article/CV reach |
| Content & journeys | `careersite_content_intelligence_v2` | Article reading, multi-article sessions, content transitions, section reach, ordered journeys |
| CTA opportunities | Same | Exposure versus click-session counts and high-exposure/zero-recorded-click diagnostics |
| Site performance | Same | Device-level p75 LCP, TTFB, CLS and slow-measurement shares |
| Attention & friction | `careersite_behavior_intelligence` | Aggregated error categories, measured section attention, CTA hover/attention, browser focus-loss context |
| Data quality | Dashboard + content RPC | Timing confirmation, measurement cohort coverage and non-comparable collectors |

Existing overview content signals and the dedicated Explore Content,
Executive Briefings, and Weekly AI views remain unchanged. This feature adds
historical intelligence, not another data source or parallel tracking system.

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

- `src/page_public_portfolio_overview.py` owns the off-by-default toggle.
- `src/page_public_legacy_insights.py` preserves the five historical reports,
  adds stateful, lazily rendered tabs and caches public traffic aggregates for five minutes.
- `src/portfolio_legacy_signal_model.py` contains pure evidence-gated
  calculations. No Streamlit or database dependencies.
- `src/page_public_legacy_intelligence.py` renders deeper reports; content
  and behavior aggregates each have separate five-minute caches and load only
  on the matching selected section. It sends an empty metadata array instead
  of performing additional CMS article discovery.
- The **Refresh legacy reports** control invalidates all three caches and
  reruns the selected view. It does not alter collected events or database rows.
- No schema grants, policies, source tables, historical data, or existing
  four-card metric definitions were changed.

## Validation checklist

1. Open the Analytics overview while signed out. Confirm four summary cards
   appear and the toggle is directly underneath them.
2. Turn it on. Confirm Executive findings renders and each of the twelve
   selector options opens without owner authentication.
3. Select **All** and compare with a narrow calendar reporting period. Check
   empty states, completed-week eligibility and sample-based notices.
4. Confirm public aggregation SQL returns the expected arrays/objects:
   dashboard `daily/devices/attribution/totals`, content
   `performance/journeys/cta_placements/experience/quality`, behavior
   `ux_signals/section_attention/element_attention/behavior_summary`.
5. Verify sensitive career/job reports and individual campaign labels are
   absent. Owner-only views and authentication must remain unchanged.
6. Compare reports on mobile/desktop for clipping, loading time and native
   selectbox stability. Toggle off should not load the new content/behavior RPCs.
7. Run `PYTHONPATH=src python -m pytest tests/test_public_legacy_analytics_toggle.py tests/test_portfolio_legacy_signal_model.py`
   when the repository's test dependencies are available.

### Current observed limitations

The historical dataset contains a substantial direct/unattributed share, some
unconfirmed durations and uneven content measurement onset in September 2026.
The six-destination navigation redesign on 23 October 2026 also changes which
routes should be compared. Prefer complete periods and quote measured
denominators before proposing site changes.
