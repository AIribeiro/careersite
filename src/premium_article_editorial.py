"""Editorial readiness checks for first-release Premium Thinking Articles.

The CMS continues to store one complete article, its subtitle and its purpose-
written public excerpt. Public website previews are derived from those fields.
These checks do not claim to protect underlying public CMS API responses.
"""
from __future__ import annotations

from html.parser import HTMLParser
import re

ARTICLE_FORMATS = frozenset({
    "article", "point of view", "decision note", "field note", "framework",
})
POLICY_START = "2026-11-12"


def is_editorial_format(kind: str) -> bool:
    return str(kind or "").strip().casefold() in ARTICLE_FORMATS


class _IntroductionParagraphs(HTMLParser):
    """Collect opening paragraphs only, before the first substantive heading."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._reading_intro = True
        self._in_paragraph = False
        self._pieces: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in {"h2", "h3", "h4"}:
            self._reading_intro = False
        if tag.lower() == "p" and self._reading_intro:
            self._in_paragraph = True
            self._pieces = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self._in_paragraph:
            text = " ".join(" ".join(self._pieces).split())
            if text:
                self.paragraphs.append(text)
            self._pieces = []
            self._in_paragraph = False

    def handle_data(self, data: str) -> None:
        if self._reading_intro and self._in_paragraph:
            self._pieces.append(data)


def opening_editorial_paragraphs(content_html: str) -> tuple[str, ...]:
    parser = _IntroductionParagraphs()
    parser.feed(str(content_html or ""))
    parser.close()
    return tuple(parser.paragraphs)


def public_intro_preview_paragraphs(content_html: str, max_words: int = 160) -> tuple[str, ...]:
    """Bound the public Article preview to paragraphs before the first heading.

    Unlike generic briefing extraction, this never reaches a paragraph from the
    later Premium analysis. The excerpt is displayed separately by the reader.
    """
    paragraphs = opening_editorial_paragraphs(content_html)
    if not paragraphs:
        return ()
    plain_body = re.sub(r"<[^>]*>", " ", content_html or "")
    total_words = len(plain_body.split())
    budget = min(max_words, max(45, int(total_words * 0.34)), max(0, total_words - 1))
    remaining = budget
    selected: list[str] = []
    for paragraph in paragraphs[:3]:
        words = paragraph.split()
        if remaining < 18:
            break
        if len(words) <= remaining:
            selected.append(paragraph)
            remaining -= len(words)
            continue
        fragment = " ".join(words[:remaining])
        # Prefer a complete sentence where possible, without taking a paragraph
        # from the restricted section just to finish the preview.
        boundary = re.search(r"^(.+[.!?])(?:\\s|$)", fragment)
        if boundary and len(boundary.group(1)) > 70:
            selected.append(boundary.group(1))
        else:
            selected.append(fragment.rstrip(" ,;:") + "…")
        break
    return tuple(selected)


def needs_first_publication_review(article) -> bool:
    """Do not impose new requirements on historic drafts or published work."""
    if not is_editorial_format(getattr(article, "kind", "")):
        return False
    if getattr(article, "legacy_key", "") or getattr(article, "published_at", ""):
        return False
    created = str(getattr(article, "created_at", "") or "")
    return not created or created[:10] >= POLICY_START


def premium_article_issues(article) -> tuple[str, ...]:
    """Content checks only: editorial sign-off is still the author's decision.

    Run in the owner CMS before first publication. Existing public/premium
    reader access rules and legacy records are not modified by these checks.
    """
    if not is_editorial_format(getattr(article, "kind", "")):
        return ()

    issues: list[str] = []
    subtitle = str(getattr(article, "subtitle", "") or "").strip()
    excerpt = str(getattr(article, "excerpt", "") or "").strip()
    if len(subtitle.split()) < 8:
        issues.append("Add a substantive subtitle explaining the executive question.")
    if len(excerpt.split()) < 20:
        issues.append(
            "Write a public executive summary of at least 20 meaningful words; "
            "the CMS renders this before registration."
        )

    paragraphs = opening_editorial_paragraphs(
        str(getattr(article, "content_html", "") or "")
    )
    if not re.search(r"<h[23]\\b", str(getattr(article, "content_html", "") or ""), re.I):
        issues.append(
            "Add a meaningful section heading after the public opening to "
            "separate it from the deeper Premium analysis."
        )
    if len(paragraphs) < 2:
        issues.append(
            "Start the article with at least two complete public-facing paragraphs "
            "before the first section heading."
        )
    elif len(" ".join(paragraphs[:2]).split()) < 65:
        issues.append(
            "Develop the first two paragraphs into at least 65 words of useful "
            "executive context and judgment before the full-edition sections."
        )
    return tuple(issues)
