# Hiring prediction: external-market shadow v1 (20 October 2026)

## Current mode and source of truth

The owner-only production forecast remains `hiring-v2-stage-evidence-provisional`, returned by
`careersite_hiring_prediction_v2`. The secondary `market-shadow-v2-role-mandates-context-only` evaluation
does not change model coefficients, offer dates, start dates, or public hiring projections.
A shadow value identical to the baseline is an **unscored control**, not an estimated
zero market effect. No personal offer probability can be calibrated from the current
small sample of advanced recruiting processes or confirmed offers.

The owner-only Analytics **Decision overview** shows the baseline and shadow evidence.
**Swedish Job Market → What affects my hiring?** provides source-linked regional and
sector detail. Each materially distinct evidence state is appended to
`public.careersite_hiring_market_shadow_history` by the authenticated owner session;
the primary forecast snapshots and JobTech v1 methodology are not rewritten.

## Registered sources and interpretation

These are read by **`source_registry_key`**, not the per-observation `source_key`.
Inactive registry entries are excluded. Source release dates and first-seen dates
must both be on or before the evaluation date. Historical periods are retained
in the comparison even when `is_current=false`; the latest market state uses
current records only. Missing or overdue observations are unavailable, never zero.

- `trr_professional_transitions`: professional transitions, duration, exits and
  new employment. Stronger relevance to searching time; never treated as a
  personal senior-director transition-duration distribution.
- `brg_gothenburg_business_cycle`: 13-municipality Göteborgsregionen survey
  measurements kept distinct from Västra Götaland, Stockholm and national demand.
- `scb_enterprise_ai_adoption`: size-specific AI use; structural demand only.
- `unionen_branschbarometern`: forward hiring sentiment; qualitative statements
  are never assigned fabricated numeric coefficients.
- `almega_services_indicator`: production versus employment, particularly ICT.
  Almega inputs overlapping SCB/KI are treated as a dependent source cluster.

`af_jobtech_target_demand` keeps its existing basket v1 definitions. Full,
already-observed months are shown as a role-specific proxy. Partial-month
counts are not compared with monthly baselines. Sparse VGR counts are marked
as low precision. There is no inferred Göteborg-only JobTech count and
advertised posts are not equated to the entire recruitment market.

## Shadow logic and constraints

1. Target-role demand: JobTech v1 compatible AI/Data leadership roles, Tier A,
   employer/geographical constraints. Strongest candidate hiring indicator.
2. Hiring environment: BRG, Unionen and Almega. Do not conflate
   confidence, production, staffing intentions and observed recruitment.
3. Professional transitions: TRR duration and movement.
4. Structural AI demand: SCB enterprise AI adoption, explicitly lower
   relevance to immediate senior vacancies.

Contradictory output and employment, missing source dates, weak regional counts
or stale surveys must reduce confidence in any interpreted direction, not prompt
a spurious positive or negative probability multiplier.

The UI reports: qualitative hiring outlook, external contribution to scoring,
regional comparisons, separate offer/start windows, calibration status,
source-linked positive and negative signals, comparison with the previous
distinct shadow evaluation, and exclusions. The initial state is
**insufficient evidence / external contribution unchanged (not scored)**.

## Validation before any promotion

Do not switch a market factor into production without at least:

1. Time-ordered folds using only observations available by their
   first-seen and publication dates; historical backfills cannot leak hindsight.
2. A directly comparable personal pipeline outcome set, with recorded offer
   dates and start dates. Do not count stale silence as rejection.
3. Baseline-versus-expanded evaluation on the same folds: offer calibration
   (Brier/log-loss where feasible), offer/start interval coverage,
   time-to-offer and time-to-start error, and week-to-week forecast stability.
4. A sample-size and uncertainty report, plus leave-one-source-cluster-out
   sensitivity testing for SCB/KI/Almega overlaps and tiny regional JobTech counts.
5. Explicit contradictory-signal, backfill, missing-source, revision and
   incomplete-API test cases. Confirm JobTech basket v1 remains unchanged.

Promotion is deliberately disabled until historical performance improves
or empirically defensible interval coverage improves. If data remain sparse,
keep all five sources as non-scoring context. Do not imply a 90% confidence or
offer probability from the pipeline credibility index.

## First recorded contextual readout (not a validated forecast adjustment)

- TRR observed average transition time: 227 days in Q2 to 243 in Q3 2026
  (selected group; +16 days, not Jair's expected transition duration).
- Göteborgsregionen service confidence 102.2 to 99.5, manufacturing 92.8
  to 103.6. This difference does not itself establish hiring demand.
- Almega Q2 2026 ICT output +4.8% YoY versus employment -1.5% YoY.
- SCB AI use in enterprises with 10+ staff 25.2% (2024) to 35% (2025);
  71.9% for enterprises with 250+ staff in 2025. This is not a vacancy count.
- Unionen spring 2026 survey described mixed, cautiously positive conditions.
- JobTech v1 September high-signal matched advertised demand: Sweden 19,
  Stockholm 12, VGR 3. These are nested geographies and small samples,
  not three independent counts.

These values are displayed from Supabase evidence dynamically; this paragraph
is a dated, immutable reference for initial regression and interpretation.

## Role ambition vs. functional conversion policy (20 October 2026)

The owner has specified a **primary ambition** of AI Director / AI Transformation Director
and equivalent enterprise Head of AI positions. His **equally valid conversion targets**
include Senior Manager of enterprise AI strategy or transformation, AI Strategy Lead,
AI Transformation Lead, Head of AI Adoption, AI Enablement/Capability Lead and similar
functional leadership roles. Lead/Manager does **not** imply a second-class match.
Role *mandate* determines fit: ownership of roadmap, operating model, governance,
adoption, stakeholders, portfolio and value realization. Engineering and implementation
craft, generic IT, quota sales and PMO are not made eligible by including AI in a title.
Data/Analytics management, Responsible AI and intelligent automation leadership remain
adjacent paths subject to their existing scope rules.

Versioned classifier: `src/hiring_target_policy.py` /
`ai-leadership-mandates-v1-2026-10-20`. The catalogue is read using the
authenticated owner-only `careersite_hiring_role_catalog_v1` RPC, not open
REST table access. Titles provide **discovery candidates only**. Keyword evidence
can mark *strategic signals for manual review* but must never certify suitability
or a vacancy's authenticity. The live 500 most-recent Swedish active listings are
deduplicated by normalized title and company, a nonrepresentative source snapshot.
Aliases, technical-heavy mandates and language/location constraints can further
reduce actual eligibility.

The owner-only Decision Overview and Swedish Job Market shadow compare:
(i) title candidates for the aspirational Director/Head lane versus (ii) the
additional functional-conversion lane, with 45-day first-seen counts;
(iii) the v2 forecast's available top-ranked interview processes by role lane;
and (iv) the unchanged conditional offer/start forecasts. A wider title basket
cannot be treated as a multiplier to personal offer odds or as faster time-to-offer.
The existing v2 SQL model already includes AI Strategy/Transformation/Adoption
Lead and Manager titles in role family A with full fit weight; role policy should
not double-count or artificially add a premium.

The earlier JobTech v1 high-signal sample (19 national September matches)
is **not** a market-census denominator and is not retroactively relabeled
or used as a Dir-only baseline. If future evidence supports a revised JobTech
basket, store it as v2 with explicit query definitions, employer/title/URL
deduplication, scope checks and matched full reporting months. Backtest its
incremental predictive value before applying any external scoring factor.
