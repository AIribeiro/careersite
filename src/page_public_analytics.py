"""Open, read-only Analytics summaries. No identifiable recruitment evidence.

The public site never retrieves job_search_analytics rows, contacts, private
notes, source workbooks, follow-up actions or CMS credentials.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from page_analytics import _fetch_hiring_intelligence
from page_content_intelligence import _fetch_rpc
from portfolio_job_correlations import (
    ANCHORS, LAGS, _site_features, _test_one, _bh_pvalues, _classify,
)
from site_analytics_public import fetch_public_analytics_rpc


def _n(x: object) -> int:
    try:
        return int(x or 0)
    except (TypeError,ValueError):
        return 0


def _job_summary(days: int = 365) -> dict:
    return fetch_public_analytics_rpc(
        "careersite_public_job_summary_v1",{"p_days":days}
    )


def _market_summary() -> dict:
    return fetch_public_analytics_rpc("careersite_public_market_summary_v1")


@st.fragment(run_every="10m")
def render_public_analytics_overview() -> None:
    st.title("Analytics overview")
    st.caption("Open, read-only evidence about portfolio activity, recruitment progress and Swedish hiring conditions.")
    try:
        hiring = _fetch_hiring_intelligence("30d")
        jobs = _job_summary()
        market = _market_summary()
    except (RuntimeError,ValueError,PermissionError):
        st.warning("The public analytics summaries are temporarily unavailable.")
        return
    q = hiring.get("quality_summary") or {}
    totals = jobs.get("totals") or {}
    signals = market.get("signals") or []
    a,b,c,d = st.columns(4)
    a.metric("Qualified portfolio sessions · 30d", _n(q.get("analysis_eligible_sessions")))
    b.metric("Dated applications · 365d", _n(totals.get("applications")))
    c.metric("Inbound interactions · 365d", _n(totals.get("responses")))
    d.metric("Completed interviews · 365d", _n(totals.get("interviews")))
    st.caption(
        "A session is not a unique visitor; job-search measures are dated, "
        "deduplicated employer-and-role events, not necessarily independent "
        "hiring processes. No recruiter, employer or private correspondence is published."
    )

    st.subheader("Recruitment activity")
    rows=jobs.get("weekly") or []
    if rows:
        chart_rows=[{"Week":r["week"],"Stage":stage,
                     "Events":_n(r.get(key))}
                    for r in rows
                    for key,stage in (("applications","Applications"),
                                      ("responses","Inbound / two-way"),
                                      ("interviews","Interviews"))]
        chart=(alt.Chart(alt.Data(values=chart_rows)).mark_line(point=True)
             .encode(x=alt.X("Week:T",title="Week"),
                     y=alt.Y("Events:Q",title="Recorded events",axis=alt.Axis(tickMinStep=1)),
                     color="Stage:N",tooltip=["Week:T","Stage:N","Events:Q"])
             .properties(height=280))
        st.altair_chart(chart,width="stretch")
    st.subheader("External market context")
    if signals:
        for row in signals[:5]:
            name = row.get("indicator_name") or row.get("indicator_key") or "Market signal"
            value = row.get("metric_value")
            description = row.get("insight_summary") or "No interpretation recorded."
            st.markdown(f"**{name}** — {value if value is not None else 'not quantified'}"
                        f" {row.get('metric_unit') or ''}")
            st.caption(str(description)[:280])
    st.caption("Select the Portfolio, Job search and Swedish market sections for detailed evidence.")


def _portfolio_job_relationships(job_report: dict) -> None:
    st.subheader("Portfolio × recruitment correlations")
    st.caption(
        "Automatically recomputed daily associations, not identifiable "
        "recruiter visits or causal evidence. Sparse outcomes are withheld."
    )
    try:
        site_payload = _fetch_rpc("careersite_portfolio_signals_daily_v1",{"p_days":365})
    except (RuntimeError,ValueError,PermissionError):
        st.caption("Portfolio correlation inputs are temporarily unavailable.")
        return
    site,features,coverage = _site_features(site_payload)
    if not site:
        st.info("The available quality-filtered tracking period is too short.")
        return
    jobs={}
    for record in job_report.get("daily") or []:
        try:
            d=date.fromisoformat(str(record["d"]))
            jobs[d] = {key:_n(record.get(key))
                       for key in ("applications","responses","interviews","rejections")}
        except (TypeError,ValueError,KeyError):
            continue

    tests=[_test_one(site,jobs,feature,outcome,lag)
           for feature in features
           for outcome in ("applications","responses","interviews","rejections")
           for lag in LAGS]
    _bh_pvalues(tests)
    for row in tests:
        row["status"] = _classify(row)
    qualified=[r for r in tests
               if r["status"] in ("Repeated association","Worth monitoring")]
    anchors=[r for r in tests
             if (r["feature"],r["outcome"],r["lag"]) in ANCHORS]
    selected = qualified[:6] or anchors
    if not qualified:
        st.info(
            "No association currently meets the evidence threshold. "
            "Early CV-link hypotheses remain under observation."
        )
    if selected:
        st.dataframe([{
            "Portfolio signal": features.get(x["feature"],x["feature"]),
            "Recruitment measure": x["outcome"].replace("_"," ").title(),
            "Timing": LAGS[x["lag"]][2],
            "r": round(x["r"],2) if x["r"] is not None else None,
            "Paired days": x["n"],
            "Evidence": x["status"],
        } for x in selected],hide_index=True,width="stretch")
    st.caption(
        f"Examined {len(tests)} possible pairs across "
        f"{coverage['coverage']} complete portfolio days. "
        "No individual reader, application, recruiter, or employer identity "
        "is involved in this comparison."
    )


@st.fragment(run_every="10m")
def render_public_job_search() -> None:
    st.title("Job Search Analytics")
    st.caption("Aggregate recruitment outcomes without private applicant records or names.")
    period=st.segmented_control(
        "Reporting horizon",[1,7,30,90,180,365,730],default=30,
        format_func=lambda x:"Today" if x==1 else f"{x} days",
        key="public_job_days",
    ) or 30
    try:
        report=_job_summary(int(period))
    except (RuntimeError,ValueError,PermissionError):
        st.warning("Public job-search statistics are temporarily unavailable.")
        return
    totals=report.get("totals") or {}
    a,b,c,d=st.columns(4)
    a.metric("Applications",_n(totals.get("applications")))
    b.metric("Inbound / two-way contacts",_n(totals.get("responses")))
    c.metric("Completed interviews",_n(totals.get("interviews")))
    d.metric("Explicit rejections",_n(totals.get("rejections")))
    st.caption(
        "Recorded primary employer-role events, deduplicated per day. "
        "An application and a subsequent response are separate events; "
        "these totals are not a cohort conversion rate."
    )
    weeks=report.get("weekly") or []
    if weeks:
        points=[{"Week":w["week"],"Event":name,"Count":_n(w.get(key))}
                for w in weeks
                for key,name in (("applications","Applications"),
                                 ("responses","Responses"),
                                 ("interviews","Completed interviews"),
                                 ("rejections","Negative decisions"))]
        plot=alt.Chart(alt.Data(values=points)).mark_line(point=True).encode(
            x=alt.X("Week:T",title=None),
            y=alt.Y("Count:Q",title="Distinct dated process events",
                    axis=alt.Axis(tickMinStep=1)),
            color="Event:N",tooltip=["Week:T","Event:N","Count:Q"]
        ).properties(height=330)
        st.altair_chart(plot,width="stretch")
    _portfolio_job_relationships(report)
    st.divider()
    st.markdown("**Where are the job predictions?**")
    st.caption(
        "The Hiring Predictor is in its own Job predictions section. "
        "Its scenario uses the full dated history, not only the selected 7- or 30-day report."
    )
    if st.button("Open Job predictions",key="public_jobs_open_predictions"):
        st.session_state["careersite_analytics_view"] = "predictions"
        st.query_params["view"] = "predictions"
        st.rerun()
    st.caption(
        "Company names, contacts, follow-up tasks, event notes, imported "
        "documents and detailed evidence downloads remain private."
    )


@st.fragment(run_every="15m")
def render_public_swedish_market() -> None:
    """Full historical market dashboard, not the reduced latest-row table."""
    from page_public_market_restored import render_public_market_restored
    render_public_market_restored()
