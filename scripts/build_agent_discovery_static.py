"""Build public, summary-only discovery files for the existing GitHub Pages site.

This is a *mirror*, not a replacement for the authoritative live Starlette
routes. The mirror has no access to reader sessions and never caches complete
CMS HTML. GitHub Pages publishing remains unchanged for social-share URLs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_discovery import (
    PUBLIC_ORIGIN, agents_text, catalogue_json, llms_text,
    markdown_summary, public_catalogue,
)
from thinking_articles import ARTICLES
from scripts.discovery_search_surface import write_search_surface

DEFAULT_SHARE_BASE = "https://airibeiro.github.io/careersite"


def _valid_base(url: str) -> str:
    url = str(url).strip().rstrip("/")
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname != "airibeiro.github.io"
        or parts.path != "/careersite"
        or parts.query or parts.fragment
        or parts.username or parts.password or parts.port
    ):
        raise ValueError("Static discovery mirror must stay within the existing first-party GitHub Pages site.")
    return url


def write_static_discovery(output: Path, catalogue: dict, share_base: str) -> dict:
    """Materialize published *summaries* under the existing Pages artifact."""
    base = _valid_base(share_base)
    if catalogue.get("catalogue_status") != "complete" or not catalogue.get("content"):
        raise RuntimeError("Refusing to publish an empty or partial CMS discovery snapshot.")

    items = []
    for source in catalogue["content"]:
        if not isinstance(source, dict):
            raise ValueError("Unexpected catalogue record.")
        # Never reuse full CMS rows: public_catalogue produces an explicit,
        # small metadata projection. Mirror URLs are not canonical URLs.
        item = dict(source)
        slug = item.get("slug", "")
        if not isinstance(slug, str) or not slug or not slug.replace("-", "").isalnum():
            raise ValueError("Invalid published slug in discovery snapshot.")
        if item.get("access") not in {"premium", "open"}:
            raise ValueError("Invalid access classification in discovery snapshot.")
        if not item.get("url", "").startswith(PUBLIC_ORIGIN + "/?page="):
            raise ValueError("Canonical URL is outside the branded portfolio.")
        item["markdown_url"] = base + "/agent/content/" + slug + ".md"
        items.append(item)

    mirrored = dict(catalogue)
    mirrored["content"] = items
    mirrored["discovery_mirror"] = base
    mirrored["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mirrored["content_policy"] = "summary_only"
    # Unlike the dynamic HTTP endpoint, a stale static Markdown file cannot
    # immediately retract content when an article is unpublished. No full
    # editorial body is ever stored in the GitHub Pages artifact.

    output.mkdir(parents=True, exist_ok=True)
    directory = output / "agent" / "content"
    directory.mkdir(parents=True, exist_ok=True)
    (output / "agent" / "catalog.json").write_text(
        catalogue_json(mirrored) + "\n", encoding="utf-8",
    )
    for item in items:
        (directory / (item["slug"] + ".md")).write_text(
            markdown_summary(item), encoding="utf-8",
        )

    llms = llms_text(mirrored)
    llms = llms.replace(
        PUBLIC_ORIGIN + "/agent/catalog.json", base + "/agent/catalog.json",
    ).replace(PUBLIC_ORIGIN + "/agents.md", base + "/agents.md")
    (output / "llms.txt").write_text(llms, encoding="utf-8")

    guide = agents_text().replace(
        "Website: " + PUBLIC_ORIGIN,
        "Website: " + PUBLIC_ORIGIN +
        "\nPublic discovery mirror: " + base +
        "\nThe mirror contains publication metadata and public summaries only."
    )
    guide = guide.replace(
        "GET /llms.txt", "GET " + base + "/llms.txt"
    ).replace(
        "GET /agent/catalog.json", "GET " + base + "/agent/catalog.json"
    ).replace(
        "GET /agent/content/{slug}.md", "GET " + base + "/agent/content/{slug}.md"
    ).replace(
        "GET /sitemap.xml", "GET " + PUBLIC_ORIGIN + "/sitemap.xml"
    )
    guide = guide.replace(
        "- GET " + PUBLIC_ORIGIN + "/sitemap.xml",
        "- GET " + base + "/sitemap.xml"
    )
    guide += (
        "\n## Public crawlable editorial summaries\n\n"
        "- HTML index: " + base + "/discover/\n"
        "- Publication feed: " + base + "/feed.xml\n"
        "- Robots directives for the ai.jairribeiro.com forwarding endpoint: "
        + base + "/robots.txt\n"
        "- These resources are public metadata summaries only; complete Premium "
        "content stays behind the Reader account experience.\n"
    )
    (output / "agents.md").write_text(guide, encoding="utf-8")

    # The Pages mirror is the actual final HTTP host of ai.jairribeiro.com.
    # Add searchable public HTML and sitemap without exporting CMS HTML bodies.
    result = write_search_surface(output, mirrored, base)
    llms_path = output / "llms.txt"
    llms = llms_path.read_text(encoding="utf-8")
    llms = llms.replace(
        "## Recent published perspectives",
        "## Crawlable discovery\n\n"
        "- [Public editorial summaries](" + base + "/discover/): "
        "Public, indexable HTML introductions and original article links.\n"
        "- [XML sitemap](" + base + "/sitemap.xml): "
        "Published discovery URLs; source publication dates.\n"
        "- [RSS updates](" + base + "/feed.xml): "
        "Latest public summaries and publication links.\n"
        "- [Crawler preferences](" + base + "/robots.txt): "
        "Public paths, including OAI-SearchBot.\n\n"
        "## Recent published perspectives",
    )
    llms_path.write_text(llms, encoding="utf-8")
    assert result["count"] == mirrored["count"]
    return mirrored


def build(output: Path, share_base: str = DEFAULT_SHARE_BASE) -> dict:
    """Read the published catalogue from Supabase; fail instead of going stale."""
    from site_cms import fetch_published_articles

    # The authoritative catalogue includes CMS metadata and publication
    # status, without any body or reader membership queries.
    published = fetch_published_articles()
    if not published:
        raise RuntimeError("CMS publication index is empty; refusing to replace last Pages release.")
    catalogue = public_catalogue(tuple(published), ARTICLES, catalogue_status="complete")
    return write_static_discovery(output, catalogue, share_base)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish summary-only agent files alongside GitHub Pages.")
    parser.add_argument("--output", default="_share_site")
    parser.add_argument("--share-base", default=DEFAULT_SHARE_BASE)
    args = parser.parse_args()
    result = build(ROOT / args.output, args.share_base)
    print(
        "Generated agent discovery mirror: "
        + str(result["count"])
        + " published items, "
        + str(sum(item["access"] == "premium" for item in result["content"]))
        + " with Premium Reader access. No full CMS bodies exported."
    )


if __name__ == "__main__":
    main()
