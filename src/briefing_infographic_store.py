from __future__ import annotations

"""Private visual approval records + public read-only infographic lookup."""

from html import escape
from datetime import datetime, timezone
from urllib.parse import quote

import streamlit as st

from briefing_adoption_artwork import artwork_data_uri
from briefing_infographic_engine import (
    REVIEW_KEYS, INFOGRAPHIC_CSS, infographic_html, source_fingerprint, validate_spec,
)
from site_cms import _request_json, _rest_url

TABLE="careersite_briefing_infographics"


def _url(article_id: str) -> str:
    return _rest_url(
        f"{TABLE}?select=*&article_id=eq.{quote(str(article_id),safe='')}"
        "&order=revision.desc&limit=1"
    )


def fetch_owner_infographic(article_id: str, access_token: str, *,
                            approved_only: bool=False) -> dict | None:
    url=_url(article_id)
    if approved_only:
        url=url.replace("&order=revision.desc", "&status=eq.approved&order=revision.desc")
    result=_request_json("GET", url,token=access_token)
    return result[0] if isinstance(result,list) and result else None


@st.cache_data(ttl=60,show_spinner=False)
def fetch_public_infographic(article_id: str) -> dict | None:
    query=_rest_url(
        f"{TABLE}?select=article_id,slug,pattern,spec,alt_text,caption,status,revision,source_fingerprint"
        f"&article_id=eq.{quote(str(article_id),safe='')}"
        "&status=eq.approved&order=revision.desc&limit=1"
    )
    result=_request_json("GET",query)
    return result[0] if isinstance(result,list) and result else None


def save_infographic_draft(access_token: str, article, spec: dict,
                          alt_text: str, caption: str,
                          note: str="") -> dict:
    if not article.id:
        raise ValueError("Save the briefing before generating its infographic.")
    validate_spec(spec)
    if len(alt_text.strip()) < 40:
        raise ValueError("Write descriptive alt text of at least 40 characters.")
    original=fetch_owner_infographic(article.id,access_token)
    payload={
        "article_id": article.id,
        "slug": article.slug,
        "pattern": spec["pattern"],
        "spec": spec,
        "alt_text": alt_text.strip(),
        "caption": caption.strip() or "Original executive decision infographic by Jair Ribeiro.",
        "status": "draft",
        "review": {},
        "source_fingerprint": source_fingerprint(article),
        "revision": int(original.get("revision",0))+1 if original else 1,
        "editorial_note": note.strip()[:1000],
        "approved_at": None,
    }
    result=_request_json("POST",_rest_url(TABLE),
        token=access_token,payload=payload,
        prefer="return=representation")
    fetch_public_infographic.clear()
    if not isinstance(result,list) or not result:
        raise RuntimeError("Infographic save did not return a record.")
    return result[0]


def approve_infographic(access_token: str, article, row: dict,
                        checks: dict, note: str="") -> dict:
    for key in REVIEW_KEYS:
        if checks.get(key) is not True:
            raise ValueError("Each quality criterion must be explicitly reviewed.")
    validate_spec(row["spec"])
    if row.get("source_fingerprint") != source_fingerprint(article):
        raise ValueError("The article changed after generation. Regenerate the infographic first.")
    if len(str(row.get("alt_text") or ""))<40:
        raise ValueError("Accessible alt text must be completed.")
    payload={
        "status": "approved", "review": {k:True for k in REVIEW_KEYS},
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "editorial_note": note.strip()[:1000],
    }
    result=_request_json("PATCH",_rest_url(f"{TABLE}?id=eq.{quote(row['id'],safe='')}"),
        token=access_token,payload=payload,prefer="return=representation")
    fetch_public_infographic.clear()
    if not isinstance(result,list) or not result:
        raise RuntimeError("The approval did not return a record.")
    return result[0]


def reject_infographic(access_token: str, row: dict, reason: str) -> None:
    if not reason.strip():
        raise ValueError("Explain what the next visual revision must correct.")
    _request_json("PATCH",_rest_url(f"{TABLE}?id=eq.{quote(row['id'],safe='')}"),
        token=access_token,payload={"status":"rejected","editorial_note":reason.strip()[:1000]},
        prefer="return=minimal")
    fetch_public_infographic.clear()


_STUDIO_ADOPTION_SLUG = "ai-adoption-four-leadership-responses"

_STUDIO_ADOPTION_CSS = """<style>
.site .ebi-studio-figure{max-width:900px;margin-inline:auto;background:#fffdf9;padding:clamp(8px,1.4vw,20px);box-shadow:0 14px 38px rgba(19,42,62,.05)}
.site .ebi-studio-picture img{width:100%;height:auto;display:block;max-width:100%;background:#fbfcfe;aspect-ratio:3/4}
.site .ebi-studio-picture img.ebi-studio-mobile{display:none}
.site .ebi-studio-actions{display:flex;justify-content:flex-end;margin-top:12px}
.site .ebi-studio-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 17px;color:#0b3553!important;text-decoration:none!important;border:1px solid #8cafbf;border-radius:6px;font:700 12px/1.4 Arial,sans-serif;transition:background-color .2s}
.site .ebi-studio-actions a:hover{background:#e9f4f7}
.site .ebi-studio-actions a:focus-visible{outline:3px solid #147ba0;outline-offset:3px}
@media(max-width:700px){
 .site .ebi-studio-picture img.ebi-studio-desktop{display:none}
 .site .ebi-studio-picture img.ebi-studio-mobile{display:block;aspect-ratio:3/4}
 .site .ebi-studio-figure{padding:8px}
 .site .ebi-studio-actions a{width:100%}
}
</style>"""


def _approved_adoption_studio(article, row: dict) -> str:
    """Responsive Studio artwork only after approval and fingerprint verification.

    The source-approved CMS visual remains the gatekeeper; the illustrated
    original is the single displayed primary infographic for this edition.
    """
    alt = str(row.get("alt_text") or "").strip()
    if len(alt) < 40:
        return ""
    alt += " A thirty-day decision cycle asks leaders to choose, listen, respond and decide."
    caption = ("Original executive infographic by Jair Ribeiro. The four responses "
               "are situational, not permanent employee types; the work-readiness "
               "checks and thirty-day diagnostic determine the next management step.")
    # No separate image request: Safari/Streamlit production has repeatedly
    # failed to serve /app/static assets inside st.html, despite local HTTP 200.
    asset = artwork_data_uri("desktop")
    mobile = artwork_data_uri("mobile") or asset
    if not asset:
        # Fail visibly with the already-approved engine visual, never a blank
        # aspect-ratio placeholder or a browser broken-image icon.
        return infographic_html(row["spec"], row["alt_text"], row["caption"], article.slug)
    return (
        INFOGRAPHIC_CSS + _STUDIO_ADOPTION_CSS
        + '<section class="ebi-section ebi-studio" data-analytics-section="briefing-infographic" '
        + 'data-hq-content-slug="' + escape(article.slug, quote=True) + '">'
        + '<figure class="ebi-figure ebi-studio-figure">'
        + '<span class="ebi-kicker">The executive visual · Four leadership responses</span>'
        + '<div class="ebi-picture ebi-studio-picture">'
        + '<img class="ebi-studio-desktop" src="' + asset + '" alt="' + escape(alt, quote=True)
        + '" loading="eager" decoding="async"/>'
        + '<img class="ebi-studio-mobile" src="' + mobile + '" alt="' + escape(alt, quote=True)
        + '" loading="eager" decoding="async"/></div>'
        + '<figcaption>' + escape(caption) + '</figcaption>'
        + '<div class="ebi-studio-actions"><a href="' + asset
        + '" download="ai-adoption-executive-infographic.webp" '
        + 'aria-label="Download the original executive AI adoption infographic">'
        + 'Download the infographic</a></div>'
        + '</figure></section>'
    )


def approved_infographic_for(article, *, row: dict | None=None) -> str:
    """Fail closed: an old approved version never renders against newer article text."""
    if not getattr(article,"id",None):
        return ""
    if row is None:
        try:
            row=fetch_public_infographic(article.id)
        except (RuntimeError,ValueError,TimeoutError):
            return ""
    if not row or row.get("status")!="approved":
        return ""
    if row.get("source_fingerprint")!=source_fingerprint(article):
        return ""
    if article.slug == _STUDIO_ADOPTION_SLUG:
        return _approved_adoption_studio(article, row)
    try:
        return infographic_html(
            row["spec"],row["alt_text"],row["caption"],article.slug
        )
    except (KeyError,TypeError,ValueError):
        return ""


def has_approved_visual(article, token: str) -> bool:
    try:
        row=fetch_owner_infographic(article.id,token,approved_only=True) if article.id else None
    except (RuntimeError,ValueError,TimeoutError):
        return False
    return bool(row and row.get("status")=="approved"
                and row.get("source_fingerprint")==source_fingerprint(article))
