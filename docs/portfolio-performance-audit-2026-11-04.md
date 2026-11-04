# Portfolio performance audit — 4 November 2026

## Scope and evidence

Pages reviewed: Home, AI Leadership, AI & Data Governance, Thinking (landing and article reader), Executive AI Briefings (library and reader), About, Contact, and private Analytics. Legacy aliases redirect into their canonical pages.

Method: live first-party web-vitals aggregates from `public.careersite_analytics_events` for the last seven days; source-code examination of route imports, CMS calls, image delivery, shared footers and infographic rendering; GitHub Actions validation. This is **not** a synthetic live-browser Lighthouse test, and no performance improvement is claimed from the historical observations. Sample counts are small for several routes, and metrics may be affected by Streamlit navigation and client instrumentation.

## Observed baseline (rolling seven-day period ending 2026-11-04)

FCP and LCP are milliseconds. Values are *median observed client-side metrics*, not measured server rendering times.

| Public page | FCP p50 (n) | LCP p50 (n) | LCP p90 | Assessment |
|---|---:|---:|---:|---|
| Home | 734 (108) | 3,148 (67) | 6,211 | Image loading and live home publication selection |
| AI Leadership (`impact`) | 11,754 (2) | 11,754 (2) | 14,268 | Severe in limited samples; large original event photographs and cold imports likely contributors |
| AI & Data Governance | 8,304 (3) | 8,304 (3) | 9,136 | Severe in limited samples; long HTML document and cross-page CMS footer previously blocking |
| Thinking landing/article | 1,056 (49) | 4,503 (51) | 6,511 | CMS catalogue/article calls, reader assets and media |
| Executive Briefings library | 1,585 (17) | 2,807 (22) | 14,442 | CMS catalogue first read and large premium library styles; notable tail latency |
| Executive Briefing reader | 1,542 (10) | 3,335 (19) | 15,830 | Individual CMS fetch and infographic/reader content |
| About | 1,501 (13) | 4,809 (13) | 7,485 | Credentials archive was fully expanded; photos/credential artwork |
| Contact | 1,494 (1) | 2,632 (2) | 2,632 | Small sample; shared startup dominates |
| Private Analytics | No public RUM | No public RUM | — | Separately imported owner-only dashboard; inspect query/cache profile independently |

These measurements predate some or all of the fixes below. The low-sample Impact, Governance and Contact measurements must not be interpreted as stable route averages.

## Completed production changes

| Area | Change | Constraint retained |
|---|---|---|
| All public routes | Route-specific page imports in `main.py`; stop eagerly importing the large Thinking, Briefings, and unrelated public-page engines | Navigation and content unaffected |
| Startup | Remove import-time fallback CV generation and defer `fpdf` import; canonical committed CV remains served as static PDF | CV download URL preserved |
| Cross-page editorial footer | A verified snapshot of all **28** published, non-Weekly AI articles and Executive Briefings; no CMS query on routine non-home footers | Random selection, publication links and content types preserved; individual libraries remain live |
| Governance footer | Governance-specific curated writing selection requires no network call | Contextual recommendations preserved |
| Home | Home-only Executive Briefings teaser extracted from the approximately 80 KB briefing engine into a small module | Original copy, colors, CSS structure and analytics event preserved |
| Public photography | Prebuilt, cacheable, responsive WebP variants for 12 curated JPEG/display-width combinations; fall back to canonical original if a derivative is unavailable | Real photographs, alt text and image-loading safety preserved |
| About | Full credentials and verification archive now starts collapsed; still available with a disclosure control | All source content retained |
| Article metadata | Defer `thinking_social` image-generation import until an article-specific metadata operation is needed | Article image handling remains intact |
| Governance framework | Keep text/vector diagram and 18 sanitizer-compatible SVG CSS assets; add 10 KB portrait and prebuilt A4 vector PDF | Framework language, mobile layout and interactive HTML retained |
| Diagnostics | Log cold startup-inclusive timings plus page build, footer selection, HTML emission and rendered document size for slow runs | No visitor-identifying data |

### Representative source-photo transfer reduction

- Public speaker/hero photograph: 1,042,500 bytes → 43,836-byte WebP (display width ≤1280).
- Thinking photograph `IMG_8281`: 2,680,280 bytes → 84,072-byte WebP (≤960).
- Navigation portrait `profile_red_bg`: 476,665 bytes → 3,546-byte WebP (≤160).
- Leadership workshop photo `IMG_0777`: 1,150,009 bytes → 235,266-byte WebP (≤1280).

Original JPEG/PNG files remain in the repository and are selected automatically when optimized derivatives are absent. The optimized assets are built in GitHub Actions, never on a visitor request.

## Remaining risk and next measurement

1. **Home:** The main Home editorial feature still prefers live CMS metadata on a cold cache miss (public catalogue request has a five-second timeout). This preserves immediate new-publication visibility. If cold Home loads remain slow, replace it with a publishing-triggered snapshot or a non-blocking client refresh rather than allowing this request to gate the page.
2. **Thinking and Executive Briefings:** Actual catalogues must remain CMS-backed for publication accuracy. Their first request can wait on CMS; cached calls have a 180-second TTL, and individual readers have a 60-second TTL. Reassess backend latencies and query response size rather than hiding missing articles.
3. **Private Analytics:** Read heavy query/range latency from owner-level logs and SQL `EXPLAIN` on the actual reporting views before changing dashboard semantics. No public measurements in the above table.
4. **Streamlit Community Cloud:** Cold process creation, WebSocket setup, redeploy/wake behavior and network stalls cannot be ruled out from client vitals alone. Page-level Python timers were added to distinguish build/footer/emit durations.
5. **Live validation:** After deployment collect at least ~30 new FCP/LCP observations for high-traffic routes and compare distributions by route and date, excluding these pre-change baseline samples. Use browser DevTools waterfall for first-visit and warm-visit checks on desktop/mobile. Avoid treating p90 LCP spikes as code regressions without checking asset/network timing.

## Acceptance gates

- No broken photography; all pages may fall back to original image assets.
- Governance image and A4 PDF are committed static files, with no per-page PDF rendering.
- A4 PDF is one page, 210 × 297 mm, and retains all six framework sections.
- Canonical route changes do not cause heavyweight cross-page imports.
- No synchronous cross-page footer CMS lookup.
- Keep article/briefing publication status authoritative on their canonical library and reader routes.
- Review route-specific Streamlit logs for actual improvements before claiming a quantified speedup.
