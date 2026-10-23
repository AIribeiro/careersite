from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thinking_articles import ARTICLES, ArticleMeta, BASE_URL
from thinking_social import ensure_article_social_image
from site_shortlinks import registered_short_links

DEFAULT_SHARE_BASE = "https://airibeiro.github.io/careersite"
X_HANDLE = "@Liberoliber"
X_CARD_VERSION = "xcard-20260917-1"


def _human_url(article: ArticleMeta, source: str = "social") -> str:
    query = urlencode(
        {
            "page": "thinking",
            "article": article.slug,
            "source": source,
            "content": article.slug,
            "utm_source": source,
            "utm_medium": "social",
            "utm_campaign": "thinking",
            "utm_content": article.slug,
        }
    )
    return f"{BASE_URL}/?{query}"


def _share_url(article: ArticleMeta, share_base: str) -> str:
    return f"{share_base.rstrip('/')}/thinking/{article.slug}/"


def _image_url(article: ArticleMeta, share_base: str) -> str:
    return f"{share_base.rstrip('/')}/social/{article.slug}.png"


def _x_image_url(article: ArticleMeta, share_base: str) -> str:
    return (
        f"{share_base.rstrip('/')}/social-x/{article.slug}.jpg"
        f"?v={X_CARD_VERSION}"
    )


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
    x_image_url = _x_image_url(article, share_base)
    fallback_human_url = _human_url(article, "social")
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
<meta name="twitter:site" content="{X_HANDLE}">
<meta name="twitter:creator" content="{X_HANDLE}">
<meta name="twitter:url" content="{html.escape(share_url, quote=True)}">
<meta name="twitter:title" content="{html.escape(article.social_title, quote=True)}">
<meta name="twitter:description" content="{html.escape(article.social_description, quote=True)}">
<meta name="twitter:image" content="{html.escape(x_image_url, quote=True)}">
<meta name="twitter:image:alt" content="{html.escape(article.title + ' — Jair Ribeiro', quote=True)}">
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
  const ua = String(navigator.userAgent || '').toLowerCase();
  if (/bot|crawler|spider|slurp|facebookexternalhit|linkedinbot|twitterbot/.test(ua)) return;

  const params = new URLSearchParams(window.location.search);
  let source = String(params.get('source') || '').trim().toLowerCase();
  if (source === 'twitter') source = 'x';
  if (source === 'fb') source = 'facebook';
  if (!['linkedin', 'x', 'facebook', 'social'].includes(source)) {{
    try {{
      const ref = document.referrer ? new URL(document.referrer).hostname.toLowerCase() : '';
      if (ref.includes('linkedin')) source = 'linkedin';
      else if (ref === 't.co' || ref.includes('x.com') || ref.includes('twitter.com')) source = 'x';
      else if (ref.includes('facebook.com') || ref.includes('fb.com') || ref.includes('messenger.com')) source = 'facebook';
      else source = 'social';
    }} catch (_) {{
      source = 'social';
    }}
  }}

  let campaign = String(params.get('utm_campaign') || '').trim().toLowerCase();
  campaign = campaign.replace(/[^a-z0-9_-]/g, '').slice(0, 100);
  if (!campaign) campaign = source === 'facebook' ? 'facebook_groups' : 'thinking';

  const target = new URL({json.dumps(BASE_URL + '/')});
  target.searchParams.set('page', 'thinking');
  target.searchParams.set('article', {json.dumps(article.slug)});
  target.searchParams.set('source', source);
  target.searchParams.set('content', {json.dumps(article.slug)});
  target.searchParams.set('utm_source', source);
  target.searchParams.set('utm_medium', 'social');
  target.searchParams.set('utm_campaign', campaign);
  target.searchParams.set('utm_content', {json.dumps(article.slug)});

  const link = document.getElementById('read-article');
  if (link) link.href = target.toString();
  window.setTimeout(() => window.location.replace(target.toString()), 900);
}});
</script>
</head>
<body>
<main>
<div class="kicker">{html.escape(article.kind_topic)} · {html.escape(article.published_label)}</div>
<h1>{html.escape(article.title)}</h1>
<p>{html.escape(article.standfirst)}</p>
<p>Opening the full article on Jair Ribeiro's portfolio.</p>
<a id="read-article" href="{html.escape(fallback_human_url, quote=True)}">Read the article →</a>
</main>
</body>
</html>
'''


def _weekly_issue_metadata(slug: str) -> dict[str, object] | None:
    """Read published-week registry metadata, never infer week from a code."""
    registry = ROOT / "src" / "weekly_ai_shortlink_registry.json"
    if not registry.is_file():
        return None
    payload = json.loads(registry.read_text(encoding="utf-8"))
    for edition in payload.get("editions", []):
        if edition.get("slug") == slug:
            return edition
    return None


def _static_shortlink_html(code: str, slug: str, channel: str, target: str) -> str:
    """Source-preserving static redirect with accurate per-edition social cards.

    The image is specific to the week only when an actual approved file exists.
    Never mislabel the generic portfolio card as a generated weekly cover.
    """
    registered_titles = {
        "ai-is-turning-data-definitions-into-a-leadership-problem":
            "AI Is Turning Data Definitions Into a Leadership Problem",
        "if-ai-does-the-routine-work-how-will-we-develop-the-next-experts":
            "If AI Does the Routine Work, How Will We Develop the Next Experts?",
        "ai-can-make-every-team-faster-and-still-leave-the-business-slow":
            "AI Can Make Every Team Faster and Still Leave the Business Slow",
    }
    edition = _weekly_issue_metadata(slug)
    if edition and edition.get("distribution_mode") == "friday_wrap":
        year = int(edition["iso_year"])
        week = int(edition["iso_week"])
        issue_title = str(edition.get("edition_title") or "").strip()
        if not issue_title:
            raise ValueError("Published Friday cover needs a verified edition_title: " + slug)
        title = f"WEEKLY AI · Week {week} · {year} — {issue_title}"
        description = "My AI week: selected developments and a practical enterprise AI leadership perspective."
    else:
        title = registered_titles.get(slug, slug.replace("-", " ").title())
        description = "Read the full article on Jair Ribeiro's Enterprise AI & Data Portfolio."
    image_path = ROOT / "static" / "weekly-ai" / f"{slug}.png"
    cover_ready = bool(edition and edition.get("distribution_mode") == "friday_wrap" and image_path.is_file())
    if cover_ready:
        og_image = f"{DEFAULT_SHARE_BASE}/social/{slug}.png"
        x_image = f"{DEFAULT_SHARE_BASE}/social-x/{slug}.jpg"
        image_props = (
            f'<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="627">\n'
            f'<meta name="twitter:image" content="{html.escape(x_image, quote=True)}">\n'
            f'<meta name="twitter:image:alt" content="{html.escape(title, quote=True)}">'
        )
    else:
        og_image = f"{BASE_URL}/app/static/jair-ribeiro-social-preview.png"
        image_props = ""
    destination = html.escape(target, quote=True)
    script_target = json.dumps(target).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Jair Ribeiro</title>
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:image" content="{html.escape(og_image, quote=True)}">
{image_props}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title, quote=True)}">
<meta name="twitter:description" content="{html.escape(description, quote=True)}">
<meta http-equiv="refresh" content="0;url={destination}">
<script>window.location.replace({script_target});</script>
</head>
<body>
<p>Opening the article in the AI &amp; Data Portfolio.</p>
<p><a href="{destination}">Read the article</a></p>
</body>
</html>
"""



def _write_x_image(source_image: Path, target_image: Path) -> None:
    with Image.open(source_image) as image:
        x_image = ImageOps.fit(
            image.convert("RGB"),
            (1200, 600),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        x_image.save(target_image, format="JPEG", quality=90, optimize=True, progressive=True)


def build(output: Path, share_base: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "thinking").mkdir(parents=True, exist_ok=True)
    (output / "social").mkdir(parents=True, exist_ok=True)
    (output / "social-x").mkdir(parents=True, exist_ok=True)
    (output / ".nojekyll").write_text("", encoding="utf-8")

    links: list[str] = []
    for article in ARTICLES:
        source_image = ensure_article_social_image(article)
        target_image = output / "social" / f"{article.slug}.png"
        shutil.copy2(source_image, target_image)
        _write_x_image(source_image, output / "social-x" / f"{article.slug}.jpg")

        article_dir = output / "thinking" / article.slug
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(
            _article_html(article, share_base), encoding="utf-8"
        )
        links.append(
            f'<li><a href="thinking/{html.escape(article.slug)}/">{html.escape(article.title)}</a></li>'
        )

    # Publish the approved weekly cover alongside the three platform redirects.
    # Generated assets must be committed by the Friday editorial workflow first.
    registry = ROOT / "src" / "weekly_ai_shortlink_registry.json"
    if registry.is_file():
        editions = json.loads(registry.read_text(encoding="utf-8")).get("editions", [])
        for edition in editions:
            if edition.get("distribution_mode") != "friday_wrap":
                continue
            slug = str(edition["slug"])
            approved_cover = ROOT / "static" / "weekly-ai" / f"{slug}.png"
            if approved_cover.is_file():
                with Image.open(approved_cover) as image:
                    if image.size != (1200, 627) or image.format != "PNG":
                        raise ValueError("Friday cover must be a 1200 × 627 PNG: " + slug)
                shutil.copy2(approved_cover, output / "social" / f"{slug}.png")
                _write_x_image(approved_cover, output / "social-x" / f"{slug}.jpg")

    # GitHub Pages serves stable, source-specific URLs independently of
    # the Streamlit Cloud query-router and its outer application iframe.
    for code, slug, channel, target in registered_short_links():
        alias_dir = output / "go" / code
        alias_dir.mkdir(parents=True, exist_ok=True)
        (alias_dir / "index.html").write_text(
            _static_shortlink_html(code, slug, channel, target),
            encoding="utf-8",
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
    parser = argparse.ArgumentParser(description="Build static social share pages for Thinking articles.")
    parser.add_argument("--output", default="_share_site")
    parser.add_argument("--share-base", default=DEFAULT_SHARE_BASE)
    args = parser.parse_args()
    output = ROOT / args.output
    build(output, args.share_base)
    print(f"Built {len(ARTICLES)} social share pages in {output}")


if __name__ == "__main__":
    main()
