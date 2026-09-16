from __future__ import annotations

"""Canonical public distribution policy for Jair Ribeiro's career site.

This module intentionally contains only the active Streamlit distribution surface.
Alternate deployments are not public distribution targets until explicitly promoted.
"""

from urllib.parse import urlencode

CANONICAL_SITE_URL = "https://jairribeiro-ai.streamlit.app/"
CANONICAL_SITE_DISPLAY = "jairribeiro-ai.streamlit.app"
CV_PORTFOLIO_LABEL = "AI & Data Portfolio"

ATTRIBUTION_SOURCES = (
    "linkedin",
    "email",
    "cv",
    "outreach",
    "application",
)


def attributed_url(
    source: str,
    *,
    page: str | None = None,
    role: str | None = None,
    fragment: str | None = None,
) -> str:
    """Build an attributed public URL using the production query convention."""
    if source not in ATTRIBUTION_SOURCES:
        raise ValueError(f"Unsupported attribution source: {source}")

    params: list[tuple[str, str]] = []
    if page and page != "home":
        params.append(("page", page))
    params.append(("source", source))
    if role:
        params.append(("role", role))

    url = CANONICAL_SITE_URL + "?" + urlencode(params)
    if fragment:
        url += "#" + fragment
    return url


PERMANENT_SURFACES = {
    "linkedin": attributed_url("linkedin"),
    "cv": attributed_url("cv"),
    "email": attributed_url("email"),
    "outreach": attributed_url("outreach"),
    "application": attributed_url("application"),
}

LINKEDIN_FEATURED = {
    "title": "Enterprise AI & Data Leadership",
    "description": "Leadership cases, role-specific perspectives and practical operating frameworks beyond the CV.",
    "url": PERMANENT_SURFACES["linkedin"],
}

APPLICATION_LENSES = {
    "head_data_ai": attributed_url(
        "application", page="enterprise", role="head-data-ai"
    ),
    "ai_transformation": attributed_url(
        "application", page="transformation", role="ai-transformation"
    ),
    "ai_governance": attributed_url(
        "application", page="governance", role="ai-governance"
    ),
    "business_driven_ai": attributed_url(
        "application", page="consulting", role="business-driven-ai"
    ),
    "ai_data_leadership": attributed_url(
        "application", page="impact", role="ai-data-leadership"
    ),
}

POST_INTERVIEW_LINKS = {
    "operating_model": attributed_url(
        "email",
        page="impact",
        role="ai-transformation",
        fragment="leadership-frameworks",
    ),
    "head_data_ai": attributed_url("email", page="enterprise", role="head-data-ai"),
    "ai_governance": attributed_url("email", page="governance", role="ai-governance"),
    "business_driven_ai": attributed_url(
        "email", page="consulting", role="business-driven-ai"
    ),
}

COPY = {
    "recruiter_default": (
        "Leadership cases and perspective beyond the CV: "
        + PERMANENT_SURFACES["outreach"]
    ),
    "recruiter_soft": (
        "If useful, I keep a concise set of leadership cases and role-specific "
        "perspectives here: "
        + PERMANENT_SURFACES["outreach"]
    ),
    "email_default": (
        "More context on my leadership experience, cases and operating perspective: "
        + PERMANENT_SURFACES["email"]
    ),
}

OPERATING_RULE = (
    "Permanent surfaces use the attributed main site; hiring interactions use the "
    "closest relevant contextual page."
)

PREFERRED_EVIDENCE_PHRASES = (
    "the examples we discussed",
    "leadership cases beyond the CV",
    "relevant perspective",
    "captured here if useful",
)
