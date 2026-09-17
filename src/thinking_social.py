from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageOps

from thinking_articles import (
    ARTICLES,
    ArticleMeta,
    article_app_url,
    article_social_image_url,
    article_url,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "static" / "thinking-visuals"
TARGET_DIR = ROOT / "static" / "thinking"
SIZE = (1200, 627)
GENERATOR_VERSION = "thinking-social-v5-article-visuals-2026-09-17"
BACKGROUND = "#07527d"


def _source_path(article: ArticleMeta) -> Path:
    return SOURCE_DIR / f"{article.key}.webp"


def _social_path(article: ArticleMeta) -> Path:
    return TARGET_DIR / f"{article.slug}.png"


def _signature_path(article: ArticleMeta) -> Path:
    return TARGET_DIR / f"{article.slug}.sha256"


def _share_path(article: ArticleMeta) -> Path:
    return TARGET_DIR / f"{article.slug}.html"


def _article_signature(article: ArticleMeta) -> str:
    source = _source_path(article)
    payload = {
        "generator": GENERATOR_VERSION,
        "size": SIZE,
        "key": article.key,
        "slug": article.slug,
        "title": article.social_title,
        "description": article.social_description,
        "kind": article.kind,
        "topic": article.topic,
        "published": article.published_iso,
        "tags": article.tags,
        "source_size": source.stat().st_size if source.exists() else 0,
        "source_mtime_ns": source.stat().st_mtime_ns if source.exists() else 0,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def ensure_article_social_image(article: ArticleMeta) -> Path:
    """Derive the Open Graph card from the article's canonical branded visual."""
    source = _source_path(article)
    if not source.is_file():
        raise FileNotFoundError(f"Missing Thinking visual: {source}")

    target = _social_path(article)
    signature_path = _signature_path(article)
    target.parent.mkdir(parents=True, exist_ok=True)
    signature = _article_signature(article)

    if target.exists() and signature_path.exists():
        try:
            if signature_path.read_text(encoding="utf-8").strip() == signature:
                with Image.open(target) as existing:
                    if existing.size == SIZE and existing.format == "PNG":
                        return target
        except OSError:
            pass

    with Image.open(source) as original:
        branded = ImageOps.fit(
            original.convert("RGB"),
            SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    branded.save(target, format="PNG", optimize=True)
    signature_path.write_text(signature + "\n", encoding="utf-8")
    return target


def _article_schema(article: ArticleMeta) -> dict[str, object]:
    canonical = article_url(article)
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.seo_description,
        "datePublished": article.published_iso,
        "dateModified": article.published_iso,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": [article_social_image_url(article)],
        "author": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": "https://jairribeiro-ai.streamlit.app/",
        },
        "publisher": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": "https://jairribeiro-ai.streamlit.app/",
        },
        "articleSection": article.topic,
        "keywords": list(article.tags),
    }


def ensure_article_share_page(article: ArticleMeta) -> Path:
    """Build the crawler document for /thinking/<slug>."""
    target = _share_path(article)
    target.parent.mkdir(parents=True, exist_ok=True)
    canonical = article_url(article)
    app_url = article_app_url(article)
    image = article_social_image_url(article)
    schema = json.dumps(_article_schema(article), ensure_ascii=False).replace("</", "<\\/")
    tags = ", ".join(article.tags)
    article_tags = "\n".join(
        f'<meta property="article:tag" content="{html.escape(tag, quote=True)}">'
        for tag in article.tags
    )

    document = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(article.seo_title, quote=True)}</title>
<meta name="description" content="{html.escape(article.seo_description, quote=True)}">
<meta name="author" content="Jair Ribeiro">
<meta name="keywords" content="{html.escape(tags, quote=True)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<link rel="image_src" href="{html.escape(image, quote=True)}">
<meta property="og:title" content="{html.escape(article.social_title, quote=True)}">
<meta property="og:description" content="{html.escape(article.social_description, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{html.escape(canonical, quote=True)}">
<meta property="og:image" content="{html.escape(image, quote=True)}">
<meta property="og:image:url" content="{html.escape(image, quote=True)}">
<meta property="og:image:secure_url" content="{html.escape(image, quote=True)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="627">
<meta property="og:image:alt" content="{html.escape(article.title + ' — Jair Ribeiro', quote=True)}">
<meta property="article:published_time" content="{article.published_iso}">
<meta property="article:modified_time" content="{article.published_iso}">
<meta property="article:author" content="Jair Ribeiro">
<meta property="article:section" content="{html.escape(article.topic, quote=True)}">
{article_tags}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(article.social_title, quote=True)}">
<meta name="twitter:description" content="{html.escape(article.social_description, quote=True)}">
<meta name="twitter:image" content="{html.escape(image, quote=True)}">
<meta name="twitter:image:alt" content="{html.escape(article.title + ' — Jair Ribeiro', quote=True)}">
<script type="application/ld+json">{schema}</script>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:760px;margin:70px auto;padding:0 24px;color:#11151b}}a{{color:#b86134}}.meta{{color:#5e6670;font-size:13px}}</style>
</head>
<body>
<p class="meta">{html.escape(article.kind_topic)} · {html.escape(article.published_label)}</p>
<h1>{html.escape(article.title)}</h1>
<p>{html.escape(article.standfirst)}</p>
<p><a href="{html.escape(app_url, quote=True)}">Read the article by Jair Ribeiro →</a></p>
</body>
</html>
'''
    target.write_text(document, encoding="utf-8")
    return target


def ensure_article_social_assets(article: ArticleMeta) -> tuple[Path, Path]:
    return ensure_article_social_image(article), ensure_article_share_page(article)


def ensure_all_article_social_assets() -> tuple[tuple[Path, Path], ...]:
    return tuple(ensure_article_social_assets(article) for article in ARTICLES)


def build_article_asset_manifest() -> dict[str, object]:
    assets = []
    for article in ARTICLES:
        image_path, html_path = ensure_article_social_assets(article)
        with Image.open(image_path) as image:
            width, height = image.size
            image_format = image.format
        assets.append(
            {
                "key": article.key,
                "slug": article.slug,
                "title": article.title,
                "topic": article.topic,
                "image": str(image_path.relative_to(ROOT)),
                "share_page": str(html_path.relative_to(ROOT)),
                "width": width,
                "height": height,
                "format": image_format,
                "signature": _article_signature(article),
            }
        )
    return {
        "generator": GENERATOR_VERSION,
        "size": list(SIZE),
        "count": len(assets),
        "articles": assets,
    }
