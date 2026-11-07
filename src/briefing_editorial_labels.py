"""Consistent visible section naming for every Executive AI Briefing.

Keep CMS title/subtitle/body byte-identical: approved infographic fingerprints
are calculated from these stored fields, not from this display-only adjustment.
"""
from __future__ import annotations

import re

LEADERSHIP_DECISION_LABEL = "The Leadership Decision"

# Older CMS editions can contain the retired term within the article itself.
# Update only visible headings, not prose, source references, metadata, or assets.
_OLD_DECISION_HEAD = re.compile(
    r"(?P<opening><(?:span|h2)\b[^>]*>)(?P<space>\s*)"
    r"(?:The executive judgment|The executive premise)"
    r"(?=\s*(?:<|:))",
    flags=re.IGNORECASE,
)


def normalize_leadership_decision_label(reader_html: str) -> str:
    """Standardize legacy heading text after rendering, without CMS writes."""
    return _OLD_DECISION_HEAD.sub(
        lambda match: (
            match.group("opening")
            + match.group("space")
            + LEADERSHIP_DECISION_LABEL
        ),
        reader_html,
    )
