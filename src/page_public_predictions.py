"""Public anonymized Hiring Predictor, with detailed Beta kept owner-only."""
from __future__ import annotations

from datetime import date

import altair as alt
import streamlit as st

from public_hiring_forecast import forecast_public_hiring
from site_analytics_public import fetch_public_analytics_rpc
from page_content_intelligence import _fetch_rpc


def _week(x: dict | None) -> str:
    if not x:
        return "Not yet estimable"
    try:
        a=date.fromisoformat(str(x["from"]))
        b=date.fromisoformat(str(x["to"]))
    except (ValueError,TypeError,KeyError):
        return "Not yet estimable"
    if a.month==b.month:
        return f"{a.day}–{b.day} {b:%b %Y}"
    return f"{a:%d %b} – {b:%d %b %Y}"


@st.fragment(run_every="15m")
def render_public_hiring_predictions() -> None:
    st.title("Job Predictions")
    st.caption(
        "Hiring Predictor · public planning edition. "
        "Based on anonymized recruitment-stage distributions, quality-filtered "
        "portfolio activity and cited Swedish market signals."
    )
    try:
        inputs=fetch_public_analytics_rpc("careersite_public_hiring_inputs_v1")
    except (RuntimeError,ValueError,PermissionError):
        st.warning("Hiring scenarios are temporarily unavailable.")
        return

    market=[]
    portfolio={}
    market_ok=False
    portfolio_ok=False
    try:
        data=fetch_public_analytics_rpc("careersite_public_market_summary_v1")
        market=data.get("signals") or []
        market_ok=True
    except (RuntimeError,ValueError,PermissionError):
        pass
    try:
        portfolio=_fetch_rpc("careersite_portfolio_signals_daily_v1",{"p_days":365})
        portfolio_ok=True
    except (RuntimeError,ValueError,PermissionError):
        pass

    result=forecast_public_hiring(inputs, portfolio, market)
    st.caption(
        "Stage inputs exclude only current evidence-verified dormant processes; "
        "unverified silence is not rejection. This aggregate planning model "
        "uses the original dated application history."
    )
    if result["status"]=="offer_recorded":
        st.info("A current offer is already documented. An additional first-offer scenario is withheld.")
        return
    if result["status"]=="insufficient":
        st.info("Not enough dated hiring-stage evidence for a meaningful planning period.")
        return

    offer=(result["windows"].get("offers") or [None])[0]
    starting=(result["windows"].get("starts") or [None])[0]
    a,b=st.columns(2)
    with a:
        st.markdown("**Highest-weighted offer week**")
        st.subheader(_week(offer))
        if offer:
            st.caption(
                f"{offer['model_week_pct']:.1f}% of this scenario's "
                "weekly model weight—not a calibrated likelihood."
            )
    with b:
        st.markdown("**Highest-weighted start week**")
        st.subheader(_week(starting))
        if starting:
            st.caption(
                f"{starting['model_week_pct']:.1f}% of this scenario's "
                "weekly model weight—not a confirmed start date."
            )

    st.markdown("**Offer-timing planning scenarios**")
    data=[{"Date":r["Date"],"Scenario":name,"Model index":round(100*r[name],1)}
          for r in result["curve"]
          for name in ("Conservative","Current pace","Faster conversion")]
    if data:
        chart=(alt.Chart(alt.Data(values=data)).mark_line()
               .encode(x=alt.X("Date:T",title="Potential offer period"),
                       y=alt.Y("Model index:Q",title="Illustrative model index (0–100)",
                               scale=alt.Scale(domain=[0,100])),
                       color="Scenario:N",
                       tooltip=["Date:T","Scenario:N","Model index:Q"])
               .properties(height=290))
        st.altair_chart(chart,width="stretch")
    st.caption(
        "The vertical scale represents scenario mathematics, not independently "
        "validated personal hiring probabilities. Conservative/current/faster "
        "assumptions vary conversion and opportunity pace, not confirmed decisions."
    )

    m1,m2,m3=st.columns(3)
    m1.metric("Future application pace assumed",f"{result['weekly_application_pace']:.1f}/week")
    m2.metric("Portfolio scenario contribution",f"{result['portfolio_effect']:+.1%}")
    m3.metric("Swedish market contribution",f"{result['market_effect']:+.1%}")
    market_context=result.get("market_context") or {}
    nowcast=market_context.get("nowcast") or {}
    if nowcast.get("components"):
        st.caption(
            f"Current-month JobTech nowcast: {nowcast.get('effect',0):+.1%}. "
            "Partial-month AI/Data leadership ad pace is compared with the "
            "previous completed month and damped for sample size and month completeness."
        )
    corroboration=float(market_context.get("corroboration_multiplier") or 1.0)
    if corroboration>1.001:
        st.caption(
            f"Cross-signal confirmation: ×{corroboration:.2f}, still bounded by "
            "the Swedish-market cap."
        )
    strategy=result.get("strategy_context") or {}
    if strategy.get("records_used"):
        st.caption(
            f"Strategy calibration: {strategy['records_used']} current job-search "
            "strategy records are consumed as qualitative guardrails. They do not "
            "receive an unvalidated probability multiplier."
        )
    with st.expander("How this edition differs from the detailed Hiring Predictor"):
        st.write(
            "This is a privacy-preserving approximation of the existing "
            f"{result['model_family']} stage-based planning model. Individual "
            "employers, roles, case notes and recruiter details are not published. "
            "Instead, current hiring stages are grouped into 30-day age buckets; "
            "that coarsening changes the estimated offer/start weeks slightly."
        )
        st.write(
            "The 30-day, 7-day or Today reporting selector in Job Search affects "
            "activity charts only. Predictions intentionally use the complete "
            "dated recruitment history and up to 365 days of portfolio data."
        )
        st.write(
            "The public model cannot use the detailed owner-only CV/contact "
            "action breakdowns or the complete per-process records. "
            "Consequently its output may differ from the protected "
            "Hiring Predictor Beta, which remains the authoritative personal "
            "planning model."
        )
        if not market_ok or not portfolio_ok:
            st.warning(
                "Some live market or portfolio data were unavailable; "
                "missing drivers were kept neutral rather than invented."
            )
        st.caption(
            "All numbers are dynamic and conditional. Historical applications "
            "can be revised; opportunities may close unexpectedly. "
            "A first day at work is modeled roughly 3–8 weeks after an offer."
        )
    st.markdown(
        "For the full role-by-role, evidence-sensitive predictor and detailed "
        "recruitment drivers, open the **[private owner workspace](?page=admin)** "
        "and choose **Decision overview**."
    )
