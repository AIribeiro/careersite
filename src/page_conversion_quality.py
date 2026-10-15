"""Conversion-quality reporting: private exact cohort and public thresholded summary.

Counting unit is one linked employer-role process with a genuine original
application date. Unknown outcomes and stale silence never become rejections.
"""
from __future__ import annotations

import altair as alt
import streamlit as st

from site_analytics_public import fetch_public_analytics_rpc
from site_cms import _request_json, _rest_url

FAMILIES = {
    "A": "A · Enterprise AI leadership",
    "B": "B · Data & Analytics leadership",
    "C": "C · Governance & Automation",
    "U": "Unclassified / other",
    "All": "All verified-date applications",
}
MILESTONES = (
    ("human_responses", "Human reply or interview"),
    ("first_interviews", "First interview reached"),
    ("subsequent_interviews", "Subsequent interview reached"),
    ("verified_offers", "Verified offer"),
)
OUTCOMES = (
    ("employer_rejections", "Employer rejection"),
    ("other_closures", "Other / unreconciled closure"),
    ("stale_no_decision", "Stale · no decision"),
    ("no_decision_known", "No decision known"),
)


def _pct(num: object, den: object) -> str:
    if num is None or den is None or not int(den):
        return "Not reportable"
    return f"{100 * int(num) / int(den):.1f}%"


def _funnel_charts(rows: list[dict], *, private: bool) -> None:
    ordered = ("A", "B", "C")
    points = []
    for row in rows:
        key = row.get("job_family")
        if key not in ordered:
            continue
        for metric, label in MILESTONES:
            value = row.get(metric)
            if value is None:
                continue
            points.append({
                "Family": FAMILIES[key],
                "Milestone": label,
                "Rate": round(100 * int(value) / max(1, int(row.get("applications") or 0)), 1),
                "Processes": int(value),
                "Applications": int(row.get("applications") or 0),
            })
    if points:
        chart = (
            alt.Chart(alt.Data(values=points))
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("Family:N", title=None, sort=[FAMILIES[k] for k in ordered],
                        axis=alt.Axis(labelAngle=0, labelLimit=200)),
                xOffset=alt.XOffset("Milestone:N"),
                y=alt.Y("Rate:Q", title="Share of verified-date applications (%)",
                        scale=alt.Scale(domainMin=0)),
                color=alt.Color("Milestone:N", title="Verified milestone"),
                tooltip=[
                    alt.Tooltip("Family:N"),
                    alt.Tooltip("Milestone:N"),
                    alt.Tooltip("Rate:Q", format=".1f"),
                    alt.Tooltip("Processes:Q", format=",d"),
                    alt.Tooltip("Applications:Q", format=",d"),
                ],
            ).properties(height=300)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("Interview and offer rates are too sparse to publish by job family.")

    statuses = []
    for row in rows:
        key = row.get("job_family")
        if key not in ordered:
            continue
        applications = row.get("applications")
        if not applications:
            continue
        for field, label in OUTCOMES:
            if row.get(field) is None:
                continue
            statuses.append({
                "Family": FAMILIES[key],
                "Disposition": label,
                "Share": 100 * int(row[field]) / int(applications),
                "Processes": int(row[field]),
            })
    if statuses:
        st.markdown("**What happened to each application cohort**")
        chart = (
            alt.Chart(alt.Data(values=statuses))
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X("Share:Q", title="Share of applications (%)", stack="zero"),
                y=alt.Y("Family:N", title=None, sort=[FAMILIES[k] for k in ordered],
                        axis=alt.Axis(labelLimit=240)),
                color=alt.Color("Disposition:N", title="Evidence-based disposition"),
                tooltip=["Family:N", "Disposition:N",
                         alt.Tooltip("Share:Q", format=".1f"),
                         alt.Tooltip("Processes:Q", format=",d")],
            ).properties(height=225)
        )
        st.altair_chart(chart, width="stretch")
        if not private:
            st.caption("Suppressed small cohorts and cells leave gaps; displayed segments do not necessarily sum to 100%.")


def render_public_conversion_quality(*, compact: bool = False) -> None:
    try:
        report = fetch_public_analytics_rpc("careersite_public_conversion_quality_v1")
    except (RuntimeError, ValueError, PermissionError, TimeoutError):
        st.caption("Evidence-linked conversion quality is temporarily unavailable.")
        return
    if not report.get("available"):
        st.caption("Insufficient verified-date applications for a meaningful conversion cohort.")
        return
    totals = report.get("totals") or {}
    groups = report.get("families") or []
    if compact:
        st.subheader("Recruitment conversion quality")
    else:
        st.subheader("From applications to actual hiring progress")
    st.caption(
        "Tracked application cohorts since 1 June 2026, linked by employer and role. "
        "A human acknowledgement is not an ATS receipt; milestones are deduplicated "
        "per process. Low-frequency cells are suppressed on this public page."
    )
    human = totals.get("human_responses")
    apps = totals.get("applications")
    if human is not None and apps:
        st.markdown(
            f"**Observed meaningful response: {_pct(human, apps)}** "
            f"({human} documented processes from {apps} dated applications). "
            "This is a documented minimum, not the final probability of receiving an interview."
        )
    else:
        st.caption("The human-response rate is not yet reportable in the anonymous aggregate.")

    stale = totals.get("stale_no_decision")
    rejected = totals.get("employer_rejections")
    if stale is not None and apps:
        st.markdown(
            f"**Pipeline uncertainty:** {stale} applications are stale with no "
            "confirmed employer decision. They are not counted as rejections."
        )
    if rejected is not None:
        st.caption(
            f"{rejected} applications in this original-date cohort match explicit "
            "employer rejection evidence. This is not the completed-cohort rejection rate."
        )
    if compact:
        st.caption("Compare the three job families and subsequent interviews in Job search → Funnel & conversion.")
        return

    _funnel_charts(groups, private=False)
    if any(row.get("job_family") == "C" and row.get("applications") is None for row in groups):
        st.caption("Tier C currently has fewer than 20 dated processes and is not disclosed separately in the public chart.")
    st.caption(
        "Application date assumptions are excluded from rates. Small cells below "
        "10 milestones are withheld, including low-frequency interviews and offers. "
        "A blank value is not a zero. Employer-role matching may combine repeat requisitions; "
        "unclassified roles remain outside the three-family comparison."
    )
    with st.expander("Data completeness and counting rules"):
        st.write(
            f"{report.get('dates_excluded', 0)} tracked processes lack an original "
            "verified date and are excluded from this cohort; assumed dates are for "
            "planning only. Public reporting requires at least 20 applications per "
            "family and at least 10 instances per milestone."
        )
        st.write(
            "First interview means a recorded invitation, confirmed scheduling or "
            "completed conversation. Subsequent interview requires explicit second-or-"
            "later-stage evidence. An offer requires a recorded offer, not a forecast. "
            "Automated receipts, employer views and candidate-initiated follow-ups "
            "are not human responses. Rejection requires a matched employer decision."
        )


def render_private_conversion_quality(token: str, *, compact: bool = False) -> None:
    try:
        report = _request_json(
            "POST", _rest_url("rpc/careersite_owner_conversion_quality_v1"),
            token=token, payload={},
        )
    except (RuntimeError, ValueError, PermissionError, TimeoutError):
        st.warning("The owner-only conversion-quality report is unavailable.")
        return
    if not isinstance(report, dict):
        st.warning("Unexpected conversion-quality reporting response.")
        return
    rows = report.get("families") or []
    overview = next((r for r in rows if r.get("job_family") == "All"), None)
    if not overview:
        st.info("No verified-date application cohort is available.")
        return
    st.subheader("Conversion quality · verified hiring milestones")
    apps = int(overview["applications"])
    human = int(overview["human_responses"])
    first = int(overview["first_interviews"])
    later = int(overview["subsequent_interviews"])
    offers = int(overview["verified_offers"])
    st.markdown(
        f"**{human} of {apps} dated application processes generated a documented human "
        f"response or interview ({_pct(human, apps)}).** "
        f"{first} reached a first interview, {later} reached a subsequent interview, "
        f"and {offers} have a verified offer."
    )
    st.caption(
        f"Evidence completeness: {report.get('all_tracked_processes')} tracked processes, "
        f"{report.get('excluded_not_originally_dated')} without an original date "
        f"({report.get('assumed_application_dates')} use a planning assumption). "
        "Do not equate missing stage evidence with an employer's lack of interest."
    )

    family = [r for r in rows if r.get("job_family") in ("A", "B", "C")]
    _funnel_charts(family, private=True)
    eligible = [r for r in family if int(r.get("human_responses", 0)) >= 10
                and int(r.get("applications", 0)) >= 30]
    if len(eligible) < 2:
        st.info(
            "No defensible ranking of the three job families yet: fewer than two "
            "families have 10 documented human responses and at least 30 dated applications. "
            "Treat observed differences as directional, not as established market effects."
        )
    else:
        leader = max(eligible, key=lambda x: x["human_response_pct"])
        st.caption(f"Strongest observed human-response share among adequately recorded "
                   f"families: {FAMILIES[leader['job_family']]} "
                   f"({_pct(leader['human_responses'], leader['applications'])}). "
                   "This is descriptive, not causal.")
    if not compact:
        with st.expander("Exact cohort reconciliation · owner only"):
            rows_out = []
            for x in rows:
                rows_out.append({
                    "Family": FAMILIES.get(x["job_family"], x["job_family"]),
                    "Dated applications": x["applications"],
                    "Human responses": x["human_responses"],
                    "Response rate": _pct(x["human_responses"], x["applications"]),
                    "First interviews": x["first_interviews"],
                    "Later interviews": x["subsequent_interviews"],
                    "Verified offers": x["verified_offers"],
                    "Explicit rejections": x["employer_rejections"],
                    "Other closures": x["other_closures"],
                    "Stale, unknown decision": x["stale_no_decision"],
                    "Other unresolved": x["no_decision_known"],
                })
            st.dataframe(rows_out, hide_index=True, width="stretch")
            st.caption(
                "Status classes are mutually exclusive. Stale means no confirmed "
                "decision and is not a rejection. Direct human replies and "
                "interview-derived human contact are disclosed separately only "
                "in the owner dataset. Original application dates determine cohort "
                "membership; more complete records may revise these lower bounds."
            )
