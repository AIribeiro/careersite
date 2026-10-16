"""Decision-first, privacy-preserving public Analytics Overview.

Keep the top level visual and evidence-led; detailed definitions live in
collapsed expanders. Never fetch the private owner prediction or process rows.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import altair as alt
import streamlit as st

from page_public_predictions import _display_date, render_date_tile
from public_rejection_insights import rejection_overview_readout


def _count(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (ValueError, TypeError):
        return 0


def _number(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def conversion_insight(report: dict) -> dict:
    """Rate only from a matched verified-date application cohort."""
    if not report.get("available"):
        return {"available": False}
    totals = report.get("totals") or {}
    applied = _number(totals.get("applications"))
    human = _number(totals.get("human_responses"))
    if applied is None or applied < 1 or human is None or not 0 <= human <= applied:
        return {"available": False}
    return {
        "available": True,
        "applications": int(applied),
        "human": int(human),
        "no_documented_human": int(applied - human),
        "observed_pct": round(100 * human / applied, 1),
        "interpretation": (
            "Documented human engagement is limited relative to dated applications."
            if human / applied < .10
            else "Human engagement is recorded; track subsequent interview progression."
        ),
    }


def pipeline_insight(report: dict) -> dict:
    """Keep ageing/no-decision and employer closure distinct."""
    metrics = report.get("metrics") or {}
    statuses = {
        str(row.get("segment")): _count(row.get("n"))
        for row in report.get("status") or [] if isinstance(row, dict)
    }
    if not statuses:
        return {"available": False}
    segments = [
        ("Engaged", statuses.get("recruiter_engaged", 0)),
        ("Recent / awaiting", statuses.get("recent_awaiting_response", 0)),
        ("Ageing / unknown decision",
         sum(statuses.get(k, 0) for k in ("stale_21_44", "stale_45_59", "stale_60_plus"))),
        ("Closed / other", statuses.get("closed", 0)),
        ("Verified dormant", statuses.get("verified_dormant", 0)),
    ]
    total = sum(n for _, n in segments)
    return {
        "available": total > 0,
        "total": total,
        "segments": [{"Process": "Tracked processes", "State": name, "Count": n}
                     for name, n in segments if n],
        "matured_unanswered": _count(metrics.get("matured_unanswered")),
        "ageing": segments[2][1],
        "engaged": segments[0][1],
        "closed": segments[3][1],
    }


def portfolio_insight(report: dict) -> dict:
    quality = report.get("quality_summary") or {}
    if not isinstance(quality, dict) or not quality:
        return {"available": False}
    eligible = _count(quality.get("analysis_eligible_sessions"))
    verified = _count(quality.get("evidence_verified_sessions"))
    intent = _count(quality.get("hiring_intent_sessions"))
    return {
        "available": True, "qualified": eligible,
        "verified": verified, "intent": intent,
        "observations": [
            {"Measure": "Qualified sessions", "Sessions": eligible},
            {"Measure": "Reached verified evidence", "Sessions": verified},
            {"Measure": "Hiring-intent events", "Sessions": intent},
        ],
        "interpretation": (
            "Qualified attention is recorded, but no on-site hiring-intent signal is verified."
            if eligible and not intent else
            "On-site hiring-intent signals are recorded; no visitor identity is established."
            if intent else
            "No qualified portfolio attention is recorded in the last 30 days."
        ),
    }


def market_demand_insight(report: dict) -> dict:
    signals = [s for s in report.get("signals") or [] if isinstance(s, dict)]
    by_key = {str(s.get("indicator_key")): s for s in signals}
    latest = by_key.get("jobtech_high_signal_target_ads_v1") or {}
    mtd = by_key.get("jobtech_high_signal_target_ads_mtd_v1") or {}
    value = _number(latest.get("metric_value"))
    delta = _number(latest.get("change_value"))
    bars = []
    insight = "Role-specific JobTech demand is not available."
    if value is not None and value >= 0 and latest.get("period_end"):
        month = date.fromisoformat(latest["period_end"])
        before = month.replace(day=1) - timedelta(days=1)
        if delta is not None and value - delta >= 0:
            previous = value - delta
            bars.append({
                "Period": before.strftime("%b %Y"), "Ads": int(previous),
                "Completeness": "Complete", "Sort": 1,
            })
            if previous > 0:
                pct = 100 * delta / previous
                insight = (
                    f"High-signal leadership ads {'rose' if delta > 0 else 'fell' if delta < 0 else 'held steady'} "
                    f"{abs(pct):.0f}% in {month:%B} vs {before:%B}."
                    if delta else f"High-signal leadership ads were unchanged in {month:%B}."
                )
            else:
                insight = "High-signal leadership ads have a new complete-month baseline."
        else:
            insight = "The most recent completed month has a verified demand observation."
        bars.append({
            "Period": month.strftime("%b %Y"), "Ads": int(value),
            "Completeness": "Complete", "Sort": 2,
        })
    mtd_value = _number(mtd.get("metric_value"))
    if mtd_value is not None and mtd_value >= 0 and mtd.get("period_end"):
        mtd_date = date.fromisoformat(mtd["period_end"])
        if not bars or mtd_date.strftime("%Y-%m") != latest.get("period_end", "")[:7]:
            bars.append({
                "Period": mtd_date.strftime("%b %Y") + " *",
                "Ads": int(mtd_value), "Completeness": "Partial", "Sort": 3,
            })
    return {
        "available": bool(bars),
        "bars": bars,
        "insight": insight,
        "partial_as_of": mtd.get("period_end") if len(bars) and
        bars[-1]["Completeness"] == "Partial" else None,
        "source": "JobTech high-signal AI/Data leadership title basket v1",
        "sector_outlook": [
            {"Sector": label, "Net outlook": int(n)}
            for key, label in (
                ("employment_outlook_services_consulting", "Services & consulting"),
                ("employment_outlook_it_tech", "IT & Tech"),
                ("employment_outlook_net_vgr", "Västra Götaland"),
            )
            if (n := _number(by_key.get(key, {}).get("metric_value"))) is not None
        ],
    }


def recent_recruitment_trend(report: dict, *, weeks: int = 8) -> list[dict]:
    """Dated inbound contact events; not an application-to-interview conversion rate."""
    rows = []
    for entry in report.get("weekly") or []:
        try:
            when = date.fromisoformat(str(entry["week"]))
        except (KeyError, TypeError, ValueError):
            continue
        rows.append({
            "Week": when.isoformat(),
            "Recorded contacts": _count(entry.get("responses")),
            "Applications": _count(entry.get("applications")),
        })
    return sorted(rows, key=lambda x: x["Week"])[-weeks:]


def _stack_chart(conversion: dict) -> alt.Chart:
    rows = [
        {"Group": "Dated applications", "Outcome": "Human response documented",
         "Processes": conversion["human"]},
        {"Group": "Dated applications", "Outcome": "No documented human response",
         "Processes": conversion["no_documented_human"]},
    ]
    return (alt.Chart(alt.Data(values=rows)).mark_bar(size=26, cornerRadiusEnd=3)
            .encode(x=alt.X("Processes:Q", title=None, stack="zero"),
                    y=alt.Y("Group:N", title=None, axis=None),
                    color=alt.Color("Outcome:N", title=None),
                    tooltip=["Outcome:N", alt.Tooltip("Processes:Q", format=",d")])
            .properties(height=85))


def _pipeline_chart(pipeline: dict) -> alt.Chart:
    return (alt.Chart(alt.Data(values=pipeline["segments"]))
            .mark_bar(size=26, cornerRadiusEnd=3)
            .encode(x=alt.X("Count:Q", title=None, stack="zero"),
                    y=alt.Y("Process:N", title=None, axis=None),
                    color=alt.Color("State:N", title=None),
                    tooltip=["State:N", alt.Tooltip("Count:Q", format=",d")])
            .properties(height=85))


def _contact_chart(weekly: list[dict]) -> alt.Chart:
    return (alt.Chart(alt.Data(values=weekly))
            .mark_line(point=alt.OverlayMarkDef(size=40), strokeWidth=2.5)
            .encode(x=alt.X("Week:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0)),
                    y=alt.Y("Recorded contacts:Q", title="Inbound/two-way contacts",
                            scale=alt.Scale(zero=True), axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip("Week:T", format="%d %b %Y"),
                             alt.Tooltip("Recorded contacts:Q", format=",d")])
            .properties(height=185))


def _market_chart(demand: dict) -> alt.Chart:
    return (alt.Chart(alt.Data(values=demand["bars"]))
            .mark_bar(cornerRadiusEnd=5)
            .encode(x=alt.X("Period:N", sort=alt.EncodingSortField(field="Sort", order="ascending"),
                            title=None),
                    y=alt.Y("Ads:Q", title="Headline-classified ads",
                            axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color("Completeness:N", title=None),
                    tooltip=["Period:N", "Completeness:N",
                             alt.Tooltip("Ads:Q", format=",d")])
            .properties(height=190))


def _portfolio_chart(portfolio: dict) -> alt.Chart:
    return (alt.Chart(alt.Data(values=portfolio["observations"]))
            .mark_bar(cornerRadiusEnd=5)
            .encode(y=alt.Y("Measure:N", sort=[
                        "Qualified sessions", "Reached verified evidence",
                        "Hiring-intent events"], title=None,
                        axis=alt.Axis(labelLimit=160)),
                    x=alt.X("Sessions:Q", title="Recorded sessions", axis=alt.Axis(tickMinStep=1)),
                    tooltip=["Measure:N", alt.Tooltip("Sessions:Q", format=",d")])
            .properties(height=185))


def render_public_overview_dashboard(
    results: dict, now: datetime, unavailable: list[str], navigate,
) -> None:
    """Render current public signal overview. Narrative is optional."""
    timing = results.get("timing") or {}
    conversion = conversion_insight(results.get("conversion") or {})
    pipeline = pipeline_insight(results.get("pipeline") or {})
    portfolio = portfolio_insight(results.get("hiring") or {})
    demand = market_demand_insight(results.get("market") or {})
    trend = recent_recruitment_trend(results.get("jobs") or {})
    rejections = results.get("rejections") or {}
    rejection_readout = rejection_overview_readout(rejections)

    st.title("Analytics overview")
    st.caption("Recruiting progress · hiring timing · AI/Data demand · portfolio evidence")

    # The timing scenario is the key user decision: always show it first.
    st.subheader("Hiring predictor")
    if timing.get("available"):
        with st.container(border=True):
            hero, offer, window = st.columns([1.5, 1, 1.15], gap="medium")
            with hero:
                st.caption("INDICATIVE FIRST DAY AT WORK")
                st.markdown(f"## {_display_date(timing['start_central'], compact=True)}")
            with offer:
                render_date_tile("Potential offer", timing["offer_central"])
            with window:
                render_date_tile("Possible start window",
                                 timing["start_earliest"],
                                 range_end=timing["start_latest"])
        st.caption(
            f"Conditional v2 scenario · assessed "
            f"{_display_date(timing['as_of'], compact=True)} · "
            "not a confirmed job or offer probability."
        )
        if timing.get("needs_refresh"):
            st.caption("Forecast is older than 14 days; awaiting an evidence refresh.")
    else:
        with st.container(border=True):
            st.markdown("**No current hiring-date scenario**")
            st.caption("A recent verified interview-stage forecast is not available.")
    if st.button("View hiring forecast", key="public_overview_predictions"):
        navigate("predictions")

    st.subheader("Where your search stands")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        with st.container(border=True):
            st.markdown("**Documented human-response conversion**")
            if conversion["available"]:
                st.markdown(f"### {conversion['observed_pct']:.1f}%")
                st.altair_chart(_stack_chart(conversion), width="stretch")
                st.caption(f"{conversion['human']} of {conversion['applications']} "
                           "dated applications · documented minimum")
                st.markdown(conversion["interpretation"])
            else:
                st.info("Matched-cohort response data is not reportable.")
    with col2:
        with st.container(border=True):
            st.markdown("**Pipeline uncertainty**")
            if pipeline["available"]:
                st.markdown(f"### {pipeline['ageing']} ageing processes")
                st.altair_chart(_pipeline_chart(pipeline), width="stretch")
                st.caption(f"{pipeline['engaged']} engaged · "
                           f"{pipeline['matured_unanswered']} mature unanswered · "
                           "silence is not rejection")
            else:
                st.info("Pipeline classifications are temporarily unavailable.")
    if st.button("Explore recruitment funnel and trends", key="public_overview_jobs"):
        navigate("jobs")

    st.subheader("Recruitment momentum")
    if trend:
        st.markdown("**Weekly documented recruiter contacts**")
        st.altair_chart(_contact_chart(trend), width="stretch")
        st.caption("Dated, recorded inbound/two-way contacts · independent of application volume.")
    else:
        st.caption("Contact trend awaits sufficient dated history.")

    left, right = st.columns(2, gap="medium")
    with left:
        st.subheader("Portfolio contribution")
        if portfolio["available"]:
            st.altair_chart(_portfolio_chart(portfolio), width="stretch")
            st.caption(portfolio["interpretation"])
        else:
            st.caption("Quality-filtered portfolio metrics are unavailable.")
        if st.button("Explore portfolio performance", key="public_overview_portfolio"):
            navigate("portfolio")
    with right:
        st.subheader("What the Swedish market is telling you")
        if demand["available"]:
            st.altair_chart(_market_chart(demand), width="stretch")
            st.caption(demand["insight"])
            if demand["partial_as_of"]:
                st.caption(f"* Partial month through {demand['partial_as_of']}; "
                           "not directly comparable with full months.")
        else:
            st.caption("Role-specific market-demand observations are unavailable.")
        if st.button("Explore Swedish market evidence", key="public_overview_market"):
            navigate("market")

    st.subheader("Rejection intelligence")
    if rejection_readout.get("status") == "ok":
        unknown_share = rejection_readout.get("unknown_share")
        if isinstance(unknown_share, (float, int)):
            st.progress(min(1., max(0., float(unknown_share))),
                        text=f"{unknown_share:.0%} of recorded rejection causes remain unknown")
        st.caption("No recurring candidate capability gap can be inferred from unexplained decisions.")
    else:
        st.caption("Rejection explanations are insufficient for a robust summary.")

    with st.expander("Recruitment conversion, pipeline & rejections · details",
                     expanded=False):
        from page_conversion_quality import render_public_conversion_quality
        from page_stale_applications import render_pipeline_health
        render_public_conversion_quality(compact=True)
        if results.get("pipeline"):
            render_pipeline_health(results["pipeline"], compact=True)
        if rejection_readout.get("status") == "ok":
            st.markdown("**Employer decision evidence**")
            st.markdown(rejection_readout["interpretation"])
            st.markdown("**Possible next move:** " + rejection_readout["action"])
            st.caption("Rejected, closed, and stale applications are different statuses; "
                       "application and decision counts use distinct cohorts.")
        else:
            st.caption(rejection_readout.get("message") or
                       "No validated rejection-cause interpretation.")
        st.caption("Interview evidence is privacy-thresholded on this public page. "
                   "Missing values are not zeros.")

    with st.expander("AI/Data market context & measurement", expanded=False):
        if demand["available"]:
            st.markdown("**Enterprise AI/Data advertised demand**")
            st.caption(demand["source"])
            st.caption(demand["insight"])
            if demand["sector_outlook"]:
                st.markdown("**Selected hiring-intention survey readings**")
                st.altair_chart(
                    alt.Chart(alt.Data(values=demand["sector_outlook"]))
                    .mark_bar(cornerRadiusEnd=5)
                    .encode(y=alt.Y("Sector:N", title=None),
                            x=alt.X("Net outlook:Q", title="Net employment outlook"),
                            tooltip=["Sector:N", "Net outlook:Q"])
                    .properties(height=160), width="stretch"
                )
                st.caption("Net employment outlook reflects stated recruitment "
                           "intentions, not hires or personal offer probability.")
        st.caption("JobTech tracks a consistent advertised-demand proxy, not the "
                   "whole Swedish job market. Small regional samples are noisy. "
                   "Stockholm vacancies are not automatically infeasible: "
                   "multi-office work, travel and relocation remain possible.")

    with st.expander("Forecast interpretation, portfolio attribution & data quality",
                     expanded=False):
        st.markdown("**Why the forecast is conditional**")
        st.caption("Hiring v2 uses verified recruiting stages and expected stage "
                   "durations. An offer and first day of work are separate events. "
                   "The model has not been validated against enough completed offers.")
        if portfolio.get("available"):
            st.caption(f"Portfolio, last 30 days: {portfolio['qualified']} qualified "
                       f"sessions; {portfolio['verified']} evidence views; "
                       f"{portfolio['intent']} hiring-intent event signals. "
                       "These are website observations, not identified recruiters.")
        st.caption("Application-date history, employer feedback and recruitment "
                   "correspondence remain owner-only. The public forecast exposes "
                   "only an explicitly published date projection.")
        st.caption(f"Checked {now:%d %b %Y at %H:%M} Stockholm · "
                   "refreshes approximately every ten minutes while the page is open.")
        if unavailable:
            st.warning("Unavailable inputs: " + ", ".join(unavailable) +
                       ". Missing values are not interpreted as zero.")
