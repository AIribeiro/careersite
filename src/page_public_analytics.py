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
    st.caption(
        "Recruitment funnel, timing, trends, portfolio relationships and "
        "Swedish market comparisons—without publishing private employer records."
    )
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
        "Events are deduplicated per dated employer–role process. "
        "These measures belong to different stages and cannot be divided "
        "to infer a valid cohort conversion rate."
    )
    focus=st.segmented_control(
        "Recruitment question",
        options=["activity","conversion","trends","portfolio","market","evidence"],
        default="activity",
        format_func=lambda x:{
            "activity":"Activity",
            "conversion":"Funnel & conversion",
            "trends":"Time trends",
            "portfolio":"Portfolio correlations",
            "market":"Market relationships",
            "evidence":"Data quality & definitions",
        }[x],
        key="public_job_focus",width="stretch",
    ) or "activity"
    st.divider()
    if focus=="activity":
        st.subheader("Dated recruitment activity")
        days=report.get("daily") or []
        if days:
            points=[{"Date":r["d"],"Event":name,"Count":_n(r.get(key))}
                    for r in days
                    for key,name in (("applications","Applications"),
                                     ("responses","Responses"),
                                     ("interviews","Completed interviews"),
                                     ("rejections","Negative decisions"))]
            plot=alt.Chart(alt.Data(values=points)).mark_bar().encode(
                x=alt.X("Date:T",title="Event date"),
                y=alt.Y("Count:Q",title="Recorded events",axis=alt.Axis(tickMinStep=1)),
                color="Event:N",tooltip=["Date:T","Event:N","Count:Q"],
            ).properties(height=290)
            st.altair_chart(plot,width="stretch")
        else:
            st.info("No dated recruitment events have been recorded in this window.")
        st.caption(
            "An empty short window means no recorded event, not a failed application "
            "or an absence of recruiter interest."
        )
    elif focus=="conversion":
        st.subheader("Funnel stages and conversion maturity")
        try:
            stage=fetch_public_analytics_rpc("careersite_public_hiring_inputs_v1")
        except (RuntimeError,ValueError,PermissionError):
            stage={}
        summary=stage.get("summary") or {}
        maturity=_n(summary.get("matured_applications"))
        contact=_n(summary.get("mature_contacts"))
        p,q,z=st.columns(3)
        p.metric("Applications old enough to assess",maturity,
                 help="Applications at least 35 days old, identified from primary records.")
        q.metric("Mature application processes with contact",contact,
                 help="Processes with recorded contact after the application.")
        z.metric("Observed mature cohort contact share",
                 f"{contact/maturity:.0%}" if maturity else "Not enough data",
                 help="Descriptive observed sample, not a forecast or a standardized rate.")
        buckets=stage.get("stage_buckets") or []
        ordered=("application","conversation","interview","progression")
        label={"application":"Application","conversation":"Conversation",
               "interview":"Interview","progression":"Progression"}
        counts={k:sum(_n(b.get("n")) for b in buckets if b.get("stage")==k)
                for k in ordered}
        if any(counts.values()):
            st.altair_chart(
                alt.Chart(alt.Data(values=[{"Stage":label[k],"Processes":counts[k],
                                            "Order":i}
                                           for i,k in enumerate(ordered)]))
                  .mark_bar(cornerRadiusEnd=3)
                  .encode(x=alt.X("Processes:Q",title="Recorded active/reviewable processes",
                                  axis=alt.Axis(tickMinStep=1)),
                          y=alt.Y("Stage:N",sort=[label[k] for k in ordered],title=None),
                          tooltip=["Stage:N","Processes:Q"]).properties(height=240),
                width="stretch",
            )
        else:
            st.info("No supported current-stage distribution available.")
        st.caption(
            "Stage counts represent mutually exclusive latest recorded stages, "
            "not funnel conversions. Some processes are stale or provisionally "
            "active; status is not continuously synchronized with employers."
        )
    elif focus=="trends":
        st.subheader("Weekly activity and directional movement")
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
                y=alt.Y("Count:Q",title="Dated event count",axis=alt.Axis(tickMinStep=1)),
                color="Event:N",tooltip=["Week:T","Event:N","Count:Q"],
            ).properties(height=310)
            st.altair_chart(plot,width="stretch")
        else:
            st.info("No weekly trend observations are available.")
        if int(period)<30:
            st.caption(
                "Short windows do not contain enough comparable weeks to infer "
                "progress. Select 90 or 365 days for a more meaningful trend."
            )
    elif focus=="portfolio":
        # Statistical screening always uses historical outcomes, irrespective
        # of the current activity reporting selector (even Today).
        try:
            history=_job_summary(365)
        except (RuntimeError,ValueError,PermissionError):
            history=report if int(period)>=365 else {"daily":[]}
        _portfolio_job_relationships(history)
    elif focus=="market":
        st.subheader("Market ↔ recruitment relationships")
        try:
            from page_public_market_restored import _load_public_market
            from job_market_correlations import analyze_market
            from page_job_market_insights import _relationship_screen
            market,jobs,portfolio=_load_public_market()
            model=analyze_market(
                market.get("history") or [],[],portfolio,
                datetime.now(ZoneInfo("Europe/Stockholm")).date(),
                public_job_summary=jobs,
            )
            _relationship_screen(model,compact=True)
        except (RuntimeError,ValueError,PermissionError,TypeError,KeyError):
            st.warning("Live market relationships are temporarily unavailable.")
        if st.button("Open full Swedish Market dashboard",key="job_market_link"):
            st.session_state["careersite_analytics_view"]="market"
            st.query_params["view"]="market"
            st.rerun()
    else:
        st.subheader("Evidence quality and privacy")
        st.write(
            "The canonical job-search table is event-based. Event counts use "
            "primary records and deduplicate each employer–role process within "
            "each date. Applications, conversations and interviews are different "
            "events; their headline totals are not a common application cohort."
        )
        st.write(
            "The public dashboard contains no individual employers, recruiter "
            "contacts, case notes, follow-up tasks, source workbooks or employer "
            "links. The detailed process tables, decisions and individualized "
            "predictor remain in the authenticated Admin/CMS owner workspace."
        )
        st.caption(f"Reporting through {report.get('through') or 'the latest available date'} "
                   f"· {report.get('method') or 'deduplicated evidence'}.")

    st.divider()
    st.markdown("**Job predictions**")
    st.caption(
        "The Hiring Predictor is in its own Job predictions section. "
        "It uses historical evidence independently of this reporting window."
    )
    if st.button("Open Job predictions",key="public_jobs_open_predictions"):
        st.session_state["careersite_analytics_view"]="predictions"
        st.query_params["view"]="predictions"
        st.rerun()


@st.fragment(run_every="15m")
def render_public_swedish_market() -> None:
    """Full historical market dashboard, not the reduced latest-row table."""
    from page_public_market_restored import render_public_market_restored
    render_public_market_restored()
