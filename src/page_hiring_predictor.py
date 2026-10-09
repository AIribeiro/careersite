"""Human-readable, owner-only Hiring Predictor Beta presentation."""
from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from hiring_predictor import forecast_hiring, MODEL_VERSION


def _month(value: str | None) -> str:
    return date.fromisoformat(value).strftime("%B %Y") if value else "Not yet clear"


def _months(start: str | None, end: str | None) -> str:
    if not start or not end:
        return "Not yet clear"
    a, b = _month(start), _month(end)
    return a if a == b else f"{a} – {b}"


def _shift(last: str | None, current: str | None) -> str | None:
    if not last or not current:
        return None
    days = (date.fromisoformat(current) - date.fromisoformat(last)).days
    if abs(days) < 14:
        return None  # Weekly scenario steps: small changes are noise.
    return "earlier" if days < 0 else "later"


def render_hiring_predictor(
    jobs: list[dict], market_model: dict | None,
    site_correlation: dict | None, hiring: dict | None,
    today: date,
) -> None:
    st.subheader("When might I get a job?")
    st.caption("Hiring Predictor · Beta · a guide for planning, not a promise.")

    result = forecast_hiring(jobs, today, market_model=market_model,
                             portfolio_correlation=site_correlation,
                             hiring_quality=hiring)
    sources = result["sources"]
    if result["status"] == "offer_recorded":
        st.info("A job offer is already documented. Your next milestone is a confirmed "
                "start date, not another predicted offer.")
        return
    if result["status"] == "insufficient":
        st.info("Too early to estimate. More dated applications and employer responses "
                "are needed before a useful planning month can be shown.")
        return

    central = result["crossings"].get("Current pace")
    faster = result["crossings"].get("Faster conversion")
    slower = result["crossings"].get("Conservative")
    start_window = result.get("start_window") or {}

    first, second, third = st.columns([1.2, 1.3, 1])
    first.metric("Possible job offer", _month(central),
                 help="The model's middle planning scenario. It is not a statistically "
                      "validated likelihood or a confirmed employer decision.")
    second.metric("Possible first day", _months(start_window.get("from"),
                                                start_window.get("to")),
                  help="Assumes roughly 3–8 weeks from offer to start. Actual notice, "
                       "contract and onboarding dates may differ.")
    third.metric("How reliable?", "Early estimate",
                 help="The data describes activity, not enough actual job offers to "
                      "measure personal offer conversion.")

    if central:
        st.markdown(
            f"**Current outlook:** If the job search continues at roughly its recent "
            f"recorded pace, **{_month(central)}** is a reasonable month to use for "
            "planning discussions—not a deadline or guaranteed outcome."
        )
    else:
        st.markdown(
            "**Current outlook:** The available evidence does not support a useful "
            "central month within the next year. This does **not** mean an offer "
            "cannot arrive sooner."
        )

    # Changes are compared within the current browser session only; no personal
    # forecasts are written to the analytics event ledger.
    previous = st.session_state.get("hiring_predictor_last_forecast")
    if previous and previous.get("as_of") <= today.isoformat():
        movement = _shift(previous.get("central"), central)
        if movement:
            st.caption(f"Since the previous check, the planning month moved {movement}. "
                       "This is a model update, not a change confirmed by an employer.")
    st.session_state["hiring_predictor_last_forecast"] = {
        "central": central, "as_of": today.isoformat(),
    }

    stages = result["active_stages"]
    advanced = sum(p["stage"] in ("interview", "progression") for p in stages)
    conversation = sum(p["stage"] == "conversation" for p in stages)
    if advanced:
        key_message = (f"{advanced} recently documented interview or later-stage "
                       "process(es) are the clearest potential near-term routes.")
    elif conversation:
        key_message = (f"{conversation} recently documented employer conversation(s) "
                       "matter more than the number of applications alone.")
    else:
        key_message = ("Most of the tracked activity has not reached a confirmed "
                       "employer conversation. New replies are the key next signal.")
    st.markdown(f"**Why the model says this:** {key_message}")
    st.caption(
        f"The model sees {sources['applications_last_28d']} linked applications in "
        f"the past 28 days, versus {sources['applications_previous_28d']} previously. "
        f"It uses a restrained pace of about {sources['assumed_weekly_pace']:.1f} "
        "applications per week in its future-search scenario."
    )
    st.caption(
        "Portfolio visits and Swedish job-market indicators are checked as context, "
        "but do not push the estimated date earlier unless a reliable link to "
        "actual hiring outcomes is established."
    )

    with st.expander("What if things move faster or slower?"):
        if faster:
            st.markdown(f"**Faster progress:** around {_month(faster)}.")
        else:
            st.markdown("**Faster progress:** a clear month is not available yet.")
        if slower:
            st.markdown(f"**Slower progress:** around {_month(slower)}.")
        else:
            st.markdown("**Slower progress:** could extend beyond the next 12 months.")
        st.caption("These scenarios change assumed hiring conversion. They are not "
                   "confidence bounds and do not predict what any employer will do.")

        with st.container():
            points = [
                {"Date": row["Date"], "Scenario": name, "Illustrative score": row[name] * 100}
                for row in result["curve"]
                for name in ("Conservative", "Current pace", "Faster conversion")
            ]
            if points:
                chart = alt.Chart(alt.Data(values=points)).mark_line(strokeWidth=2).encode(
                    x=alt.X("Date:T", title="Potential offer period"),
                    y=alt.Y("Illustrative score:Q", title="Model scenario scale (0–100)",
                            scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color("Scenario:N"),
                    tooltip=["Date:T", "Scenario:N",
                             alt.Tooltip("Illustrative score:Q", format=".0f")],
                ).properties(height=230)
                st.altair_chart(chart, width="stretch")
            st.caption("The chart uses an arbitrary scenario scale to compare timing "
                       "assumptions. It is not a measured percentage chance of being hired.")

    with st.expander("How is this calculated?"):
        st.markdown(
            "**Your job search:** Dated, duplicate-checked hiring events; verified "
            "interviews and two-way contact; ages and known closures of active processes; "
            "and recent application pace."
        )
        st.caption(
            f"Only {sources['linked_application_processes']} application processes have "
            "enough linked event records for this model"
            + (f", compared with {sources['official_application_total']} applications "
               "in the official cumulative snapshot." if sources["official_application_total"]
               is not None else ".")
        )
        st.caption(
            f"{sources['mature_applied_processes']} tracked applications are at least "
            f"35 days old; {sources['mature_with_human_contact']} have a dated inbound "
            "or two-way contact, interview or progression. Missing history is not "
            "treated as rejection or zero conversion."
        )
        st.markdown(
            "**Market and portfolio:** Current indicators and anonymous activity are "
            "reviewed, but not treated as direct predictors of an offer."
        )
        st.markdown(
            "**Assumptions:** The model combines stage-specific offer assumptions "
            "with a smoothed contact rate from older tracked applications. It reduces "
            "the impact of unconfirmed and old processes, and keeps future application "
            "volume within a cautious limit. No personal offer rate has been verified."
        )
        for note in result["limitations"]:
            st.caption("• " + note)
        st.caption(f"Model {MODEL_VERSION} · refreshed {today:%d %B %Y} when new "
                   "data is available on the Analytics Overview.")
