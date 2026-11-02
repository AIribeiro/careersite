from __future__ import annotations

"""Private visual approval records + public read-only infographic lookup."""

from datetime import datetime, timezone
from urllib.parse import quote

import streamlit as st

from briefing_infographic_engine import (
    REVIEW_KEYS, infographic_html, source_fingerprint, validate_spec,
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
        f"{TABLE}?select=*&article_id=eq.{quote(str(article_id),safe='')}"
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
