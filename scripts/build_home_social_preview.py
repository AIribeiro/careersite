"""Crawler-readable homepage social preview for the existing GitHub Pages bridge.

This page is an optional distribution entrypoint. It does not change Spaceship's
masked forwarding, the canonical portfolio, reader authentication, or DNS.
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRANDED_SITE = "https://jairribeiro.com/"
PREVIEW_FILE = ROOT / "static" / "jair-ribeiro-social-preview.png"
TITLE = "Jair Ribeiro | Executive AI & Data Leadership"
DESCRIPTION = (
    "Executive perspectives on enterprise AI, data strategy, governance "
    "and adoption. Explore practical thinking, briefings and advisory."
)
IMAGE_NAME = "jair-ribeiro-home.png"
FAVICON_NAME = "favicon.png"


def write_home_share(output: Path, share_base: str) -> None:
    """Write one static 1200×630 OG landing page and its local image assets."""
    parsed = urlsplit(share_base)
    if (
        parsed.scheme != "https" or parsed.hostname != "airibeiro.github.io"
        or parsed.path.rstrip("/") != "/careersite"
        or parsed.query or parsed.fragment
    ):
        raise ValueError("Homepage bridge must use the established GitHub Pages site.")
    if not PREVIEW_FILE.is_file():
        raise FileNotFoundError("Approved portfolio social image is not committed.")

    with Image.open(PREVIEW_FILE) as source:
        if source.format != "PNG" or source.size != (1200, 630):
            raise ValueError("Expected approved 1200x630 PNG social image.")

    output.mkdir(parents=True, exist_ok=True)
    image_dir = output / "social"
    image_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PREVIEW_FILE, image_dir / IMAGE_NAME)

    # Tab favicon is separate from the social preview and deliberately simple.
    favicon = Image.new("RGB", (96, 96), "#0b1220")
    draw = ImageDraw.Draw(favicon)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 49)
    except OSError:
        font = ImageFont.load_default()
    draw.text((14, 15), "JR", fill="#e9bd9d", font=font)
    favicon.save(output / FAVICON_NAME, format="PNG", optimize=True)

    base = share_base.rstrip("/")
    url = base + "/"
    image_url = base + "/social/" + IMAGE_NAME
    favicon_url = base + "/" + FAVICON_NAME
    # The HTML head must be complete in the first server response. Client-side
    # Streamlit meta injection and an iframe do not satisfy social scrapers.
    markup = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESCRIPTION__">
<meta name="author" content="Jair Ribeiro">
<meta name="robots" content="noindex,follow,max-image-preview:large">
<link rel="canonical" href="__BRANDED__">
<link rel="icon" type="image/png" sizes="96x96" href="__FAVICON__">
<link rel="image_src" href="__IMAGE__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESCRIPTION__">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jair Ribeiro">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="__URL__">
<meta property="og:image" content="__IMAGE__">
<meta property="og:image:secure_url" content="__IMAGE__">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Jair Ribeiro — Executive AI and Data Leadership">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESCRIPTION__">
<meta name="twitter:image" content="__IMAGE__">
<meta name="twitter:image:alt" content="Jair Ribeiro — Executive AI and Data Leadership">
<style>
:root{color-scheme:light}
body{margin:0;background:#f4f0e8;color:#0b1220;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:660px;margin:10vh auto;padding:36px 24px}
small{color:#a35831;letter-spacing:.12em;text-transform:uppercase;font-weight:700}
h1{font:500 clamp(34px,6vw,58px)/1.07 Georgia,serif;letter-spacing:-.03em}
a{color:#0b1220;text-decoration:underline;text-underline-offset:4px}
</style>
<script>
// Social bots read this static head. Real browsers continue to the portfolio.
// Query attribution is passed through; unknown query keys are discarded.
window.addEventListener('load', () => {
  const ua = String(navigator.userAgent || '').toLowerCase();
  if (/bot|crawler|spider|facebookexternalhit|linkedinbot|twitterbot|slackbot|discordbot|telegrambot|whatsapp|preview/.test(ua)) return;
  const destination = new URL(__BRANDED_JS__);
  const allowed = new Set(['source','src','role','utm_source','utm_medium','utm_campaign','utm_content','content','page','article']);
  const incoming = new URLSearchParams(window.location.search);
  for (const [key, value] of incoming.entries()) {
    if (allowed.has(key) && !destination.searchParams.has(key)) {
      destination.searchParams.set(key, value.slice(0, 150));
    }
  }
  const link = document.getElementById('open-portfolio');
  if (link) link.href = destination.toString();
  window.location.replace(destination.toString());
});
</script>
</head>
<body>
<main>
<small>Executive AI &amp; Data Leadership</small>
<h1>Jair Ribeiro</h1>
<p>Strategy, governance, adoption and practical executive perspectives on enterprise AI.</p>
<p><a id="open-portfolio" href="__BRANDED__">Open portfolio</a></p>
<noscript><p>Continue to the portfolio using the link above.</p></noscript>
</main>
</body>
</html>
"""
    replacements = {
        "__TITLE__": html.escape(TITLE, quote=True),
        "__DESCRIPTION__": html.escape(DESCRIPTION, quote=True),
        "__BRANDED__": html.escape(BRANDED_SITE, quote=True),
        "__BRANDED_JS__": json.dumps(BRANDED_SITE),
        "__URL__": html.escape(url, quote=True),
        "__IMAGE__": html.escape(image_url, quote=True),
        "__FAVICON__": html.escape(favicon_url, quote=True),
    }
    for placeholder, replacement in replacements.items():
        markup = markup.replace(placeholder, replacement)
    (output / "index.html").write_text(markup, encoding="utf-8")

    # Public contact entrypoint. Preserve the existing analytics attribution
    # and legacy URL without exposing the campaign name in the share URL.
    # Keep canonical SEO and the existing home bridge unchanged.
    outreach_url = base + "/getintouch/"
    outreach_destination = BRANDED_SITE + "?source=outreach"
    outreach = markup.replace(
        f'property="og:url" content="{html.escape(url, quote=True)}"',
        f'property="og:url" content="{html.escape(outreach_url, quote=True)}"',
    ).replace(
        "  const link = document.getElementById('open-portfolio');",
        "  if (!destination.searchParams.has('source') && !destination.searchParams.has('src') && !destination.searchParams.has('utm_source')) {\n"
        "    destination.searchParams.set('source', 'outreach');\n"
        "  }\n"
        "  const link = document.getElementById('open-portfolio');",
    ).replace(
        f'id="open-portfolio" href="{html.escape(BRANDED_SITE, quote=True)}"',
        f'id="open-portfolio" href="{html.escape(outreach_destination, quote=True)}"',
    )
    for route in ("getintouch", "outreach"):
        # The old route remains a compatibility alias with the new OG URL.
        route_dir = output / route
        route_dir.mkdir(parents=True, exist_ok=True)
        (route_dir / "index.html").write_text(outreach, encoding="utf-8")

