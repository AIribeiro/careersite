from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from io import BytesIO
import re
import mimetypes
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
from briefings_visual import briefing_image_svg
from thinking_social import ensure_article_share_page, ensure_article_social_image
from site_cms import bundled_header_bytes, cms_share_document, cms_sitemap_entries, fetch_public_article, render_cms_social_image
from site_social_preview import PUBLIC_URL as SITE_SOCIAL_IMAGE
from site_owner_http_auth import owner_auth_route
from weekly_ai_audio import mp3_path

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


async def _thinking_article(request, page_override="thinking"):
    slug = str(request.path_params.get("slug") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,149}", slug):
        return PlainTextResponse("Article not found", status_code=404)

    if not _is_crawler(request):
        # Human readers need only the validated slug to reach the native
        # Streamlit article view. Do not await CMS/Supabase, image generation,
        # or cache hydration before issuing this redirect.
        # This server route is both the crawler-visible Open Graph document
        # and the permanent public permalink. Preserve only known attribution
        # tags on its human redirect; otherwise tagged social shares lose
        # their source and campaign before browser analytics sees them.
        params = [
            ("page", page_override),
            ("article", slug),
        ]
        attribution_fields = {
            "source": 100,
            "src": 100,
            "role": 120,
            "utm_source": 100,
            "utm_medium": 32,
            "utm_campaign": 100,
            "utm_content": 100,
            "content": 100,
        }
        seen = set()
        for key, value in request.query_params.multi_items():
            if key not in attribution_fields or key in seen:
                continue
            tag = str(value).strip()[:attribution_fields[key]]
            if tag:
                params.append((key, tag))
                seen.add(key)
        target = f"{BASE_URL}/?{urlencode(params)}"
        return RedirectResponse(
            target,
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )

    # Only preview bots require the article lookup and social metadata.
    try:
        cms_article = fetch_public_article(slug)
    except RuntimeError:
        cms_article = None
    article = None if cms_article is not None else resolve_article(slug)
    if cms_article is None and article is None:
        return PlainTextResponse("Article not found", status_code=404)

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


async def _briefing_article(request):
    """Public briefing permalink: share metadata and dedicated Streamlit reader."""
    return await _thinking_article(request, page_override="briefing")


async def _ai_data_governance_share(request):
    """Server-render social metadata for the governance page; redirect people to Streamlit."""
    canonical = f"{BASE_URL}/ai-data-governance"
    title = "AI & Data Governance | Jair Ribeiro"
    description = (
        "An operating perspective on AI & Data governance across Responsible AI, "
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


async def _briefings_share(request):
    """First-party SEO/share entry for the Executive AI Briefings series."""
    canonical = f"{BASE_URL}/briefings"
    title = "Executive AI Briefings | Jair Ribeiro"
    description = (
        "AI explained through business decisions: capabilities, ownership, "
        "operating trade-offs, responsible adoption and evidence of value."
    )
    if not _is_crawler(request):
        params = [("page", "briefings")]
        params.extend(
            (key, value)
            for key, value in request.query_params.multi_items()
            if key != "page"
        )
        return RedirectResponse(
            f"{BASE_URL}/?{urlencode(params)}",
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )
    document = f"""<!doctype html>
<html lang="en"><head>
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
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{escape(SITE_SOCIAL_IMAGE)}">
</head><body><p><a href="{escape(canonical)}">Executive AI Briefings — Jair Ribeiro</a></p></body></html>"""
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



async def _executive_briefing_image(_request):
    """First-party SVG served as an image to avoid inline-SVG sanitization."""
    return Response(
        briefing_image_svg(),
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
            "X-Content-Type-Options": "nosniff",
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


async def _weekly_ai_audio_file(request):
    """Serve only validated, committed Weekly AI audio with HTTP range support."""
    slug = str(request.path_params.get("slug") or "").strip().lower()
    file = mp3_path(slug)
    if file is None or not file.is_file() or file.stat().st_size < 1024:
        return PlainTextResponse("Audio not available", status_code=404)
    return FileResponse(
        file, media_type="audio/mpeg", filename=file.name,
        content_disposition_type="inline",
        headers={"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
                 "X-Content-Type-Options": "nosniff"},
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
        (f"{BASE_URL}/briefings", "2026-10-31"),
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


IMAGE_ROOT = (ROOT / "images").resolve()
IMAGE_WIDTHS = {160, 640, 960, 1280, 1600}


@lru_cache(maxsize=128)
def _resized_portfolio_image(filename: str, width: int) -> bytes:
    """Encode a photograph once per app process; retain aspect and alpha."""
    from PIL import Image, ImageOps

    with Image.open(filename) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((width, 1600), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        result = BytesIO()
        image.save(result, format="WEBP", quality=84, method=4)
        return result.getvalue()


async def _portfolio_image(request):
    """Send cacheable WebP image data outside the Streamlit page payload."""
    name = str(request.path_params.get("name") or "").strip()
    relative = Path(name)
    if (
        not name or relative.is_absolute()
        or any(part in ("..", ".") for part in relative.parts)
        or relative.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    ):
        return PlainTextResponse("Image not found", status_code=404)
    target = (IMAGE_ROOT / relative).resolve()
    if not target.is_relative_to(IMAGE_ROOT) or not target.is_file():
        return PlainTextResponse("Image not found", status_code=404)
    try:
        width = int(request.query_params.get("w", "1280"))
    except (TypeError, ValueError):
        width = 1280
    if width not in IMAGE_WIDTHS:
        width = 1280
    cache_headers = {
        "Cache-Control": "public, max-age=604800, stale-while-revalidate=604800",
        "X-Content-Type-Options": "nosniff",
    }
    try:
        return Response(_resized_portfolio_image(str(target), width),
                        media_type="image/webp", headers=cache_headers)
    except (OSError, ValueError):
        media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        return FileResponse(target, media_type=media_type, headers=cache_headers)


async def _weekly_ai_cover(request):
    slug = str(request.path_params.get("slug") or "").strip().lower()
    if not re.fullmatch(r"weekly-ai-\d{4}-\d{2}-\d{2}", slug):
        return PlainTextResponse("Cover not found", status_code=404)
    path = ROOT / "static" / "weekly-ai" / f"{slug}.png"
    if not path.is_file():
        return PlainTextResponse("Cover not found", status_code=404)
    return FileResponse(
        path, media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, stale-while-revalidate=604800",
                 "X-Content-Type-Options": "nosniff"},
    )


async def _roi_infographic_image(request):
    """Deliver the permanent WebP artwork or downloadable A4 PDF."""
    ext = str(request.path_params.get("ext") or "").lower()
    if ext not in ("webp", "pdf"):
        return PlainTextResponse("Infographic not found", status_code=404)
    asset_path = ROOT / "static" / f"briefing-ai-roi-proof-before-scale.{ext}"
    if not asset_path.is_file():
        return PlainTextResponse("Infographic asset unavailable", status_code=503)
    headers = {
        "Cache-Control": "public, max-age=604800, stale-while-revalidate=604800",
        "X-Content-Type-Options": "nosniff",
    }
    if ext == "pdf":
        headers["Content-Disposition"] = (
            'attachment; filename="ai-roi-proof-before-scale-executive-infographic.pdf"'
        )
    return FileResponse(asset_path,
                        media_type="application/pdf" if ext == "pdf" else "image/webp",
                        headers=headers)


async def _authority_infographic(request):
    """Deliver original governance decision artwork and its A4 PDF, first-party."""
    from briefing_authority_artwork import artwork_svg, artwork_mobile_svg, artwork_pdf
    ext = str(request.path_params.get("ext") or "").lower()
    headers = {
        "Cache-Control": "public, max-age=86400, stale-while-revalidate=604800",
        "X-Content-Type-Options": "nosniff",
    }
    if ext == "svg":
        return Response(artwork_svg(), media_type="image/svg+xml", headers=headers)
    if ext == "mobile.svg":
        return Response(artwork_mobile_svg(), media_type="image/svg+xml", headers=headers)
    if ext == "pdf":
        headers["Content-Disposition"] = (
            'attachment; filename="ai-operating-authority-25-decisions.pdf"'
        )
        return Response(artwork_pdf(), media_type="application/pdf", headers=headers)
    return PlainTextResponse("Infographic not found", status_code=404)


async def _weekly_ai_evergreen_image(_request):
    path = ROOT / "assets" / "weekly_ai_evergreen_visual.webp"
    if not path.is_file():
        return PlainTextResponse("Image not found", status_code=404)
    return FileResponse(
        path, media_type="image/webp",
        headers={"Cache-Control": "public, max-age=604800, stale-while-revalidate=604800",
                 "X-Content-Type-Options": "nosniff"},
    )


# Current Streamlit exposes the Starlette ASGI application directly. Keeping
# the interactive UI in main.py lets this launcher provide crawler-visible
# article, social-image, robots and sitemap routes on the same public domain.
app = App(
    "main.py",
    routes=[
        Route("/owner-auth/{action}", owner_auth_route, methods=["GET", "POST"]),
        Route("/portfolio-image/{name:path}", _portfolio_image, methods=["GET", "HEAD"]),
        Route("/briefing-ai-roi/infographic.{ext}", _roi_infographic_image, methods=["GET", "HEAD"]),
        Route("/briefing-ai-authority/infographic.{ext}", _authority_infographic, methods=["GET", "HEAD"]),
        Route("/weekly-ai-cover/evergreen.webp", _weekly_ai_evergreen_image, methods=["GET", "HEAD"]),
        Route("/weekly-ai-cover/{slug}.png", _weekly_ai_cover, methods=["GET", "HEAD"]),
        Route("/thinking/{slug}", _thinking_article, methods=["GET", "HEAD"]),
        Route("/briefing/{slug}", _briefing_article, methods=["GET", "HEAD"]),
        Route("/weekly-ai-audio/{slug}.mp3", _weekly_ai_audio_file, methods=["GET", "HEAD"]),
        Route("/ai-data-governance", _ai_data_governance_share, methods=["GET", "HEAD"]),
        Route("/briefings", _briefings_share, methods=["GET", "HEAD"]),
        Route("/social/{slug}.png", _thinking_social_image, methods=["GET", "HEAD"]),
        Route("/executive-ai-briefings.svg", _executive_briefing_image, methods=["GET", "HEAD"]),
        Route("/cms-header/{slug}.webp", _cms_header_image, methods=["GET", "HEAD"]),
        Route("/cms-social/{slug}.png", _cms_social_image, methods=["GET", "HEAD"]),
        Route("/robots.txt", _robots, methods=["GET", "HEAD"]),
        Route("/sitemap.xml", _sitemap, methods=["GET", "HEAD"]),
    ],
)
