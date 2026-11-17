# AI & Data Market Signals — monthly editions and administrator refresh

Operational standard as of 17 November 2026.

## Monthly research versions

The source of truth is `public.portfolio_market_signal_monthly_archive`. Every
row is a **frozen JSON snapshot** with its original source observations and
interpretations, stored separately from the mutable publisher intake tables.
Supabase row-level security grants read access only to verified Advisory
members while the Market Signals service is enabled, plus verified admins.
Neither anonymous users nor ordinary readers have write privileges.

A published edition automatically creates a new immutable snapshot. Withdrawn
or revised publications must use a new edition slug; do not rewrite an older
edition. Historical source revisions can be disclosed in later editions, but
must not silently alter what readers saw in previous versions.

Backfilled monthly archive:

- June–October 2026: five **retrospective** historical title-basket-only views,
  three complete-month JobTech v1 observations each, reconstructed on
  17 November from material verified 16 November. Not original monthly releases.
- November 2026: one full published edition with 30 approved observations and
  four authored executive analyses, issued 16 November 2026.

The reader selector limits the historical archive to the source-relevant
dashboards. The full eight-dashboard interface is reserved for editions with
the necessary approved source coverage.

## Admin refresh: one click and an accountable audit

Advisory Operations → Market Signals management → **Refresh sources & analytics**.

The refresh button:

1. Reconfirms the member's server-side admin role. No email/user-agent or
   query-parameter claims can authorize it.
2. Reads the complete original-source registry, checks all **nine** registered
   publisher URLs with explicit request limits, and records each response.
3. Probes JobTech and, when reachable, attempts a frozen-title-basket-v1 replay
   for the latest complete approved month across Historical Ads and JobSearch,
   with deduplication and no partial-query success claims.
4. Recalculates the latest signed-off evidence manifest, source populations,
   complete-month leadership series, interpretation references and checksum.
5. Creates one owner-only, append-only
   `portfolio_market_signal_refresh_runs` audit record through
   `portfolio_market_signal_record_refresh_v1`. Partial and failed runs remain
   visible, not silently reclassified as successful.

**Important boundary:** successful access to a publisher website is not
verification that a new statistical release has been ingested. Unsupported
sources remain marked *pending review*. Numeric differences detected by
replay are preserved in the refresh audit as candidate revisions; the
published reader dashboard and monthly historical snapshots are unchanged
until source verification and edition sign-off.

No automatic editorial approval, broad job-market imports, personalised job
analytics or historical backdating is permitted.

## Public oldest-data demo

The fourth landing-card points to the open route
`?page=advisory-market-demo`. Anyone can download a source-linked A4 PDF,
without registration, from a **fixed** June–August 2026 historical JobTech
sample (nine approved observations). It shows realistic executive analysis,
cautions, audit trail and an evidence register.

Later SCB AI adoption and Brainville consulting data are **not** inserted into
those earlier months. The demo's research reconstruction date is 17 November
2026. The downloadable public PDF is deliberately separate from the
authenticated full edition and never reads private tables or personal data.

## Quality and access checks

The Market Signals CI checks the old landing page, source-led full PDF,
immutable monthly reader shapes, public historical PDF, administrator
authorization, valid publisher URL allowlist, evidence checksum and
regression for the previously crashing dashboard caveat argument.

At release, verify a real authenticated member selection and a public
no-login PDF download in mobile and tablet browsers. A GitHub CI pass alone
does not verify a particular hosting deployment.
