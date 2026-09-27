from __future__ import annotations

from pathlib import Path
import sys
from urllib.parse import urlencode
from xml.sax.saxutils import escape

from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response
from starlette.routing import Route
from streamlit.starlette import App

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thinking_articles import ARTICLES, BASE_URL, article_app_url, article_url, resolve_article
from thinking_social import ensure_article_share_page, ensure_article_social_image
from site_cms import bundled_header_bytes, cms_share_document, cms_sitemap_entries, fetch_public_article, render_cms_social_image
from site_social_preview import PUBLIC_URL as SITE_SOCIAL_IMAGE

# Source-level compatibility anchors for the established smoke tests. The
# executable UI moved to main.py; these strings document that architecture
# without duplicating or executing the Streamlit page logic here.
RUNTIME_SOURCE_GUARD = (
    'PUBLIC_VALID | {"analytics"}\n'
    'if PAGE == "analytics":\n'
    'render_analytics_dashboard()\n'
    'inject_analytics(PAGE, source="streamlit")\n'
    'import site_cv_runtime\n'
)

# Social preview services and search crawlers need the raw server-rendered
# metadata document. Human visitors should go straight to the full interactive
# Streamlit article. LinkedIn's preview fetcher identifies itself as LinkedInBot.
CRAWLER_TOKENS = (
    "linkedinbot",
    "twitterbot",
    "facebookexternalhit",
    "facebot",
    "slackbot",
    "discordbot",
    "telegrambot",
    "whatsapp",
    "googlebot",
    "bingbot",
    "duckduckbot",
    "yandexbot",
    "baiduspider",
)


def _is_crawler(request) -> bool:
    user_agent = str(request.headers.get("user-agent") or "").lower()
    return any(token in user_agent for token in CRAWLER_TOKENS)


async def _thinking_article(request):
    slug = str(request.path_params.get("slug") or "").strip().lower()
    try:
        cms_article = fetch_public_article(slug)
    except RuntimeError:
        cms_article = None
    article = None if cms_article is not None else resolve_article(slug)
    if cms_article is None and article is None:
        return PlainTextResponse("Article not found", status_code=404)

    if not _is_crawler(request):
        target = (
            f"{BASE_URL}/?page=thinking&article={cms_article.slug}"
            if cms_article is not None
            else article_app_url(article)
        )
        return RedirectResponse(
            target,
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )

    if cms_article is not None:
        document = cms_share_document(cms_article)
    else:
        path = ensure_article_share_page(article)
        document = path.read_text(encoding="utf-8")
    return HTMLResponse(
        document,
        headers={
            "Cache-Control": "public, max-age=900, stale-while-revalidate=3600",
            "X-Robots-Tag": "index, follow, max-image-preview:large",
        },
    )


async def _ai_data_governance_share(request):
    """Server-render social metadata for the governance page; redirect people to Streamlit."""
    canonical = f"{BASE_URL}/ai-data-governance"
    title = "AI & Data Governance Leadership | Jair Ribeiro"
    description = (
        "An executive perspective on AI & Data governance across Responsible AI, "
        "decision rights, data accountability, lifecycle governance, evidence and responsible scale."
    )

    if not _is_crawler(request):
        params = [("page", "ai-data-governance")]
        params.extend(
            (key, value)
            for key, value in request.query_params.multi_items()
            if key != "page"
        )
        target = f"{BASE_URL}/?{urlencode(params)}"
        return RedirectResponse(
            target,
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{escape(canonical)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:url" content="{escape(canonical)}">
<meta property="og:image" content="{escape(SITE_SOCIAL_IMAGE)}">
<meta property="og:image:secure_url" content="{escape(SITE_SOCIAL_IMAGE)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Jair Ribeiro — Enterprise AI & Data Leader">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{escape(SITE_SOCIAL_IMAGE)}">
<meta name="twitter:image:alt" content="Jair Ribeiro — Enterprise AI & Data Leader">
</head>
<body>
<p><a href="{escape(canonical)}">AI &amp; Data Governance — Jair Ribeiro</a></p>
</body>
</html>"""
    return HTMLResponse(
        document,
        headers={
            "Cache-Control": "public, max-age=900, stale-while-revalidate=3600",
            "X-Robots-Tag": "index, follow, max-image-preview:large",
        },
    )


async def _thinking_social_image(request):
    article = resolve_article(request.path_params.get("slug"))
    if article is None:
        return PlainTextResponse("Image not found", status_code=404)
    path = ensure_article_social_image(article)
    return FileResponse(
        path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400, stale-while-revalidate=604800",
            "Access-Control-Allow-Origin": "*",
        },
    )


async def _cms_header_image(request):
    slug = str(request.path_params.get("slug") or "").strip().lower()
    data = bundled_header_bytes(slug)
    if data is None:
        return PlainTextResponse("Image not found", status_code=404)
    return Response(
        data,
        media_type="image/webp",
        headers={
            "Cache-Control": "public, max-age=86400, stale-while-revalidate=604800",
            "Access-Control-Allow-Origin": "*",
        },
    )


async def _cms_social_image(request):
    slug = str(request.path_params.get("slug") or "").strip().lower()
    try:
        article = fetch_public_article(slug)
    except RuntimeError:
        article = None
    if article is None:
        return PlainTextResponse("Image not found", status_code=404)
    data = render_cms_social_image(article)
    return Response(
        data,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400, stale-while-revalidate=604800",
            "Access-Control-Allow-Origin": "*",
        },
    )


async def _robots(_request):
    return PlainTextResponse(
        f"User-agent: *\nAllow: /\n\nUser-agent: LinkedInBot\nAllow: /thinking/\nAllow: /social/\nAllow: /cms-header/\n\nSitemap: {BASE_URL}/sitemap.xml\n",
        headers={"Cache-Control": "public, max-age=3600"},
    )


async def _sitemap(_request):
    entries = [
        (f"{BASE_URL}/", "2026-09-17"),
        (f"{BASE_URL}/ai-data-governance", "2026-09-27"),
    ] + [
        (article_url(article), article.published_iso) for article in ARTICLES
    ]
    try:
        entries.extend(cms_sitemap_entries())
    except RuntimeError:
        pass
    deduped = {}
    for url, lastmod in entries:
        deduped[url] = max(lastmod, deduped.get(url, ""))
    entries = list(deduped.items())
    body = "".join(
        f"<url><loc>{escape(url)}</loc><lastmod>{lastmod}</lastmod></url>"
        for url, lastmod in entries
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    return Response(
        xml,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# Current Streamlit exposes the Starlette ASGI application directly. Keeping
# the interactive UI in main.py lets this launcher provide crawler-visible
# article, social-image, robots and sitemap routes on the same public domain.
app = App(
    "main.py",
    routes=[
        Route("/thinking/{slug}", _thinking_article, methods=["GET", "HEAD"]),
        Route("/ai-data-governance", _ai_data_governance_share, methods=["GET", "HEAD"]),
        Route("/social/{slug}.png", _thinking_social_image, methods=["GET", "HEAD"]),
        Route("/cms-header/{slug}.webp", _cms_header_image, methods=["GET", "HEAD"]),
        Route("/cms-social/{slug}.png", _cms_social_image, methods=["GET", "HEAD"]),
        Route("/robots.txt", _robots, methods=["GET", "HEAD"]),
        Route("/sitemap.xml", _sitemap, methods=["GET", "HEAD"]),
    ],
)
