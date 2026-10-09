"""Concise, owner-only presentation of the experimental offer-date predictor."""
from __future__ import annotations

from datetime import date, timedelta

import altair as alt
import streamlit as st

from hiring_predictor import forecast_hiring, MODEL_VERSION


def _month(value: str | None) -> str:
    if not value:
        return "Not reached within 12 months"
    d = date.fromisoformat(value)
    return d.strftime("%b %Y")


def render_hiring_predictor(jobs: list[dict], market_model: dict | None,
                            site_correlation: dict | None, hiring: dict | None,
                            today: date) -> None:
    st.subheader("Hiring predictor")
    st.caption("Experimental beta · scenario estimate of when a job offer might arrive. "
               "A start date could be later.")
    result = forecast_hiring(jobs, today, market_model=market_model,
                             portfolio_correlation=site_correlation,
                             hiring_quality=hiring)
    sources = result["sources"]

    if result["status"] == "offer_recorded":
        st.info("An offer event is already recorded. Check the current process and signed "
                "agreement instead of projecting a first offer.")
        return
    if result["status"] == "insufficient":
        st.info("Not enough dated job-search history or current pipeline evidence for "
                "a defensible scenario date. The predictor will populate as records arrive.")
        return

    crossing = result["crossings"]
    baseline = crossing["Current pace"]
    fastest = crossing["Faster conversion"]
    slowest = crossing["Conservative"]

    with st.container(border=True):
        a, b, c = st.columns([1.3, 1.4, 1.0])
        a.metric("Central scenario · offer", _month(baseline),
                 help="Date when the uncalibrated current-pace model first crosses "
                      "an illustrative 50% cumulative offer likelihood. Not an empirical median.")
        if fastest and slowest:
            case_range = f"{_month(fastest)} – {_month(slowest)}"
        elif fastest:
            case_range = f"{_month(fastest)} – beyond 12 months"
        else:
            case_range = "Not estimable"
        b.metric("Sensitivity range", case_range,
                 help="Faster vs conservative assumed conversion. This is NOT a statistical "
                      "confidence interval or a guaranteed hiring window.")
        c.metric("Evidence confidence", result["confidence"],
                 help="No observed offer-conversion sample is available to validate "
                      "the assumed stage-to-offer rates.")

        if not baseline:
            st.warning("The present assumptions do not reach a 50% crossing within a year. "
                       "This is not a prediction that no job will be found.")
        else:
            st.caption("Conditional on a similar search pace and assumed stage conversion. "
                       "Dates move automatically as the recorded pipeline changes. "
                       "This is a planning scenario, not a reliable personal probability.")

        st.markdown("**What is shaping the estimate**")
        stages = result["active_stages"]
        advanced = sum(r["stage"] in ("progression", "interview") for r in stages)
        conversations = sum(r["stage"] == "conversation" for r in stages)
        st.markdown(
            f"- **Current pipeline:** {advanced} recently documented interview/advanced "
            f"processes and {conversations} conversation-stage processes remain potentially open; "
            "unknown-status cases are discounted."
        )
        st.markdown(
            f"- **Search momentum:** {sources['applications_last_28d']} recorded applications "
            f"in the latest 28 days versus {sources['applications_previous_28d']} "
            "in the preceding 28. Volume affects future opportunities, not a guaranteed offer."
        )
        if sources["qualified_portfolio_sessions_30d"]:
            st.markdown(
                f"- **Portfolio evidence:** {sources['qualified_portfolio_sessions_30d']} "
                "qualified sessions in 30 days; visitor attention is not assumed to be "
                "recruiter interest or a job offer."
            )
        else:
            st.markdown("- **Portfolio evidence:** no qualified 30-day session measure "
                        "available for this forecast.")
        st.markdown(
            f"- **Swedish market:** {sources['market_indicator_series']} independently tracked "
            "indicator series reviewed as context. No unsupported market-to-offer multiplier."
        )

    with st.expander("Forecast scenarios, input coverage and assumptions"):
        st.caption("Illustrative cumulative likelihood of at least one recorded offer, "
                   "not a calibrated personal probability. Shaded differences between "
                   "scenarios are sensitivity to assumptions, not statistical uncertainty.")
        plotting = [
            {"Date": r["Date"], "Scenario": label, "Illustrative likelihood": r[label] * 100}
            for r in result["curve"] for label in
            ("Conservative", "Current pace", "Faster conversion")
        ]
        if plotting:
            chart = alt.Chart(alt.Data(values=plotting)).mark_line(strokeWidth=2.5).encode(
                x=alt.X("Date:T", title="Potential offer date"),
                y=alt.Y("Illustrative likelihood:Q", title="Scenario likelihood (%)",
                        scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Scenario:N"),
                tooltip=["Date:T", "Scenario:N",
                         alt.Tooltip("Illustrative likelihood:Q", format=".1f")],
            ).properties(height=240)
            st.altair_chart(chart, width="stretch")
        st.markdown("**Coverage / quality checks**")
        st.caption(
            f"{sources['primary_events']} primary dated events over "
            f"{sources['job_history_days']} days · "
            f"{sources['tracked_processes']} linked processes · "
            f"{sources['mature_applied_processes']} mature application processes · "
            f"{sources['recorded_offer_events']} recorded offers · "
            f"{sources['market_observations']} market observations · "
            f"{sources['portfolio_repeated_associations']} repeated portfolio associations · "
            f"{sources['market_repeated_associations']} repeated market associations."
        )
        st.markdown("**Model assumptions**")
        st.caption(
            "Stage-specific offer chances are illustrative, not calibrated to your own history: "
            "application 1.2%, human conversation 6.5%, completed interview 18%, "
            "explicit progression 32%. A Weibull-style time curve models decision delays; "
            "weekly new-application arrivals reflect the last 56 days. Conservative / "
            "faster scenarios scale those conversion assumptions by 0.55× / 1.5×. "
            "Stale or unconfirmed processes contribute less. The model neither interprets "
            "generic recruitment outlook figures as personal probabilities nor counts "
            "anonymous visits as employers. A 50% crossing is only a scenario reference point."
        )
        for item in result["limitations"]:
            st.caption("• " + item)
        st.caption(f"Model {MODEL_VERSION} · calculated {today:%d %b %Y} · "
                   "automatically recalculated when Overview refreshes. "
                   "No extra sign-in or tracking is required.")
