"""Read-only, public, machine-readable discovery for Jair Ribeiro's portfolio.

This module deliberately consumes *catalogue metadata* only. It never loads
article body HTML, reader identities, unpublished drafts, infographics or PDFs.
Website agent guidance is not a substitute for authentication or RLS.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import json
import re
from urllib.parse import urlencode

from article_access import article_is_locked, is_editorial_article
from weekly_ai_reader_access import latest_weekly_ai_slug

PUBLIC_ORIGIN = "https://jairribeiro.com"
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,148}[a-z0-9])?$")
_TAGS = re.compile(r"<[^>]*>")
_SPACE = re.compile(r"\s+")


def safe_slug(value: object) -> str:
    slug = str(value or "").strip().lower()
    return slug if _SLUG.fullmatch(slug) else ""


def plain_text(value: object, limit: int = 560) -> str:
    """Prevent HTML and multiline Markdown injection in public snippets."""
    text = _SPACE.sub(" ", unescape(_TAGS.sub(" ", str(value or "")))).strip()
    return text[:limit].rsplit(" ", 1)[0].strip() if len(text) > limit else text


def _type(article: object) -> str:
    kind = str(getattr(article, "kind", "") or "").strip().lower()
    category = str(getattr(article, "category", "") or "").strip().lower()
    if kind == "executive briefing":
        return "executive_briefing"
    if kind == "weekly brief" and category == "weekly ai":
        return "weekly_ai"
    return "article"


def _published_date(article: object) -> str:
    value = str(getattr(article, "published_at", "") or "")
    if not value:
        value = str(getattr(article, "published_iso", "") or "")
    return value[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value[:10]) else ""


def _publication_url(slug: str, type_: str) -> str:
    page = "briefing" if type_ == "executive_briefing" else "thinking"
    return PUBLIC_ORIGIN + "/?" + urlencode({"page": page, "article": slug})


def _access(article: object, type_: str, articles: tuple, weekly_latest: str | None, now: datetime) -> str:
    if type_ == "executive_briefing":
        return "premium"
    if type_ == "weekly_ai":
        # If the Weekly AI catalogue is incomplete, conservatively protect
        # that week's edition rather than infer an earlier public release.
        return "premium" if not weekly_latest or str(article.slug) == weekly_latest else "open"
    if is_editorial_article(article):
        return "premium" if article_is_locked(article, now=now, published=articles) else "open"
    return "open"


def public_catalogue(
    published: tuple | list,
    legacy: tuple | list = (),
    *,
    now: datetime | None = None,
    catalogue_status: str = "complete",
) -> dict:
    """Use published CMS metadata, with legacy authored articles as fallback.

    No access policy changes are made here. 'Premium' describes the reader
    experience, not proof that an upstream asset or CMS row is inaccessible.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    articles = tuple(
        article for article in published
        if str(getattr(article, "status", "") or "").casefold() == "published"
        and safe_slug(getattr(article, "slug", ""))
    )
    weekly_latest = latest_weekly_ai_slug(articles) if articles else None
    items = []
    seen = set()
    for article in articles:
        slug = safe_slug(article.slug)
        if slug in seen:
            continue
        seen.add(slug)
        type_ = _type(article)
        synopsis = plain_text(
            getattr(article, "excerpt", "") or
            getattr(article, "subtitle", "") or
            getattr(article, "meta_description", "")
        )
        items.append({
            "slug": slug,
            "title": plain_text(getattr(article, "title", ""), 220),
            "type": type_,
            "topic": plain_text(getattr(article, "category", ""), 100),
            "published": _published_date(article),
            "summary": synopsis,
            "access": _access(article, type_, articles, weekly_latest, now),
            "url": _publication_url(slug, type_),
            "markdown_url": PUBLIC_ORIGIN + "/agent/content/" + slug + ".md",
        })
    for article in legacy:
        slug = safe_slug(getattr(article, "slug", ""))
        if not slug or slug in seen:
            continue
        seen.add(slug)
        items.append({
            "slug": slug,
            "title": plain_text(getattr(article, "title", ""), 220),
            "type": "article",
            "topic": plain_text(getattr(article, "topic", ""), 100),
            "published": _published_date(article),
            "summary": plain_text(getattr(article, "standfirst", "")),
            "access": "open",
            "url": _publication_url(slug, "article"),
            "markdown_url": PUBLIC_ORIGIN + "/agent/content/" + slug + ".md",
        })
    items.sort(key=lambda row: (row["published"], row["slug"]), reverse=True)
    return {
        "schema_version": "1.0",
        "site": PUBLIC_ORIGIN,
        "publisher": "Jair Ribeiro",
        "catalogue_status": catalogue_status,
        "count": len(items),
        "content": items,
    }


def llms_text(catalogue: dict) -> str:
    """Small, conventional llms.txt entrypoint; full index lives in JSON."""
    lines = [
        "# Jair Ribeiro | Enterprise AI & Data Leadership",
        "",
        "> Independent executive writing on enterprise AI, governance,",
        "> adoption, portfolio decisions, data accountability, and value.",
        "",
        "This site presents Jair Ribeiro's professional perspectives. "
        "Editorial analysis is not a guarantee of company results or professional advice.",
        "The public content directory is refreshed from the published portfolio catalogue.",
        "Premium Reader editions offer public summaries; full text and PDFs require "
        "reader authentication in the website interface.",
        "",
        "## Start here",
        "",
        "- [Portfolio](" + PUBLIC_ORIGIN + "/): Professional profile and current writing.",
        "- [Thinking](" + PUBLIC_ORIGIN + "/?page=thinking): Essays, decisions and field observations.",
        "- [Executive AI Briefings](" + PUBLIC_ORIGIN + "/?page=briefings): Executive-level decision briefings.",
        "- [Premium Reader library](" + PUBLIC_ORIGIN + "/?page=readers): Free registered access to complete editions.",
        "- [Agent catalogue](" + PUBLIC_ORIGIN + "/agent/catalog.json): All published metadata and access status in JSON.",
        "- [Agent guidance](" + PUBLIC_ORIGIN + "/agents.md): Content boundaries and citation guidance.",
        "",
        "## Recent published perspectives",
        "",
    ]
    for item in catalogue.get("content", ())[:24]:
        label = item["title"].replace("[", "").replace("]", "")
        state = "Premium Reader" if item["access"] == "premium" else "open"
        lines.append(
            "- [" + label + "](" + item["markdown_url"] + "): "
            + item["type"].replace("_", " ").title()
            + " · " + state
            + (" · " + item["topic"] if item["topic"] else "")
            + "."
        )
    lines.extend([
        "",
        "## Access and attribution",
        "",
        "- Use the canonical jairribeiro.com URL from each catalogue record when linking.",
        "- Cite the author and exact title; distinguish a public summary from the complete edition.",
        "- Do not claim access to full Premium text from these discovery endpoints.",
        "- Do not access private reader, administrative, download, or authentication endpoints.",
        "- The catalogue is discovery metadata, not a request for model training or a grant of reuse rights.",
        "",
    ])
    return "\n".join(lines)


def agents_text() -> str:
    """Agent-facing web content guide; independent of the coding-agent AGENTS.md."""
    return "\n".join([
        "# Agent guide | Jair Ribeiro",
        "",
        "Website: " + PUBLIC_ORIGIN,
        "Publisher: Jair Ribeiro",
        "Contact: info@jairribeiro.com",
        "",
        "## Purpose",
        "",
        "Help research assistants discover published executive perspectives on "
        "enterprise AI, AI governance, responsible adoption, data and analytics, "
        "AI operating models, and evidence of value.",
        "",
        "## Read-only discovery",
        "",
        "- GET /llms.txt for a short editorial map.",
        "- GET /agent/catalog.json for published metadata and public access status.",
        "- GET /agent/content/{slug}.md for a **public summary only**.",
        "- GET /sitemap.xml for the published URL index.",
        "- Follow canonical jairribeiro.com links for human-readable pages.",
        "",
        "## Attribution and accuracy",
        "",
        "- Attribute perspectives to Jair Ribeiro, with exact titles and canonical URLs.",
        "- Do not imply endorsement, direct employment history, or verified measured "
        "results unless the linked public source supports those claims.",
        "- Treat public summaries as excerpts, not the full editorial argument.",
        "- Prefer the publication date over a crawl date; do not invent sources.",
        "",
        "## Reader privacy and access",
        "",
        "- Executive AI Briefings remain Premium Reader editions.",
        "- The latest published Weekly AI edition is Premium; older issues are open.",
        "- Article access follows the seven-day and successor-publication policy.",
        "- Never attempt to bypass sign-in, retrieve unpublished drafts, enumerate "
        "readers, use owner routes, or fetch member downloads without permission.",
        "- robots.txt is crawler guidance, not a security or authorization mechanism.",
        "- This file grants no training, reproduction, or redistribution rights.",
        "",
        "## Technical status",
        "",
        "These endpoints provide structured public discovery, not a general-purpose "
        "agent action API, authenticated MCP server, or tool-execution permission.",
        "",
    ]) + "\n"


def markdown_summary(item: dict) -> str:
    """Safe metadata-only Markdown: never include content_html or PDF assets."""
    summary = item.get("summary") or "A public summary is not available for this edition."
    lines = [
        "# " + item["title"],
        "",
        "Author: Jair Ribeiro",
        "Published: " + (item["published"] or "Publication date unavailable"),
        "Series: " + item["type"].replace("_", " ").title(),
        "Topic: " + (item["topic"] or "Enterprise AI"),
        "Access: " + ("Premium Reader — free registration" if item["access"] == "premium" else "Open access"),
        "Canonical: " + item["url"],
        "",
        "## Public executive summary",
        "",
        summary,
        "",
    ]
    if item["access"] == "premium":
        lines.extend([
            "## Full edition",
            "",
            "The complete edition is available to registered readers through "
            "the canonical website link. Full text and downloadable assets "
            "are intentionally not provided by this endpoint.",
            "",
        ])
    return "\n".join(lines)


def robots_text() -> str:
    return "\n".join([
        "User-agent: *",
        "Allow: /",
        "Allow: /llms.txt",
        "Allow: /agents.md",
        "Allow: /agent/catalog.json",
        "Allow: /agent/content/",
        "Disallow: /owner-auth/",
        "Disallow: /readers-admin",
        "Disallow: /readers/download/",
        "Disallow: /readers/",
        "Disallow: /admin",
        "Disallow: /?page=admin",
        "Disallow: /?page=analytics",
        "Disallow: /?page=readers",
        "",
        "Sitemap: " + PUBLIC_ORIGIN + "/sitemap.xml",
        "",
    ])


def catalogue_json(catalogue: dict) -> str:
    return json.dumps(catalogue, ensure_ascii=False, separators=(",", ":"))
