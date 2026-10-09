"""Readable, owner-only trend signals for the private Job Search Analytics page."""
from __future__ import annotations

import altair as alt
import streamlit as st

from job_search_trends import SERIES, analyze_trends


PALETTE = ["#527bd9", "#22b8b0", "#b98a45", "#b46e69"]


def _movement(now: int, before: int | None) -> str:
    if before is None:
        return "No comparable baseline"
    difference = now - before
    return f"{difference:+,} vs preceding 28d" if difference else "No change vs preceding 28d"


def _summary(trends: dict) -> None:
    recent, before = trends["recent"], trends["previous"]
    comparable = trends["baseline_available"] and trends["current_complete"]
    limited = (trends["coverage"]["previous_dated"] or 0) < 5
    if not comparable:
        st.info("Select at least 56 days of activity to compare two complete 28-day periods. The current window remains visible.")
    elif limited:
        st.info("The earlier 28-day period contains fewer than five dated records. Treat large changes as a coverage signal, not proof that market response has improved or declined.")

    columns = st.columns(4)
    for col, label in zip(columns, SERIES):
        current = recent[label]
        previous = before[label] if comparable and before is not None else None
        col.metric(
            label,
            current,
            delta=_movement(current, previous) if previous is not None else None,
            delta_color="off",
            help="Distinct, exact employer + role processes with dated, deduplicated evidence within the period. One process counts once per measure and period.",
        )
    st.caption(
        f"Recent window: {max(trends['recent_start'], trends['selected_start']).isoformat()}–{trends['selected_end'].isoformat()}"
        + (f" · Previous: {trends['previous_start'].isoformat()}–{trends['previous_end'].isoformat()}" if comparable else "")
        + ". These are activity counts, not application-to-interview conversion rates. Events may concern applications submitted earlier."
    )

    if not comparable:
        return
    signal_lines = []
    for name, plain in (
        (SERIES[0], "Dated applications"),
        (SERIES[1], "Inbound or two-way contacts"),
        (SERIES[2], "Completed interviews"),
    ):
        current, prior = recent[name], before[name]
        if current == prior:
            signal_lines.append(f"**{plain}:** unchanged at {current} distinct processes.")
        else:
            verb = "increased" if current > prior else "decreased"
            signal_lines.append(f"**{plain}:** {verb} from {prior} to {current} distinct processes.")
    st.markdown("  \n".join(signal_lines))
    if limited:
        st.caption("Interpretation confidence: limited by the earlier period's sparse dated evidence and potential differences in import coverage.")


def _history(trends: dict) -> None:
    st.subheader("Recorded movement over time")
    st.caption("Separate the volume of submissions from two-way engagement, completed interviews and explicit decisions. Zeroes represent no matching dated records, not verified inactivity.")
    cadence = st.segmented_control(
        "Trend grouping", ["Week", "Month"], default="Week",
        key="job_trends_granularity",
    ) or "Week"
    values = trends["weekly" if cadence == "Week" else "monthly"]
    if not values:
        st.info("No dated, linkable process evidence in this activity window.")
        return
    chart = alt.Chart(alt.Data(values=values)).mark_line(
        point=alt.OverlayMarkDef(size=55, filled=True), strokeWidth=2.7
    ).encode(
        x=alt.X("Date:T", title=f"{cadence} starting", axis=alt.Axis(format="%b %d" if cadence == "Week" else "%b %Y")),
        y=alt.Y("Processes:Q", title="Distinct processes", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("Measure:N", sort=list(SERIES), scale=alt.Scale(domain=list(SERIES), range=PALETTE)),
        tooltip=[alt.Tooltip("Date:T", title="Period begins", format="%d %b %Y"), "Measure:N", "Processes:Q"],
    ).properties(height=355)
    st.altair_chart(chart, width="stretch")
    st.caption("A process may appear in multiple stages and multiple periods. Dated status flags on earlier application events are not treated as later rejection events; the most recent period may be incomplete.")


def _matured_cohorts(trends: dict) -> None:
    cohort = trends["cohorts"]
    st.subheader("Are applications producing conversations and interviews?")
    st.caption(
        "28-day outcome window by application month. Only linked processes with an application at least 28 days old are measured. "
        "Contacts require recorded inbound/two-way evidence; interviews require explicit held/completed evidence. "
        "This follows each application for the same number of days rather than crediting future activity to the month in which it occurred."
    )
    a, b, c = st.columns(3)
    a.metric("Applications with 28-day follow-up", cohort["matured"])
    b.metric("Reached contact within 28d", f"{cohort['contacted']}/{cohort['matured']}" if cohort["matured"] else "—")
    c.metric("Completed interview within 28d", f"{cohort['interviewed']}/{cohort['matured']}" if cohort["matured"] else "—")
    if cohort["pending"]:
        st.caption(f"{cohort['pending']} newer application process(es) excluded from conversion calculations until they reach 28 days.")
    if not cohort["matured"]:
        st.info("No application cohort is old enough for a comparable 28-day outcome measure.")
        return

    rows = [r for r in cohort["rows"] if r["Matured"]]
    long = []
    for r in rows:
        for label, key, numerator in (
            ("Contact rate", "Contact %", "Contact within 28d"),
            ("Interview rate", "Interview %", "Interview within 28d"),
        ):
            long.append({
                "Month": r["Month"],
                "Outcome": label,
                "Rate": r[key],
                "Observed": r[numerator],
                "Matured": r["Matured"],
            })
    chart = alt.Chart(alt.Data(values=long)).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("Month:T", title="Application month", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("Rate:Q", title="Observed within 28 days (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Outcome:N", scale=alt.Scale(domain=["Contact rate", "Interview rate"], range=PALETTE[:2])),
        tooltip=["Month:T", "Outcome:N", alt.Tooltip("Rate:Q", format=".1f"), "Observed:Q", "Matured:Q"],
    ).properties(height=300)
    st.altair_chart(chart, width="stretch")
    st.dataframe(cohort["rows"], hide_index=True, width="stretch", column_config={
        "Contact %": st.column_config.NumberColumn("Contact %", format="%.1f%%"),
        "Interview %": st.column_config.NumberColumn("Interview %", format="%.1f%%"),
    })
    if any(r["Matured"] < 5 for r in rows):
        st.caption("Some monthly cohorts contain fewer than five mature applications. Percentages are descriptive and may move sharply after a single contact or interview.")
    st.caption("A missing interaction is not evidence of employer rejection. Process linking uses exact employer/role normalization; repeat vacancies or aliases may need manual reconciliation.")


def _official_changes(trends: dict) -> None:
    snapshots = trends["snapshots"]
    if snapshots is None:
        st.caption("Official snapshot changes are portfolio-wide and are not displayed under an employer filter.")
        return
    if not snapshots["current_date"]:
        st.info("No official snapshots available as of the selected end date.")
        return
    st.subheader("Official search totals: latest movement")
    if snapshots["previous_date"]:
        st.caption(f"Latest official snapshot: {snapshots['current_date']} · Previous: {snapshots['previous_date']}. These figures cover the entire search and are separate from the event trend charts.")
    else:
        st.caption(f"Official totals as of {snapshots['current_date']}. A second snapshot is needed to calculate movement.")
    columns = st.columns(3)
    for col, item in zip(columns, snapshots["metrics"]):
        value = item["Current"]
        delta = item["Delta"]
        col.metric(
            item["Label"], f"{value:,}" if value is not None else "—",
            delta=f"{delta:+,} since prior snapshot" if delta is not None else None,
            delta_color="off",
        )
    st.caption("Active / unresolved is a conservative working remainder, not proof of an active recruiter conversation. Negative decisions and applications are cumulative accounting totals, not period-specific event rates.")


def render_job_search_trends(records, start, end, employer: str) -> None:
    """The first reporting tab: trends before detailed audits and diagnostics."""
    trends = analyze_trends(records, start, end, employer)
    trends["selected_start"], trends["selected_end"] = start, end
    st.subheader("What is changing in the job search?")
    st.caption("Compare documented, distinct hiring processes in two equal 28-day windows; see whether applications are turning into conversations, not just growing in number.")
    _summary(trends)
    st.divider()
    _history(trends)
    st.divider()
    _matured_cohorts(trends)
    st.divider()
    _official_changes(trends)
    coverage = trends["coverage"]
    with st.expander("Trend evidence and coverage"):
        st.write(
            f"{coverage['linked_dated']} of {coverage['all_dated']} dated primary event records are linkable to a specific employer and role. "
            f"{coverage['undated']} canonical records have no event date and are omitted from time-series comparisons."
        )
        st.write("The charts are drawn from canonical event history. Snapshot totals, secondary workbook representations and narrative rows are never added to those counts.")
