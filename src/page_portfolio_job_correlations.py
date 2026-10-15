"""Private, self-updating portfolio ↔ recruitment correlation view."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from page_content_intelligence import _fetch_rpc
from portfolio_job_correlations import (
    ANCHORS, FEATURES, LAGS, OUTCOMES, _aligned_values, _site_features,
    analyze_portfolio_job_correlations,
)
from site_owner_persistence import persistent_owner_session


def _description(row: dict, model: dict) -> str:
    source = model["features"].get(row["feature"],row["feature"])
    outcome = model["outcomes"].get(row["outcome"],row["outcome"])
    lag = LAGS[row["lag"]][2].lower()
    return f"{source} ↔ {outcome} ({lag})"


def _value(v: float | None) -> str:
    return f"{v:+.2f}" if v is not None else "—"


def _private_signal_readout(row: dict) -> str:
    if row.get("r") is None:
        return "Too few recorded events to interpret."
    if row["status"] == "Repeated association":
        return "A repeated day-level association passed the screening checks, not a causal link."
    if row["status"] == "Worth monitoring":
        return "An emerging association passed initial checks; it needs more validation."
    if row["status"] == "Unstable / weak":
        return "The observed relationship is weak or unstable."
    if abs(row["r"]) < .25:
        return "Little consistent overlap is visible in the current observations."
    direction = "positive" if row["r"] > 0 else "negative"
    return f"Preliminary {direction} same-day overlap; not enough history to validate."


def _trend_dashboard(report: dict) -> None:
    """Display independent trailing-week movements, without visitor attribution."""
    site = report["site_daily"]
    jobs = report["job_daily"]
    if len(site) < 7:
        st.caption("Trend visuals will appear after seven complete recorded days.")
        return
    ordered = sorted(site,key=lambda x:x["Date"])
    points = []
    for i in range(6,len(ordered)):
        window = ordered[i-6:i+1]
        days = [datetime.fromisoformat(r["Date"]).date() for r in window]
        points.append({
            "Date":ordered[i]["Date"],
            "CV-linked sessions":sum(int(r.get("cv_link_visitors",0)) for r in window),
            "Applications":sum(jobs.get(d,{}).get("applications",0) for d in days),
            "Recruitment contacts":sum(jobs.get(d,{}).get("responses",0) for d in days),
        })
    points = points[-90:]
    st.markdown("**How CV attention and recruitment activity are moving**")
    left,right = st.columns(2)
    with left:
        st.caption("CV-linked portfolio sessions")
        chart = alt.Chart(alt.Data(values=points)).mark_line(
            point=True,strokeWidth=2,
        ).encode(
            x=alt.X("Date:T",title="Day"),
            y=alt.Y("CV-linked sessions:Q",title="Sessions · trailing 7 days",
                    scale=alt.Scale(zero=True)),
            tooltip=["Date:T","CV-linked sessions:Q"],
        ).properties(height=240)
        st.altair_chart(chart,width="stretch")
    with right:
        st.caption("Applications and inbound recruitment contacts")
        chart = alt.Chart(alt.Data(values=points)).transform_fold(
            ["Applications","Recruitment contacts"],as_=["Event","Count"],
        ).mark_line(point=True,strokeWidth=2).encode(
            x=alt.X("Date:T",title="Day"),
            y=alt.Y("Count:Q",title="Events · trailing 7 days",
                    scale=alt.Scale(zero=True)),
            color=alt.Color("Event:N",title="Recruitment event"),
            tooltip=["Date:T","Event:N","Count:Q"],
        ).properties(height=240)
        st.altair_chart(chart,width="stretch")
    st.caption(
        "Trailing seven-day totals on independent axes. Similar movement does "
        "not connect a portfolio session to an employer, recruiter or decision."
    )
    if len(points) >= 8:
        current,prior = points[-1],points[-8]
        def movement(name: str) -> str:
            now,old = current[name],prior[name]
            return "increased" if now>old else "decreased" if now<old else "was unchanged"
        st.markdown(
            "**Recent movement:** CV-linked sessions "
            f"{movement('CV-linked sessions')}; inbound recruitment contacts "
            f"{movement('Recruitment contacts')} versus the preceding seven days. "
            "This is descriptive activity, not a conversion rate."
        )


def _anchor_cards(report: dict) -> None:
    st.markdown("**What the two CV-link hypotheses suggest**")
    pairs = {row["outcome"]:row for row in report["anchors"]}
    left,right = st.columns(2)
    with left:
        st.markdown("**Recruitment conversations**")
        row = pairs.get("responses")
        st.write(_private_signal_readout(row) if row else "No comparable events available.")
    with right:
        st.markdown("**Applications submitted**")
        row = pairs.get("applications")
        st.write(_private_signal_readout(row) if row else "No comparable events available.")
    if report["coverage"]["coverage"] < 42:
        st.caption(
            f"{report['coverage']['coverage']} complete days available; the statistical "
            "screen requires at least 42, and a repeated association needs a longer "
            "history plus sufficient independent events."
        )
        st.markdown(
            "**Next step:** Continue collecting qualified sessions and dated employer "
            "contacts. Do not change portfolio strategy based on these coefficients."
        )
    elif report["top_status"] is None:
        st.markdown(
            "**Next step:** Track verified hiring conversations rather than "
            "interpreting raw traffic as progress."
        )
    else:
        st.markdown(
            "**Next step:** Check whether qualifying patterns remain stable over "
            "time before drawing a practical conclusion."
        )

def _ranking(report: dict) -> None:
    st.subheader("Automatically discovered relationships")
    established = [r for r in report["ranked"] if r["status"]=="Repeated association"]
    watch = [r for r in report["ranked"] if r["status"]=="Worth monitoring"]
    if established:
        st.markdown(f"**{len(established)} repeated association(s) pass the conservative screening rules.** These are not causal claims.")
    elif watch:
        st.info(f"{len(watch)} pattern(s) merit monitoring. None yet satisfies the repeated-association criteria.")
    else:
        st.info(
            "No cross-dataset correlation currently meets the evidence threshold. "
            "The system keeps evaluating the hypotheses and will show new candidates as the observation window grows."
        )
    if not established and not watch:
        st.caption("Until at least 42 complete daily observations are available, strong-sounding correlations are deliberately withheld.")

    show = established + watch
    if show:
        rows = []
        for item in show[:12]:
            rows.append({
                "Portfolio behavior":report["features"][item["feature"]],
                "Job-search event":report["outcomes"][item["outcome"]],
                "Timing":LAGS[item["lag"]][2],
                "Pearson r":round(item["r"],2),
                "Rank r":round(item["rho"],2) if item["rho"] is not None else None,
                "Adjusted q*":item["q"],
                "Paired days":item["n"],
                "Classification":item["status"],
            })
        st.dataframe(rows,hide_index=True,width="stretch")
        st.caption("*Multiple-testing correction is a statistical screening aid; time dependence, shared market conditions, weekday patterns and incomplete provenance limit inference.")
    if report["discovered"]:
        examples = report["discovered"][:5]
        st.markdown("**Emerging page or referral-source signals:** " +
                    "; ".join(_description(x,report) for x in examples) + ".")
    st.caption(
        f"{len(report['features'])} qualified source/page/behavior measures × "
        f"{len(OUTCOMES)} job-search outcomes × {len(LAGS)} timing windows = "
        f"{report['total_tests']} candidate comparisons; {report['tested']} had sufficient "
        "coverage for the statistical screen. Sparse and constant series are not ranked."
    )


def _movement(report: dict, source: dict) -> None:
    st.subheader("Are the relationships changing?")
    if report["coverage"]["coverage"] < 56:
        st.caption("This comparison will activate once 56+ complete daily observations are available.")
        return
    from portfolio_job_correlations import _test_one
    descriptions = report["anchors"][:]
    descriptions.extend([x for x in report["ranked"] if x["status"] in ("Repeated association","Worth monitoring")
                         and (x["feature"],x["outcome"],x["lag"]) not in ANCHORS][:3])
    site, _, _ = _site_features(source)
    data = []
    for candidate in descriptions:
        from_date = report["coverage"]["end"]
        previous_site = {d:v for d,v in site.items() if d <= from_date - __import__("datetime").timedelta(days=28)}
        if len(previous_site) < 28:
            continue
        recent = _test_one(site,report["job_daily"],candidate["feature"],candidate["outcome"],candidate["lag"],window=28)
        older = _test_one(previous_site,report["job_daily"],candidate["feature"],candidate["outcome"],candidate["lag"],window=28)
        if (recent["r"] is not None and older["r"] is not None and recent["outcome_days"]>=3 and older["outcome_days"]>=3):
            diff = recent["r"]-older["r"]
            data.append({
                "Relationship":_description(candidate,report),
                "Prior 28d r":round(older["r"],2),
                "Latest 28d r":round(recent["r"],2),
                "Movement":round(diff,2),
                "Interpretation": "Direction changed" if recent["r"] * older["r"] < 0 else
                    "Stronger" if abs(recent["r"]) > abs(older["r"]) else "Weaker / stable"
            })
    if data:
        st.dataframe(data,hide_index=True,width="stretch")
        st.caption("The two 28-day comparisons are descriptive, not independently validated. A change in source tagging or newly imported job history can alter coefficients.")
    else:
        st.caption("Recent or earlier 28-day windows do not yet contain enough recorded events to compare reliably.")


def _scatter(report: dict, site_payload: dict) -> None:
    candidates = report["anchors"] + [r for r in report["ranked"]
                                      if r["status"] in ("Repeated association","Worth monitoring")
                                      and (r["feature"],r["outcome"],r["lag"]) not in ANCHORS][:5]
    if not candidates:
        return
    choices = {_description(r,report):r for r in candidates}
    st.subheader("Inspect the daily evidence")
    selected = st.selectbox("Relationship",list(choices),key="job_portfolio_corr_inspection")
    candidate = choices[selected]
    site,_,_ = _site_features(site_payload)
    dates,x,y = _aligned_values(site,report["job_daily"],candidate["feature"],
                                candidate["outcome"],LAGS[candidate["lag"]])
    points = [{"Date":d.isoformat(),"Portfolio":xi,"Job events":yi} for d,xi,yi in zip(dates,x,y)]
    if points:
        plot = alt.Chart(alt.Data(values=points)).mark_circle(size=75,opacity=.72).encode(
            x=alt.X("Portfolio:Q",title=report["features"][candidate["feature"]],axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Job events:Q",title=report["outcomes"][candidate["outcome"]],axis=alt.Axis(tickMinStep=1)),
            tooltip=["Date:T","Portfolio:Q","Job events:Q"],
        ).properties(height=310)
        st.altair_chart(plot,width="stretch")
    st.caption("Each point is one calendar day (or its preceding exposure window). Days with no matching event are true observed zeroes; incomplete first and current days are excluded.")


@st.fragment(run_every="15m")
def render_portfolio_job_correlations() -> None:
    """Refresh both private datasets while the owner keeps this dashboard open."""
    st.subheader("Portfolio attention and recruitment progress")
    st.caption(
        "Visual comparisons of qualified portfolio attention and recorded recruitment "
        "outcomes. Aggregate timing patterns are not recruiter attribution."
    )
    try:
        session = persistent_owner_session()
        if not session or not session.get("access_token"):
            st.warning("Portfolio owner sign-in is required.")
            return
        st.session_state["cms_auth"] = session
        site = _fetch_rpc("careersite_portfolio_signals_daily_v1",{"p_days":365})
        # Import locally to avoid coupling the metrics layer to the dashboard UI.
        from page_job_search_analytics import fetch_job_records
        jobs = fetch_job_records(str(st.session_state["cms_auth"]["access_token"]))
        report = analyze_portfolio_job_correlations(site,jobs)
    except (RuntimeError,PermissionError,ValueError,TimeoutError):
        st.warning("Cross-dataset analysis could not be refreshed. Other Job Search Analytics reports remain available.")
        return
    if report["notice"]:
        st.info(report["notice"])
        return
    detail = report["coverage"]
    st.caption(
        f"Last checked {datetime.now(ZoneInfo('Europe/Stockholm')):%d %b %Y, %H:%M} (Stockholm) · "
        f"{detail['coverage']} complete days · {detail['first']:%d %b %Y}–{detail['end']:%d %b %Y}. "
        "Refreshes every 15 minutes while this dashboard is open. Current day is excluded."
    )
    if report["top_status"] is None:
        st.info(
            "No confirmed portfolio-to-recruitment relationship yet. "
            "The engine is monitoring early patterns but will not present them as hiring impact."
        )
    _trend_dashboard(report)
    _anchor_cards(report)
    with st.expander("Evidence & diagnostics · candidate relationships and raw calculations"):
        _ranking(report)
        _movement(report,site)
        _scatter(report,site)
    with st.expander("Methodology, evidence limits and automatic discovery"):
        st.markdown(
            "Daily sessions are quality-filtered using V5 tracking, explicit test exclusions and the "
            "portfolio's suspected-automation screen. The first partial rollout day and current incomplete "
            "day are omitted. Job events use only deduplicated primary evidence, dated to the event and "
            "counted once per employer/role/day. Undated material and official snapshots are excluded.\n\n"
            "Each signal is tested against five recorded recruitment outcomes at three timings (same day, "
            "previous 1–3 days, and previous 4–7 days). Newly visited pages and tagged sources join "
            "the analysis only after at least 15 sessions across four dates. "
            "Candidates must pass exposure and outcome coverage, Pearson/Spearman agreement, a weekday "
            "and dominant-day sensitivity check, and Benjamini–Hochberg screening. Longer histories must "
            "show similar direction in both halves before being called *repeated*. Testing many signals "
            "can create accidental correlations and the p/q screens assume more day-to-day independence "
            "than may exist; labels are descriptive and cannot establish causality. "
            "A higher correlation is not proof that a specific recruiter visited the portfolio.\n\n"
            "The automatic process updates calculations, discovers qualifying categories, and revises "
            "or demotes previous patterns as evidence changes. It does not retrain a model, infer identities, "
            "alter the source data, or automatically change the portfolio."
        )
    if st.button("Recalculate now",key="job_portfolio_corr_reload"):
        st.rerun(scope="fragment")
