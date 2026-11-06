# Portfolio Analytics — public Advanced Insights

Updated: 6 November 2026

## Default public experience

The public URL is `/?page=analytics&view=overview`. The four summary cards
are followed immediately by **Advanced Insights**, with six purpose-built,
clickable, horizontally scrollable tabs. No toggle, owner login or dropdown
is needed. The active tab alone is rendered, using Streamlit's stateful
`st.tabs(on_change="rerun")` API and its `.open` property; switching tabs
does not fetch every reporting RPC.

All tabs are executive-style analytical dashboards: KPI scorecards, visual
rankings, ratio comparisons, evidence-based diagnostic callouts, and measured
denominator notes. **No default raw data tables** are displayed. Counts and
measurement context appear in tooltips and captions.

## Six-tab reporting architecture

| Tab | Questions and evidence | Public aggregate source |
| --- | --- | --- |
| **Overview & trends** | Decision-oriented findings, traffic movements, measured engagement, portfolio destinations and leadership-lens reach | `careersite_analytics_dashboard_v2` |
| **Audience & origins** | Country estimates, recognized referring websites, landing and exit patterns, devices, browsers, operating systems, languages and time zones | Traffic RPC (`countries`, `referrers`, `landing_pages`, `exit_pages`, technology cohorts) |
| **Attribution & campaigns** | Broad channel source, engagement outcomes, campaign reach, editorial campaign categories, link-purpose role tags, channel × campaign comparisons, tag-coverage confidence | Traffic RPC (`attribution`) + `careersite_content_intelligence_v2` (`campaigns`) |
| **Content & actions** | Reading depth, content transitions, section reach, CTA exposure/activation, downloads and contact interaction | Traffic RPC + content intelligence RPC |
| **Engagement & UX** | Active-time distribution, engagement timing, device performance, technical failure signals and CTA attention | Traffic RPC + content and `careersite_behavior_intelligence` RPCs |
| **Data quality** | Instrumentation coverage, missing durations, collector distinctions, confidence and historical comparability | Traffic + content intelligence RPCs |

The tab reduction from twelve to six is a visual reorganization of existing
collected evidence—not a deletion of data or a new event collector.

### Attribution semantics

- **Source / channel:** first recorded UTM-style source label. Where
  measured, LinkedIn, Facebook, Threads, X, WhatsApp, AI assistants, Search,
  CV distribution, Email/newsletter and application-link traffic are shown as
  separate broad source categories. Unrecognized sources remain grouped.
  These are tracking tags, not verified visitor origins or employer identities.
- **Referrer:** an observed browser referral host, grouped to known platforms.
  Missing referrer is explicitly retained in the untagged/no-referrer KPI.
  Referrers and source tags need not match.
- **Country:** coarse network location, not nationality, residence or human
  identity. Automated traffic and hosting infrastructure can affect counts.
- **Role tag:** the purpose of a tracked link (e.g., `weeklyai` or `article`);
  it is **NOT an observed visitor job title**. It must never be presented
  as occupational audience segmentation.
- **Campaign:** an editorial/distribution initiative identified by a campaign
  tag. Known public portfolio campaigns are given readable titles. Unknown
  or potentially private labels are grouped into `Other tagged campaigns`.
  Untagged traffic is shown separately in coverage KPIs.
- **Campaign × channel:** observed attribution pairing within the *content*
  collector; filtering and measured-sample thresholds apply.
- **Denominators:** role tags come from traffic source-role cohorts; campaign
  outcomes come from the independent content-campaign collector. Their
  session totals, engagement counts and reader cohorts must not be added
  together or treated as identical.
- **Privacy:** public dashboards publish aggregate grouped observations.
  No raw tokens, named private campaigns, recruiter/company identity,
  visitor identifiers, IP addresses or individual trails. The owner-only
  attribution audits remain private.

Existing Explore Content, Executive Briefings and Weekly AI views remain
available and their visual-first reporting standard is preserved.

## Dashboard presentation standard for public Analytics

This rule also applies outside the six Advanced Insights tabs:

- **Explore content** keeps ranked reading charts, period comparisons,
  section attention, topic trends and site-experience visuals. The repeated
  exact-metrics dataframes and dense comparison tables have been retired;
  values remain available in chart hover and contextual captions.
- **Weekly AI** retains editorial and audio scorecards, edition trends,
  campaign composition and publisher-link charts, without the long
  per-edition, source or campaign tables.
- **Executive Briefings** shows readership and engagement rankings,
  the leading briefing's quality KPIs and visual library-card discovery,
  without exposing per-briefing dataframes.
- **Article source reporting** keeps source distribution and hover detail,
  removing its duplicate exact-source table.

**Analytical hierarchy:** business question → high-confidence KPI →
comparative visualization → measured denominator → interpretation and next
check. Small or missing samples are labeled as unavailable rather than
represented as zero. Browser sessions are not identified people.

## Definitions and safe inferences

- **Session**: browser-tab/collector session, not a unique person. Session
  definitions differ across traffic, content and behavior RPCs. Never add their
  totals or use one collector's total as another's denominator.
- **Recorded engagement**: session engagement as reported by that specific
  collector, not verified human attention.
- **Channel**: first-touch UTM source cohorts grouped into recognized platforms
  (with Facebook, Threads, X and WhatsApp shown separately), search, CV,
  email and untagged/other sources. Raw unknown labels are not rendered.
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
  module. Its public heading is **Advanced Insights**, and six grouped stateful
  tabs remain visible on every visit. Only the active tab renders.
- `src/page_public_legacy_intelligence.py` delivers the source, content,
  CTA, performance, attention and measurement dashboard panels. Reusable
  KPI strips, ranked charts and evidence/next-check notes are used instead
  of dataframes.
- `src/portfolio_legacy_signal_model.py` calculates evidence-gated traffic insights.
- `src/portfolio_public_attribution.py` maps allowed public editorial campaigns,
  role tags and referrer hosts into safe, meaningful cohorts without revealing
  arbitrary input strings or inferring visitor professions.
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
2. Switch among all six tabs. Each contains KPI/chart/interpretation
   presentation, not `st.dataframe` or `st.table` output. Also check the
   public Explore Content, Weekly AI and Executive Briefings analytics screens.
3. Confirm mobile tab navigation scrolls horizontally and the page renders
   only the selected tab's expensive content/behavior RPC.
4. Check selected periods, empty states, no-data labels and measured
   denominators. In particular, do not present missing observations as zero.
5. Verify source, role-tag and campaign views, expected campaign/cohort totals, and absence of private job/campaign records.
6. Run `PYTHONPATH=src python -m pytest tests/test_public_legacy_analytics_toggle.py tests/test_portfolio_legacy_signal_model.py tests/test_portfolio_public_attribution.py`
   in a repository environment with the test dependencies installed.
7. Verify Streamlit Cloud deployment after the latest GitHub commit.
   GitHub commits alone do not confirm that the live application has updated.

### Current observed limitations

The historical dataset contains a substantial direct/unattributed share, some
unconfirmed durations and uneven content measurement onset in September 2026.
The six-destination navigation redesign on 23 October 2026 also changes which
routes should be compared. Prefer complete periods and quote measured
denominators before proposing site changes.
