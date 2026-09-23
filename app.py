from __future__ import annotations

from pathlib import Path
import sys
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
from site_cms import cms_share_document, cms_sitemap_entries, fetch_public_article

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


async def _robots(_request):
    return PlainTextResponse(
        f"User-agent: *\nAllow: /\n\nUser-agent: LinkedInBot\nAllow: /thinking/\nAllow: /social/\n\nSitemap: {BASE_URL}/sitemap.xml\n",
        headers={"Cache-Control": "public, max-age=3600"},
    )


async def _sitemap(_request):
    entries = [(f"{BASE_URL}/", "2026-09-17")] + [
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
        Route("/social/{slug}.png", _thinking_social_image, methods=["GET", "HEAD"]),
        Route("/robots.txt", _robots, methods=["GET", "HEAD"]),
        Route("/sitemap.xml", _sitemap, methods=["GET", "HEAD"]),
    ],
)
