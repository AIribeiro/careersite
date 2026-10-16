"""Public decision-first hiring outlook.

Only the explicitly published date-only v2 scenario is shown anonymously.
Employer, role, interview, recruiter and application evidence remain private.
Historical beta forecast math is not rendered as a live prediction.
"""
from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from page_conversion_quality import render_public_conversion_quality
from site_analytics_public import (
    fetch_public_analytics_rpc, fetch_public_hiring_timing_v2,
)


def _display_date(value: str | None, *, compact: bool = False) -> str:
    """Human-readable dates without platform-dependent %-d formatting."""
    try:
        day = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return "Not available"
    return f"{day.day} {day:%b %Y}" if compact else f"{day.day} {day:%B %Y}"


def _start_window(timing: dict) -> str:
    a = date.fromisoformat(timing["start_earliest"])
    b = date.fromisoformat(timing["start_latest"])
    return f"{a.day} {a:%b} – {b.day} {b:%b}"


def _timing_chart(timing: dict) -> alt.Chart:
    """Visual date ranges, not a cumulative hiring-probability curve."""
    data = [
        {"Milestone": "Offer", "Earliest": timing["offer_earliest"],
         "Midpoint": timing["offer_central"], "Latest": timing["offer_latest"]},
        {"Milestone": "Start", "Earliest": timing["start_earliest"],
         "Midpoint": timing["start_central"], "Latest": timing["start_latest"]},
    ]
    source = alt.Data(values=data)
    y = alt.Y("Milestone:N", sort=["Offer", "Start"],
              title=None, axis=alt.Axis(labelFontSize=13))
    start = alt.X("Earliest:T", title=None,
                  axis=alt.Axis(format="%d %b", labelAngle=0, tickCount=5))
    tooltip = [
        alt.Tooltip("Milestone:N"),
        alt.Tooltip("Earliest:T", title="Early scenario", format="%d %b %Y"),
        alt.Tooltip("Midpoint:T", title="Central scenario", format="%d %b %Y"),
        alt.Tooltip("Latest:T", title="Later scenario", format="%d %b %Y"),
    ]
    window = (
        alt.Chart(source)
        .mark_bar(size=17, cornerRadius=5)
        .encode(x=start, x2="Latest:T", y=y, tooltip=tooltip)
    )
    midpoint = (
        alt.Chart(source)
        .mark_point(size=115, filled=True, shape="diamond")
        .encode(x="Midpoint:T", y=y, tooltip=tooltip)
    )
    return (window + midpoint).properties(height=118)


def _week(x: dict | None) -> str:
    """Legacy date formatter for historical beta regression fixtures."""
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
    st.title("When could I get my next job?")
    try:
        timing = fetch_public_hiring_timing_v2()
    except (RuntimeError, ValueError, PermissionError, TimeoutError):
        timing = {"available": False}

    if timing.get("available"):
        with st.container(border=True):
            st.caption("INDICATIVE FIRST DAY AT WORK")
            st.markdown(f"# {_display_date(timing['start_central'])}")
            st.caption(
                "Conditional on current interview processes progressing to an offer."
            )

        offer, starting, window = st.columns(3, gap="small")
        with offer:
            with st.container(border=True):
                st.metric("Potential job offer", _display_date(
                    timing["offer_central"], compact=True))
        with starting:
            with st.container(border=True):
                st.metric("Potential start", _display_date(
                    timing["start_central"], compact=True))
        with window:
            with st.container(border=True):
                st.metric("Possible start window", _start_window(timing))
                st.caption("2026–2027" if timing["start_earliest"][:4] !=
                           timing["start_latest"][:4] else
                           timing["start_earliest"][:4])

        st.markdown("**Offer and start timing range**")
        st.altair_chart(_timing_chart(timing), width="stretch")
        st.caption(
            f"Ranges show early–late scenarios; diamonds mark central dates. "
            f"Updated {_display_date(timing['as_of'])} · "
            "Not a confirmed offer or calibrated hiring probability."
        )
        if timing.get("needs_refresh"):
            st.warning("This scenario is older than two weeks; the next verified "
                       "recruitment update will refresh it.")
    else:
        with st.container(border=True):
            st.markdown("## No current start-date scenario")
            st.caption(
                "The latest published v2 forecast is unavailable or too old. "
                "The page does not substitute unvalidated offer-week estimates."
            )

    st.divider()
    with st.expander("Recruitment evidence and conversion", expanded=False):
        st.caption(
            "Human responses and verified interview progression are stronger "
            "signals than application volume. A scheduled interview is not "
            "a completed one. Silence is not a verified rejection."
        )
        render_public_conversion_quality(compact=False)

    with st.expander("Methodology, market context and limitations", expanded=False):
        st.markdown(
            "**Current model:** Hiring Prediction v2 uses confirmed recruiting "
            "stages, role alignment and evidence freshness. Its date range is "
            "conditional on future successful progression, not an observed "
            "30-, 60- or 90-day chance of getting hired."
        )
        st.caption(
            "Historic beta 4.3 model-week curves have been retired from the "
            "current page because their arbitrary weights did not measure "
            "personal hiring probabilities."
        )
        try:
            market = fetch_public_analytics_rpc(
                "careersite_public_market_summary_v1")
        except (RuntimeError, ValueError, PermissionError, TimeoutError):
            market = None
        if isinstance(market, dict) and market.get("signals"):
            st.caption(
                "Swedish labour-market signals provide context, not proof of "
                "a particular employer's hiring decision."
            )
        st.caption(
            "Only dates from a specifically published v2 projection appear "
            "here. Employer names, interviews, application records and "
            "contact details remain private."
        )

    st.caption(
        "See detailed role-by-role evidence in the "
        "**[private Decision overview](?page=admin)**."
    )
