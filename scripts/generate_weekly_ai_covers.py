#!/usr/bin/env python3
"""Publish immutable Friday WEEKLY AI covers from verified CMS and approved portrait.

This is intentionally deterministic: no recurring identity hallucinations,
per-week image-generation expense, or unreviewed changes to Jair's appearance.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
from urllib import parse, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from weekly_ai_brand_cover import save_friday_cover, render_friday_cover, SIZE

REGISTRY = ROOT / "src" / "weekly_ai_shortlink_registry.json"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rnqweoxtynelfirffmlr.supabase.co").rstrip("/")
PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")


def published_article(slug: str) -> dict | None:
    if not PUBLISHABLE_KEY:
        raise RuntimeError("Missing public Supabase read key")
    query=parse.urlencode({
        "select":"slug,title,subtitle,content_html,kind,category,status,published_at",
        "slug":"eq." + slug,
        "status":"eq.published",
        "category":"eq.Weekly AI",
        "kind":"eq.Weekly Brief",
        "limit":"1",
    })
    req=request.Request(SUPABASE_URL + "/rest/v1/careersite_articles?" + query,
                        headers={"apikey":PUBLISHABLE_KEY, "Accept":"application/json"})
    with request.urlopen(req,timeout=30) as response:
        rows=json.loads(response.read().decode("utf-8"))
    if not isinstance(rows,list):
        raise RuntimeError("Unexpected public CMS result")
    return rows[0] if rows else None


def validate_issue(edition: dict, article: dict) -> None:
    slug=str(edition["slug"])
    if article.get("slug")!=slug:
        raise ValueError("CMS/registry slug mismatch")
    year,week=int(edition["iso_year"]),int(edition["iso_week"])
    publish_date=date.fromisoformat(slug.removeprefix("weekly-ai-"))
    if publish_date!=date.fromisocalendar(year,week,5) or publish_date<date(2026,10,23):
        raise ValueError("Friday cover slug must be publication-Friday ISO date")
    title=str(edition.get("edition_title") or "").strip()
    cms_title=str(article.get("title") or "")
    if not title or title.casefold() not in cms_title.casefold():
        raise ValueError("Visual headline must equal the published CMS issue headline")
    actual_body=str(article.get("content_html") or "")
    links=actual_body.count('<a href=')
    if not 3<=links<=5 or "Leadership signal:" not in actual_body:
        raise ValueError("Weekly issue missing original publisher credits or synthesis")
    if len(edition.get("story_keys",[]))!=links:
        raise ValueError("Story key count does not match sourced CMS reports")
    if article.get("status")!="published":
        raise ValueError("Only published issues can receive public Friday covers")


def publish_cover(edition: dict, *, dry_run: bool=False) -> str:
    slug=str(edition["slug"])
    output=ROOT / "static" / "weekly-ai" / f"{slug}.png"
    article=published_article(slug)
    if article is None:
        return "SKIP unpublished " + slug
    validate_issue(edition,article)
    if output.is_file():
        from PIL import Image, ImageChops
        with Image.open(output) as existing:
            if existing.size!=SIZE or existing.format!="PNG":
                raise ValueError("Existing Friday cover is corrupt; never overwrite silently")
            if slug == "weekly-ai-2026-10-23":
                # One-time fidelity correction: replace the initial programmatic
                # pilot with the user's expressly approved original Week 43 art.
                approved = render_friday_cover(
                    iso_year=int(edition["iso_year"]), iso_week=int(edition["iso_week"]),
                    title=str(edition["edition_title"]),
                    subtitle=str(edition.get("cover_subtitle") or "Friday perspective · one minute"),
                )
                if ImageChops.difference(existing.convert("RGB"), approved).getbbox():
                    if dry_run:
                        return "DRY RUN restore user-approved pilot visual " + slug
                    approved.save(output,format="PNG",optimize=True)
                    return "RESTORED user-approved pilot visual " + slug
        return "SKIP immutable existing " + slug
    if dry_run:
        return "DRY RUN verified " + slug
    save_friday_cover(
        iso_year=int(edition["iso_year"]), iso_week=int(edition["iso_week"]),
        title=str(edition["edition_title"]),
        subtitle=str(edition.get("cover_subtitle") or "Friday perspective · one minute"),
        output=output,
    )
    return "CREATED " + str(output)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--dry-run",action="store_true")
    parser.add_argument("--slug",default="",help="Limit to one exact published Friday slug")
    args=parser.parse_args()
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows=[edition for edition in registry["editions"]
          if edition.get("distribution_mode")=="friday_wrap"
          and (not args.slug or edition.get("slug")==args.slug)]
    for edition in rows:
        print(publish_cover(edition,dry_run=args.dry_run))
    if args.slug and not rows:
        raise SystemExit("Slug is not a registered Friday wrap: " + args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())