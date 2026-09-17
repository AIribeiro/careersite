from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thinking_articles import ARTICLES, ArticleMeta, BASE_URL
from thinking_social import ensure_article_social_image

DEFAULT_SHARE_BASE = "https://airibeiro.github.io/careersite"


def _human_url(article: ArticleMeta) -> str:
    query = urlencode(
        {
            "page": "thinking",
            "article": article.slug,
            "source": "linkedin",
            "content": article.slug,
        }
    )
    return f"{BASE_URL}/?{query}"


def _share_url(article: ArticleMeta, share_base: str) -> str:
    return f"{share_base.rstrip('/')}/thinking/{article.slug}/"


def _image_url(article: ArticleMeta, share_base: str) -> str:
    return f"{share_base.rstrip('/')}/social/{article.slug}.png"


def _schema(article: ArticleMeta, share_base: str) -> dict[str, object]:
    share_url = _share_url(article, share_base)
    image_url = _image_url(article, share_base)
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.seo_description,
        "datePublished": article.published_iso,
        "dateModified": article.published_iso,
        "mainEntityOfPage": {"@type": "WebPage", "@id": share_url},
        "image": [image_url],
        "author": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": BASE_URL,
        },
        "publisher": {
            "@type": "Person",
            "name": "Jair Ribeiro",
            "url": BASE_URL,
        },
        "articleSection": article.topic,
        "keywords": list(article.tags),
    }


def _article_html(article: ArticleMeta, share_base: str) -> str:
    share_url = _share_url(article, share_base)
    image_url = _image_url(article, share_base)
    human_url = _human_url(article)
    schema_json = json.dumps(_schema(article, share_base), ensure_ascii=False).replace("</", "<\\/")
    tag_meta = "\n".join(
        f'<meta property="article:tag" content="{html.escape(tag, quote=True)}">'
        for tag in article.tags
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(article.seo_title)}</title>
<meta name="description" content="{html.escape(article.seo_description, quote=True)}">
<meta name="author" content="Jair Ribeiro">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{html.escape(share_url, quote=True)}">
<link rel="image_src" href="{html.escape(image_url, quote=True)}">
<meta property="og:title" content="{html.escape(article.social_title, quote=True)}">
<meta property="og:description" content="{html.escape(article.social_description, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{html.escape(share_url, quote=True)}">
<meta property="og:image" content="{html.escape(image_url, quote=True)}">
<meta property="og:image:secure_url" content="{html.escape(image_url, quote=True)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="627">
<meta property="og:image:alt" content="{html.escape(article.title + ' — Jair Ribeiro', quote=True)}">
<meta property="article:published_time" content="{article.published_iso}">
<meta property="article:modified_time" content="{article.published_iso}">
<meta property="article:author" content="Jair Ribeiro">
<meta property="article:section" content="{html.escape(article.topic, quote=True)}">
{tag_meta}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(article.social_title, quote=True)}">
<meta name="twitter:description" content="{html.escape(article.social_description, quote=True)}">
<meta name="twitter:image" content="{html.escape(image_url, quote=True)}">
<script type="application/ld+json">{schema_json}</script>
<style>
body{{margin:0;background:#f4f0e8;color:#11151b;font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:820px;margin:8vh auto;padding:36px;background:#fffdf8;border-top:5px solid #b86134}}
.kicker{{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#b86134}}
h1{{font:500 clamp(38px,6vw,68px)/1.02 Georgia,serif;letter-spacing:-.03em;margin:18px 0}}
p{{color:#5e6670}}a{{display:inline-block;margin-top:16px;color:#fff;background:#0b1220;padding:12px 16px;text-decoration:none;font-weight:700}}
</style>
<script>
window.addEventListener('load', () => {{
  window.setTimeout(() => window.location.replace({json.dumps(human_url)}), 900);
}});
</script>
</head>
<body>
<main>
<div class="kicker">{html.escape(article.kind_topic)} · {html.escape(article.published_label)}</div>
<h1>{html.escape(article.title)}</h1>
<p>{html.escape(article.standfirst)}</p>
<p>Opening the full article on Jair Ribeiro's portfolio.</p>
<a href="{html.escape(human_url, quote=True)}">Read the article →</a>
</main>
</body>
</html>
'''


def build(output: Path, share_base: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "thinking").mkdir(parents=True, exist_ok=True)
    (output / "social").mkdir(parents=True, exist_ok=True)
    (output / ".nojekyll").write_text("", encoding="utf-8")

    links: list[str] = []
    for article in ARTICLES:
        source_image = ensure_article_social_image(article)
        target_image = output / "social" / f"{article.slug}.png"
        shutil.copy2(source_image, target_image)

        article_dir = output / "thinking" / article.slug
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(
            _article_html(article, share_base), encoding="utf-8"
        )
        links.append(
            f'<li><a href="thinking/{html.escape(article.slug)}/">{html.escape(article.title)}</a></li>'
        )

    index = "<!doctype html><html><head><meta charset='utf-8'><meta name='robots' content='noindex'></head><body><h1>Jair Ribeiro — Thinking</h1><ul>" + "".join(links) + "</ul></body></html>"
    (output / "index.html").write_text(index, encoding="utf-8")

    sitemap_items = "".join(
        f"<url><loc>{html.escape(_share_url(article, share_base))}</loc><lastmod>{article.published_iso}</lastmod></url>"
        for article in ARTICLES
    )
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap_items}</urlset>'
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static LinkedIn share pages for Thinking articles.")
    parser.add_argument("--output", default="_share_site")
    parser.add_argument("--share-base", default=DEFAULT_SHARE_BASE)
    args = parser.parse_args()
    output = ROOT / args.output
    build(output, args.share_base)
    print(f"Built {len(ARTICLES)} LinkedIn share pages in {output}")


if __name__ == "__main__":
    main()
