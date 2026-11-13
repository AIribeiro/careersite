"""Crawlable, metadata-only public discovery pages for the Pages mirror.

The final serving host for ai.jairribeiro.com (301) is GitHub Pages.
Publish only explicitly projected public catalogue fields. Never serialize
CMS content_html, aside_html, PDFs, auth state or owner/private fields.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

PAGES_BASE = "https://airibeiro.github.io/careersite"
BRANDED_DISCOVERY = "https://ai.jairribeiro.com"
_BRAND = "Jair Ribeiro"
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,148}[a-z0-9])?$")


def _safe_item(item: dict, base: str) -> dict:
    """Allowlist: excluded body fields cannot slip into a generated page."""
    slug = str(item.get("slug") or "")
    if not _SLUG.fullmatch(slug):
        raise ValueError("Invalid public discovery slug")
    url = str(item.get("url") or "")
    if not url.startswith("https://jairribeiro.com/?page="):
        raise ValueError("Discovery entry requires branded canonical reading URL")
    access = str(item.get("access") or "")
    if access not in ("premium", "open"):
        raise ValueError("Unknown access classification")
    published = str(item.get("published") or "")
    if published and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
        raise ValueError("Invalid published date")
    return {
        "slug": slug,
        "title": str(item.get("title") or "")[:220],
        "summary": str(item.get("summary") or "")[:560],
        "topic": str(item.get("topic") or "")[:100],
        "type": str(item.get("type") or ""),
        "access": access,
        "published": published,
        "url": url,
        "discovery_url": base + "/discover/" + slug + "/",
    }


def _html(page_title: str, description: str, address: str, body: str, *, schema=None) -> str:
    title = escape(page_title)
    desc = escape(description, quote=True)
    canonical = escape(address, quote=True)
    structured = ""
    if schema:
        structured = '<script type="application/ld+json">' + json.dumps(
            schema, ensure_ascii=False, separators=(",", ":"),
        ).replace("<", "\\u003c") + "</script>"
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | {_BRAND}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{_BRAND}">
<meta property="og:title" content="{escape(page_title, quote=True)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
{structured}
<style>
:root{{color-scheme:light;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#182b40;background:#f6f8fb}}
body{{margin:0}}header,main,footer{{max-width:840px;margin:auto;padding:24px}}
header{{border-bottom:1px solid #d4dde7}}a{{color:#175477;text-underline-offset:3px}}a:hover{{color:#063a57}}
h1{{font-size:clamp(28px,4vw,44px);line-height:1.13}}h2{{font-size:20px}}
article{{padding:22px 0;border-bottom:1px solid #d4dde7}}
.detail{{color:#486175;font-size:14px;letter-spacing:.02em}}
summary,p{{font-size:17px;line-height:1.65}}.eyebrow{{text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:#4e6576}}
.cta{{display:inline-block;border:1px solid #abc1d2;padding:10px 14px;border-radius:7px;text-decoration:none;font-weight:600}}
footer{{font-size:13px;color:#4e6576}}
</style></head><body>
<header><a href="https://jairribeiro.com/">Jair Ribeiro · Enterprise AI &amp; Data Leadership</a></header>
<main>{body}</main>
<footer>Public discovery summaries only. Complete editions and Reader services remain at <a href="https://jairribeiro.com/">jairribeiro.com</a>.</footer>
</body></html>
"""


def write_search_surface(output: Path, catalogue: dict, share_base: str) -> dict:
    """Generate real crawlable HTML, XML sitemap, RSS feed and a safe manifest."""
    base = share_base.rstrip("/")
    if base != PAGES_BASE:
        raise ValueError("Search discovery links must target the actual Pages HTTP host")
    if catalogue.get("catalogue_status") != "complete" or not catalogue.get("content"):
        raise RuntimeError("Refusing to index an incomplete published catalogue")

    entries = [_safe_item(item, base) for item in catalogue["content"]]
    if len(entries) != len({e["slug"] for e in entries}):
        raise ValueError("Duplicate slugs in discovery output")
    folder = output / "discover"
    folder.mkdir(parents=True, exist_ok=True)
    items_html = []
    manifest = {}
    for entry in entries:
        blob = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        manifest[entry["slug"]] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        summary = entry["summary"] or "A public summary is not currently available."
        state = "Premium Reader" if entry["access"] == "premium" else "Open edition"
        meta = " · ".join(s for s in (entry["type"].replace("_", " ").title(), entry["topic"], entry["published"], state) if s)
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": entry["title"],
            "description": summary,
            "author": {"@type": "Person", "name": _BRAND, "url": "https://jairribeiro.com/?page=about"},
            "publisher": {"@type": "Person", "name": _BRAND},
            "url": entry["discovery_url"],
            "mainEntityOfPage": entry["discovery_url"],
        }
        if entry["published"]:
            schema["datePublished"] = entry["published"]
        body = (
            '<p class="eyebrow">Public editorial summary</p>'
            + "<h1>" + escape(entry["title"]) + "</h1>"
            + '<p class="detail">' + escape(meta) + "</p>"
            + "<h2>Executive overview</h2><p>" + escape(summary) + "</p>"
            + '<p><a class="cta" rel="noopener" href="' + escape(entry["url"], quote=True)
            + '">Open the full publication on jairribeiro.com</a></p>'
            + '<p class="detail">This page contains the public summary, not the complete publication. '
            + ('Registration is required to read the full Premium edition.' if entry["access"] == "premium"
               else "The complete article is available on the portfolio.") + "</p>"
        )
        article_dir = folder / entry["slug"]
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(
            _html(entry["title"], summary, entry["discovery_url"], body, schema=schema),
            encoding="utf-8",
        )
        items_html.append(
            '<article><h2><a href="' + escape(entry["discovery_url"], quote=True)
            + '">' + escape(entry["title"]) + "</a></h2>"
            + '<p class="detail">' + escape(meta) + "</p><p>" + escape(summary) + "</p></article>"
        )

    index_body = (
        '<p class="eyebrow">Independent research · Public index</p>'
        "<h1>Executive AI and Data Perspectives</h1>"
        "<p>Published briefings, articles and Weekly AI perspectives by Jair Ribeiro. "
        "Every listing provides a public executive summary and directs readers to "
        "the canonical portfolio for complete editions.</p>"
        + "".join(items_html)
    )
    (folder / "index.html").write_text(
        _html("Executive AI and Data Perspectives", "Explore public summaries of Jair Ribeiro's executive AI writing.",
              base + "/discover/", index_body), encoding="utf-8",
    )

    NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
    sitemap = ET.Element("urlset", xmlns=NS)
    def add_url(loc, date=""):
        node = ET.SubElement(sitemap, "url")
        ET.SubElement(node, "loc").text = loc
        if date:
            ET.SubElement(node, "lastmod").text = date
    add_url(base + "/discover/")
    for item in entries:
        add_url(item["discovery_url"], item["published"])
    ET.ElementTree(sitemap).write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for tag, value in (
        ("title", "Jair Ribeiro — Public Executive AI Perspectives"),
        ("link", base + "/discover/"),
        ("description", "Public editorial summaries; complete editions remain on jairribeiro.com."),
        ("language", "en"),
    ):
        ET.SubElement(channel, tag).text = value
    for entry in entries[:30]:
        row = ET.SubElement(channel, "item")
        for tag, value in (
            ("title", entry["title"]),
            ("link", entry["discovery_url"]),
            ("description", entry["summary"]),
            ("guid", entry["discovery_url"]),
        ):
            ET.SubElement(row, tag).text = value
    ET.ElementTree(rss).write(output / "feed.xml", encoding="utf-8", xml_declaration=True)

    (output / "robots.txt").write_text(
        "\n".join([
            "# ai.jairribeiro.com forwards these URLs to the GitHub Pages publishing host.",
            "# Apply these rules to ai.jairribeiro.com. The Pages root robots policy",
            "# is managed by the provider and cannot be changed from this repository.",
            "User-agent: OAI-SearchBot",
            "Allow: /",
            "",
            "User-agent: *",
            "Allow: /",
            "Disallow: /readers/",
            "Disallow: /admin/",
            "Disallow: /owner-auth/",
            "",
            "Sitemap: " + BRANDED_DISCOVERY + "/sitemap.xml",
            "",
        ]), encoding="utf-8",
    )
    (output / "agent" / "publication-state.json").write_text(
        json.dumps({"version": 1, "canonical_discovery_base": base,
                    "records": manifest}, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return {"count": len(entries), "manifest": manifest}
