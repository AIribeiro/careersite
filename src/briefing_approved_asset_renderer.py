from __future__ import annotations

"""Shared, source-locked premium infographic delivery for new Executive Briefings.

New editions require only a per-slug immutable artwork manifest and the
approved CMS row. The same reader produces a single first-party infographic,
a separate A4 PDF CTA, and bounded data:image/webp assets; no new article-
specific Python renderer or browser image request is needed.

Legacy editions without manifests remain on their existing proven paths.
"""

import base64
import hashlib
from html import escape
from io import BytesIO
import json
from functools import lru_cache
from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "static" / "briefing-artwork"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.(?:webp|pdf)$")
HASH = re.compile(r"^[a-f0-9]{64}$")
MAX_INLINE_BYTES = 1_500_000
MAX_PDF_BYTES = 12_000_000

CSS = """<style>
.site .canonical-infographic{max-width:980px;margin:26px auto 38px;background:#fffdf9;
padding:clamp(9px,1.6vw,20px);border:1px solid #d6e2e4;
box-shadow:0 14px 40px rgba(12,38,62,.065)}
.site .canonical-infographic-top{display:flex;align-items:center;
justify-content:space-between;gap:22px;padding:8px 5px 20px}
.site .canonical-infographic-heading{min-width:0}
.site .canonical-infographic-kicker{font:800 10px/1.5 Arial,sans-serif;
text-transform:uppercase;letter-spacing:.13em;color:#996a49}
.site .canonical-infographic-heading h2{font:500 clamp(24px,2.9vw,34px)/1.16 Georgia,serif;
margin:8px 0;color:#122b41}
.site .canonical-infographic-heading p{font:13px/1.6 Arial,sans-serif;
color:#566b76;margin:0}
.site .canonical-infographic-download{display:inline-flex;align-items:center;
justify-content:center;flex:0 0 auto;min-height:46px;border-radius:5px;
background:#13354b;border:1px solid #13354b;padding:12px 19px;
font:750 12px/1.45 Arial,sans-serif;color:white!important;
text-decoration:none!important}
.site .canonical-infographic-download:hover{background:#22566e}
.site .canonical-infographic-download:focus-visible{outline:3px solid #3b91a5;outline-offset:3px}
.site .canonical-infographic img{width:100%;height:auto;max-width:100%;
background:#f8faf9;border:1px solid #dce5e7}
.site .canonical-infographic .canonical-mobile{display:none}
.site .canonical-infographic .canonical-desktop{display:block}
.site .canonical-infographic figcaption{margin:14px 4px 2px;
font:12px/1.65 Arial,sans-serif;color:#596c77}
@media(max-width:750px){
.site .canonical-infographic{padding:7px}
.site .canonical-infographic-top{display:block;padding:10px 9px 16px}
.site .canonical-infographic-download{width:100%;margin-top:16px}
.site .canonical-infographic .canonical-mobile{display:block}
.site .canonical-infographic .canonical-desktop{display:none}
}</style>"""


class ArtworkError(ValueError):
    """Artwork is missing, stale, corrupt, oversized, or out of scope."""


def _slug(value: str) -> str:
    if not isinstance(value, str) or len(value) > 120 or not SLUG.fullmatch(value):
        raise ArtworkError("Invalid briefing slug")
    return value


def _file(root: Path, filename: str) -> Path:
    if not isinstance(filename, str) or not NAME.fullmatch(filename):
        raise ArtworkError("Invalid artwork asset filename")
    path = (root / filename).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ArtworkError("Artwork path escapes the published bundle")
    return path


def _file_bytes(path: Path, expected_sha: str, max_size: int) -> bytes:
    if not isinstance(expected_sha, str) or not HASH.fullmatch(expected_sha):
        raise ArtworkError("Missing immutable artwork checksum")
    try:
        size = path.stat().st_size
        if not (1000 < size < max_size):
            raise ArtworkError("Artwork missing or exceeds inline size budget")
        data = path.read_bytes()
    except OSError as exc:
        raise ArtworkError("Approved artwork file does not exist") from exc
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ArtworkError("Artwork SHA-256 mismatch")
    return data


def _image_bytes(root: Path, spec: dict) -> bytes:
    try:
        path = _file(root, spec["file"])
        if path.suffix.lower() != ".webp":
            raise ArtworkError("Inline artwork must be WebP")
        data = _file_bytes(path, spec["sha256"], MAX_INLINE_BYTES)
        if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            raise ArtworkError("Invalid WebP byte signature")
        with Image.open(BytesIO(data)) as im:
            if im.format != "WEBP" or im.size != (spec["width"], spec["height"]):
                raise ArtworkError("Approved artwork dimensions do not match manifest")
            im.verify()
        return data
    except (KeyError, TypeError, ValueError, OSError) as exc:
        if isinstance(exc, ArtworkError):
            raise
        raise ArtworkError("Invalid image manifest") from exc


def load_bundle(slug: str, *, asset_root: Path | None = None) -> dict | None:
    slug = _slug(slug)
    base = (asset_root or ROOT).resolve()
    directory = base / slug
    manifest = directory / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ArtworkError("Artwork manifest is corrupt") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ArtworkError("Unsupported artwork manifest")
    if data.get("slug") != slug or not HASH.fullmatch(str(data.get("article_fingerprint", ""))):
        raise ArtworkError("Artwork manifest identity is invalid")
    if not isinstance(data.get("revision"), str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", data["revision"]
    ):
        raise ArtworkError("Missing immutable artwork revision")
    for variant in ("desktop", "mobile", "pdf"):
        if not isinstance(data.get(variant), dict):
            raise ArtworkError("Incomplete approved artwork bundle")
    data["_root"] = directory
    return data


def validate_bundle(bundle: dict) -> tuple[bytes, bytes, bytes]:
    root = bundle["_root"]
    desktop = _image_bytes(root, bundle["desktop"])
    mobile = _image_bytes(root, bundle["mobile"])
    pdf_spec = bundle["pdf"]
    pdf_path = _file(root, pdf_spec["file"])
    if pdf_path.suffix.lower() != ".pdf":
        raise ArtworkError("Printable asset must be a PDF")
    pdf = _file_bytes(pdf_path, pdf_spec["sha256"], MAX_PDF_BYTES)
    if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-2048:]:
        raise ArtworkError("Approved PDF is corrupt or incomplete")
    return desktop, mobile, pdf


@lru_cache(maxsize=40)
def _encoded(data: bytes) -> str:
    if len(data) >= MAX_INLINE_BYTES:
        raise ArtworkError("Image too large for reliable inline delivery")
    return "data:image/webp;base64," + base64.b64encode(data).decode("ascii")


def render_approved_bundle(article, row: dict, *, asset_root: Path | None = None) -> str | None:
    """None means no manifest (legacy path); empty string means fail closed."""
    try:
        bundle = load_bundle(article.slug, asset_root=asset_root)
    except ArtworkError:
        return ""
    if bundle is None:
        return None
    from briefing_infographic_engine import source_fingerprint

    fingerprint = source_fingerprint(article)
    if (getattr(article, "status", "") != "published"
        or row.get("status") != "approved"
        or row.get("source_fingerprint") != fingerprint
        or bundle["article_fingerprint"] != fingerprint):
        return ""
    alt = str(row.get("alt_text") or "").strip()
    if len(alt) < 40:
        return ""
    try:
        desktop, mobile, _ = validate_bundle(bundle)
    except ArtworkError:
        return ""
    title = escape(str(bundle.get("heading") or "The executive visual"), quote=False)
    deck = escape(str(bundle.get("deck") or "Original decision infographic by Jair Ribeiro."), quote=False)
    caption = escape(str(row.get("caption") or "Original executive decision infographic by Jair Ribeiro."))
    slug = escape(article.slug, quote=True)
    revision = escape(bundle["revision"], quote=True)
    return (
        CSS + '<section class="ebi-section canonical-infographic-section" '
        'data-analytics-section="briefing-infographic" data-hq-content-slug="' + slug + '" '
        'data-artwork-revision="' + revision + '">'
        '<figure class="canonical-infographic">'
        '<div class="canonical-infographic-top"><div class="canonical-infographic-heading">'
        '<span class="canonical-infographic-kicker">Original executive infographic</span>'
        '<h2>' + title + '</h2><p>' + deck + '</p></div>'
        '<a class="canonical-infographic-download" '
        'href="/briefing-artwork/' + slug + '/download.pdf?v=' + revision + '" '
        'download="' + slug + '-executive-infographic.pdf">'
        '&#8595; Download infographic · A4 PDF</a></div>'
        '<img class="canonical-desktop" loading="eager" decoding="async" '
        'src="' + _encoded(desktop) + '" '
        'width="' + str(bundle["desktop"]["width"]) + '" height="' + str(bundle["desktop"]["height"])
        + '" alt="' + escape(alt, quote=True) + '"/>'
        '<img class="canonical-mobile" loading="eager" decoding="async" '
        'src="' + _encoded(mobile) + '" '
        'width="' + str(bundle["mobile"]["width"]) + '" height="' + str(bundle["mobile"]["height"])
        + '" alt="' + escape(alt, quote=True) + '"/>'
        '<figcaption>' + caption + '</figcaption></figure></section>'
    )


def verified_pdf_for_article(article, *, asset_root: Path | None = None) -> bytes | None:
    """Return PDF only for a source-identical, published CMS article."""
    from briefing_infographic_engine import source_fingerprint
    if getattr(article, "status", "") != "published":
        return None
    try:
        bundle = load_bundle(article.slug, asset_root=asset_root)
        if not bundle or bundle["article_fingerprint"] != source_fingerprint(article):
            return None
        _, _, pdf = validate_bundle(bundle)
        return pdf
    except ArtworkError:
        return None
