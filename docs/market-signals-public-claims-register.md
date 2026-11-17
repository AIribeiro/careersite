# Market Signals public promise register — Edition 01

Reviewed: 17 November 2026. Scope: public landing and historical sample, verified
against Supabase published edition `ai-data-market-review-2026-11-edition-01`,
the member dashboard code, the full-report PDF generator, and the public
historical-sample PDF. This is a content and availability audit, not a claim
that every hosted browser session or publisher endpoint has been rechecked.

## What we can say now

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
