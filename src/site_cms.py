from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import time
import unicodedata
from urllib import error, parse, request
from uuid import uuid4

import bleach
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageFilter, ImageOps

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL

OWNER_EMAIL = "jair.ribeiro@outlook.it"
TABLE = "careersite_articles"
IMAGE_BUCKET = "careersite-article-images"
BASE_URL = "https://jairribeiro-ai.streamlit.app"
DEFAULT_SOCIAL_IMAGE = f"{BASE_URL}/app/static/jair-ribeiro-social-preview.png"

ALLOWED_TAGS = [
    "p", "br", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s",
    "blockquote", "ul", "ol", "li", "a", "hr", "code", "pre", "div", "span",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "div": ["class"],
    "span": ["class"],
}

DOMAIN_PHRASES = (
    "enterprise ai", "ai strategy", "ai governance", "responsible ai", "ai adoption",
    "operating model", "ai operating model", "data governance", "data readiness",
    "business value", "ai value", "ai roi", "ai portfolio", "portfolio management",
    "agentic ai", "generative ai", "genai", "artificial intelligence", "data analytics",
    "data and analytics", "change management", "human accountability", "ai coe",
    "center of excellence", "centre of excellence", "scale readiness", "ai scale",
)

STOPWORDS = {
    "about", "after", "again", "against", "also", "among", "another", "because", "before",
    "being", "between", "both", "business", "could", "does", "doing", "during", "each",
    "from", "have", "having", "into", "itself", "more", "most", "other", "over", "same",
    "should", "some", "such", "than", "that", "their", "there", "these", "they", "this",
    "through", "under", "very", "what", "when", "where", "which", "while", "with", "would",
    "your", "ours", "ourselves", "the", "and", "for", "are", "but", "not", "you", "all",
    "can", "has", "had", "was", "were", "will", "its", "our", "how", "why", "who",
}

CATEGORY_RULES = (
    ("AI Governance", ("governance", "responsible ai", "accountability", "risk", "control")),
    ("AI Adoption", ("adoption", "change management", "workflow", "literacy", "capability")),
    ("Portfolio & Value", ("portfolio", "roi", "value", "investment", "use case", "use-case")),
    ("AI Operating Model", ("operating model", "coe", "center of excellence", "centre of excellence", "ownership")),
    ("Data & Analytics", ("data governance", "data readiness", "analytics", "data quality", "data ownership")),
    ("Enterprise AI", ("enterprise ai", "scale", "strategy", "agentic", "generative ai", "genai")),
)


@dataclass
class CmsArticle:
    id: str | None = None
    title: str = ""
    slug: str = ""
    subtitle: str = ""
    content_html: str = ""
    aside_html: str = ""
    excerpt: str = ""
    header_image_url: str = ""
    header_image_alt: str = ""
    seo_title: str = ""
    meta_description: str = ""
    keywords: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()
    category: str = ""
    kind: str = "Article"
    source_url: str = ""
    status: str = "draft"
    featured: bool = False
    legacy_key: str = ""
    read_minutes: int = 1
    social_title: str = ""
    social_description: str = ""
    author_name: str = "Jair Ribeiro"
    show_tags_publicly: bool = False
    published_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "CmsArticle":
        def text(name: str) -> str:
            value = row.get(name)
            return "" if value is None else str(value)

        return cls(
            id=text("id") or None,
            title=text("title"),
            slug=text("slug"),
            subtitle=text("subtitle"),
            content_html=text("content_html"),
            aside_html=text("aside_html"),
            excerpt=text("excerpt"),
            header_image_url=text("header_image_url"),
            header_image_alt=text("header_image_alt"),
            seo_title=text("seo_title"),
            meta_description=text("meta_description"),
            keywords=tuple(row.get("keywords") or ()),
            hashtags=tuple(row.get("hashtags") or ()),
            category=text("category"),
            kind=text("kind") or "Article",
            source_url=text("source_url"),
            status=text("status") or "draft",
            featured=bool(row.get("featured", False)),
            legacy_key=text("legacy_key"),
            read_minutes=max(1, int(row.get("read_minutes") or 1)),
            social_title=text("social_title"),
            social_description=text("social_description"),
            author_name=text("author_name") or "Jair Ribeiro",
            show_tags_publicly=bool(row.get("show_tags_publicly", False)),
            published_at=text("published_at"),
            created_at=text("created_at"),
            updated_at=text("updated_at"),
        )

    @property
    def topic(self) -> str:
        return self.category or "Enterprise AI"

    @property
    def tags(self) -> tuple[str, ...]:
        return self.keywords

    @property
    def published_iso(self) -> str:
        value = self.published_at or self.updated_at or self.created_at
        return value[:10] if value else datetime.now(timezone.utc).date().isoformat()

    @property
    def published_label(self) -> str:
        return format_date(self.published_at or self.updated_at or self.created_at)

    @property
    def kind_topic(self) -> str:
        return f"{self.kind} · {self.topic}"

    @property
    def read_label(self) -> str:
        label = self.published_label or "Draft"
        return f"{label} · {self.read_minutes} min read"


def sanitize_article_html(value: str) -> str:
    cleaned = bleach.clean(
        value or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    cleaned = re.sub(r'<a\s+([^>]*href="https?://[^>]+)>', _safe_external_link, cleaned, flags=re.I)
    return cleaned.strip()


def _safe_external_link(match: re.Match[str]) -> str:
    attrs = match.group(1)
    if "target=" not in attrs.lower():
        attrs += ' target="_blank"'
    if "rel=" not in attrs.lower():
        attrs += ' rel="noopener noreferrer"'
    return f"<a {attrs}>"


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:150] or f"article-{int(time.time())}"


def _trim_sentence(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    shortened = value[: max(0, limit - 1)].rstrip()
    cut = max(shortened.rfind(". "), shortened.rfind("; "), shortened.rfind(", "))
    if cut >= int(limit * 0.6):
        shortened = shortened[: cut + 1]
    else:
        space = shortened.rfind(" ")
        if space > 0:
            shortened = shortened[:space]
    return shortened.rstrip(" ,;:-") + "…"


def _seo_title(title: str) -> str:
    base = re.sub(r"\s+", " ", title).strip()
    suffix = " | Jair Ribeiro"
    if len(base) + len(suffix) <= 60:
        return base + suffix
    return _trim_sentence(base, 59)


def _keyword_candidates(title: str, body: str) -> list[str]:
    corpus = f"{title} {body}".lower()
    candidates: list[str] = []
    for phrase in DOMAIN_PHRASES:
        if phrase in corpus:
            candidates.append(phrase.title().replace("Ai", "AI").replace("Roi", "ROI").replace("Coe", "CoE"))

    words = re.findall(r"\b[a-zA-Z][a-zA-Z-]{3,}\b", f"{title} {body}")
    counts: dict[str, int] = {}
    display: dict[str, str] = {}
    for word in words:
        key = word.lower().strip("-")
        if key in STOPWORDS or len(key) < 4:
            continue
        counts[key] = counts.get(key, 0) + 1
        display.setdefault(key, word)
    for key, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        candidate = display[key].strip("-.,:;")
        if candidate and candidate.lower() not in {x.lower() for x in candidates}:
            candidates.append(candidate)
        if len(candidates) >= 10:
            break
    return candidates[:10]


def _category(title: str, body: str) -> str:
    corpus = f"{title} {body}".lower()
    best = (0, "Enterprise AI")
    for category, terms in CATEGORY_RULES:
        score = sum(corpus.count(term) for term in terms)
        if score > best[0]:
            best = (score, category)
    return best[1]


def _hashtag(value: str) -> str:
    special = {
        "enterprise ai": "#EnterpriseAI", "ai strategy": "#AIStrategy", "ai governance": "#AIGovernance",
        "responsible ai": "#ResponsibleAI", "ai adoption": "#AIAdoption", "ai roi": "#AIROI",
        "ai value": "#AIValue", "ai portfolio": "#AIPortfolio", "ai operating model": "#AIOperatingModel",
        "operating model": "#OperatingModel", "data governance": "#DataGovernance",
        "data readiness": "#DataReadiness", "agentic ai": "#AgenticAI", "generative ai": "#GenerativeAI",
        "genai": "#GenAI", "ai coe": "#AICoE", "business value": "#BusinessValue",
    }
    key = value.lower().strip()
    if key in special:
        return special[key]
    parts = re.findall(r"[A-Za-z0-9]+", value)
    return "#" + "".join(part[:1].upper() + part[1:] for part in parts)[:48]


def generate_metadata(title: str, content_html: str, subtitle: str = "", has_image: bool = False) -> dict[str, object]:
    body = strip_html(content_html)
    source = subtitle.strip() or body
    excerpt = _trim_sentence(body or subtitle, 280)
    meta = _trim_sentence(source, 158)
    keywords = _keyword_candidates(title, body)
    category = _category(title, body)
    seed = [category] + keywords
    hashtags: list[str] = []
    for item in seed:
        tag = _hashtag(item)
        if tag != "#" and tag.lower() not in {x.lower() for x in hashtags}:
            hashtags.append(tag)
        if len(hashtags) >= 8:
            break
    words = re.findall(r"\b\w+\b", body)
    return {
        "slug": slugify(title),
        "seo_title": _seo_title(title),
        "meta_description": meta,
        "excerpt": excerpt,
        "keywords": keywords[:10],
        "hashtags": hashtags[:8],
        "category": category,
        "social_title": _trim_sentence(title, 100),
        "social_description": _trim_sentence(subtitle.strip() or excerpt, 180),
        "header_image_alt": f'Header image for “{title.strip()}” by Jair Ribeiro' if has_image and title.strip() else "",
        "read_minutes": max(1, min(120, math.ceil(max(1, len(words)) / 220))),
    }


def format_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y")
    except (ValueError, TypeError):
        return str(value)[:10]


def _request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: object | None = None,
    prefer: str | None = None,
    timeout: int = 15,
) -> object:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"apikey": ANALYTICS_PUBLISHABLE_KEY, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if prefer:
        headers["Prefer"] = prefer
    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            message = parsed.get("msg") or parsed.get("message") or parsed.get("error_description") or detail
        except json.JSONDecodeError:
            message = detail
        raise RuntimeError(f"Supabase request failed ({exc.code}): {str(message)[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError("Supabase is temporarily unreachable.") from exc


def _rest_url(query: str) -> str:
    return f"{ANALYTICS_URL.rstrip('/')}/rest/v1/{query}"


def owner_signup(password: str) -> dict:
    if len(password) < 12:
        raise ValueError("Use a password with at least 12 characters.")
    result = _request_json(
        "POST",
        f"{ANALYTICS_URL.rstrip('/')}/auth/v1/signup",
        payload={"email": OWNER_EMAIL, "password": password},
    )
    return result if isinstance(result, dict) else {}


def owner_signin(password: str) -> dict:
    result = _request_json(
        "POST",
        f"{ANALYTICS_URL.rstrip('/')}/auth/v1/token?grant_type=password",
        payload={"email": OWNER_EMAIL, "password": password},
    )
    if not isinstance(result, dict) or not result.get("access_token"):
        raise RuntimeError("Sign-in did not return an authenticated session.")
    user = result.get("user") or {}
    email_value = str(user.get("email") or "").lower()
    if email_value != OWNER_EMAIL:
        raise RuntimeError("This account is not authorized for the portfolio CMS.")
    return result


def owner_refresh(refresh_token: str) -> dict:
    result = _request_json(
        "POST",
        f"{ANALYTICS_URL.rstrip('/')}/auth/v1/token?grant_type=refresh_token",
        payload={"refresh_token": refresh_token},
    )
    if not isinstance(result, dict) or not result.get("access_token"):
        raise RuntimeError("Could not refresh the owner session.")
    return result


def ensure_owner_session(session: dict | None) -> dict | None:
    if not session:
        return None
    expires_at = int(session.get("expires_at") or 0)
    if expires_at and expires_at - int(time.time()) > 90:
        return session
    refresh_token = str(session.get("refresh_token") or "")
    if not refresh_token:
        return None
    try:
        return owner_refresh(refresh_token)
    except RuntimeError:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_published_articles() -> tuple[CmsArticle, ...]:
    query = (
        f"{TABLE}?select=*&status=eq.published&"
        "order=featured.desc,published_at.desc.nullslast,updated_at.desc"
    )
    result = _request_json("GET", _rest_url(query))
    rows = result if isinstance(result, list) else []
    return tuple(CmsArticle.from_row(row) for row in rows)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_public_article(slug: str) -> CmsArticle | None:
    safe_slug = parse.quote(slugify(slug), safe="")
    query = f"{TABLE}?select=*&slug=eq.{safe_slug}&status=eq.published&limit=1"
    result = _request_json("GET", _rest_url(query))
    if isinstance(result, list) and result:
        return CmsArticle.from_row(result[0])
    return None


def admin_list_articles(access_token: str) -> list[CmsArticle]:
    query = f"{TABLE}?select=*&order=updated_at.desc"
    result = _request_json("GET", _rest_url(query), token=access_token)
    rows = result if isinstance(result, list) else []
    return [CmsArticle.from_row(row) for row in rows]


def _article_payload(article: CmsArticle) -> dict[str, object]:
    return {
        "title": article.title.strip(),
        "slug": slugify(article.slug or article.title),
        "subtitle": article.subtitle.strip() or None,
        "content_html": sanitize_article_html(article.content_html),
        "aside_html": sanitize_article_html(article.aside_html),
        "excerpt": article.excerpt.strip(),
        "header_image_url": article.header_image_url.strip() or None,
        "header_image_alt": article.header_image_alt.strip() or None,
        "seo_title": article.seo_title.strip() or None,
        "meta_description": article.meta_description.strip() or None,
        "keywords": list(article.keywords),
        "hashtags": [tag if str(tag).startswith("#") else f"#{tag}" for tag in article.hashtags],
        "category": article.category.strip() or None,
        "kind": article.kind.strip() or "Article",
        "source_url": article.source_url.strip() or None,
        "status": article.status if article.status in {"draft", "published"} else "draft",
        "featured": bool(article.featured),
        "legacy_key": article.legacy_key.strip() or None,
        "read_minutes": max(1, min(120, int(article.read_minutes or 1))),
        "social_title": article.social_title.strip() or None,
        "social_description": article.social_description.strip() or None,
        "author_name": "Jair Ribeiro",
        "show_tags_publicly": bool(article.show_tags_publicly),
        "published_at": article.published_at or None,
    }


def save_article(access_token: str, article: CmsArticle) -> CmsArticle:
    if not article.title.strip():
        raise ValueError("Title is required.")
    if not strip_html(article.content_html):
        raise ValueError("Article body is required.")
    payload = _article_payload(article)
    if article.id:
        result = _request_json(
            "PATCH",
            _rest_url(f"{TABLE}?id=eq.{parse.quote(article.id, safe='')}"),
            token=access_token,
            payload=payload,
            prefer="return=representation",
        )
    else:
        result = _request_json(
            "POST",
            _rest_url(TABLE),
            token=access_token,
            payload=payload,
            prefer="return=representation",
        )
    rows = result if isinstance(result, list) else []
    if not rows:
        raise RuntimeError("The article save returned no row.")
    saved = CmsArticle.from_row(rows[0])
    if saved.status == "published" and saved.featured and saved.id:
        _request_json(
            "PATCH",
            _rest_url(
                f"{TABLE}?featured=eq.true&id=neq.{parse.quote(saved.id, safe='')}"
            ),
            token=access_token,
            payload={"featured": False},
            prefer="return=minimal",
        )
    fetch_published_articles.clear()
    fetch_public_article.clear()
    return saved


def delete_article(access_token: str, article_id: str) -> None:
    _request_json(
        "DELETE",
        _rest_url(f"{TABLE}?id=eq.{parse.quote(article_id, safe='')}"),
        token=access_token,
        prefer="return=minimal",
    )
    fetch_published_articles.clear()
    fetch_public_article.clear()


def change_article_status(access_token: str, article_id: str, status: str) -> CmsArticle:
    if status not in {"draft", "published"}:
        raise ValueError("Unsupported article status.")
    result = _request_json(
        "PATCH",
        _rest_url(f"{TABLE}?id=eq.{parse.quote(article_id, safe='')}"),
        token=access_token,
        payload={"status": status},
        prefer="return=representation",
    )
    rows = result if isinstance(result, list) else []
    if not rows:
        raise RuntimeError("The article status update returned no row.")
    fetch_published_articles.clear()
    fetch_public_article.clear()
    return CmsArticle.from_row(rows[0])


def duplicate_article(access_token: str, article: CmsArticle) -> CmsArticle:
    copy_article = CmsArticle(**asdict(article))
    copy_article.id = None
    copy_article.title = f"Copy of {article.title}"
    copy_article.slug = f"{slugify(article.slug or article.title)}-copy-{int(time.time())}"
    copy_article.status = "draft"
    copy_article.featured = False
    copy_article.legacy_key = ""
    copy_article.published_at = ""
    copy_article.created_at = ""
    copy_article.updated_at = ""
    return save_article(access_token, copy_article)


HEADER_IMAGE_SIZE = (1600, 800)


def normalize_header_image(data: bytes, mime_type: str) -> bytes:
    """Normalize CMS header art to a safe 2:1 canvas without cropping source content."""
    if not data:
        raise ValueError("Header image is empty.")
    try:
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
    except Exception as exc:
        raise ValueError("Header image could not be decoded.") from exc

    target_w, target_h = HEADER_IMAGE_SIZE
    target_ratio = target_w / target_h
    source_ratio = image.width / max(image.height, 1)

    if image.size == HEADER_IMAGE_SIZE and mime_type == "image/webp":
        return data

    if abs(source_ratio - target_ratio) < 0.01:
        canvas = image.resize(HEADER_IMAGE_SIZE, Image.Resampling.LANCZOS)
    else:
        background = ImageOps.fit(
            image,
            HEADER_IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        ).filter(ImageFilter.GaussianBlur(radius=28))
        foreground = ImageOps.contain(
            image,
            HEADER_IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
        )
        x = (target_w - foreground.width) // 2
        y = (target_h - foreground.height) // 2
        background.paste(foreground, (x, y))
        canvas = background

    output = BytesIO()
    canvas.save(output, format="WEBP", quality=92, method=6)
    return output.getvalue()


def upload_header_image(access_token: str, slug: str, filename: str, mime_type: str, data: bytes) -> str:
    if mime_type not in {"image/jpeg", "image/png", "image/webp", "image/avif"}:
        raise ValueError("Header image must be JPEG, PNG, WebP or AVIF.")
    if len(data) > 5 * 1024 * 1024:
        raise ValueError("Header image must be 5 MB or smaller.")

    normalized = normalize_header_image(data, mime_type)
    if len(normalized) > 5 * 1024 * 1024:
        raise ValueError("Normalized header image must be 5 MB or smaller.")

    path = f"{slugify(slug)}/{int(time.time())}-{uuid4().hex[:10]}.webp"
    url = f"{ANALYTICS_URL.rstrip('/')}/storage/v1/object/{IMAGE_BUCKET}/{parse.quote(path, safe='/')}"
    headers = {
        "apikey": ANALYTICS_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "image/webp",
    }
    req = request.Request(url, data=normalized, method="POST", headers=headers)
    try:
        with request.urlopen(req, timeout=30):
            pass
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Image upload failed ({exc.code}): {detail[:240]}") from exc
    return f"{ANALYTICS_URL.rstrip('/')}/storage/v1/object/public/{IMAGE_BUCKET}/{parse.quote(path, safe='/')}"
def delete_header_image(access_token: str, image_url: str) -> None:
    marker = f"/storage/v1/object/public/{IMAGE_BUCKET}/"
    if marker not in image_url:
        return
    path = parse.unquote(image_url.split(marker, 1)[1])
    url = f"{ANALYTICS_URL.rstrip('/')}/storage/v1/object/{IMAGE_BUCKET}/{parse.quote(path, safe='/')}"
    headers = {
        "apikey": ANALYTICS_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
    }
    req = request.Request(url, method="DELETE", headers=headers)
    try:
        with request.urlopen(req, timeout=20):
            pass
    except error.HTTPError:
        return


def bundled_header_parts(slug: str) -> tuple[Path, ...]:
    directory = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "cms_headers"
        / slugify(slug)
    )
    if not directory.is_dir():
        return ()
    return tuple(sorted(directory.glob("part_*.b64")))


def bundled_header_bytes(slug: str) -> bytes | None:
    parts = bundled_header_parts(slug)
    if not parts:
        return None
    try:
        data = b"".join(
            base64.b64decode(part.read_text(encoding="utf-8").strip(), validate=True)
            for part in parts
        )
    except (OSError, ValueError):
        return None
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    return data


def effective_header_image_url(article: CmsArticle) -> str:
    if article.header_image_url:
        return article.header_image_url
    data = bundled_header_bytes(article.slug)
    if data is None:
        return ""
    version = hashlib.sha256(data).hexdigest()[:12]
    return (
        f"{BASE_URL}/cms-header/{parse.quote(slugify(article.slug), safe='')}.webp"
        f"?v={version}"
    )


def embedded_header_image_src(article: CmsArticle) -> str:
    """Use bundled article art inline so the visible page never depends on a second HTTP route."""
    data = bundled_header_bytes(article.slug)
    if data is not None:
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/webp;base64,{encoded}"
    return article.header_image_url.strip()


def article_relative_url(article: CmsArticle) -> str:
    return f"?page=thinking&article={parse.quote(article.slug, safe='')}"


def article_url(article: CmsArticle) -> str:
    return f"{BASE_URL}/thinking/{parse.quote(article.slug, safe='')}"


def article_preview_url(article: CmsArticle) -> str:
    return f"{article_url(article)}?source=application&role=Test"


def _cms_fallback_cover(article: CmsArticle, css_class: str) -> str:
    subtitle = article.subtitle or article.excerpt
    return f'''<div class="{escape(css_class, quote=True)} cms-fallback-cover" role="img" aria-label="{escape(article.header_image_alt or article.title, quote=True)}">
<div class="cms-cover-copy"><span>People · Data · AI · Real Impact</span><strong>{escape(article.title)}</strong><p>{escape(subtitle)}</p></div>
<div class="cms-cover-network" aria-hidden="true"><i>AI</i><b>CIO</b><b>CDO</b><b>Business</b><b>Risk</b><b>HR</b><b>CoE</b></div>
</div>'''


CMS_FALLBACK_CSS = '''<style>
.cms-fallback-cover{position:relative;overflow:hidden;min-height:330px;aspect-ratio:2/1;background:radial-gradient(circle at 82% 28%,rgba(255,185,118,.28),transparent 26%),linear-gradient(122deg,#07182b 0%,#173750 62%,#7b6658 100%);color:#fff;border:1px solid rgba(255,255,255,.17);box-shadow:0 20px 48px rgba(0,0,0,.20)}
.cms-cover-copy{position:absolute;left:5%;top:9%;width:55%;z-index:2}.cms-cover-copy span{display:block;font:750 11px/1.2 Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#c9d7e3;margin-bottom:34px}.cms-cover-copy strong{display:block;font:650 clamp(28px,4.1vw,58px)/1.02 Georgia,serif;letter-spacing:-.025em}.cms-cover-copy p{max-width:700px;margin:20px 0 0;font:400 clamp(13px,1.45vw,20px)/1.42 Arial,sans-serif;color:#e4ebef}
.cms-cover-network{position:absolute;right:4%;bottom:8%;width:34%;height:72%;border:1px solid rgba(255,255,255,.16);border-radius:50%}.cms-cover-network:before,.cms-cover-network:after{content:"";position:absolute;left:50%;top:50%;width:86%;height:1px;background:rgba(255,255,255,.30);transform:translate(-50%,-50%) rotate(30deg)}.cms-cover-network:after{transform:translate(-50%,-50%) rotate(-30deg)}.cms-cover-network i{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:grid;place-items:center;width:86px;height:86px;border-radius:50%;background:#f1eee8;color:#132331;font:800 30px/1 Arial,sans-serif;font-style:normal;z-index:2}.cms-cover-network b{position:absolute;padding:8px 11px;border:1px solid rgba(255,255,255,.35);background:rgba(7,24,43,.75);font:650 11px/1 Arial,sans-serif;letter-spacing:.04em}.cms-cover-network b:nth-of-type(1){left:7%;top:13%}.cms-cover-network b:nth-of-type(2){right:9%;top:10%}.cms-cover-network b:nth-of-type(3){right:-2%;top:45%}.cms-cover-network b:nth-of-type(4){right:8%;bottom:9%}.cms-cover-network b:nth-of-type(5){left:10%;bottom:8%}.cms-cover-network b:nth-of-type(6){left:-3%;top:46%}
@media(max-width:760px){.cms-fallback-cover{min-height:390px;aspect-ratio:auto}.cms-cover-copy{width:88%}.cms-cover-network{opacity:.28;width:58%;right:-12%}.cms-cover-copy strong{font-size:34px}}
</style>'''


def _share_footer(article: CmsArticle) -> str:
    canonical = article_url(article)
    linkedin = "https://www.linkedin.com/feed/?" + parse.urlencode({"shareActive": "true", "shareUrl": canonical})
    x_url = "https://twitter.com/intent/tweet?" + parse.urlencode({"url": canonical, "text": article.social_title or article.title})
    mailto = "mailto:?" + parse.urlencode({"subject": article.social_title or article.title, "body": f"{article.social_description or article.excerpt}\n\n{canonical}"})
    return f'''<section class="article-share"><div class="article-share-grid"><div><p class="eyebrow">Share this article</p><h3>Useful for someone working through the same decision?</h3><p>Share it directly, or copy the permanent article link.</p></div><div class="share-actions"><a class="share-btn primary" href="{escape(linkedin, quote=True)}" target="_blank" rel="noopener noreferrer" data-hq-event="article_share_linkedin">LinkedIn ↗</a><a class="share-btn" href="{escape(x_url, quote=True)}" target="_blank" rel="noopener noreferrer" data-hq-event="article_share_x">X ↗</a><a class="share-btn" href="{escape(mailto, quote=True)}" data-hq-event="article_share_email">Email</a><button class="share-btn" type="button" data-copy-url="{escape(canonical, quote=True)}" data-hq-event="article_share_copy">Copy link</button></div></div><div class="share-meta"><span>{escape(article.kind_topic)}</span><span>·</span><span>{escape(article.published_label)}</span><span>·</span><a href="?page=thinking" target="_self">More Thinking</a><span class="share-copy-status" data-copy-status></span></div></section>'''


def render_cms_article(article: CmsArticle) -> str:
    from site_components import footer, nav, opportunity
    from thinking_core import THINKING_CSS

    image = ""
    header_image_url = embedded_header_image_src(article)
    if header_image_url:
        image = f'''<div class="cms-article-image"><img src="{escape(header_image_url, quote=True)}" alt="{escape(article.header_image_alt or article.title, quote=True)}" loading="eager" decoding="async"></div>'''
    elif article.legacy_key:
        try:
            from page_thinking import _image
            image = _image(article.legacy_key, "article-cover")
        except Exception:
            image = _cms_fallback_cover(article, "cms-article-image")
    else:
        image = _cms_fallback_cover(article, "cms-article-image")

    tags = ""
    if article.show_tags_publicly and article.hashtags:
        tags = '<div class="themebar">' + ''.join(f'<span>{escape(tag)}</span>' for tag in article.hashtags) + '</div>'

    source = ""
    if article.source_url:
        source = f'''<p class="cms-source"><a href="{escape(article.source_url, quote=True)}" target="_blank" rel="noopener">Original publication ↗</a></p>'''

    aside = article.aside_html.strip()
    if not aside:
        keyword_lines = ''.join(f'<div>{escape(keyword)}</div>' for keyword in article.keywords[:5])
        aside = f'''<span>{escape(article.category or "Article")}</span><strong>{escape(article.read_label)}</strong><div class="article-questions">{keyword_lines}</div><p>Published in Jair Ribeiro's selected Thinking portfolio.</p>'''

    css = '''<style>
.cms-article-image{margin:26px 0 0}.cms-article-image img{display:block;width:100%;max-height:620px;object-fit:cover;border:1px solid rgba(255,255,255,.16);box-shadow:0 20px 48px rgba(0,0,0,.22)}
.cms-source{margin-top:28px!important;padding-top:18px;border-top:1px solid var(--line)}.cms-source a{font-size:11px;font-weight:850;text-decoration:none}.article-body h3{margin:34px 0 14px;font:500 26px/1.15 Georgia,serif}.article-body ul,.article-body ol{margin:0 0 24px;padding-left:24px;color:#343b43;font-size:16px;line-height:1.75}.article-body li{margin:7px 0}.article-body hr{border:0;border-top:1px solid var(--line);margin:34px 0}
</style>'''

    return f'''{THINKING_CSS}{CMS_FALLBACK_CSS}{css}{nav("thinking")}<main><section class="article-hero"><div class="container"><a class="article-back" href="?page=thinking" target="_self">← Back to Thinking</a><div class="article-meta">{escape(article.kind_topic)}</div><h1>{escape(article.title)}</h1><p class="standfirst">{escape(article.subtitle or article.excerpt)}</p><div class="article-date">{escape(article.read_label)}</div>{image}</div></section><section class="section paper"><div class="container article-layout"><article class="article-body">{article.content_html}{tags}{source}{_share_footer(article)}</article><aside class="article-aside">{aside}</aside></div></section>{opportunity()}</main>{footer()}'''


def inject_cms_landing(document: str) -> str:
    published = list(fetch_published_articles())
    cms_articles = [article for article in published if not article.legacy_key]
    featured = next((article for article in cms_articles if article.featured), None)

    if featured is not None:
        featured_image = ""
        featured_header_url = embedded_header_image_src(featured)
        if featured_header_url:
            featured_image = (
                f'<div class="thinking-thumb cms-thinking-thumb">'
                f'<img src="{escape(featured_header_url, quote=True)}" '
                f'alt="{escape(featured.header_image_alt or featured.title, quote=True)}" '
                f'loading="eager" decoding="async"></div>'
            )
        else:
            featured_image = _cms_fallback_cover(featured, "thinking-thumb cms-thinking-thumb")
        featured_copy = featured.subtitle or featured.excerpt
        featured_html = (
            f'<article class="featured-thinking">{featured_image}'
            f'<div class="kicker">{escape(featured.kind_topic)}</div>'
            f'<h2>{escape(featured.title)}</h2>'
            f'<p>{escape(featured_copy)}</p>'
            f'<a class="read-live" href="{escape(article_relative_url(featured), quote=True)}" '
            f'target="_self" data-hq-event="cms_featured_article_open">Read the article →</a>'
            f'<div class="meta">{escape(featured.published_label)} · '
            f'{escape(featured.topic)} · {featured.read_minutes} min</div></article>'
        )
        document = re.sub(
            r'<article class="featured-thinking">.*?</article>',
            lambda _match: featured_html,
            document,
            count=1,
            flags=re.S,
        )

    articles = [
        article for article in cms_articles
        if featured is None or article.id != featured.id
    ]
    if not articles:
        return CMS_FALLBACK_CSS + document

    cards = []
    for article in articles[:6]:
        thumb = ""
        card_header_url = embedded_header_image_src(article)
        if card_header_url:
            thumb = (
                f'<div class="cms-thinking-thumb"><img '
                f'src="{escape(card_header_url, quote=True)}" '
                f'alt="{escape(article.header_image_alt or article.title, quote=True)}" '
                f'loading="lazy" decoding="async"></div>'
            )
        cards.append(
            f'<a class="recent-card" href="{escape(article_relative_url(article), quote=True)}" '
            f'target="_self" data-hq-event="cms_article_open">{thumb}'
            f'<div class="kicker">{escape(article.kind_topic)}</div>'
            f'<h3>{escape(article.title)}</h3><p>{escape(article.excerpt)}</p>'
            f'<div class="read">{escape(article.read_label)} →</div></a>'
        )
    section = (
        '<section class="section white cms-latest"><div class="container">'
        '<div class="head"><div><p class="eyebrow">Latest publications</p>'
        '<h2>New writing published directly to the portfolio.</h2></div>'
        '<p>Current articles appear here as soon as they are published through the private editor.</p>'
        '</div><div class="recent-grid">' + ''.join(cards) + '</div></div></section>'
        '<style>.cms-thinking-thumb{margin:-25px -25px 20px;aspect-ratio:2/1;overflow:hidden;'
        'background:#0b1220;display:flex;align-items:center;justify-content:center}.cms-thinking-thumb img{'
        'width:100%;height:100%;display:block;object-fit:contain;object-position:center center}.featured-thinking '
        '.cms-thinking-thumb{margin:0 0 22px;aspect-ratio:2/1}</style>'
    )
    marker = '<section class="section white"><div class="container"><div class="head"><div><p class="eyebrow">Recent thinking</p>'
    if marker in document:
        return CMS_FALLBACK_CSS + document.replace(marker, section + marker, 1)
    return CMS_FALLBACK_CSS + section + document


def cms_share_document(article: CmsArticle) -> str:
    canonical = article_url(article)
    legacy_social = bool(article.legacy_key and not article.header_image_url)
    image = (
        effective_header_image_url(article)
        or (f"{BASE_URL}/social/{article.slug}.png" if article.legacy_key else DEFAULT_SOCIAL_IMAGE)
    )
    description = article.meta_description or article.excerpt
    image_size_meta = (
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="627">'
        if legacy_social else ""
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": description,
        "datePublished": article.published_iso,
        "dateModified": (article.updated_at or article.published_at or article.published_iso)[:10],
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": [image],
        "author": {"@type": "Person", "name": "Jair Ribeiro", "url": BASE_URL},
        "publisher": {"@type": "Person", "name": "Jair Ribeiro", "url": BASE_URL},
        "articleSection": article.topic,
        "keywords": list(article.keywords),
    }
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(article.seo_title or article.title)}</title><meta name="description" content="{escape(description, quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{escape(canonical, quote=True)}"><link rel="image_src" href="{escape(image, quote=True)}"><meta property="og:type" content="article"><meta property="og:title" content="{escape(article.social_title or article.title, quote=True)}"><meta property="og:description" content="{escape(article.social_description or description, quote=True)}"><meta property="og:url" content="{escape(canonical, quote=True)}"><meta property="og:image" content="{escape(image, quote=True)}">{image_size_meta}<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(article.social_title or article.title, quote=True)}"><meta name="twitter:description" content="{escape(article.social_description or description, quote=True)}"><meta name="twitter:image" content="{escape(image, quote=True)}"><meta property="article:published_time" content="{escape(article.published_iso, quote=True)}"><meta property="article:modified_time" content="{escape((article.updated_at or article.published_at or article.published_iso), quote=True)}"><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace('</', '<\\/')}</script></head><body><main><h1>{escape(article.title)}</h1><p>{escape(description)}</p><p><a href="{escape(article_relative_url(article), quote=True)}">Read the full article</a></p></main></body></html>'''


def inject_cms_article_metadata(article: CmsArticle) -> None:
    canonical = article_url(article)
    image = effective_header_image_url(article) or DEFAULT_SOCIAL_IMAGE
    description = article.meta_description or article.excerpt
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": description,
        "datePublished": article.published_iso,
        "dateModified": article.updated_at or article.published_at or article.published_iso,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": [image],
        "author": {"@type": "Person", "name": "Jair Ribeiro", "url": BASE_URL},
        "articleSection": article.topic,
        "keywords": list(article.keywords),
    }
    script = f'''
<script>
(() => {{
  const doc = window.parent.document;
  const title = {json.dumps(article.seo_title or article.title)};
  const description = {json.dumps(description)};
  const canonical = {json.dumps(canonical)};
  const image = {json.dumps(image)};
  doc.title = title;
  const setMeta = (selector, attr, key, value) => {{
    let el = doc.head.querySelector(selector);
    if (!el) {{ el = doc.createElement('meta'); el.setAttribute(attr, key); doc.head.appendChild(el); }}
    el.setAttribute('content', value || '');
  }};
  setMeta('meta[name="description"]','name','description',description);
  setMeta('meta[name="robots"]','name','robots','index,follow,max-image-preview:large');
  setMeta('meta[property="og:type"]','property','og:type','article');
  setMeta('meta[property="og:title"]','property','og:title',{json.dumps(article.social_title or article.title)});
  setMeta('meta[property="og:description"]','property','og:description',{json.dumps(article.social_description or description)});
  setMeta('meta[property="og:url"]','property','og:url',canonical);
  setMeta('meta[property="og:image"]','property','og:image',image);
  setMeta('meta[name="twitter:card"]','name','twitter:card','summary_large_image');
  setMeta('meta[name="twitter:title"]','name','twitter:title',{json.dumps(article.social_title or article.title)});
  setMeta('meta[name="twitter:description"]','name','twitter:description',{json.dumps(article.social_description or description)});
  setMeta('meta[name="twitter:image"]','name','twitter:image',image);
  setMeta('meta[property="article:published_time"]','property','article:published_time',{json.dumps(article.published_at or article.published_iso)});
  setMeta('meta[property="article:modified_time"]','property','article:modified_time',{json.dumps(article.updated_at or article.published_at or article.published_iso)});
  let link = doc.head.querySelector('link[rel="canonical"]');
  if (!link) {{ link = doc.createElement('link'); link.setAttribute('rel','canonical'); doc.head.appendChild(link); }}
  link.setAttribute('href', canonical);
  let schema = doc.head.querySelector('script[data-jair-cms-article]');
  if (!schema) {{ schema = doc.createElement('script'); schema.type = 'application/ld+json'; schema.dataset.jairCmsArticle = 'true'; doc.head.appendChild(schema); }}
  schema.textContent = JSON.stringify({json.dumps(schema)});
}})();
</script>'''
    components.html(script, height=0, width=0)


def cms_sitemap_entries() -> list[tuple[str, str]]:
    return [(article_url(article), (article.updated_at or article.published_at or article.published_iso)[:10]) for article in fetch_published_articles()]
