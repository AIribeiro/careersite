from __future__ import annotations

import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from thinking_articles import (
    ARTICLES,
    ArticleMeta,
    article_app_url,
    article_share_url,
    article_social_image_url,
    article_url,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "profile_red_bg.jpg.jpg"
TARGET_DIR = ROOT / "static" / "thinking"
# LinkedIn's sharing module recommends 1.91:1 and documents 1200x627 as its
# minimum large-preview dimensions. Use that exact canvas for article cards.
SIZE = (1200, 627)

NAVY = "#0b1220"
WHITE = "#fffdf8"
COPPER = "#b86134"
COPPER_LIGHT = "#f0c09d"
EYEBROW = "#e6aa7d"
MUTED = "#c4ceda"
MUTED_DARK = "#95a2b4"
DIVIDER = "#364052"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    suffix = "-Bold" if bold else ""
    candidates = [
        Path(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf"),
        Path(
            "/usr/share/fonts/truetype/liberation2/"
            + ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
        ),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and bbox[2] - bbox[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _title_layout(draw: ImageDraw.ImageDraw, title: str) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in (56, 52, 48, 44, 40, 36):
        font = _font(size, bold=True)
        lines = _wrap(draw, title, font, 710)
        if len(lines) <= 4:
            return font, lines
    font = _font(34, bold=True)
    return font, _wrap(draw, title, font, 710)[:4]


def _social_path(article: ArticleMeta) -> Path:
    return TARGET_DIR / f"{article.slug}.png"


def _share_path(article: ArticleMeta) -> Path:
    return TARGET_DIR / f"{article.slug}.html"


def ensure_article_social_image(article: ArticleMeta) -> Path:
    target = _social_path(article)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and SOURCE.exists() and target.stat().st_mtime >= SOURCE.stat().st_mtime:
        try:
            with Image.open(target) as existing:
                if existing.size == SIZE and existing.format == "PNG":
                    return target
        except OSError:
            pass

    canvas = Image.new("RGB", SIZE, NAVY)
    draw = ImageDraw.Draw(canvas)

    if SOURCE.exists():
        with Image.open(SOURCE) as source:
            photo = ImageOps.fit(
                source.convert("RGB"),
                (330, SIZE[1]),
                method=Image.Resampling.LANCZOS,
                centering=(0.52, 0.38),
            )
        canvas.paste(photo, (870, 0))
        draw.rectangle((848, 0, 870, SIZE[1]), fill=COPPER)

    label = f"{article.kind.upper()} · {article.topic.upper()}"
    draw.text((70, 66), label, font=_font(20, bold=True), fill=EYEBROW)

    title_font, title_lines = _title_layout(draw, article.social_title)
    y = 132
    line_height = int(getattr(title_font, "size", 44) * 1.16)
    for line in title_lines:
        draw.text((70, y), line, font=title_font, fill=WHITE)
        y += line_height

    divider_y = min(430, max(360, y + 24))
    draw.line((70, divider_y, 760, divider_y), fill=DIVIDER, width=2)
    draw.text((70, divider_y + 28), "Jair Ribeiro", font=_font(25, bold=True), fill=COPPER_LIGHT)
    draw.text((70, divider_y + 68), "Enterprise AI & Data Leadership", font=_font(22), fill=MUTED)
    draw.text((70, 560), "jairribeiro-ai.streamlit.app", font=_font(18, bold=True), fill=MUTED_DARK)

    canvas.save(target, format="PNG", optimize=True)
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
    """Build the non-redirecting crawler document for /thinking/<slug>."""
    target = _share_path(article)
    target.parent.mkdir(parents=True, exist_ok=True)
    canonical = article_url(article)
    app_url = article_app_url(article)
    share = article_share_url(article)
    image = article_social_image_url(article)
    schema = json.dumps(_article_schema(article), ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(article.social_title, quote=True)
    description = html.escape(article.social_description, quote=True)
    seo_title = html.escape(article.seo_title, quote=True)
    canonical_html = html.escape(canonical, quote=True)
    app_url_html = html.escape(app_url, quote=True)
    share_html = html.escape(share, quote=True)
    image_html = html.escape(image, quote=True)
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
<title>{seo_title}</title>
<meta name="description" content="{html.escape(article.seo_description, quote=True)}">
<meta name="author" content="Jair Ribeiro">
<meta name="keywords" content="{html.escape(tags, quote=True)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{canonical_html}">
<link rel="image_src" href="{image_html}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{share_html}">
<meta property="og:image" content="{image_html}">
<meta property="og:image:url" content="{image_html}">
<meta property="og:image:secure_url" content="{image_html}">
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
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image_html}">
<meta name="twitter:image:alt" content="{html.escape(article.title + ' — Jair Ribeiro', quote=True)}">
<script type="application/ld+json">{schema}</script>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:760px;margin:70px auto;padding:0 24px;color:#11151b}}a{{color:#b86134}}.meta{{color:#5e6670;font-size:13px}}</style>
</head>
<body>
<p class="meta">{html.escape(article.kind_topic)} · {html.escape(article.published_label)}</p>
<h1>{html.escape(article.title)}</h1>
<p>{html.escape(article.standfirst)}</p>
<p><a href="{app_url_html}">Read the article by Jair Ribeiro →</a></p>
</body>
</html>
'''
    target.write_text(document, encoding="utf-8")
    return target


def ensure_article_social_assets(article: ArticleMeta) -> tuple[Path, Path]:
    return ensure_article_social_image(article), ensure_article_share_page(article)


def ensure_all_article_social_assets() -> tuple[tuple[Path, Path], ...]:
    return tuple(ensure_article_social_assets(article) for article in ARTICLES)
