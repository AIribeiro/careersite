"""Shared executive Advisory presentation language.

Rollout Readiness Advisor established the reference hierarchy and visual system.
Other Advisory services reuse that hierarchy while retaining service-specific
content, authentication and approval requirements.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from page_rollout_workspace_ui import WORKSPACE_CSS


def _safe(value: object, limit: int = 1200) -> str:
    return escape(str(value if value is not None else "")[:limit], quote=True)


def service_overview(
    *,
    hero: str,
    description: str,
    access: str,
    assessment_format: str,
    saved_count: int,
    outputs: tuple[tuple[str, str, str], ...],
    steps: tuple[tuple[str, str], ...],
    boundary: str,
    kicker: str = "PRIVATE EXECUTIVE DECISION ADVISORY",
    outputs_headline: str = "One business decision. Three concrete outputs.",
    method_headline: str = "Focused input. Decision-ready output.",
) -> None:
    """Render the same card hierarchy, spacing and typography as Rollout.

    All content is escaped. Output labels and steps may differ by assessment,
    but the executive service page keeps the same information architecture.
    """
    if len(outputs) != 3 or len(steps) != 3:
        raise ValueError("The Advisory service template requires three outputs and steps.")
    cards = "".join(
        '<article><span class="eyebrow">' + f"{i:02d} · " + _safe(label) +
        '</span><strong>' + _safe(title) + '</strong><p>' + _safe(detail) + '</p></article>'
        for i, (label, title, detail) in enumerate(outputs, 1)
    )
    sequence = "".join(
        '<div><b>' + f"{i:02d}" + '</b><strong>' + _safe(label) +
        '</strong><span>' + _safe(detail) + '</span></div>'
        for i, (label, detail) in enumerate(steps, 1)
    )
    plural = "" if saved_count == 1 else "s"
    st.html(
        WORKSPACE_CSS +
        '<div class="rl-workspace">'
        '<section class="hero"><span class="eyebrow">' + _safe(kicker) + '</span>'
        '<h2>' + _safe(hero) + '</h2><p>' + _safe(description) + '</p></section>'
        '<div class="summarybar"><span>ACCESS · ' + _safe(access) + '</span>'
        '<span>FORMAT · ' + _safe(assessment_format) + '</span>'
        f'<span>HISTORY · {saved_count} saved decision{plural}</span></div>'
        '<div class="section-head"><span class="eyebrow">What you receive</span>'
        '<h3>' + _safe(outputs_headline) + '</h3>'
        '<p>A decision advisory service, not a generic AI assessment or project tracker.</p>'
        '</div><div class="three-col">' + cards + '</div>'
        '<div class="section-head"><span class="eyebrow">How it works</span>'
        '<h3>' + _safe(method_headline) + '</h3></div>'
        '<div class="steps">' + sequence + '</div>'
        '<div class="callout"><strong>Decision and access boundaries</strong>' +
        _safe(boundary) + '</div></div>'
    )


def case_header(
    *,
    title: str,
    date: str,
    context: str,
    status: str = "",
    synthetic: bool = False,
) -> None:
    """Consistent selected-case header for all private service reports."""
    parts = [p for p in (context, status) if p]
    st.html(
        WORKSPACE_CSS + '<div class="rl-workspace"><div class="section-head">'
        '<span class="eyebrow">Selected assessment · ' + _safe(date, 32) + '</span>'
        '<h3>' + _safe(title, 150) + '</h3>'
        '<p>' + " · ".join(_safe(p, 250) for p in parts) + '</p>'
        '</div>' +
        ('<div class="provenance"><strong>Synthetic assessment.</strong> '
         'Any reported context and figures are illustrative and not independently verified.'
         '</div>' if synthetic else '') +
        '</div>'
    )
