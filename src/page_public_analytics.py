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
    st.title("Analytics overview")
    st.caption(
        "Decision overview · recruitment progress, portfolio attention, "
        "hiring predictions and Swedish labour-market evidence in one place."
    )
    now=datetime.now(ZoneInfo("Europe/Stockholm"))
    results={}
    unavailable=[]
    sources={
        "hiring":lambda:_fetch_hiring_intelligence("30d"),
        "jobs":lambda:_job_summary(365),
        "market":_market_summary,
        "forecast":lambda:fetch_public_analytics_rpc("careersite_public_hiring_inputs_v1"),
        "rejections":lambda:fetch_public_analytics_rpc("careersite_public_rejection_summary_v1"),
    }
    for name,loader in sources.items():
        try:
            results[name]=loader()
        except (RuntimeError,ValueError,PermissionError,TimeoutError):
            unavailable.append(name)
    st.caption(
        f"Checked {now:%d %b %Y, %H:%M} Stockholm · "
        "automatic read-only refresh every 10 minutes while this view is open."
    )
    if unavailable:
        st.warning(
            "Some evidence is temporarily unavailable: "+
            ", ".join(unavailable)+". The remaining sections stay usable."
        )
    hiring=results.get("hiring") or {}
    jobs=results.get("jobs") or {}
    market=results.get("market") or {}
    overview=(jobs.get("totals") or {})
    quality=(hiring.get("quality_summary") or {})
    from job_search_outlook import render_search_outlook
    render_search_outlook(results.get("jobs"), results.get("forecast"), now.date())
    metrics=st.columns(4)
    metrics[0].metric("Qualified portfolio sessions · 30d",
                      _n(quality.get("analysis_eligible_sessions")))
    metrics[1].metric("Applications · dated history",_n(overview.get("applications")))
    metrics[2].metric("Employer conversations · dated history",_n(overview.get("responses")))
    metrics[3].metric("Completed interviews · dated history",_n(overview.get("interviews")))
    st.caption(
        "Job counts are distinct dated process events, not a cohort funnel "
        "or offer probabilities. Session totals do not identify people."
    )

    st.divider()
    st.subheader("Hiring predictor")
    forecast=results.get("forecast")
    if forecast:
        try:
            from public_hiring_forecast import forecast_public_hiring
            from page_public_predictions import _week
            # Overview omits optional data sources rather than silently
            # inventing an employer interaction or a market signal.
            projection=forecast_public_hiring(
                forecast,None,market.get("signals") or [],
            )
            if projection["status"]=="scenario":
                offer=(projection.get("windows",{}).get("offers") or [None])[0]
                start=(projection.get("windows",{}).get("starts") or [None])[0]
                a,b=st.columns(2)
                a.metric("Leading offer week",_week(offer))
                b.metric("Leading potential start week",_week(start))
                st.caption(
                    "These dates are scenario planning periods, not guaranteed "
                    "interviews, offers or employment starts."
                )
            else:
                st.info("A prediction is not presently supported by the recorded evidence.")
        except (ValueError,TypeError,KeyError,RuntimeError):
            st.warning("The hiring scenario could not be recalculated.")
    else:
        st.info("Hiring scenario inputs are temporarily unavailable.")
    if st.button("Explore Job predictions",key="public_overview_predictions"):
        _navigate_public_analytics("predictions")

    st.divider()
    st.subheader("Where your search stands")
    if jobs:
        dated=[]
        for row in jobs.get("daily") or []:
            try:
                d=date.fromisoformat(str(row["d"]))
            except (KeyError,ValueError,TypeError):
                continue
            if d<=now.date():
                dated.append((d,row))
        recent=[r for d,r in dated if 0 <=(now.date()-d).days <28]
        prior=[r for d,r in dated if 28 <=(now.date()-d).days <56]
        a,b,c=st.columns(3)
        for column,key,label in (
            (a,"applications","Applications · last 28 days"),
            (b,"responses","Responses · last 28 days"),
            (c,"interviews","Interviews · last 28 days"),
        ):
            new=sum(_n(x.get(key)) for x in recent)
            old=sum(_n(x.get(key)) for x in prior)
            column.metric(label,new,delta=f"{new-old:+d} vs prior 28d",
                          delta_color="off")
        if sum(_n(x.get("applications")) for x in recent) > sum(
            _n(x.get("applications")) for x in prior
        ) and sum(_n(x.get("responses")) for x in recent) <= sum(
            _n(x.get("responses")) for x in prior
        ):
            st.info(
                "Recorded applications increased without an accompanying rise "
                "in inbound or two-way contacts. Review targeting and response "
                "latency rather than assuming greater volume means progress."
            )
        st.caption(
            "Dated recruitment events reflect recorded evidence, not live "
            "employer ATS statuses. Individual follow-ups remain private."
        )
    else:
        st.caption("Public recruitment summary is temporarily unavailable.")
    if st.button("Explore recruitment funnel and trends",key="public_overview_jobs"):
        _navigate_public_analytics("jobs")

    st.divider()
    st.subheader("Rejection intelligence")
    st.caption("What negative decisions explain, what remains unknown, and what to do next.")
    rejection_report=results.get("rejections") or {}
    rejection_readout=rejection_overview_readout(rejection_report)
    if rejection_readout["status"]=="ok":
        total=rejection_readout["total"]
        unknown=_n(rejection_report.get("unknown_causes"))
        confirmed=_n(rejection_report.get("confirmed_explanations"))
        recent=rejection_report.get("recent_decisions_30d")
        cols=st.columns(3)
        cols[0].metric(
            "Employer decisions · last 30d",
            str(recent) if recent is not None else "—",
            help="Dated negative hiring decisions per canonical process. Suppressed when fewer than 10; not an application rejection rate.",
        )
        cols[1].metric(
            "Cause remains unknown",
            f"{rejection_readout['unknown_share']:.1%}",
            help=f"{unknown} of {total} distinct negative hiring processes. Unknown is not evidence of a candidate skill gap.",
        )
        cols[2].metric(
            "Confirmed explanations",
            f"{confirmed} / {total}",
            help="Confidence in the recorded explanation, not an employer offer probability. May include a confirmed relative candidate comparison.",
        )
        # Separate observation volume from a real rejection rate. A matched
        # application/decision pair is a documented minimum, not cohort closure.
        reason_count=rejection_report.get("comparative_selection_count")
        cohort_pct=rejection_readout.get("cohort_minimum_pct")
        stage_cols=st.columns(3)
        stage_cols[0].metric(
            "Leading explained pattern",
            f"Comparative selection · {reason_count}" if reason_count is not None else "Unverified",
            help="Employers selected other candidates; no recurring capability gap is established by these messages.",
        )
        stage_cols[1].metric(
            "Minimum linked rejection share",
            f"{cohort_pct:.1f}%" if cohort_pct is not None else "—",
            help="Only exact employer-and-role matches between dated applications and negative decisions since June 2026. Lower bound for the matched tracked cohort; not a final rejection rate.",
        )
        stage_cols[2].metric(
            "Application pairs assessed",
            str(rejection_readout.get("cohort_applications") or "—"),
            help="Unique employer-and-role groups with dated application evidence since 1 June 2026; grouping can combine distinct requisitions.",
        )
        if cohort_pct is not None:
            st.caption(
                f"**Rate interpretation:** {rejection_readout['cohort_matched_negative']} of "
                f"{rejection_readout['cohort_applications']} tracked application pairs have a "
                "matching negative decision. This is a **documented minimum**, not your "
                "overall rejection rate: missing application links, repeat requisitions and "
                "recent unresolved applications prevent a complete denominator."
            )
        previous=rejection_readout.get("previous_decisions_30d")
        if previous is not None and recent is not None:
            st.markdown("**Decision-volume trend · two adjacent 30-day periods**")
            volume=[
                {"Period":"Previous 30 days","Decisions":_n(previous)},
                {"Period":"Latest 30 days","Decisions":_n(recent)},
            ]
            st.altair_chart(
                alt.Chart(alt.Data(values=volume)).mark_bar(cornerRadiusEnd=6).encode(
                    x=alt.X("Period:N",sort=["Previous 30 days","Latest 30 days"],title=None),
                    y=alt.Y("Decisions:Q",title="Recorded negative decisions",axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip("Period:N"),alt.Tooltip("Decisions:Q",format=",d")],
                ).properties(height=155), width="stretch"
            )
            st.caption("Counts reflect both recruitment activity and evidence coverage. Rising decision volume does not, by itself, mean a rising rejection rate.")
        if rejection_readout.get("comparison_readout"):
            st.caption(rejection_readout["comparison_readout"])
        st.markdown(f"**{rejection_readout['evidence_status']}** — {rejection_readout['interpretation']}")
        st.markdown(f"**Evidence-based next move:** {rejection_readout['action']}")
        if rejection_readout["cautions"]:
            st.caption("Evidence gaps: "+" · ".join(rejection_readout["cautions"])+".")
        st.caption(
            "Employer decision date, not the date an email was analyzed. "
            "These counts cannot be divided by applications from a different cohort. "
            "Detailed reasons and correspondence remain in owner-only Admin → Rejection Analytics."
        )
    elif rejection_report:
        st.caption(rejection_readout["message"])
    else:
        st.caption("The aggregate rejection signal is temporarily unavailable; private records are never loaded by public Analytics.")

    st.divider()
    st.subheader("Portfolio contribution")
    if hiring:
        verified=_n(quality.get("evidence_verified_sessions"))
        qualified=_n(quality.get("analysis_eligible_sessions"))
        intent=_n(quality.get("hiring_intent_sessions"))
        a,b,c=st.columns(3)
        a.metric("Qualified visitor sessions",qualified)
        b.metric("Evidence-verified sessions",verified,
                 f"{verified/qualified:.0%} of qualified" if qualified else None,
                 delta_color="off")
        c.metric("Hiring-intent session signals",intent,
                 f"{intent/qualified:.0%} of qualified" if qualified else None,
                 delta_color="off")
        st.caption(
            "Portfolio behavior indicates attention, not a confirmed employer "
            "or recruiter identity. Hiring intent is an on-site event proxy."
        )
    else:
        st.caption("Portfolio behavior metrics are temporarily unavailable.")
    if st.button("Explore portfolio performance",key="public_overview_portfolio"):
        _navigate_public_analytics("portfolio")

    st.divider()
    st.subheader("What the Swedish market is telling you")
    signals=market.get("signals") or []
    if signals:
        from page_job_market_insights import _latest_by_indicator, _readouts, _format_value
        latest=_latest_by_indicator(signals)
        highlights=[latest[x] for x in (
            "employment_outlook_net_vgr",
            "employment_outlook_it_tech",
            "employment_outlook_services_consulting",
        ) if x in latest]
        if highlights:
            columns=st.columns(min(3,len(highlights)))
            for col,entry in zip(columns,highlights):
                col.metric(entry.get("indicator_name") or "Employment outlook",
                           _format_value(entry),
                           help=f"Published source observation: {entry.get('observation_date')}. "
                                "Survey outlook is not a personal probability.")
        for label,statement in _readouts(latest)[:2]:
            st.markdown(f"**{label}** — {statement}")
        if not highlights:
            st.caption(
                "Latest market observations are available, but there are no "
                "matching regional outlook snapshots in this release."
            )
    else:
        st.caption("External market observations are temporarily unavailable.")
    if st.button("Explore complete Swedish market history",key="public_overview_market"):
        _navigate_public_analytics("market")
    st.caption(
        "No causal relationship between anonymous visits and recruitment "
        "outcomes is assumed. Detailed job processes remain private."
    )


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
