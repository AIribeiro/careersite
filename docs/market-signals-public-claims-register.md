# Market Signals public claims register — Executive Edition 2.0.2 and archived releases

Reviewed: 17 November 2026. Scope: public landing and historical sample, verified
against Supabase published edition `ai-data-market-review-2026-11-edition-01`,
the member dashboard code, the full-report PDF generator, and the public
historical-sample PDF. This is a content and availability audit, not a claim
that every hosted browser session or publisher endpoint has been rechecked.

## Current public publication — Executive Edition 2.0.2 (17 November 2026)

The public landing page was updated following the independently audited V2 publication.
Its claims are limited to the signed-off member evidence and reports:

| Public promise | Published evidence / implementation | Interpretation boundary |
| --- | --- | --- |
| 43 published observations | `sweden-ai-data-market-review-2026-11-v2-0-2` edition archive references the same 43 immutable observations | Observations are not 43 independent source datasets |
| Five executive decision perspectives | Five content chapters in `portfolio_market_signal_editorial_v2.analysis` | Analyses and recommendations are editorial judgements, not survey findings |
| Six evidence series / five publishing organisations | SCB enterprise AI, SCB recruitment needs, derived JobTech v1, Brainville, KI business survey, European Commission Sweden Digital Decade | Two series are from SCB; distinct measures are not independently replicated findings |
| Three conditional scenarios, six agenda decisions | Versioned V2 editorial manuscript and authenticated report generator | No probability claim or universal hiring forecast |
| Full Executive Market Review PDF | `market_intelligence_v2.build_executive_market_pdf` uses the signed-off edition and manuscript, an authored cover summary and source-level methods, populations, caveats and dates | Requires a verified Advisory member; website deployment and authenticated download must be separately verified |
| Five focused Executive Decision Brief PDFs | `market_intelligence_v2.build_executive_decision_pdf` keyed to the selected decision perspective | Supporting original evidence retained and linked |
| 159,500 vacancies, Q2 2026 | SCB LOR survey; 127,500 advertised, 32,100 where employers recruited using other channels | All-economy estimate; the vacancies are not completed hires, rounded components may differ and YoY +8% is within uncertainty |
| 110.7 business confidence, October 2026 | KI total-business confidence indicator; past staffing balance 2; expected next staffing balance 7 | Confidence and net balances are not completed recruitment |
| 68 national Digital Decade measures, EUR 3.55bn | EC Sweden 2026 national Digital Decade roadmap | Combined digital-policy budgets, not AI-exclusive spending or corporate ROI |

**Editorial correction record (17 Nov 2026):** the landing-page headline no longer describes other-channel vacancies as jobs already filled. The executive manuscript no longer compares AI use growth against unmeasured capability and hiring growth rates. The cover is authored within length limits. PDF source registers disclose methodology, denominator, caveat, publication and verification vintage per observation. The exact [JobTech v1 selection and reproduction contract](market_signals/JOBTECH_V1_REPRODUCTION.md) is published without embedded service credentials; the historical API can still revise results. These corrections do not change numeric evidence records.

**Verification boundary:** automated content tests, render preflight and GitHub checks are not equivalent to a signed-in download from the live hosted domain. Never mark that step complete based solely on CI.

Executive Editions 2.0 and 2.0.1 retain their original signed-off records; the v2.0.2 successor clarifies selection bias and evidence comparability without altering the 43 numeric observations. The original Edition 01 remains accessible through the frozen monthly archive and
retains its 30 observations, four original interpretations, three publisher families,
and the figures and report that were available on 16 November. The public June–August
research demonstration remains deliberately limited to that historic JobTech basket.

## Selection and comparability rules — Edition 2.0.2

| Series | Observable claim | What cannot be inferred |
| --- | --- | --- |
| SCB 2026 enterprise IT | Reported AI use among enterprises with at least 10 employees in the 2026 survey | Year-over-year growth without an SNI 2025 / industry-coverage reconciliation; ROI, company operating readiness, causal business outcomes |
| Arbetsförmedlingen JobTech, researcher-derived title basket | Count of indexed advertisements selected by 30 search seeds and headline-only inclusion/exclusion rules, with dated extraction | Nationwide AI leadership demand, unadvertised executive searches, operating/product/digital titles outside the sample, hired people, talent shortages, or exact historical replay without archived source records |
| Brainville October marketplace | Year-on-year change in listings on one broad consulting platform | National or AI-specific consultant supply, pricing, demand, skill availability, or representative trend independent of changes in platform participation |
| SCB Q2 vacancies | Survey estimates for advertised and other-channel vacant positions | Completed hires, AI specialist positions, or a statistically confirmed Q2 year-on-year change |
| KI business survey | Confidence indicator and employment net balances | Completed hires or a causal response to enterprise AI investment |

The three published limits appear beside the executive reading in the full PDF and member view, and relevant limitations appear before the supporting sources in each focused decision PDF. The report also states the evidence boundaries on the public landing page. This is a **disclosure and interpretation correction**, not a statistical resampling or new independent validation of the selected JobTech records. The old signed-off editions and historical June–August sample remain available without retroactive changes to their numeric observations.

## Original November Edition 01 — historical claim record

## What we could say in Edition 01

| Public claim | Evidence behind it | Important constraint |
| --- | --- | --- |
| "30 published data points" | `portfolio_market_signal_editions.evidence_codes` has 30; published data points in `portfolio_market_signal_points` total 30 | These are observations, not 30 statistically independent datasets |
| "Four written analyses" | Published `portfolio_market_signal_briefs`: adoption, leadership adverts, build/recruit/contract, data/governance barriers | Four authored views, not four independent empirical studies |
| "Three data sources" | SCB, Arbetsförmedlingen JobTech-derived title basket, Brainville marketplace | JobTech metrics are calculated from advertisements, not figures published as a count of all AI roles |
| SCB 49% overall, 85% 250+ | Published `scb_2026_ai_10plus`, `scb_2026_ai_250plus` and [SCB 5 Nov 2026 release](https://www.scb.se/hitta-statistik/statistik-efter-amne/forskning-och-det-digitala-samhallet/det-digitala-samhallet/it-anvandning-i-foretag/pong/statistiknyhet/it-anvandning-i-foretag-2026/) | Reported tool use, not outcomes or ROI. SCB changed industry classification/coverage in 2026 |
| JobTech 29 ads in October | `jobtech_v1_oct_se` and fixed v1 classification, Historical Ads + JobSearch | Selected senior AI/Data/Analytics job titles, not all vacancies, unique roles, hires or candidate scarcity |
| Brainville +10.7% / +18.5% | `brainville_202610_assignments_yoy` and `brainville_202610_consultants_yoy`; publisher’s [Oct 2026 note](https://www.brainville.com/sv/Blog/Post/1923) | Two separate YoY cohorts across all consulting disciplines. Not an AI specialist market estimate |
| Eight Observatory sections | `src/page_advisory_market_observatory.py:DASHBOARDS` | Eight UI sections, not eight fully populated research datasets |
| Full November report PDF | `build_market_review_pdf` via `market_review_pdf` | A dated Edition 01 analysis of the approved 30 points; not a live market forecast |
| Four focused decision-brief PDFs | `executive_pdf` builds the selected authored analysis plus sources and a printable, blank decision record | Working material, not personalised investment advice or automatic verdict |
| Downloadable source CSV | `_ledger` / `_evidence_csv` in member Observatory | Only rows published and selected in the ledger are included |
| Monthly archives | Five retrospective JobTech-only June–October views plus full published November Edition 01 | June–October are not complete historical editions and were reconstructed in November |
| Public sample, June–August | `public_historical_demo_pdf`, nine JobTech points, five-page PDF | Public sample does not include later SCB or Brainville findings; no registration needed |

## Claims removed or qualified

- **"Current edition"** changed to a fixed, explicitly dated **November 2026 /
  Edition 01**. A later edition must not silently make this public snapshot
  appear current.
- **"Eight ways to interrogate the market"** changed to eight *sections*,
  explicitly identifying that skills, management-pay and wider sector indicators
  still await publisher and editorial approval.
- **"Cross-source interpretations"** changed to **"Interpretations & trade-offs"**:
  two published comparisons use two observations from the same publisher.
  Cross-source validation cannot be claimed for every comparison.
- **"Genuine, no-registration", "source families", "decision-ready" and
  "no invented conclusions"** replaced with plain-language explanations of
  what the reader receives and where it stops.
- Removed language suggesting JobTech can estimate market-wide hiring, that
  Brainville describes AI specialist capacity, or that enterprise AI adoption
  proves measured economic value.
- Clarified that the historical public PDF was **prepared in November 2026**
  from older JobTech observations, not published contemporaneously in June,
  July or August.

## How to maintain accuracy

1. New published releases must update this register, public copy and
   `tests/test_market_signals_claims_contract.py` together.
2. Promises about downloads require a working export function and a successful
   PDF contract test, not just a navigation link.
3. A dashboard may remain visible for orientation without numeric data, but the
   public landing must explicitly say when the relevant numbers are still
   under review.
4. Published figures must remain connected to original source dates,
   populations and units. Do not use two unrelated percentages as a market
   index or causal claim.
5. Public historical views must never silently acquire data from a later
   publication period; preserve each archive's scope and retrospective label.
6. Passing CI verifies source code and generated test artifacts; it does not
   alone prove the latest Streamlit Cloud deployment or live authenticated
   customer journey is working.
