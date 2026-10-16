"""Public hiring outlook: evidence-led, without private v2 process details.

The prior public beta model inferred spurious offer weeks from aggregate
stage counts and hypothetical future applications. The authoritative personal
interview-stage v2 model is owner-only and must never be called anonymously.
The old public beta math remains as historical code, but is not rendered.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from page_conversion_quality import render_public_conversion_quality
from site_analytics_public import fetch_public_analytics_rpc


def _week(x: dict | None) -> str:
    """Legacy historical date formatting; not used for live public predictions."""
    if not x:
        return "Not yet estimable"
    try:
        a = date.fromisoformat(str(x["from"]))
        b = date.fromisoformat(str(x["to"]))
    except (ValueError, TypeError, KeyError):
        return "Not yet estimable"
    if a.month == b.month:
        return f"{a.day}–{b.day} {b:%b %Y}"
    return f"{a:%d %b} – {b:%d %b %Y}"


@st.fragment(run_every="15m")
def render_public_hiring_predictions() -> None:
    st.title("Job Predictions")
    st.caption(
        "Hiring Prediction v2 · evidence-first edition. This public view uses "
        "privacy-thresholded cohort statistics, not private recruiter records."
    )
    st.markdown("**The current personal forecast is based on verified recruiting stages.**")
    st.info(
        "An employer's confirmed interview progression matters more than "
        "an application count. Public, aggregated stage history cannot reliably "
        "identify a personal offer week or first day at work."
    )

    st.markdown("**What the latest evidence can establish**")
    st.caption(
        "Recorded human responses and interviews provide stronger indications of "
        "recruiting traction than job-application volume. Confirmed subsequent "
        "interview invitations are distinct from completed interviews. "
        "Employer silence represents uncertainty, not a verified rejection."
    )
    render_public_conversion_quality(compact=False)

    st.markdown("**What cannot yet be inferred**")
    st.caption(
        "There are not enough verified offer outcomes to calibrate a personal "
        "30-, 60- or 90-day offer probability. Historical beta 4.3 curves and "
        "highest-weighted offer weeks are therefore no longer presented as "
        "current forecasts."
    )

    try:
        market = fetch_public_analytics_rpc("careersite_public_market_summary_v1")
    except (RuntimeError, ValueError, PermissionError, TimeoutError):
        market = None
    if isinstance(market, dict) and market.get("signals"):
        st.caption(
            "Swedish labour-market and target-role demand evidence remains an "
            "external contextual factor. It does not establish an employer's "
            "decision about an individual candidate."
        )

    with st.expander("What changed in the hiring methodology?"):
        st.markdown(
            "**V2 (current, private):** verified employer contact, scheduled versus "
            "completed interviews, subsequent-round progression, role alignment, "
            "evidence freshness and employer decisions. Its credibility index is "
            "a descriptive pipeline score, not a hiring probability."
        )
        st.markdown(
            "**Beta 4.3 (historical):** scenario curves built from 30-day "
            "aggregated stages, hypothetical application pace and capped "
            "market/portfolio multipliers. These produced illustrative week "
            "weights, not validated personal employment forecasts."
        )
        st.caption(
            "The stage-level evidence required for v2 is owner-only, including "
            "specific employers, hiring-manager correspondence, roles and "
            "interview appointments. It is not exposed through this page."
        )

    st.markdown(
        "To see the **current role-by-role v2 forecast and conditional hiring "
        "window**, open the **[private owner workspace](?page=admin)** and "
        "select **Decision overview**."
    )
