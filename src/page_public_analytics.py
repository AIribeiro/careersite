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
from site_analytics_public import fetch_public_analytics_rpc, fetch_public_hiring_timing_v2
from page_public_overview_dashboard import render_public_overview_dashboard
from public_rejection_insights import rejection_overview_readout


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


def _navigate_public_analytics(view: str) -> None:
    if view not in ("portfolio","jobs","predictions","market"):
        return
    st.session_state["careersite_analytics_view"]=view
    st.query_params["view"]=view
    st.rerun()


@st.fragment(run_every="10m")
def render_public_analytics_overview() -> None:
    """Public, decision-first visual overview of read-only evidence."""
    now = datetime.now(ZoneInfo("Europe/Stockholm"))
    results = {}
    unavailable = []
    sources = {
        "hiring": lambda: _fetch_hiring_intelligence("30d"),
        "jobs": lambda: _job_summary(365),
        "market": _market_summary,
        "conversion": lambda: fetch_public_analytics_rpc(
            "careersite_public_conversion_quality_v1"),
        "rejections": lambda: fetch_public_analytics_rpc(
            "careersite_public_rejection_summary_v1"),
        "pipeline": lambda: fetch_public_analytics_rpc(
            "careersite_public_pipeline_health_v1"),
        "timing": fetch_public_hiring_timing_v2,
    }
    for name, loader in sources.items():
        try:
            results[name] = loader()
        except (RuntimeError, ValueError, PermissionError, TimeoutError, KeyError):
            unavailable.append(name)
    render_public_overview_dashboard(
        results, now, unavailable, _navigate_public_analytics
    )


def _portfolio_recruitment_trends(site: dict, jobs: dict) -> list[dict]:
    """Seven-day trailing event counts on complete, quality-filtered days only."""
    dates = sorted(site)
    if len(dates) < 7:
        return []
    series = []
    for end in range(6, len(dates)):
        period = dates[end-6:end+1]
        series.append({
            "Date": dates[end].isoformat(),
            "CV-linked sessions": sum(site[d].get("cv_link_visitors", 0) for d in period),
            "Applications": sum(jobs.get(d, {}).get("applications", 0) for d in period),
            "Recruitment contacts": sum(jobs.get(d, {}).get("responses", 0) for d in period),
        })
    return series[-90:]


def _portfolio_signal_explanation(row: dict | None) -> str:
    """Give a calibrated interpretation, never a recruiter or causal attribution."""
    if not row or row.get("r") is None:
        return "There are too few distinct recorded events to interpret this relationship."
    status = row["status"]
    if status == "Repeated association":
        return ("A repeated aggregate pattern passes the evidence checks. "
                "This is not proof of hiring impact.")
    if status == "Worth monitoring":
        return ("A directional pattern passed initial checks, but repetition "
                "and stronger evidence are still needed.")
    if status == "Unstable / weak":
        return "The pattern is too weak or unstable to support a recruitment conclusion."
    r = row["r"]
    if abs(r) < .25:
        return "Little consistent same-day overlap is visible in the early observations."
    if r > 0:
        return ("Some positive same-day overlap is visible. The sample is too short "
                "to determine whether it persists.")
    return ("Some negative same-day overlap is visible. The sample is too short "
            "to determine whether it persists.")


def _movement_label(latest: int, previous: int) -> str:
    if latest > previous:
        return "increased"
    if latest < previous:
        return "decreased"
    return "was unchanged"


def _portfolio_job_relationships(job_report: dict) -> None:
    st.subheader("Does portfolio attention accompany recruitment progress?")
    st.caption(
        "Compare quality-filtered CV activity with dated recruitment events. "
        "This is an aggregate timing comparison, not recruiter identification "
        "or evidence that portfolio visits caused hiring responses."
    )
    try:
        site_payload = _fetch_rpc("careersite_portfolio_signals_daily_v1", {"p_days":365})
    except (RuntimeError,ValueError,PermissionError,TimeoutError):
        st.caption("Portfolio relationship inputs are temporarily unavailable.")
        return
    site,features,coverage = _site_features(site_payload)
    if not site:
        st.info("Not enough complete, quality-filtered tracking days to display a trend.")
        return
    jobs = {}
    for record in job_report.get("daily") or []:
        try:
            d = date.fromisoformat(str(record["d"]))
            jobs[d] = {key:_n(record.get(key))
                       for key in ("applications","responses","interviews","rejections")}
        except (TypeError,ValueError,KeyError):
            continue

    tests = [_test_one(site,jobs,feature,outcome,lag)
             for feature in features
             for outcome in ("applications","responses","interviews","rejections")
             for lag in LAGS]
    _bh_pvalues(tests)
    for row in tests:
        row["status"] = _classify(row)
    qualified = [r for r in tests
                 if r["status"] in ("Repeated association","Worth monitoring")]
    anchors = {(r["feature"],r["outcome"],r["lag"]):r for r in tests
               if (r["feature"],r["outcome"],r["lag"]) in ANCHORS}
    response_signal = anchors.get(("cv_link_visitors","responses","same_day"))
    application_signal = anchors.get(("cv_link_visitors","applications","same_day"))
    enough_days = coverage["coverage"] >= 42

    if qualified:
        st.markdown(
            "**Assessment: relationships worth examining, not confirmed hiring impact.** "
            "Some aggregate timing patterns pass the screening checks. They cannot "
            "identify who visited the portfolio or explain an employer's decision."
        )
    elif not enough_days:
        st.markdown(
            "**Assessment: too early to establish a recruitment relationship.** "
            "The observation period is short. The charts show activity, "
            "but any apparent overlap remains a hypothesis."
        )
    else:
        st.markdown(
            "**Assessment: no reliable relationship currently identified.** "
            "Portfolio activity and recruitment outcomes have not passed the "
            "conservative association checks."
        )

    trends = _portfolio_recruitment_trends(site,jobs)
    if trends:
        st.markdown("**How the two activity streams are moving**")
        left,right = st.columns(2)
        with left:
            st.caption("CV-linked portfolio sessions")
            cv_chart = alt.Chart(alt.Data(values=trends)).mark_line(
                point=True,strokeWidth=2,
            ).encode(
                x=alt.X("Date:T",title="Day"),
                y=alt.Y("CV-linked sessions:Q",title="Sessions · trailing 7 days",
                        scale=alt.Scale(zero=True)),
                tooltip=[alt.Tooltip("Date:T",title="Week ending"),
                         alt.Tooltip("CV-linked sessions:Q",title="Sessions")],
            ).properties(height=240)
            st.altair_chart(cv_chart,width="stretch")
        with right:
            st.caption("Applications and incoming recruitment contacts")
            contact_chart = alt.Chart(alt.Data(values=trends)).transform_fold(
                ["Applications","Recruitment contacts"],as_=["Event","Count"],
            ).mark_line(point=True,strokeWidth=2).encode(
                x=alt.X("Date:T",title="Day"),
                y=alt.Y("Count:Q",title="Events · trailing 7 days",
                        scale=alt.Scale(zero=True)),
                color=alt.Color("Event:N",title="Recruitment event"),
                tooltip=[alt.Tooltip("Date:T",title="Week ending"),
                         alt.Tooltip("Event:N"),
                         alt.Tooltip("Count:Q",title="Events")],
            ).properties(height=240)
            st.altair_chart(contact_chart,width="stretch")
        st.caption(
            "Independent vertical scales; both charts use seven-day trailing totals. "
            "Similar movement is not evidence that the same people or employers "
            "generated both activities."
        )
        if len(trends) >= 8:
            current,prior = trends[-1],trends[-8]
            st.markdown(
                "**Recent direction:** CV-linked sessions "
                f"{_movement_label(current['CV-linked sessions'],prior['CV-linked sessions'])}; "
                "inbound/two-way recruitment contacts "
                f"{_movement_label(current['Recruitment contacts'],prior['Recruitment contacts'])} "
                "versus the preceding seven-day period. "
                "These are separate activity measures, not a conversion funnel."
            )
    else:
        st.caption("Trend charts will appear after seven complete tracking days.")

    st.markdown("**What the initial signals suggest**")
    left,right = st.columns(2)
    with left:
        st.markdown("**Recruitment conversations**")
        st.write(_portfolio_signal_explanation(response_signal))
    with right:
        st.markdown("**Applications submitted**")
        st.write(_portfolio_signal_explanation(application_signal))
    if not enough_days:
        st.caption(
            f"Evidence maturity: {coverage['coverage']} complete tracking days so far. "
            "At least 42 are required before the statistical screen activates; "
            "longer history and enough independent events are still required."
        )
        st.markdown(
            "**Next step:** Continue consistent CV-link and referral tracking, "
            "then reassess the pattern as more complete days and employer events accrue."
        )
    elif not qualified:
        st.markdown(
            "**Next step:** Keep tracking qualified portfolio attention and genuine "
            "employer responses. Do not treat higher traffic alone as hiring progress."
        )
    else:
        st.markdown(
            "**Next step:** Review the direction and stability of the emerging patterns "
            "before changing any job-search or portfolio activity."
        )

    with st.expander("Evidence & methodology · coefficients, coverage and screening"):
        selected = qualified[:6] or [row for row in (response_signal,application_signal)
                                      if row is not None]
        if selected:
            st.dataframe([{
                "Portfolio signal": features.get(x["feature"],x["feature"]),
                "Recruitment measure": x["outcome"].replace("_"," ").title(),
                "Timing": LAGS[x["lag"]][2],
                "Pearson r": round(x["r"],2) if x["r"] is not None else None,
                "Paired days": x["n"],
                "Assessment": x["status"],
            } for x in selected],hide_index=True,width="stretch")
        st.caption(
            f"{len(tests)} feature/outcome/timing comparisons were evaluated across "
            f"{coverage['coverage']} complete portfolio days. "
            "The screen applies minimum coverage, rank agreement, sensitivity checks "
            "and multiple-testing correction. Sparse results are not validated. "
            "No identifiable reader, recruiter, employer or application is joined "
            "to a portfolio visit; same-day correlation cannot establish causation."
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
    st.caption(
        "Start with evidence-linked cohort conversion. The reporting horizon below "
        "applies to dated activity only; conversion always uses original dated "
        "applications since 1 June 2026, not a mismatched event window."
    )
    focus=st.segmented_control(
        "Recruitment question",
        options=["activity","pipeline","conversion","trends","portfolio","market","evidence"],
        default="conversion",
        format_func=lambda x:{
            "activity":"Activity",
            "pipeline":"Pipeline Health",
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
    elif focus=="pipeline":
        try:
            health=fetch_public_analytics_rpc("careersite_public_pipeline_health_v1")
        except (RuntimeError,ValueError,PermissionError):
            health={}
        from page_stale_applications import render_pipeline_health
        render_pipeline_health(health)
    elif focus=="conversion":
        from page_conversion_quality import render_public_conversion_quality
        render_public_conversion_quality()
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
