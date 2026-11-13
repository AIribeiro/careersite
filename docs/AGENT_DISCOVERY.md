# AI-readable portfolio discovery

Status: repository implementation, pending branded-domain routing verification.

## Contract

The public application exposes five read-only endpoints and upgrades the existing crawler paths:

| Endpoint | Type | Content |
|---|---|---|
| `/llms.txt` | text/plain | Short site map following the emerging llms.txt convention |
| `/agents.md` | text/markdown | Website research-agent guidance (not repository coding-agent instructions) |
| `/agent/catalog.json` | application/json | Automatically assembled published article metadata, public summaries, access state |
| `/agent/content/{slug}.md` | text/markdown | Public executive summary of one published edition, **never the complete Premium text** |
| `/robots.txt` | text/plain | Advisory crawler preferences plus the canonical sitemap |
| `/sitemap.xml` | application/xml | Branded-domain publication URLs and other public pages |

Publisher: Jair Ribeiro. Canonical origin: `https://jairribeiro.com`. All supported website links use the root brand rather than a Streamlit hostname or a separate subdomain.

The feed sources **live CMS catalogue metadata** via `fetch_published_articles()` (never `fetch_public_article()` or `select=*`), and includes legacy published editorial metadata if absent from the CMS. The in-app CMS metadata cache lasts 180 seconds; the new public endpoints advertise a corresponding 180-second cache period. Publishing a new item therefore does not require a repository change. If the live CMS is unavailable, the feed returns the legacy subset and advertises `"catalogue_status": "partial"`; it does not claim completeness or invent items.

### Editorial access policy

The same access rules used in the reader are applied to catalogue labels:

- **Executive AI Briefings:** Premium Reader always.
- **Weekly AI:** the latest *published* edition is Premium; preceding editions are open.
- **Articles:** remain Premium for at least seven days, and until a newer Article is published.
- **Legacy first-party authored articles:** open where not replaced by published CMS records.

The Markdown summary never emits CMS body HTML, aside HTML, infographics, full article PDFs, reader identities, or unpublished entries. No autonomous read or write actions are exposed. There is no registration shortcut, bot-specific content entitlement, or MCP execution endpoint.

**Rights:** `robots.txt`, `llms.txt` and `agents.md` do not grant rights to crawl where otherwise prohibited, train models, reproduce entire editions, or bypass copyright or access restrictions.

## Critical access-control prerequisite

This implementation does **not** claim to secure Premium CMS text end-to-end. As of 13 Nov 2026, Supabase grants the `anon` role `SELECT` on `public.careersite_articles.content_html` and `aside_html` for published rows. Existing application code fetches full published rows through `fetch_public_article()`. Some public media are also stored in GitHub. The UI-level registration requirement is not a data-layer entitlement check. Do not describe Premium content as technically inaccessible to anonymous clients until a privileged authenticated read path, revised database privileges/RLS or projection, and private PDF storage have been deployed and regression tested. Follow `docs/READER_MEMBERSHIP.md` for the wider migration.

Agent discovery does not expand that exposure: it reads only metadata and deliberately does not include full content. Do not publish `llms-full.txt` from existing CMS rows.

## Branded domain and deployment

The Streamlit code now handles these paths when requests actually reach its `app.py` Starlette routes. That does **not** mean that the endpoints resolve at `jairribeiro.com`.

The current Spaceship **masking/iframe** setup serves an outer HTML page on the brand domain, with Streamlit loaded inside it. A request to `https://jairribeiro.com/llms.txt` can therefore return Spaceship's HTML wrapper or a path fallback instead of `text/plain` even when `https://jairribeiro-ai.streamlit.app/llms.txt` is served correctly. A meta title or the `embed=true` query flag does not solve this for crawlers.

**Required infrastructure condition:** configure the branded domain's HTTP layer (reverse proxy, edge route, or first-party hosting) to forward `/llms.txt`, `/agents.md`, `/agent/*`, `/robots.txt`, and `/sitemap.xml` to the application (preserving content-type, response status and query string), or serve a safely generated static export at the branded root. DNS changes alone cannot direct individual URL paths. Route only these read-only paths until reader login redirects and cookies are tested; avoid transparently proxying member endpoints without a security review.

Suggested acceptance checks against the **branded domain**, not merely the native Streamlit app:

```bash
curl -fsSL -D - https://jairribeiro.com/llms.txt | head -25
curl -fsSL -D - https://jairribeiro.com/agents.md | head -25
curl -fsSL https://jairribeiro.com/agent/catalog.json | python -m json.tool | head -25
curl -fsSL https://jairribeiro.com/agent/content/ai-governance-explained-to-executives.md
curl -fsSL https://jairribeiro.com/robots.txt
curl -fsSL https://jairribeiro.com/sitemap.xml
```

Pass conditions: direct 200 responses; text/plain, text/markdown, application/json and application/xml as appropriate; no iframe or sign-in redirect; zero private HTML; 404 for unknown slugs; no unpublished records; sitemap contains canonical root-domain URLs. Validate 180-second catalogue freshness after publication and after a new Weekly AI edition moves the previous edition to open access.

## Analytics and attribution

Browser telemetry only runs for pages executed by visitors and cannot measure bot requests to `/llms.txt` or `/agent/*`. Do **not** infer bot traffic from page views or label a user-agent string as a verified AI crawler. Once the branded domain runs behind an HTTP edge with request logs, report separate aggregates for `agent_discovery_request`, `agent_catalog_request`, `agent_summary_request`, `verified_search_bot`, `unverified_user_agent`, and `human_browser`, using provider-verified bot classification where possible. Aggregate without raw IP, persistent individual identifier or full user-agent strings. No fabricated historical counts.

## Validation

```bash
PYTHONPATH=src python -m unittest tests.test_agent_discovery
python -m py_compile app.py src/agent_discovery.py tests/test_agent_discovery.py
```

Unit and CI tests do not establish deployment reachability through Spaceship. Finish the HTTP checks above after any infrastructure change.
