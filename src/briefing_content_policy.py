from __future__ import annotations

"""Editorial identity guard for Executive AI Briefings.

Only independently verified public names of the author's former employers are
used to screen editorial text and links. This complements, not replaces,
human review for sensitive or recognizable operational details.
"""

from html import unescape
import re


_EXECUTIVE_BRIEFING_KIND = "executive briefing"
# A conservative set of publicly known former-employer names and abbreviations.
# Case-insensitive word boundaries avoid matches inside unrelated words.
_EMPLOYER_NAME_RE = re.compile(
    r"(?<!\w)(?:"
    r"volvo(?:\s+(?:group|trucks))?"
    r"|msx(?:i)?(?:\s+international)?"
    r"|kimberly[\s-]?clark"
    r"|ibm"
    r"|hewlett[\s-]?packard(?:\s+enterprise)?"
    r"|hpe"
    r")(?!\w)",
    flags=re.IGNORECASE,
)

_PUBLIC_ARTICLE_FIELDS = (
    "title", "slug", "subtitle", "excerpt", "content_html", "aside_html",
    "source_url", "header_image_url", "header_image_alt", "seo_title",
    "meta_description", "social_title", "social_description",
)


def validate_briefing_employer_anonymity(article: object) -> None:
    """Block names of known former employers in any public briefing field.

    This does not establish that an anonymized case is genuinely field-informed.
    The editorial release checklist still requires independent human review.
    """
    if str(getattr(article, "kind", "")).strip().casefold() != _EXECUTIVE_BRIEFING_KIND:
        return

    for field in _PUBLIC_ARTICLE_FIELDS:
        value = str(getattr(article, field, "") or "")
        if _EMPLOYER_NAME_RE.search(unescape(value)):
            raise ValueError(
                "Executive AI Briefings must not identify current or former "
                "employers, including in examples, references, links, "
                f"disclaimers or metadata. Review field: {field}."
            )
