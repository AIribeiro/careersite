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
from site_cms import ensure_owner_session


def _description(row: dict, model: dict) -> str:
    source = model["features"].get(row["feature"],row["feature"])
    outcome = model["outcomes"].get(row["outcome"],row["outcome"])
    lag = LAGS[row["lag"]][2].lower()
    return f"{source} ↔ {outcome} ({lag})"


def _value(v: float | None) -> str:
    return f"{v:+.2f}" if v is not None else "—"


def _anchor_cards(report: dict) -> None:
    st.subheader("Two hypotheses under continuous review")
    st.caption("These were observed in October 2026. Their values are recomputed on every update; no relationship is presumed to persist.")
    cols = st.columns(2)
    for col, row in zip(cols, report["anchors"]):
        with col:
            st.metric(_description(row,report), _value(row["r"]), help="Pearson r on independent, complete daily observations. Not a measure of causal impact.")
            st.caption(
                f"{row['status']} · {row['n']} complete paired days · "
                f"{row['exposure_days']} exposure days · {row['outcome_days']} outcome days"
            )
    st.caption("An observed correlation is a population-level timing pattern. A visitor cannot be linked to an application, employer or recruiter.")


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
    st.subheader("Portfolio × Job Search Intelligence")
    st.caption(
        "Automatic review of changing traffic, reading patterns and recruitment activity. "
        "New page and referral-source signals enter the screening pool once sufficiently observed."
    )
    try:
        session = ensure_owner_session(st.session_state.get("cms_auth"))
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
    _anchor_cards(report)
    st.divider()
    _ranking(report)
    st.divider()
    _movement(report,site)
    st.divider()
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
