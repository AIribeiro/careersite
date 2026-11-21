"""Compact, publication-led home announcement.

The first frame comes from local, verified releases. A tiny browser-side query
upgrades it to the latest published Content Studio item without blocking Python
rendering or importing the heavy CMS reader. New credentials in the visible
credential catalog are discovered from source metadata at deploy time.
"""
from __future__ import annotations

import ast
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL

ROOT = Path(__file__).resolve().parents[1]

# Release metadata for pages and standalone features, which do not live in the
# article CMS. Major editorial releases can be declared here. New page routes and credential
# cards are also auto-discovered by the deployment release-feed workflow.
# Use the date the public item became available, not a routine file edit date.
SITE_RELEASES = (
    {
        "type": "Executive research",
        "title": "Sweden’s AI & Data Market: Evidence for Executive Decisions",
        "description": (
            "The November 2026 review goes beyond job listings to examine AI adoption, "
            "recruitment demand, business confidence and regional conditions. "
            "Five executive perspectives, three outlook scenarios and practical "
            "recommendations draw on 43 published observations from six sources."
        ),
        "date": "2026-11-17T09:47:15+01:00",
        "href": "?page=advisory-market-signals",
        "cta": "Read the executive review",
    },
    {
        "type": "Page update",
        "title": "AI & Data Governance — Executive Framework",
        "description": "Explore the illustrated framework for enterprise AI and data ownership, decisions and controls.",
        "date": "2026-11-04",
        "href": "?page=ai-data-governance",
        "cta": "Explore the framework",
    },
    {
        "type": "Certification",
        "title": "Strengthen Your Business Savvy",
        "description": "Harvard Business Review · Four-course specialization on Coursera",
        "date": "2026-10-28",
        "href": "?page=about#credentials-evidence",
        "cta": "Explore the credential",
    },
    {
        "type": "New page",
        "title": "AI & Data Governance",
        "description": "A practical view of AI governance, data accountability and the decisions behind responsible scale.",
        "date": "2026-10-10",
        "href": "?page=ai-data-governance",
        "cta": "Explore the page",
    },
)


@dataclass(frozen=True)
class NewsItem:
    type: str
    title: str
    description: str
    published_at: datetime
    href: str
    cta: str


def _timestamp(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _safe_relative_href(value: str) -> str:
    # All destinations must stay on this portfolio, never a CMS-provided URL.
    if not value.startswith("?page=") or urlparse(value).netloc:
        return "?page=home"
    return value


def _static_items() -> tuple[NewsItem, ...]:
    items = []
    for row in SITE_RELEASES:
        moment = _timestamp(row["date"])
        if moment is not None:
            items.append(NewsItem(
                type=row["type"],
                title=row["title"],
                description=row["description"],
                published_at=moment,
                href=_safe_relative_href(row["href"]),
                cta=row["cta"],
            ))
    # Editorial releases outrank machine-discovered route descriptions. A
    # historical sample, unpublished utility or generic placeholder is never
    # promoted just because a route was created after the actual service.
    curated_hrefs = {row["href"] for row in SITE_RELEASES}
    # GitHub release workflow appends public page/credential launch events here.
    # This file is tiny, local to the deployment, and requires no network call.
    try:
        generated = json.loads((ROOT / "data" / "portfolio_release_feed.json").read_text(encoding="utf-8"))
        published = generated.get("items", [])
    except (OSError, ValueError, TypeError, AttributeError):
        published = []
    for row in published:
        if not isinstance(row, dict):
            continue
        description = str(row.get("description") or "").strip()
        href = str(row.get("href") or "")
        if (
            row.get("promote_home") is False
            or (str(row.get("key", "")).startswith("page:") and href in curated_hrefs)
            or (str(row.get("key", "")).startswith("page:") and href.endswith("-demo"))
            or description in {"", "Discover the newly published portfolio page."}
        ):
            continue
        moment = _timestamp(row.get("date", ""))
        if moment is None or not all(isinstance(row.get(k), str) and row[k] for k in ("type", "title", "href")):
            continue
        items.append(NewsItem(
            type=row["type"],
            title=row["title"],
            description=description,
            published_at=moment,
            href=_safe_relative_href(row["href"]),
            cta=str(row.get("cta") or "Explore the update"),
        ))
    return tuple(items)


def _credential_items() -> tuple[NewsItem, ...]:
    """Read the public credential catalog without importing its media-heavy UI.

    This automatically picks up new cards added to FLAGSHIP, CREDLY_BADGES or
    ACCREDIBLE_BADGES. Catalog month dates are conservatively ranked from the
    first of that month; explicit release events can supply an exact date.
    """
    source = ROOT / "src" / "page_certifications.py"
    try:
        stat = source.stat()
    except OSError:
        return ()
    # File content changes only on deployment; avoid reparsing the entire
    # credential page on every Streamlit rerun. A changed file invalidates
    # this cache automatically without caching the current date.
    return _credential_items_cached(source, stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=16)
def _credential_items_cached(source: Path, mtime_ns: int, size: int) -> tuple[NewsItem, ...]:
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    except (OSError, SyntaxError, UnicodeError):
        return ()

    items = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(
            isinstance(target, ast.Name)
            and target.id in {"FLAGSHIP", "CREDLY_BADGES", "ACCREDIBLE_BADGES"}
            for target in node.targets
        ) or not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for entry in node.value.elts:
            if not isinstance(entry, ast.Dict):
                continue
            data = {}
            for key, val in zip(entry.keys, entry.values):
                try:
                    name = ast.literal_eval(key)
                    if name in {"title", "issuer", "date"}:
                        data[name] = ast.literal_eval(val)
                except (ValueError, TypeError, SyntaxError):
                    continue
            if not all(isinstance(data.get(k), str) and data[k] for k in ("title", "issuer", "date")):
                continue
            try:
                date = datetime.strptime(data["date"], "%b %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            items.append(NewsItem(
                type="Certification",
                title=data["title"],
                description=data["issuer"] + " · Verified credential",
                published_at=date,
                href="?page=about#credentials-evidence",
                cta="Explore the credential",
            ))
    return tuple(items)


def latest_local_release(now: datetime | None = None) -> NewsItem:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    releases = [item for item in _static_items() + _credential_items() if item.published_at <= now]
    return max(releases, key=lambda item: item.published_at)


NEWS_CSS = """<style>
.site .home-news-strip{background:#f3f0eb;border-bottom:1px solid #ded5ca}
.site .home-news-inner{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding-top:22px;padding-bottom:23px;text-align:center}
.site .home-news-copy{min-width:0;width:100%;max-width:960px;display:flex;flex-direction:column;align-items:center;gap:9px;text-align:center}
.site .home-news-overline{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:11px;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}
.site .home-news-heading{color:#a66b48}
.site .home-news-meta{color:#7c7d7c;letter-spacing:.07em}
.site .home-news-overline .home-news-dot{width:5px;height:5px;border-radius:50%;background:#c48e6c}
.site .home-news-title{color:#1a2d41;font:500 clamp(23px,2.8vw,31px)/1.2 Georgia,serif;letter-spacing:-.012em;margin:0;overflow-wrap:anywhere}
.site .home-news-summary{display:block;font:400 clamp(13px,1.25vw,15px)/1.68 Arial,sans-serif;color:#435669;max-width:860px;margin:0 auto;text-align:center}
.site .home-news-link{display:inline-flex;align-items:center;justify-content:center;gap:9px;flex:0 0 auto;align-self:center;min-height:36px;padding:6px 0;margin:5px auto 0;border-bottom:1px solid #a87856;color:#233d56!important;text-decoration:none!important;font:750 13px/1.4 Arial,sans-serif;white-space:nowrap}
.site .home-news-link:hover,.site .home-news-link:focus-visible{color:#955c39!important;border-bottom-color:#955c39}
@media(max-width:760px){.site .home-news-inner{gap:7px;padding-top:18px;padding-bottom:19px}.site .home-news-copy{max-width:100%}.site .home-news-link{align-self:center;margin:3px auto 0}}
@media(prefers-reduced-motion:reduce){.site .home-news-link{transition:none}}
</style>"""


def home_whats_new() -> str:
    item = latest_local_release()
    date = item.published_at.astimezone(ZoneInfo("Europe/Stockholm")).strftime("%d %b %Y").lstrip("0")
    return NEWS_CSS + (
        '<section class="home-news-strip" id="home-whats-new" '
        'aria-label="What’s new in the portfolio" data-analytics-section="home-whats-new">'
        '<div class="container home-news-inner">'
        '<div class="home-news-copy" aria-live="polite">'
        '<div class="home-news-overline">'
        '<span class="home-news-heading">What’s new?</span>'
        '<span class="home-news-dot" aria-hidden="true"></span>'
        f'<span class="home-news-meta" data-news-meta>{escape(item.type)} · {escape(date)}</span>'
        '</div>'
        f'<h2 class="home-news-title" data-news-title>{escape(item.title)}</h2>'
        f'<span class="home-news-summary" data-news-summary>{escape(item.description)}</span>'
        '</div>'
        f'<a class="home-news-link" href="{escape(item.href, quote=True)}" target="_self" '
        'data-hq-event="home_whats_new_open" data-news-link>'
        f'{escape(item.cta)} <span aria-hidden="true">→</span></a>'
        '</div></section>'
    )


def inject_live_home_update() -> None:
    """Non-blocking public CMS metadata read on Home; never downloads article bodies.

    The static first frame works when Supabase is unavailable. Newly published
    and updated articles, Weekly AI editions and Executive Briefings override
    it by the real public revision time; draft material is never promoted.
    """
    import streamlit.components.v1 as components

    initial = latest_local_release().published_at.isoformat()
    endpoint = ANALYTICS_URL.rstrip("/") + "/rest/v1/careersite_articles"
    market_endpoint = (
        ANALYTICS_URL.rstrip("/")
        + "/rest/v1/rpc/portfolio_public_market_release_timestamp_v1"
    )
    script = """
<script>
(function () {
  "use strict";
  const doc = window.parent.document;
  const endpoint = %s;
  const marketEndpoint = %s;
  const apiKey = %s;
  const localPublished = Date.parse(%s);
  let displayedAt = localPublished;
  const query = "?select=title,slug,subtitle,excerpt,kind,published_at,updated_at,created_at"
    + "&status=eq.published&order=updated_at.desc.nullslast,published_at.desc.nullslast&limit=24";
  const validSlug = /^[a-z0-9][a-z0-9-]*$/;
  let busy = false;

  function labelFor(row) {
    const kind = String(row.kind || "").trim().toLowerCase();
    if (kind === "executive briefing") {
      return {label: "Executive briefing", page: "briefing", action: "Read the briefing"};
    }
    if (kind === "weekly brief" || kind === "weekly ai" || /^weekly-ai-/.test(row.slug || "")) {
      return {label: "Weekly AI", page: "thinking", action: "Read this edition"};
    }
    return {label: "Article", page: "thinking", action: "Read the article"};
  }

  function cmsItems(rows) {
    if (!Array.isArray(rows)) return [];
    return rows.map(row => {
      const published = Date.parse(row.published_at || row.created_at || "");
      const updated = Date.parse(row.updated_at || "");
      return {
        source: "cms", row: row,
        time: Math.max(Number.isFinite(published) ? published : 0,
                       Number.isFinite(updated) ? updated : 0),
        revised: Number.isFinite(updated) && Number.isFinite(published)
            && updated > published + 60000,
      };
    }).filter(item =>
      validSlug.test(item.row.slug || "") &&
      typeof item.row.title === "string" && item.row.title.trim() &&
      Number.isFinite(item.time) && item.time > 0 &&
      item.time <= Date.now() + 60000
    );
  }

  function marketItem(item) {
    // The public RPC returns only a fixed set of approved release metadata.
    // Do not follow an arbitrary destination or embed HTML from its response.
    if (!item || Array.isArray(item) || typeof item !== "object" ||
        item.href !== "?page=advisory-market-signals" ||
        typeof item.title !== "string" || !item.title.trim()) return [];
    const time = Date.parse(item.date || "");
    if (!Number.isFinite(time) || time > Date.now() + 60000) return [];
    return [{source: "market", row: item, time: time, revised: false}];
  }

  async function refresh() {
    if (busy || doc.visibilityState === "hidden") return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const headers = {"apikey": apiKey, "Accept": "application/json"};
    try {
      // Neither feed can block the other. A failed or restricted source leaves
      // the already-valid local release rendered without any error message.
      const requests = await Promise.allSettled([
        fetch(endpoint + query, {
          headers: headers, cache: "no-store", signal: controller.signal,
        }),
        fetch(marketEndpoint, {
          headers: headers, cache: "no-store", signal: controller.signal,
        }),
      ]);
      const entries = [];
      if (requests[0].status === "fulfilled" && requests[0].value.ok) {
        try { entries.push(...cmsItems(await requests[0].value.json())); } catch (_error) {}
      }
      if (requests[1].status === "fulfilled" && requests[1].value.ok) {
        try { entries.push(...marketItem(await requests[1].value.json())); } catch (_error) {}
      }
      entries.sort((a, b) => b.time - a.time);
      if (!entries.length || entries[0].time <= displayedAt) return;
      const root = doc.querySelector("#home-whats-new");
      if (!root) return;
      const latest = entries[0];
      const meta = root.querySelector("[data-news-meta]");
      const title = root.querySelector("[data-news-title]");
      const summary = root.querySelector("[data-news-summary]");
      const link = root.querySelector("[data-news-link]");
      if (!meta || !title || !summary || !link) return;
      const published = new Date(latest.time).toLocaleDateString("en-GB", {
        day: "numeric", month: "short", year: "numeric", timeZone: "Europe/Stockholm"
      });
      if (latest.source === "market") {
        meta.textContent = "Market review updated · " + published;
        title.textContent = latest.row.title;
        summary.textContent = latest.row.description || "A new executive research edition is available.";
        link.href = "?page=advisory-market-signals";
        link.textContent = "Read the latest review →";
        link.setAttribute("data-hq-content-type", "market_signals");
        link.setAttribute("data-hq-content-slug", "");
      } else {
        const kind = labelFor(latest.row);
        meta.textContent = (latest.revised ? "Updated " + kind.label.toLowerCase() :
                            kind.label) + " · " + published;
        title.textContent = latest.row.title;
        summary.textContent = latest.row.subtitle || latest.row.excerpt ||
          "Newly published on the portfolio.";
        const params = new URLSearchParams({page: kind.page, article: latest.row.slug});
        link.href = "?" + params.toString();
        link.textContent = kind.action + " →";
        link.setAttribute("data-hq-content-slug", latest.row.slug);
        link.setAttribute("data-hq-content-type", kind.page === "briefing" ? "briefing" :
          kind.label === "Weekly AI" ? "weekly_ai" : "article");
      }
      displayedAt = latest.time;
    } catch (_error) {
      // Keep the locally verified first frame when a feed is unavailable.
    } finally {
      clearTimeout(timeout);
      busy = false;
    }
  }

  refresh();
  const interval = setInterval(refresh, 120000);
  doc.addEventListener("visibilitychange", () => {
    if (doc.visibilityState === "visible") refresh();
  });
  window.addEventListener("pagehide", () => clearInterval(interval), {once: true});
})();
</script>
""" % (
        json.dumps(endpoint),
        json.dumps(market_endpoint),
        json.dumps(ANALYTICS_PUBLISHABLE_KEY),
        json.dumps(initial),
    )
    components.html(script, height=0, width=0, scrolling=False)
